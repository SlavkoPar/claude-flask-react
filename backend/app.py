import os
import ssl
import urllib3
import sqlite3
from flask import Flask, request, jsonify, Response, stream_with_context, session, redirect
from flask_cors import CORS
from anthropic import Anthropic
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth
from database.db import (
    get_db,
    init_db,
    seed_db,
    seed_groups,
    seed_questions,
    seed_answers,
    seed_question_answers,
    get_or_create_google_user,
    get_groups,
    get_group_options,
    get_group,
    create_group,
    update_group,
    delete_group,
    get_questions,
    get_question,
    create_question,
    update_question,
    delete_question,
    get_answers,
    get_answer,
    create_answer,
    update_answer,
    delete_answer,
    get_assigned_answers,
    get_unassigned_answers,
    assign_answer,
    unassign_answer,
    search_questions,
    get_candidate_answers,
    mark_answer_fixed,
    mark_answer_not_fixed,
)

load_dotenv()


ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

CORS(app, supports_credentials=True, origins=[FRONTEND_URL])

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = os.environ.get("MODEL", "claude-sonnet-4-6")

oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

GOOGLE_REDIRECT_URI = f"{FRONTEND_URL}/auth/google/callback"

with app.app_context():
    init_db()
    seed_db()
    seed_groups()
    seed_questions()
    seed_answers()
    seed_question_answers()


# ── Google OAuth ──────────────────────────────────────────────────────────────

@app.route("/auth/google")
def google_login():
    return google.authorize_redirect(GOOGLE_REDIRECT_URI)


@app.route("/auth/google/callback")
def google_callback():
    token = google.authorize_access_token()
    user_info = token.get("userinfo")
    user = get_or_create_google_user(
        name=user_info["name"],
        email=user_info["email"],
        google_id=user_info["sub"],
    )
    session["user_id"] = user["id"]
    return redirect(FRONTEND_URL)


# ── Auth API ──────────────────────────────────────────────────────────────────

