import os
from flask import Flask, request, jsonify, Response, stream_with_context, session, redirect
from flask_cors import CORS
from anthropic import Anthropic
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth
from database.db import get_db, init_db, seed_db, get_or_create_google_user

load_dotenv()

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
