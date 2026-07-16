import json
import os
import re
import sqlite3
from werkzeug.security import generate_password_hash

from database import vector_store

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "my.db")
IMPORT_DIR = os.path.join(os.path.dirname(__file__), "import")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            google_id TEXT UNIQUE,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    # Migration: add google_id to databases created before this column existed
    try:
        conn.execute("ALTER TABLE users ADD COLUMN google_id TEXT")
        conn.commit()
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_id "
            "ON users (google_id) WHERE google_id IS NOT NULL"
        )
        conn.commit()
    except sqlite3.OperationalError:
        pass  # column already exists
    conn.close()

    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_id INTEGER REFERENCES groups(id),
            user_id INTEGER NOT NULL REFERENCES users(id),
            name TEXT NOT NULL,
            description TEXT,
            has_child_groups BOOLEAN NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE (parent_id, name)
        )
    """)
    conn.commit()
    # Migration: add num_of_questions to databases created before this column existed
    try:
        conn.execute("ALTER TABLE groups ADD COLUMN num_of_questions INTEGER NOT NULL DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # column already exists
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_groups_parent_name ON groups (parent_id, name)"
    )
    conn.commit()
    conn.close()

    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            group_id INTEGER NOT NULL REFERENCES groups(id),
            text TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            modified_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    # Migration: add num_of_assigned_answers to databases created before this column existed
    try:
        conn.execute("ALTER TABLE questions ADD COLUMN num_of_assigned_answers INTEGER NOT NULL DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # column already exists
    # Migration: add modified_at to databases created before this column existed
    try:
        conn.execute("ALTER TABLE questions ADD COLUMN modified_at TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # column already exists
    conn.execute("UPDATE questions SET modified_at = created_at WHERE modified_at IS NULL")
    conn.commit()
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_questions_text ON questions (text)")
    conn.commit()
    conn.close()

    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            short_desc TEXT NOT NULL UNIQUE,
            description TEXT,
            link TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_answers_short_desc ON answers (short_desc)")
    conn.commit()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS question_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL REFERENCES questions(id),
            answer_id INTEGER NOT NULL REFERENCES answers(id),
            clicks_to_Fixed INTEGER DEFAULT 0,
            user_id INTEGER NOT NULL REFERENCES users(id),
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    # Migration: rename clicks_to_Fixed to clicks_to_Fixed on databases created before this rename
    try:
        conn.execute("ALTER TABLE question_answers RENAME COLUMN clicks_to_Fixed TO clicks_to_Fixed")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # already renamed (or column never existed)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL REFERENCES questions(id),
            answer_id INTEGER NOT NULL REFERENCES answers(id),
            user_id INTEGER NOT NULL REFERENCES users(id),
            action TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            group_id INTEGER REFERENCES groups(id),
            description TEXT NOT NULL,
            content TEXT NOT NULL,
            link TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    # Migration: add pdf_filename/pdf_data to databases created before the
    # original PDF upload was also stored (not just its extracted text)
    try:
        conn.execute("ALTER TABLE documents ADD COLUMN pdf_filename TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # column already exists
    try:
        conn.execute("ALTER TABLE documents ADD COLUMN pdf_data BLOB")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # column already exists
    # Migration: add group_id to databases created before documents were
    # grouped. Left nullable here (existing rows have none yet) — see
    # backfill_document_groups(), which files them under "Uncategorized".
    try:
        conn.execute("ALTER TABLE documents ADD COLUMN group_id INTEGER REFERENCES groups(id)")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # column already exists
    conn.close()


def seed_db():
    conn = get_db()
    row = conn.execute("SELECT id FROM users LIMIT 1").fetchone()
    if row:
        conn.close()
        return
    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@my.com", generate_password_hash("demo123")),
    )
    conn.commit()
    conn.close()


def seed_groups():
    conn = get_db()
    row = conn.execute("SELECT id FROM groups LIMIT 1").fetchone()
    if row:
        conn.close()
        return
    with open(os.path.join(IMPORT_DIR, "groups.json"), encoding="utf-8") as f:
        groups = json.load(f)
    for g in groups:
        conn.execute(
            "INSERT INTO groups (id, parent_id, user_id, name, description, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (g["id"], g["parent_id"], 1, g["name"], g["description"], g["created_at"]),
        )
    conn.execute("""
        UPDATE groups SET has_child_groups = 1
        WHERE id IN (SELECT DISTINCT parent_id FROM groups WHERE parent_id IS NOT NULL)
    """)
    conn.commit()
    conn.close()


def seed_questions():
    conn = get_db()
    row = conn.execute("SELECT id FROM questions LIMIT 1").fetchone()
    if row:
        conn.close()
        return
    with open(os.path.join(IMPORT_DIR, "questions.json"), encoding="utf-8") as f:
        questions = json.load(f)
    for q in questions:
        conn.execute(
            "INSERT INTO questions (id, user_id, group_id, text, description, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (q["id"], 1, q["group_id"], q["text"], q["description"], q["created_at"]),
        )
    conn.execute("""
        UPDATE groups SET num_of_questions =
            (SELECT COUNT(*) FROM questions q WHERE q.group_id = groups.id)
    """)
    conn.commit()
    conn.close()


def seed_answers():
    conn = get_db()
    row = conn.execute("SELECT id FROM answers LIMIT 1").fetchone()
    if row:
        conn.close()
        return
    with open(os.path.join(IMPORT_DIR, "answers.json"), encoding="utf-8") as f:
        answers = json.load(f)
    for a in answers:
        conn.execute(
            "INSERT INTO answers (id, user_id, short_desc, description, link, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (a["id"], 1, a["short_desc"], a["description"], a["link"], a["created_at"]),
        )
    conn.commit()
    conn.close()


def seed_question_answers():
    conn = get_db()
    row = conn.execute("SELECT id FROM question_answers LIMIT 1").fetchone()
    if row:
        conn.close()
        return
    with open(os.path.join(IMPORT_DIR, "question_answers.json"), encoding="utf-8") as f:
        question_answers = json.load(f)
    for qa in question_answers:
        conn.execute(
            "INSERT INTO question_answers (id, question_id, answer_id, user_id, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (qa["id"], qa["question_id"], qa["answer_id"], 1, qa["created_at"]),
        )
    conn.execute("""
        UPDATE questions SET num_of_assigned_answers =
            (SELECT COUNT(*) FROM question_answers qa WHERE qa.question_id = questions.id)
    """)
    conn.commit()
    conn.close()


def seed_documents():
    conn = get_db()
    row = conn.execute("SELECT id FROM documents LIMIT 1").fetchone()
    if row:
        conn.close()
        return
    with open(os.path.join(IMPORT_DIR, "documents.json"), encoding="utf-8") as f:
        documents = json.load(f)
    for d in documents:
        conn.execute(
            "INSERT INTO documents (id, user_id, description, content, link, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (d["id"], 1, d["description"], d["content"], d["link"], d["created_at"]),
        )
    conn.commit()
    conn.close()


def get_user_by_email(email):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return dict(user) if user else None


def get_or_create_google_user(name, email, google_id):
    conn = get_db()
    # Look up by google_id first (fastest path)
    user = conn.execute(
        "SELECT * FROM users WHERE google_id = ?", (google_id,)
    ).fetchone()
    if user:
        conn.close()
        return dict(user)
    # Link to an existing email account
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()
    if user:
        conn.execute(
            "UPDATE users SET google_id = ? WHERE id = ?",
            (google_id, user["id"]),
        )
        conn.commit()
        conn.close()
        return dict(user)
    # Create a new Google-only account ('google' is an invalid werkzeug hash →
    # check_password_hash will always return False for these users)
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash, google_id) VALUES (?, ?, ?, ?)",
        (name, email, "google", google_id),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return {"id": user_id, "name": name, "email": email, "google_id": google_id}


# ── Groups ──────────────────────────────────────────────────────────────────

def get_groups(parent_id=None, name=None):
    conn = get_db()
    columns = "id, name, description, has_child_groups, num_of_questions"
    if name:
        sql = f"SELECT {columns} FROM groups WHERE name LIKE ? COLLATE NOCASE"
        params = [f"%{name}%"]
        if parent_id is not None:
            sql += " AND parent_id = ?"
            params.append(parent_id)
    else:
        sql = f"SELECT {columns} FROM groups WHERE parent_id IS ?"
        params = [parent_id]
    sql += " ORDER BY name"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_group_options():
    conn = get_db()
    rows = conn.execute(
        "SELECT id, name, parent_id FROM groups ORDER BY name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_group(group_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM groups WHERE id = ?", (group_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def _recompute_has_child_groups(conn, group_id):
    if group_id is None:
        return
    conn.execute(
        "UPDATE groups SET has_child_groups = "
        "EXISTS(SELECT 1 FROM groups c WHERE c.parent_id = groups.id) WHERE id = ?",
        (group_id,),
    )


def create_group(user_id, name, parent_id, description):
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO groups (parent_id, user_id, name, description) VALUES (?, ?, ?, ?)",
            (parent_id, user_id, name, description),
        )
        group_id = cursor.lastrowid
        _recompute_has_child_groups(conn, parent_id)
        conn.commit()
    finally:
        conn.close()
    return group_id


def update_group(group_id, name, parent_id, description):
    conn = get_db()
    try:
        old = conn.execute(
            "SELECT parent_id FROM groups WHERE id = ?", (group_id,)
        ).fetchone()
        old_parent_id = old["parent_id"] if old else None
        conn.execute(
            "UPDATE groups SET name = ?, parent_id = ?, description = ? WHERE id = ?",
            (name, parent_id, description, group_id),
        )
        _recompute_has_child_groups(conn, old_parent_id)
        if parent_id != old_parent_id:
            _recompute_has_child_groups(conn, parent_id)
        conn.commit()
    finally:
        conn.close()


def delete_group(group_id):
    conn = get_db()
    old = conn.execute(
        "SELECT parent_id FROM groups WHERE id = ?", (group_id,)
    ).fetchone()
    old_parent_id = old["parent_id"] if old else None
    try:
        conn.execute("DELETE FROM groups WHERE id = ?", (group_id,))
        _recompute_has_child_groups(conn, old_parent_id)
        conn.commit()
    finally:
        conn.close()


# ── Questions ─────────────────────────────────────────────────────────────────

def get_questions(group_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT id, group_id, text, description, num_of_assigned_answers, created_at FROM questions "
        "WHERE group_id = ? ORDER BY id",
        (group_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_question(question_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM questions WHERE id = ?", (question_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def _recompute_num_of_questions(conn, group_id):
    conn.execute(
        "UPDATE groups SET num_of_questions = "
        "(SELECT COUNT(*) FROM questions q WHERE q.group_id = groups.id) WHERE id = ?",
        (group_id,),
    )


def _question_embedding_text(text, description):
    return f"{text}\n\n{description}" if description else text


def backfill_question_embeddings():
    conn = get_db()
    rows = conn.execute("SELECT id, text, description FROM questions").fetchall()
    conn.close()
    vector_store.backfill_if_needed(
        "questions", ((r["id"], _question_embedding_text(r["text"], r["description"])) for r in rows)
    )


def create_question(user_id, group_id, text, description):
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO questions (user_id, group_id, text, description, modified_at) "
            "VALUES (?, ?, ?, ?, datetime('now'))",
            (user_id, group_id, text, description),
        )
        question_id = cursor.lastrowid
        _recompute_num_of_questions(conn, group_id)
        conn.commit()
    finally:
        conn.close()
    vector_store.add_embedding("questions", question_id, _question_embedding_text(text, description))
    return question_id


UNCATEGORIZED_GROUP_NAME = "Uncategorized"


def get_or_create_uncategorized_group(user_id):
    """Root group that sidebar-searched filters (which matched a document but no
    existing question) get filed under when saved as a new question."""
    for g in get_groups(name=UNCATEGORIZED_GROUP_NAME):
        if g["name"] == UNCATEGORIZED_GROUP_NAME:
            return g["id"]
    return create_group(
        user_id, UNCATEGORIZED_GROUP_NAME, None,
        "Questions auto-saved from sidebar filters that matched a document",
    )


def find_question_by_text(text):
    conn = get_db()
    row = conn.execute("SELECT * FROM questions WHERE text = ?", (text,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_question_from_filter(user_id, text):
    """Called once a sidebar filter matches no question but does match a
    document: scans every document that vector-matches the filter (oldest
    first) for paragraphs containing it verbatim, stores them as answers
    (deduped). If the filter only appears in the document's description (not
    its content), the whole content is used as the answer instead. Per
    document, the `sentence` surrounding the filter match is used to
    find-or-create a question by exact text — a brand-new question gets the
    extracted answers assigned immediately, an existing one only when the
    document is newer than its modified_at. Returns the last document's
    question (or None if the filter wasn't found verbatim in any matched
    document's content or description)."""
    question = None
    for document in _documents_matching_filter(text):
        content_text = _document_full_text(document["content"])
        paragraphs = _filter_paragraph_matches(document["content"], text)
        sentence = _extract_sentence(content_text, text)
        if not paragraphs and text.lower() in (document["description"] or "").lower():
            paragraphs = [content_text]
            sentence = _extract_sentence(document["description"], text)
        if not paragraphs or not sentence:
            continue

        answer_ids = [_get_or_create_answer_from_paragraph(user_id, p) for p in paragraphs]

        found = find_question_by_text(sentence)
        if not found:
            group_id = get_or_create_uncategorized_group(user_id)
            question_id = create_question(user_id, group_id, sentence, None)
            found = get_question(question_id)
            for answer_id in answer_ids:
                if not _is_answer_assigned(found["id"], answer_id):
                    assign_answer(user_id, found["id"], answer_id)
        elif document["created_at"] > found["modified_at"]:
            for answer_id in answer_ids:
                if not _is_answer_assigned(found["id"], answer_id):
                    assign_answer(user_id, found["id"], answer_id)

        question = get_question(found["id"])

    return question


def update_question(question_id, text, description):
    conn = get_db()
    try:
        conn.execute(
            "UPDATE questions SET text = ?, description = ?, modified_at = datetime('now') WHERE id = ?",
            (text, description, question_id),
        )
        conn.commit()
    finally:
        conn.close()
    vector_store.add_embedding("questions", question_id, _question_embedding_text(text, description))


def delete_question(question_id):
    conn = get_db()
    old = conn.execute(
        "SELECT group_id FROM questions WHERE id = ?", (question_id,)
    ).fetchone()
    group_id = old["group_id"] if old else None
    conn.execute("DELETE FROM question_answers WHERE question_id = ?", (question_id,))
    conn.execute("DELETE FROM questions WHERE id = ?", (question_id,))
    if group_id is not None:
        _recompute_num_of_questions(conn, group_id)
    conn.commit()
    conn.close()
    vector_store.remove_embedding("questions", question_id)


# ── Answers ───────────────────────────────────────────────────────────────────

def _answer_embedding_text(short_desc, description):
    return f"{short_desc}\n\n{description}" if description else short_desc


def backfill_answer_embeddings():
    conn = get_db()
    rows = conn.execute("SELECT id, short_desc, description FROM answers").fetchall()
    conn.close()
    vector_store.backfill_if_needed(
        "answers", ((r["id"], _answer_embedding_text(r["short_desc"], r["description"])) for r in rows)
    )


def get_answers(name=None):
    conn = get_db()
    columns = "id, user_id, short_desc, description, link, created_at"
    if name:
        sql = f"SELECT {columns} FROM answers WHERE short_desc LIKE ? COLLATE NOCASE ORDER BY short_desc"
        rows = conn.execute(sql, (f"%{name}%",)).fetchall()
    else:
        sql = f"SELECT {columns} FROM answers ORDER BY short_desc"
        rows = conn.execute(sql).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_answer(answer_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM answers WHERE id = ?", (answer_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_answer(user_id, short_desc, description, link):
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO answers (user_id, short_desc, description, link) VALUES (?, ?, ?, ?)",
            (user_id, short_desc, description, link),
        )
        answer_id = cursor.lastrowid
        conn.commit()
    finally:
        conn.close()
    vector_store.add_embedding("answers", answer_id, _answer_embedding_text(short_desc, description))
    return answer_id


def update_answer(answer_id, short_desc, description, link):
    conn = get_db()
    try:
        conn.execute(
            "UPDATE answers SET short_desc = ?, description = ?, link = ? WHERE id = ?",
            (short_desc, description, link, answer_id),
        )
        conn.commit()
    finally:
        conn.close()
    vector_store.add_embedding("answers", answer_id, _answer_embedding_text(short_desc, description))


def delete_answer(answer_id):
    conn = get_db()
    try:
        conn.execute("DELETE FROM answers WHERE id = ?", (answer_id,))
        conn.commit()
    finally:
        conn.close()
    vector_store.remove_embedding("answers", answer_id)


# ── Documents ─────────────────────────────────────────────────────────────────

def _document_embedding_text(description, content):
    return f"{description}\n\n{content}"


def backfill_document_embeddings():
    conn = get_db()
    rows = conn.execute("SELECT id, description, content FROM documents").fetchall()
    conn.close()
    vector_store.backfill_if_needed(
        "documents", ((r["id"], _document_embedding_text(r["description"], r["content"])) for r in rows)
    )


def _document_snippet(content, length=300):
    content = content.strip()
    return content[:length] + ("…" if len(content) > length else "")


def search_documents(query, k=5):
    """Semantic search over document embeddings. Returns documents ranked by
    FAISS L2 distance (ascending, so most relevant first)."""
    matches = vector_store.search("documents", query, k=k)
    if not matches:
        return []
    distance_by_id = {m["id"]: m["distance"] for m in matches}

    conn = get_db()
    placeholders = ",".join("?" for _ in matches)
    rows = conn.execute(
        f"SELECT id, description, content, link, created_at FROM documents WHERE id IN ({placeholders})",
        list(distance_by_id.keys()),
    ).fetchall()
    conn.close()

    results = [dict(r) for r in rows]
    for r in results:
        r["snippet"] = _document_snippet(r.pop("content"))
        r["distance"] = distance_by_id[r["id"]]
    results.sort(key=lambda r: r["distance"])
    return results


def _document_full_text(content):
    """PDF-derived documents store `content` as JSON `{"filename", "pages":
    [...]}`; documents created directly hold plain text. Returns the text to
    run filter/paragraph matching against either way."""
    try:
        parsed = json.loads(content)
    except (ValueError, TypeError):
        return content
    if isinstance(parsed, dict) and "pages" in parsed:
        return "\n\n".join(parsed["pages"])
    return content


def _document_paragraphs(text):
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(paragraphs) > 1:
        return paragraphs
    # No blank-line breaks (e.g. PDF-extracted text) — one paragraph per line
    return [line.strip() for line in text.splitlines() if line.strip()]


def _filter_paragraph_matches(content, filter_text):
    """Find every paragraph containing `filter_text` (case-insensitive
    substring) plus the paragraph right after it. A document can contain more
    than one match."""
    paragraphs = _document_paragraphs(_document_full_text(content))
    needle = filter_text.lower()
    matches = []
    for i, para in enumerate(paragraphs):
        if needle in para.lower():
            pair = para if i + 1 >= len(paragraphs) else f"{para}\n{paragraphs[i + 1]}"
            matches.append(pair)
    return matches


def _extract_sentence(text, filter_text):
    """Return the sentence around the first case-insensitive occurrence of
    `filter_text` in `text`, bounded by a period, a newline, or the start/end
    of the document. Used as the question text when a sidebar filter is saved
    from a document match. Returns None if `filter_text` isn't found."""
    idx = text.lower().find(filter_text.lower())
    if idx == -1:
        return None
    start = max(text.rfind(".", 0, idx), text.rfind("\n", 0, idx)) + 1
    match_end = idx + len(filter_text)
    end_candidates = [e for e in (text.find(".", match_end), text.find("\n", match_end)) if e != -1]
    end = min(end_candidates) if end_candidates else len(text)
    sentence = text[start:end].strip()
    return sentence or None


def _documents_matching_filter(filter_text, k=5):
    """Same FAISS document search as search_documents, but returns full rows
    (content + created_at) needed to extract filter-matched answers, ordered
    by created_at ascending per the vector-search spec's assignment rule."""
    matches = vector_store.search("documents", filter_text, k=k)
    if not matches:
        return []
    conn = get_db()
    placeholders = ",".join("?" for _ in matches)
    rows = conn.execute(
        f"SELECT id, description, content, created_at FROM documents WHERE id IN ({placeholders})",
        [m["id"] for m in matches],
    ).fetchall()
    conn.close()
    results = [dict(r) for r in rows]
    results.sort(key=lambda r: r["created_at"])
    return results


def _find_answer_by_description(description):
    conn = get_db()
    row = conn.execute("SELECT id FROM answers WHERE description = ?", (description,)).fetchone()
    conn.close()
    return row["id"] if row else None


def _find_answer_by_short_desc(short_desc):
    conn = get_db()
    row = conn.execute("SELECT id FROM answers WHERE short_desc = ?", (short_desc,)).fetchone()
    conn.close()
    return row["id"] if row else None


def _get_or_create_answer_from_paragraph(user_id, paragraph):
    existing_id = _find_answer_by_description(paragraph)
    if existing_id:
        return existing_id
    short_desc = paragraph if len(paragraph) <= 80 else paragraph[:77] + "…"
    try:
        return create_answer(user_id, short_desc, paragraph, None)
    except sqlite3.IntegrityError:
        # Two distinct paragraphs can truncate to the same short_desc (now UNIQUE)
        # even though their full descriptions differ — reuse the existing answer.
        return _find_answer_by_short_desc(short_desc)


def _is_answer_assigned(question_id, answer_id):
    conn = get_db()
    row = conn.execute(
        "SELECT id FROM question_answers WHERE question_id = ? AND answer_id = ?",
        (question_id, answer_id),
    ).fetchone()
    conn.close()
    return row is not None


def backfill_document_groups():
    """Files any pre-existing document without a group_id (created before
    documents were grouped) under its creator's "Uncategorized" group."""
    conn = get_db()
    rows = conn.execute("SELECT id, user_id FROM documents WHERE group_id IS NULL").fetchall()
    conn.close()
    for r in rows:
        group_id = get_or_create_uncategorized_group(r["user_id"])
        conn = get_db()
        conn.execute("UPDATE documents SET group_id = ? WHERE id = ?", (group_id, r["id"]))
        conn.commit()
        conn.close()


def get_documents(name=None, group_id=None):
    conn = get_db()
    columns = "d.id, d.user_id, d.group_id, g.name AS group_name, d.description, d.link, d.created_at"
    sql = f"SELECT {columns} FROM documents d LEFT JOIN groups g ON g.id = d.group_id WHERE 1=1"
    params = []
    if name:
        sql += " AND d.description LIKE ? COLLATE NOCASE"
        params.append(f"%{name}%")
    if group_id is not None:
        sql += " AND d.group_id = ?"
        params.append(group_id)
    sql += " ORDER BY g.name, d.description"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_document(document_id):
    conn = get_db()
    row = conn.execute(
        "SELECT id, user_id, group_id, description, content, link, created_at, pdf_filename, "
        "(pdf_data IS NOT NULL) AS has_pdf FROM documents WHERE id = ?",
        (document_id,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    document = dict(row)
    document["has_pdf"] = bool(document["has_pdf"])
    return document


def get_document_pdf(document_id):
    conn = get_db()
    row = conn.execute(
        "SELECT pdf_filename, pdf_data FROM documents WHERE id = ?", (document_id,)
    ).fetchone()
    conn.close()
    if not row or row["pdf_data"] is None:
        return None
    return dict(row)


def create_document(user_id, group_id, description, content, link, pdf_filename=None, pdf_data=None):
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO documents (user_id, group_id, description, content, link, pdf_filename, pdf_data) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, group_id, description, content, link, pdf_filename, pdf_data),
    )
    document_id = cursor.lastrowid
    conn.commit()
    conn.close()
    vector_store.add_embedding("documents", document_id, _document_embedding_text(description, content))
    return document_id


def update_document(document_id, group_id, description, content, link, pdf_filename=None, pdf_data=None):
    conn = get_db()
    if pdf_data is not None:
        conn.execute(
            "UPDATE documents SET group_id = ?, description = ?, content = ?, link = ?, "
            "pdf_filename = ?, pdf_data = ? WHERE id = ?",
            (group_id, description, content, link, pdf_filename, pdf_data, document_id),
        )
    else:
        conn.execute(
            "UPDATE documents SET group_id = ?, description = ?, content = ?, link = ? WHERE id = ?",
            (group_id, description, content, link, document_id),
        )
    conn.commit()
    conn.close()
    vector_store.add_embedding("documents", document_id, _document_embedding_text(description, content))


def delete_document(document_id):
    conn = get_db()
    conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
    conn.commit()
    conn.close()
    vector_store.remove_embedding("documents", document_id)


# ── Question <-> Answer assignment ───────────────────────────────────────────

def _recompute_num_of_assigned_answers(conn, question_id):
    conn.execute(
        "UPDATE questions SET num_of_assigned_answers = "
        "(SELECT COUNT(*) FROM question_answers qa WHERE qa.question_id = questions.id) WHERE id = ?",
        (question_id,),
    )


def get_assigned_answers(question_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT a.id, a.short_desc, a.description, a.link, a.created_at "
        "FROM answers a JOIN question_answers qa ON qa.answer_id = a.id "
        "WHERE qa.question_id = ? ORDER BY a.short_desc",
        (question_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_unassigned_answers(question_id, name=None):
    conn = get_db()
    sql = (
        "SELECT id, short_desc, description, link, created_at FROM answers "
        "WHERE id NOT IN (SELECT answer_id FROM question_answers WHERE question_id = ?)"
    )
    params = [question_id]
    if name:
        sql += " AND short_desc LIKE ? COLLATE NOCASE"
        params.append(f"%{name}%")
    sql += " ORDER BY short_desc"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def assign_answer(user_id, question_id, answer_id):
    conn = get_db()
    conn.execute(
        "INSERT INTO question_answers (question_id, answer_id, user_id) VALUES (?, ?, ?)",
        (question_id, answer_id, user_id),
    )
    _recompute_num_of_assigned_answers(conn, question_id)
    conn.commit()
    conn.close()


def unassign_answer(question_id, answer_id):
    conn = get_db()
    conn.execute(
        "DELETE FROM question_answers WHERE question_id = ? AND answer_id = ?",
        (question_id, answer_id),
    )
    _recompute_num_of_assigned_answers(conn, question_id)
    conn.commit()
    conn.close()


# ── Sidebar: question search, candidate answers, fixed/not-fixed ────────────

# Above this distance a match is considered unrelated rather than found, so an
# irrelevant filter reports zero matches — the Sidebar relies on that "not
# found" signal to fall back to searching documents instead.
QUESTION_MATCH_MAX_DISTANCE = 1.1


def search_questions(query, limit=20):
    matches = vector_store.search("questions", query, k=limit, max_distance=QUESTION_MATCH_MAX_DISTANCE)
    if not matches:
        return []
    conn = get_db()
    placeholders = ",".join("?" for _ in matches)
    rows = conn.execute(
        f"SELECT id, group_id, text FROM questions WHERE id IN ({placeholders})",
        [m["id"] for m in matches],
    ).fetchall()
    conn.close()
    by_id = {r["id"]: dict(r) for r in rows}
    return [by_id[m["id"]] for m in matches if m["id"] in by_id]


RELATED_DOCUMENTS_LIMIT = 3


def get_candidate_answers(question_id, k=10):
    """Answers assigned to the question (real clicks_to_Fixed), plus answers not
    yet assigned whose embedding is a FAISS vector-search match for the question
    text (treated as clicks_to_Fixed = 0). Ordered by clicks_to_Fixed desc. Every
    candidate carries the same `related_documents` — the question text's own
    vector-search matches against `documents` — joined in as extra context."""
    question = get_question(question_id)
    if not question:
        return []

    conn = get_db()
    assigned = [dict(r) for r in conn.execute(
        "SELECT a.id, a.short_desc, a.description, a.link, qa.clicks_to_Fixed "
        "FROM answers a JOIN question_answers qa ON qa.answer_id = a.id "
        "WHERE qa.question_id = ?",
        (question_id,),
    ).fetchall()]
    assigned_ids = {a["id"] for a in assigned}

    matched_ids = [
        m["id"] for m in vector_store.search("answers", question["text"], k=k)
        if m["id"] not in assigned_ids
    ]
    matched = []
    if matched_ids:
        placeholders = ",".join("?" for _ in matched_ids)
        rows = conn.execute(
            f"SELECT id, short_desc, description, link FROM answers WHERE id IN ({placeholders})",
            matched_ids,
        ).fetchall()
        by_id = {r["id"]: dict(r) for r in rows}
        # rebuild in FAISS relevance order — SQL's `IN (...)` doesn't preserve list order
        matched = [by_id[i] for i in matched_ids if i in by_id]
        for answer in matched:
            answer["clicks_to_Fixed"] = 0
    conn.close()

    candidates = assigned + matched
    candidates.sort(key=lambda a: a["clicks_to_Fixed"], reverse=True)
    if candidates:
        related_documents = search_documents(question["text"], k=RELATED_DOCUMENTS_LIMIT)
        for candidate in candidates:
            candidate["related_documents"] = related_documents
    return candidates


def mark_answer_fixed(user_id, question_id, answer_id):
    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM question_answers WHERE question_id = ? AND answer_id = ?",
        (question_id, answer_id),
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE question_answers SET clicks_to_Fixed = clicks_to_Fixed + 1 WHERE id = ?",
            (existing["id"],),
        )
    else:
        conn.execute(
            "INSERT INTO question_answers (question_id, answer_id, user_id, clicks_to_Fixed) "
            "VALUES (?, ?, ?, 1)",
            (question_id, answer_id, user_id),
        )
    _recompute_num_of_assigned_answers(conn, question_id)
    conn.execute(
        "INSERT INTO history (question_id, answer_id, user_id, action) VALUES (?, ?, ?, 'fixed')",
        (question_id, answer_id, user_id),
    )
    conn.commit()
    conn.close()


def mark_answer_not_fixed(user_id, question_id, answer_id):
    conn = get_db()
    conn.execute(
        "INSERT INTO history (question_id, answer_id, user_id, action) VALUES (?, ?, ?, 'not_fixed')",
        (question_id, answer_id, user_id),
    )
    conn.commit()
    conn.close()
