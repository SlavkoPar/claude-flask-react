import os
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from anthropic import Anthropic
from dotenv import load_dotenv
 
load_dotenv()
 
app = Flask(__name__)
CORS(app)  # In production, restrict this to your frontend's origin
 
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
 
MODEL = os.environ.get("MODEL", "claude-sonnet-4-6")
 
@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Non-streaming chat endpoint.
    Expects JSON: { "messages": [{"role": "user", "content": "..."}, ...] }
    """
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
        # response.content is a list of blocks; concatenate text blocks
        text = "".join(
            block.text for block in response.content if block.type == "text"
        )
        return jsonify({"reply": text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
 
 
@app.route("/api/chat/stream", methods=["POST"])
def chat_stream():
    """
    Streaming chat endpoint (Server-Sent Events style, plain text chunks).
    Expects the same JSON body as /api/chat.
    """
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