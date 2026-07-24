import io
import json
import logging
import os
import ssl
import urllib3
import sqlite3
from flask import Flask, request, jsonify, Response, stream_with_context, session, redirect, send_file
from flask_cors import CORS
from anthropic import Anthropic
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth
from werkzeug.security import check_password_hash
from database.db import (
    get_db,
    init_db,
    seed_db,
    get_user_by_email,
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
    create_question_from_filter,
    backfill_question_embeddings,
    update_question,
    delete_question,
    get_answers,
    get_answer,
    create_answer,
    update_answer,
    delete_answer,
    backfill_answer_embeddings,
    get_assigned_answers,
    get_unassigned_answers,
    assign_answer,
    unassign_answer,
    search_questions,
    get_candidate_answers,
    mark_answer_fixed,
    mark_answer_not_fixed,
    seed_documents,
    backfill_document_groups,
    backfill_document_embeddings,
    get_documents,
    get_document,
    get_document_pdf,
    create_document,
    update_document,
    delete_document,
    search_documents,
)
from pypdf import PdfReader
from scripts.clean_db import main as clean_db_main

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()


ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
# In production, frontend and backend live on different *.onrender.com subdomains —
# each counts as its own "site", so the session cookie needs SameSite=None to be sent
# on cross-site fetches. SameSite=None requires Secure, which in turn requires HTTPS,
# so both must flip together with FLASK_ENV (Secure cookies are dropped over local http).
IS_PRODUCTION = os.environ.get("FLASK_ENV") == "production"
app.config.update(
    SESSION_COOKIE_SAMESITE="None" if IS_PRODUCTION else "Lax",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=IS_PRODUCTION,
)

# CORS(app, supports_credentials=True, origins=[FRONTEND_URL])
# This explicitly allows your React application domain
CORS(app, resources={r"/api/*": {"origins": FRONTEND_URL}}, supports_credentials=True)


# client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
# MODEL = os.environ.get("MODEL", "claude-sonnet-4-6")

oauth = OAuth(app)
logger.info("GOOGLE_CLIENT_ID=%s", os.environ.get("GOOGLE_CLIENT_ID"))
logger.info("GOOGLE_CLIENT_SECRET=%s", os.environ.get("GOOGLE_CLIENT_SECRET"))
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
    # seed_groups()
    # seed_questions()
    # seed_answers()
    # seed_question_answers()
    # seed_documents()
    # backfill_document_groups()
    # backfill_document_embeddings()
    # backfill_answer_embeddings()
    # backfill_question_embeddings()


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

@app.route("/api/auth/demo-login", methods=["POST"])
def demo_login():
    user = get_user_by_email("demo@my.com")
    if not user or not check_password_hash(user["password_hash"], "demo123"):
        return jsonify({"error": "Demo user not available"}), 401
    session["user_id"] = user["id"]
    return jsonify({"user": {"id": user["id"], "name": user["name"], "email": user["email"]}})


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
    try:
        group_id = create_group(user_id, values["name"], values["parent_id"], values["description"])
    except sqlite3.IntegrityError:
        return jsonify({"error": "A group with this name already exists under the same parent", "values": values}), 400
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
    try:
        update_group(group_id, values["name"], values["parent_id"], values["description"])
    except sqlite3.IntegrityError:
        return jsonify({"error": "A group with this name already exists under the same parent", "values": values}), 400
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
    try:
        question_id = create_question(user_id, int(group_id), values["text"], values["description"])
    except sqlite3.IntegrityError:
        return jsonify({"error": "A question with this text already exists", "values": values}), 400
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
    try:
        update_question(question_id, values["text"], values["description"])
    except sqlite3.IntegrityError:
        return jsonify({"error": "A question with this text already exists", "values": values}), 400
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
    try:
        answer_id = create_answer(user_id, values["short_desc"], values["description"], values["link"])
    except sqlite3.IntegrityError:
        return jsonify({"error": "An answer with this short description already exists", "values": values}), 400
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
    try:
        update_answer(answer_id, values["short_desc"], values["description"], values["link"])
    except sqlite3.IntegrityError:
        return jsonify({"error": "An answer with this short description already exists", "values": values}), 400
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


# ── Documents ─────────────────────────────────────────────────────────────────

def _parse_document_payload(data):
    """Validate a document create/update payload. Returns (values, error)."""
    description = (data.get("description") or "").strip()
    content = (data.get("content") or "").strip()
    link = (data.get("link") or "").strip() or None
    raw_group_id = data.get("group_id")
    values = {"description": description, "content": content, "link": link, "group_id": raw_group_id}

    if not description:
        return values, "Description is required"
    if not content:
        return values, "Content is required"

    group_id = None
    if raw_group_id not in (None, "", "null"):
        try:
            group_id = int(raw_group_id)
        except (TypeError, ValueError):
            return values, "Invalid group"
    if not group_id or not get_group(group_id):
        return values, "Group is required"

    return {"description": description, "content": content, "link": link, "group_id": group_id}, None


@app.route("/api/documents")
def documents_list():
    if not _current_user_id():
        return jsonify({"error": "Not authenticated"}), 401
    name = request.args.get("name") or None
    group_id = request.args.get("group_id")
    group_id = int(group_id) if group_id not in (None, "", "null") else None
    return jsonify(get_documents(name=name, group_id=group_id))


@app.route("/api/documents/search")
def documents_search():
    if not _current_user_id():
        return jsonify({"error": "Not authenticated"}), 401
    q = request.args.get("q") or ""
    if not q:
        return jsonify([])
    return jsonify(search_documents(q))


@app.route("/api/documents/<int:document_id>")
def documents_get(document_id):
    if not _current_user_id():
        return jsonify({"error": "Not authenticated"}), 401
    document = get_document(document_id)
    if not document:
        return jsonify({"error": "Document not found"}), 404
    return jsonify(document)