@app.route("/api/auth/me")
def auth_me():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"user": None}), 401
    conn = get_db()
    row = conn.execute(
        "SELECT id, name, email FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    if not row:
        return jsonify({"user": None}), 401
    return jsonify({"user": dict(row)})


@app.route("/api/auth/logout", methods=["POST"])
def auth_logout():
    session.clear()
    return jsonify({"ok": True})


# ── Groups ────────────────────────────────────────────────────────────────────

def _current_user_id():
    return session.get("user_id")


def _parse_group_payload(data):
    """Validate a group create/update payload. Returns (values, error) where
    error is a message string, or (values, None) on success."""
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip() or None
    raw_parent_id = data.get("parent_id")
    values = {"name": name, "description": description, "parent_id": raw_parent_id}

    if not name:
        return values, "Name is required"

    parent_id = None
    if raw_parent_id not in (None, "", "null"):
        try:
            parent_id = int(raw_parent_id)
        except (TypeError, ValueError):
            return values, "Invalid parent group"
        if not get_group(parent_id):
            return values, "Parent group does not exist"

    return {"name": name, "description": description, "parent_id": parent_id}, None


@app.route("/api/groups")
def groups_list():
    if not _current_user_id():
        return jsonify({"error": "Not authenticated"}), 401
    parent_id = request.args.get("parent_id")
    parent_id = int(parent_id) if parent_id not in (None, "", "null") else None
    name = request.args.get("name") or None
    return jsonify(get_groups(parent_id=parent_id, name=name))


@app.route("/api/groups/options")
def groups_options():
    if not _current_user_id():
        return jsonify({"error": "Not authenticated"}), 401
    return jsonify(get_group_options())


@app.route("/api/groups/<int:group_id>")
def groups_get(group_id):
    if not _current_user_id():
        return jsonify({"error": "Not authenticated"}), 401
    group = get_group(group_id)
    if not group:
        return jsonify({"error": "Group not found"}), 404
    return jsonify(group)


@app.route("/api/groups", methods=["POST"])
def groups_create():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    data = request.get_json(force=True) or {}
    values, error = _parse_group_payload(data)
    if error:
        return jsonify({"error": error, "values": values}), 400
    group_id = create_group(user_id, values["name"], values["parent_id"], values["description"])
    return jsonify(get_group(group_id)), 201


@app.route("/api/groups/<int:group_id>", methods=["PUT"])
def groups_update(group_id):
    if not _current_user_id():
        return jsonify({"error": "Not authenticated"}), 401
    if not get_group(group_id):
        return jsonify({"error": "Group not found"}), 404
    data = request.get_json(force=True) or {}
    values, error = _parse_group_payload(data)
    if error:
        return jsonify({"error": error, "values": values}), 400
    update_group(group_id, values["name"], values["parent_id"], values["description"])
    return jsonify(get_group(group_id))


@app.route("/api/groups/<int:group_id>", methods=["DELETE"])
def groups_delete(group_id):
    if not _current_user_id():
        return jsonify({"error": "Not authenticated"}), 401
    if not get_group(group_id):
        return jsonify({"error": "Group not found"}), 404
    try:
        delete_group(group_id)
    except sqlite3.IntegrityError:
        return jsonify({"error": "Cannot delete a group that still has child groups or questions"}), 400
    return jsonify({"ok": True})


# ── Questions ─────────────────────────────────────────────────────────────────

def _parse_question_payload(data):
    """Validate a question create/update payload. Returns (values, error)."""
    text = (data.get("text") or "").strip()
    description = (data.get("description") or "").strip() or None
    values = {"text": text, "description": description}

    if not text:
        return values, "Text is required"

    return values, None


@app.route("/api/questions")
def questions_list():
    if not _current_user_id():
        return jsonify({"error": "Not authenticated"}), 401
    group_id = request.args.get("group_id")
    if not group_id:
        return jsonify({"error": "group_id is required"}), 400
    return jsonify(get_questions(int(group_id)))


@app.route("/api/questions", methods=["POST"])
def questions_create():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    data = request.get_json(force=True) or {}
    group_id = data.get("group_id")
    if not group_id or not get_group(int(group_id)):
        return jsonify({"error": "Group does not exist"}), 400
    values, error = _parse_question_payload(data)
    if error:
        return jsonify({"error": error, "values": values}), 400
    question_id = create_question(user_id, int(group_id), values["text"], values["description"])
    return jsonify(get_question(question_id)), 201


@app.route("/api/questions/<int:question_id>", methods=["PUT"])
def questions_update(question_id):
    if not _current_user_id():
        return jsonify({"error": "Not authenticated"}), 401
    if not get_question(question_id):
        return jsonify({"error": "Question not found"}), 404
    data = request.get_json(force=True) or {}
    values, error = _parse_question_payload(data)
    if error:
        return jsonify({"error": error, "values": values}), 400
    update_question(question_id, values["text"], values["description"])
    return jsonify(get_question(question_id))


@app.route("/api/questions/<int:question_id>", methods=["DELETE"])
def questions_delete(question_id):
    if not _current_user_id():
        return jsonify({"error": "Not authenticated"}), 401
    if not get_question(question_id):
        return jsonify({"error": "Question not found"}), 404
    delete_question(question_id)
    return jsonify({"ok": True})


# ── Answers ───────────────────────────────────────────────────────────────────

def _parse_answer_payload(data):
    """Validate an answer create/update payload. Returns (values, error)."""
    short_desc = (data.get("short_desc") or "").strip()
    description = (data.get("description") or "").strip() or None
    link = (data.get("link") or "").strip() or None
    values = {"short_desc": short_desc, "description": description, "link": link}

    if not short_desc:
        return values, "Short description is required"

    return values, None


@app.route("/api/answers")
def answers_list():
    if not _current_user_id():
        return jsonify({"error": "Not authenticated"}), 401
    name = request.args.get("name") or None
    return jsonify(get_answers(name=name))


@app.route("/api/answers/<int:answer_id>")
def answers_get(answer_id):
    if not _current_user_id():
        return jsonify({"error": "Not authenticated"}), 401
    answer = get_answer(answer_id)
    if not answer:
        return jsonify({"error": "Answer not found"}), 404
    return jsonify(answer)


@app.route("/api/answers", methods=["POST"])
def answers_create():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    data = request.get_json(force=True) or {}
    values, error = _parse_answer_payload(data)
    if error:
        return jsonify({"error": error, "values": values}), 400
    answer_id = create_answer(user_id, values["short_desc"], values["description"], values["link"])
    return jsonify(get_answer(answer_id)), 201


@app.route("/api/answers/<int:answer_id>", methods=["PUT"])
def answers_update(answer_id):
    if not _current_user_id():
        return jsonify({"error": "Not authenticated"}), 401
    if not get_answer(answer_id):
        return jsonify({"error": "Answer not found"}), 404
    data = request.get_json(force=True) or {}
    values, error = _parse_answer_payload(data)
    if error:
        return jsonify({"error": error, "values": values}), 400
    update_answer(answer_id, values["short_desc"], values["description"], values["link"])
    return jsonify(get_answer(answer_id))


@app.route("/api/answers/<int:answer_id>", methods=["DELETE"])
def answers_delete(answer_id):
    if not _current_user_id():
        return jsonify({"error": "Not authenticated"}), 401
    if not get_answer(answer_id):
        return jsonify({"error": "Answer not found"}), 404
    try:
        delete_answer(answer_id)
    except sqlite3.IntegrityError:
        return jsonify({"error": "Cannot delete an answer that is still assigned to questions"}), 400
    return jsonify({"ok": True})


# ── Question <-> Answer assignment ────────────────────────────────────────────

@app.route("/api/questions/<int:question_id>/answers")
def question_assigned_answers(question_id):
    if not _current_user_id():
        return jsonify({"error": "Not authenticated"}), 401
    if not get_question(question_id):
        return jsonify({"error": "Question not found"}), 404
    return jsonify(get_assigned_answers(question_id))


@app.route("/api/questions/<int:question_id>/answers/unassigned")
def question_unassigned_answers(question_id):
    if not _current_user_id():
        return jsonify({"error": "Not authenticated"}), 401
    if not get_question(question_id):
        return jsonify({"error": "Question not found"}), 404
    name = request.args.get("name") or None
    return jsonify(get_unassigned_answers(question_id, name=name))


@app.route("/api/questions/<int:question_id>/answers/assign", methods=["POST"])
def question_answers_assign(question_id):
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    if not get_question(question_id):
        return jsonify({"error": "Question not found"}), 404
    data = request.get_json(force=True) or {}
    answer_id = data.get("answer_id")
    if not answer_id or not get_answer(int(answer_id)):
        return jsonify({"error": "Answer does not exist"}), 400
    assign_answer(user_id, question_id, int(answer_id))
    return jsonify(get_question(question_id)), 201


@app.route("/api/questions/<int:question_id>/answers/<int:answer_id>/unassign", methods=["POST"])
def question_answers_unassign(question_id, answer_id):
    if not _current_user_id():
        return jsonify({"error": "Not authenticated"}), 401
    if not get_question(question_id):
        return jsonify({"error": "Question not found"}), 404
    unassign_answer(question_id, answer_id)
    return jsonify(get_question(question_id))


# ── Sidebar: question search, candidate answers, fixed/not-fixed ─────────────

@app.route("/api/questions/search")
def questions_search():
    if not _current_user_id():
        return jsonify({"error": "Not authenticated"}), 401
    q = request.args.get("q") or ""
    if not q:
        return jsonify([])
    return jsonify(search_questions(q))


@app.route("/api/questions/<int:question_id>/candidate-answers")
def questions_candidate_answers(question_id):
    if not _current_user_id():
        return jsonify({"error": "Not authenticated"}), 401
    if not get_question(question_id):
        return jsonify({"error": "Question not found"}), 404
    return jsonify(get_candidate_answers(question_id))


@app.route("/api/questions/<int:question_id>/answers/<int:answer_id>/fixed", methods=["POST"])
def questions_answer_fixed(question_id, answer_id):
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    if not get_question(question_id):
        return jsonify({"error": "Question not found"}), 404
    if not get_answer(answer_id):
        return jsonify({"error": "Answer not found"}), 404
    mark_answer_fixed(user_id, question_id, answer_id)
    return jsonify({"ok": True})


@app.route("/api/questions/<int:question_id>/answers/<int:answer_id>/not-fixed", methods=["POST"])
def questions_answer_not_fixed(question_id, answer_id):
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    if not get_question(question_id):
        return jsonify({"error": "Question not found"}), 404
    if not get_answer(answer_id):
        return jsonify({"error": "Answer not found"}), 404
    mark_answer_not_fixed(user_id, question_id, answer_id)
    return jsonify({"ok": True})


# ── Chat ──────────────────────────────────────────────────────────────────────

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True) or {}
    messages = data.get("messages", [])
    if not messages:
        return jsonify({"error": "messages is required"}), 400
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            messages=messages,
        )
        text = "".join(
            block.text for block in response.content if block.type == "text"
        )
        return jsonify({"reply": text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat/stream", methods=["POST"])
def chat_stream():
    data = request.get_json(force=True) or {}
    messages = data.get("messages", [])
    if not messages:
        return jsonify({"error": "messages is required"}), 400

    def generate():
        with client.messages.stream(
            model=MODEL,
            max_tokens=1024,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text

    return Response(stream_with_context(generate()), mimetype="text/plain")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
