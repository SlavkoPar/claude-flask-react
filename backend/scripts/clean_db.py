"""One-off script: wipe transactional tables, re-seed groups, rebuild the
FAISS indexes, and re-import the Remote_Controller.pdf demo document."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pypdf import PdfReader

from database.db import get_db, init_db, seed_groups, create_document, IMPORT_DIR

TABLES = ["history", "question_answers", "documents", "questions", "answers", "groups"]

FAISS_FILES = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "database", f"faiss_{ns}.index")
    for ns in ("questions", "answers", "documents")
]


def counts(conn):
    return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in TABLES}


def main():
    init_db()  # apply any pending column migrations (e.g. documents.group_id) before wiping

    conn = get_db()
    before = counts(conn)

    for table in TABLES:
        if table == "groups":
            conn.execute("PRAGMA foreign_keys = OFF")
            conn.execute("DELETE FROM groups")
            conn.execute("PRAGMA foreign_keys = ON")
        else:
            conn.execute(f"DELETE FROM {table}")
    conn.commit()
    conn.close()

    seed_groups()

    for path in FAISS_FILES:
        path = os.path.normpath(path)
        if os.path.exists(path):
            os.remove(path)
            print(f"Deleted {path}")

    with open(os.path.join(IMPORT_DIR, "groups.json"), encoding="utf-8") as f:
        groups = json.load(f)
    group = next(
        g for g in groups
        if "remote" in g["name"].lower() or "ctrl" in g["name"].lower()
    )
    group_id = group["id"]

    pdf_path = os.path.join(IMPORT_DIR, "Remote_Controller.pdf")
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()
    reader = PdfReader(pdf_path)
    pages = [page.extract_text() or "" for page in reader.pages]
    content = json.dumps({"filename": "Remote_Controller.pdf", "pages": pages}, ensure_ascii=False)

    document_id = create_document(
        user_id=1,
        group_id=group_id,
        description="Remote Controller",
        content=content,
        link=None,
        pdf_filename="Remote_Controller.pdf",
        pdf_data=pdf_data,
    )
    print(f"Created document id={document_id} in group '{group['name']}' (id={group_id})")

    conn = get_db()
    after = counts(conn)
    conn.close()

    print(f"\n{'table':<20}{'before':>10}{'after':>10}")
    for t in TABLES:
        print(f"{t:<20}{before[t]:>10}{after[t]:>10}")


if __name__ == "__main__":
    main()
