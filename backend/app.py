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
    get_or_create_google_user,
    get_groups,
    get_group_options,
    get_group,
    create_group,
    update_group,
    delete_group,
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
        return jsonify({"error": "Cannot delete a group that still has child groups"}), 400
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
