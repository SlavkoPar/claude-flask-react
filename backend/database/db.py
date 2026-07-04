import json
import os
import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = "my.db"
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
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    # Migration: add num_of_questions to databases created before this column existed
    try:
        conn.execute("ALTER TABLE groups ADD COLUMN num_of_questions INTEGER NOT NULL DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # column already exists
    conn.close()

    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            group_id INTEGER NOT NULL REFERENCES groups(id),
            text TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    # Migration: add num_of_assigned_answers to databases created before this column existed
    try:
        conn.execute("ALTER TABLE questions ADD COLUMN num_of_assigned_answers INTEGER NOT NULL DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # column already exists
    conn.close()

    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            short_desc TEXT NOT NULL,
            description TEXT,
            link TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS question_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL REFERENCES questions(id),
            answer_id INTEGER NOT NULL REFERENCES answers(id),
            clicksTo_Fixed INTEGER DEFAULT 0,
            user_id INTEGER NOT NULL REFERENCES users(id),
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
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
    cursor = conn.execute(
        "INSERT INTO groups (parent_id, user_id, name, description) VALUES (?, ?, ?, ?)",
        (parent_id, user_id, name, description),
    )
    group_id = cursor.lastrowid
    _recompute_has_child_groups(conn, parent_id)
    conn.commit()
    conn.close()
    return group_id


def update_group(group_id, name, parent_id, description):
    conn = get_db()
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


def create_question(user_id, group_id, text, description):
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO questions (user_id, group_id, text, description) VALUES (?, ?, ?, ?)",
        (user_id, group_id, text, description),
    )
    question_id = cursor.lastrowid
    _recompute_num_of_questions(conn, group_id)
    conn.commit()
    conn.close()
    return question_id


def update_question(question_id, text, description):
    conn = get_db()
    conn.execute(
        "UPDATE questions SET text = ?, description = ? WHERE id = ?",
        (text, description, question_id),
    )
    conn.commit()
    conn.close()


def delete_question(question_id):
    conn = get_db()
    old = conn.execute(
        "SELECT group_id FROM questions WHERE id = ?", (question_id,)
    ).fetchone()
    group_id = old["group_id"] if old else None
    conn.execute("DELETE FROM questions WHERE id = ?", (question_id,))
    if group_id is not None:
        _recompute_num_of_questions(conn, group_id)
    conn.commit()
    conn.close()


# ── Answers ───────────────────────────────────────────────────────────────────

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
    cursor = conn.execute(
        "INSERT INTO answers (user_id, short_desc, description, link) VALUES (?, ?, ?, ?)",
        (user_id, short_desc, description, link),
    )
    answer_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return answer_id


def update_answer(answer_id, short_desc, description, link):
    conn = get_db()
    conn.execute(
        "UPDATE answers SET short_desc = ?, description = ?, link = ? WHERE id = ?",
        (short_desc, description, link, answer_id),
    )
    conn.commit()
    conn.close()


def delete_answer(answer_id):
    conn = get_db()
    try:
        conn.execute("DELETE FROM answers WHERE id = ?", (answer_id,))
        conn.commit()
    finally:
        conn.close()


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
