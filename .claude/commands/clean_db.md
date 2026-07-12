---
description: Empty history, question_answers, documents, questions, groups and answers, then (re-)import groups from groups.json and Remote_Controller.pdf as a document
allowed-tools: Read, Bash(python3:*)
---

Read database/db.py to understand the schema, the get_db() helper,
seed_groups(), and the vector_store module (database/vector_store.py).

Then write and run a Python script using Bash that:

1. Opens a connection with get_db() (foreign_keys is ON) and deletes all
   rows from these tables, (do NOT touch `users`), in this order so foreign keys aren't violated
   (children before parents) :
   - history
   - question_answers
   - documents
   - questions
   - answers
   - groups — self-referential (`parent_id`), so wrap this one delete with
     `PRAGMA foreign_keys = OFF` / `PRAGMA foreign_keys = ON` to avoid
     parent/child ordering errors on the full-table wipe
   

2. Calls `seed_groups()` to (re-)import groups from
   `database/import/groups.json` — since `groups` was just emptied above,
   this repopulates it (it only inserts when the table is empty, so it's
   safe to call even if a future version of this script doesn't empty
   `groups`).

3. Deletes the FAISS index files so stale embeddings for now-deleted rows
   don't linger (they're rebuilt automatically by the app's
   `backfill_*_embeddings()` calls on next startup):
   - database/faiss_questions.index
   - database/faiss_answers.index
   - database/faiss_documents.index
4. Imports `database/import/Remote_Controller.pdf` as a document via
   `create_document()` (which also embeds it into the FAISS `documents`
   index) — extract its text with `pypdf.PdfReader` the same way
   `/api/documents/extract-pdf` does, and use:
   - user_id: the demo user (id 1)
   - group_id: look up the group by name at run time (don't hardcode the
     id) — the source is whatever `database/import/groups.json`'s leaf
     "remote controllers" group is currently named (it's been renamed
     before, e.g. to "Rem ctrls"); match case-insensitively on the group
     whose name contains "remote" or "ctrl" rather than an exact string
   - description: "Remote Controller"
   - content: `{"filename": "Remote_Controller.pdf", "pages": [...]}` (same
     shape the extract-pdf endpoint produces)
   - pdf_filename/pdf_data: the original file's name and raw bytes, so
     "Download original PDF" works on the created document too

5. Prints a before/after row count for every table.
