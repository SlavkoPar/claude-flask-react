# Claude + Flask + React Setup

## Backend (Flask)

```
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and paste your real key from console.anthropic.com:

```
ANTHROPIC_API_KEY=sk-ant-...
```

Run it:

```
python app.py
```

This starts the server at `http://localhost:5000` with two endpoints:

- `POST /api/chat` — returns the full reply as JSON: `{ "reply": "..." }`
- `POST /api/chat/stream` — streams the reply as plain text chunks

Both expect: `{ "messages": [{ "role": "user", "content": "Hello" }] }`

## Frontend (React)

Drop `frontend-src/Chat.jsx` into your React app's `src/` folder, then use it:

```jsx
import Chat from "./Chat";

function App() {
  return <Chat />;
}

export default App;
```

If you don't have a React app yet:

```
npm create vite@latest my-app -- --template react
cd my-app
npm install
```

Then copy `Chat.jsx` into `my-app/src/` and import it in `App.jsx` as above.

Run it:

```
npm run dev
```

## Why the key lives only in the backend

`ANTHROPIC_API_KEY` is read by Flask from `.env` on the server. The React app
never sees it — it only talks to your own `/api/chat` endpoint. This is the
correct pattern; never expose this key in frontend code or env vars prefixed
with `VITE_`/`REACT_APP_`, since those get bundled into the browser bundle.

## CORS note

`flask-cors` is wide open (`CORS(app)`) for local development. Before
deploying, restrict it, e.g.:

```python
CORS(app, origins=["https://yourdomain.com"])
```

## Streaming (optional)

To use `/api/chat/stream` from React, read the response body as a stream
instead of `res.json()`:

```js
const res = await fetch(`${BACKEND_URL}/api/chat/stream`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ messages: newMessages }),
});

const reader = res.body.getReader();
const decoder = new TextDecoder();
let result = "";

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  result += decoder.decode(value);
  // update state with `result` as it grows
}
```