def _read_pdf_upload():
    file = request.files.get("file")
    if not file or not file.filename:
        return None, None
    return file.filename, file.read()


@app.route("/api/documents", methods=["POST"])
def documents_create():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    values, error = _parse_document_payload(request.form)
    if error:
        return jsonify({"error": error, "values": values}), 400
    pdf_filename, pdf_data = _read_pdf_upload()
    document_id = create_document(
        user_id, values["group_id"], values["description"], values["content"], values["link"],
        pdf_filename, pdf_data,
    )
    return jsonify(get_document(document_id)), 201


@app.route("/api/documents/<int:document_id>", methods=["PUT"])
def documents_update(document_id):
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    document = get_document(document_id)
    if not document:
        return jsonify({"error": "Document not found"}), 404
    if document["user_id"] != user_id:
        return jsonify({"error": "Only the creator can modify this document"}), 403
    values, error = _parse_document_payload(request.form)
    if error:
        return jsonify({"error": error, "values": values}), 400
    pdf_filename, pdf_data = _read_pdf_upload()
    update_document(
        document_id, values["group_id"], values["description"], values["content"], values["link"],
        pdf_filename, pdf_data,
    )
    return jsonify(get_document(document_id))


@app.route("/api/documents/<int:document_id>", methods=["DELETE"])
def documents_delete(document_id):
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    document = get_document(document_id)
    if not document:
        return jsonify({"error": "Document not found"}), 404
    if document["user_id"] != user_id:
        return jsonify({"error": "Only the creator can delete this document"}), 403
    delete_document(document_id)
    return jsonify({"ok": True})


@app.route("/api/documents/extract-pdf", methods=["POST"])
def documents_extract_pdf():
    if not _current_user_id():
        return jsonify({"error": "Not authenticated"}), 401
    file = request.files.get("file")
    if not file or not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "A PDF file is required"}), 400
    try:
        reader = PdfReader(file.stream)
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception:
        return jsonify({"error": "Could not read PDF file"}), 400
    content = json.dumps({"filename": file.filename, "pages": pages}, ensure_ascii=False)
    return jsonify({"content": content})


@app.route("/api/documents/<int:document_id>/pdf")
def documents_get_pdf(document_id):
    if not _current_user_id():
        return jsonify({"error": "Not authenticated"}), 401
    if not get_document(document_id):
        return jsonify({"error": "Document not found"}), 404
    pdf = get_document_pdf(document_id)
    if not pdf:
        return jsonify({"error": "No PDF stored for this document"}), 404
    return send_file(
        io.BytesIO(pdf["pdf_data"]),
        mimetype="application/pdf",
        download_name=pdf["pdf_filename"] or "document.pdf",
    )


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
    results = search_questions(q)
    logger.info("questions/search q=%r -> %d match(es)", q, len(results))
    return jsonify(results)


@app.route("/api/questions/from-filter", methods=["POST"])
def questions_create_from_filter():
    """Persist a sidebar search filter as a real question (under the
    'Uncategorized' group) once it's been matched to a document, so it — and
    its vector-searched candidate answers — can be found directly next time."""
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    data = request.get_json(force=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "Text is required"}), 400
    question = create_question_from_filter(user_id, text)
    if not question:
        logger.info("questions/from-filter text=%r -> no matching document content", text)
        return jsonify({"error": "Filter text was not found verbatim in any matched document"}), 404
    logger.info("questions/from-filter text=%r -> question id=%s %r", text, question["id"], question["text"])
    return jsonify(question), 201


@app.route("/api/questions/<int:question_id>/candidate-answers")
def questions_candidate_answers(question_id):
    if not _current_user_id():
        return jsonify({"error": "Not authenticated"}), 401
    if not get_question(question_id):
        return jsonify({"error": "Question not found"}), 404
    candidates = get_candidate_answers(question_id)
    logger.info("questions/%s/candidate-answers -> %d candidate(s)", question_id, len(candidates))
    return jsonify(candidates)


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


# ── Admin ─────────────────────────────────────────────────────────────────────

@app.route("/api/admin/clean_db", methods=["POST"])
def admin_clean_db():
    # Wipes history/questions/answers/documents/groups for every user (not just
    # the caller's own data) and re-seeds demo content, so it's dev-only.
    # if IS_PRODUCTION:
    #     return jsonify({"error": "Not available in production"}), 403
    # if not _current_user_id():
    #     return jsonify({"error": "Not authenticated"}), 401
    result = clean_db_main()
    logger.info(
        "admin/clean_db user_id=%s created=%d documents", _current_user_id(), len(result["created_documents"])
    )
    return jsonify(result)


# ── Chat ──────────────────────────────────────────────────────────────────────

# @app.route("/api/chat", methods=["POST"])
# def chat():
#     data = request.get_json(force=True) or {}
#     messages = data.get("messages", [])
#     if not messages:
#         return jsonify({"error": "messages is required"}), 400
#     try:
#         response = client.messages.create(
#             model=MODEL,
#             max_tokens=1024,
#             messages=messages,
#         )
#         text = "".join(
#             block.text for block in response.content if block.type == "text"
#         )
#         return jsonify({"reply": text})
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


# @app.route("/api/chat/stream", methods=["POST"])
# def chat_stream():
#     data = request.get_json(force=True) or {}
#     messages = data.get("messages", [])
#     if not messages:
#         return jsonify({"error": "messages is required"}), 400

#     def generate():
#         with client.messages.stream(
#             model=MODEL,
#             max_tokens=1024,
#             messages=messages,
#         ) as stream:
#             for text in stream.text_stream:
#                 yield text

#     return Response(stream_with_context(generate()), mimetype="text/plain")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
