"""One-off script: wipe transactional tables, re-seed groups, rebuild the
FAISS indexes, and re-import every PDF in database/import/ as a document."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pypdf import PdfReader

from database.db import get_db, init_db, seed_groups, create_document, get_or_create_uncategorized_group, IMPORT_DIR

TABLES = ["history", "question_answers", "documents", "questions", "answers", "groups"]

FAISS_FILES = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "database", f"faiss_{ns}.index")
    for ns in ("questions", "answers", "documents")
]

# Words shorter than this are too generic to safely match a filename against a
# group name (e.g. "TV") and are skipped to avoid false-positive categorization.
MIN_MATCH_WORD_LEN = 3


def counts(conn):
    return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in TABLES}


def _find_group_id(groups, filename):
    """Best-effort: file a PDF under the group whose name shares a keyword
    with its filename (e.g. "Remote Controller.pdf" matches a group renamed
    to "Rem ctrls"). Returns None if nothing matches, so the caller can fall
    back to "Uncategorized"."""
    stem_words = [w for w in os.path.splitext(filename)[0].lower().split() if len(w) >= MIN_MATCH_WORD_LEN]
    for g in groups:
        name_words = [w for w in g["name"].lower().split() if len(w) >= MIN_MATCH_WORD_LEN]
        if any(nw in sw or sw in nw for nw in name_words for sw in stem_words):
            return g["id"]
    return None


def main():
    """Wipes and reseeds the database. Returns
    {"before": {...}, "after": {...}, "deleted_faiss_files": [...], "created_documents": [...]}
    so callers (CLI or an HTTP endpoint) can report what happened."""
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

    deleted_faiss_files = []
    for path in FAISS_FILES:
        path = os.path.normpath(path)
        if os.path.exists(path):
            os.remove(path)
            deleted_faiss_files.append(path)

    with open(os.path.join(IMPORT_DIR, "groups.json"), encoding="utf-8") as f:
        groups = json.load(f)

    created_documents = []
    pdf_filenames = sorted(f for f in os.listdir(IMPORT_DIR) if f.lower().endswith(".pdf"))
    for filename in pdf_filenames:
        pdf_path = os.path.join(IMPORT_DIR, filename)
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()
        reader = PdfReader(pdf_path)
        pages = [page.extract_text() or "" for page in reader.pages]
        content = json.dumps({"filename": filename, "pages": pages}, ensure_ascii=False)

        group_id = _find_group_id(groups, filename)
        if group_id is not None:
            group_name = next(g["name"] for g in groups if g["id"] == group_id)
        else:
            group_id = get_or_create_uncategorized_group(1)
            group_name = "Uncategorized"

        description = os.path.splitext(filename)[0].replace("_", " ").strip()

        document_id = create_document(
            user_id=1,
            group_id=group_id,
            description=description,
            content=content,
            link=None,
            pdf_filename=filename,
            pdf_data=pdf_data,
        )
        created_documents.append({
            "id": document_id, "filename": filename, "group_id": group_id, "group_name": group_name,
        })

    conn = get_db()
    after = counts(conn)
    conn.close()

    return {
        "before": before,
        "after": after,
        "deleted_faiss_files": deleted_faiss_files,
        "created_documents": created_documents,
    }


if __name__ == "__main__":
    result = main()
    for path in result["deleted_faiss_files"]:
        print(f"Deleted {path}")
    for doc in result["created_documents"]:
        print(f"Created document id={doc['id']} ({doc['filename']!r}) in group '{doc['group_name']}' (id={doc['group_id']})")
    print(f"\n{'table':<20}{'before':>10}{'after':>10}")
    for t in TABLES:
        print(f"{t:<20}{result['before'][t]:>10}{result['after'][t]:>10}")
