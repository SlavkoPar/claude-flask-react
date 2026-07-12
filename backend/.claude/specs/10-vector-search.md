# Spec: Vector search

> Status: implemented (2026-07-09). Notes on how it was built vs. this draft:
> - Added `faiss-cpu` and `sentence-transformers` as new dependencies despite
>   the "No new dependencies" line below — FAISS embeddings aren't feasible
>   with the stdlib, same kind of draft/rules mismatch as in
>   `09-documents.md`. Embeddings are generated locally with the
>   `all-MiniLM-L6-v2` sentence-transformers model (no external API key
>   required).
> - One FAISS index per embedded table (`database/faiss_documents.index`,
>   `database/faiss_answers.index`), persisted to disk and loaded into an
>   in-memory `IndexIDMap(IndexFlatL2)` on first use each process start.
>   `database/vector_store.py` holds the model + index plumbing; `db.py`
>   calls into it on create/update/delete for `documents` and `answers`,
>   keyed by each row's own auto-incremented id.
> - `GET /api/documents/search?q=` — embeds the query, does a FAISS lookup
>   against `documents`, returns matches ranked by ascending L2 distance with
>   a short text `snippet`.
> - `get_candidate_answers(question_id)` (used by the Sidebar) no longer uses
>   SOUNDEX word-overlap matching (spec `07-sidebar.md`'s original rule) — it
>   now vector-searches the `answers` FAISS index using the question's own
>   text, excludes ids already assigned to the question, and treats the
>   matches as `clicks_to_Fixed = 0`, same as before. Assigned answers keep
>   their real `clicks_to_Fixed` and are still listed first.
> - Sidebar filter fallback: the question search (`GET /api/questions/search`)
>   runs first as the user types; if it returns no matches, the same typed
>   filter is sent to `GET /api/documents/search`. If that finds a document,
>   the filter text itself is saved as a new question via the new
>   `POST /api/questions/from-filter` endpoint, filed under an auto-created
>   "Uncategorized" root group (`questions.group_id` is `NOT NULL` and no
>   catch-all group existed in the seed data) — then its candidate answers
>   are fetched through the normal (vector-search) path above, so Fixed/Not
>   Fixed work exactly like any other question. Typing the same filter again
>   now matches the saved question directly via `search_questions`'s vector
>   search, so no duplicate question gets created.
> - `search_questions` (the same `GET /api/questions/search` used above) was
>   switched from `text LIKE ?` to FAISS vector search too, for consistency
>   with documents/answers — a third index, `database/faiss_questions.index`,
>   embeds `questions.text` (+ `description` when set), kept in sync by
>   `create_question`/`update_question`/`delete_question`, with
>   `backfill_question_embeddings()` populating it for pre-existing rows.
>   Unlike documents/answers search, this one applies a distance cutoff
>   (`QUESTION_MATCH_MAX_DISTANCE = 1.1` in `db.py`) so a genuinely unrelated
>   filter still reports zero matches — the Sidebar's fallback-to-documents
>   step above depends on that "not found" signal, and a bare top-k vector
>   search would otherwise always return *something* once any question
>   exists.


> For document search (GET /api/documents/search?q=), I use semantic vector search, not keyword matching: The query text is embedded with the all-MiniLM-L6-v2 sentence-transformers model (384-dim vector, normalized).

> That vector is compared against a FAISS IndexIDMap(IndexFlatL2) — a flat (brute-force, exact) index storing one embedding per document, keyed by the document's own SQLite id.

> FAISS returns the k nearest neighbors by L2 (Euclidean) distance, so results are ranked by meaning/similarity rather than shared words — e.g. "remote control not working" correctly matched the "SBB remote controller troubleshooting guide" document even though none of those words appear verbatim in its description.

> This replaced the old LIKE '%...%' / SOUNDEX-style matching used elsewhere in the app (e.g. get_answers(name=...) still uses plain LIKE, and the sidebar's old candidate-answer matching used SOUNDEX before I swapped it for the same FAISS approach). It's brute-force exact search (no approximate/quantized index like IVF or HNSW), which is fine at this dataset size — it'd be worth revisiting only if the document/answer counts grew into the tens of thousands.

## Overview

## Depends on
- Step 9: Documents
- Step 6: Answers
- Step 7: Sidebar

## Routes
- `GET /api/documents/search?q=` — semantic search over documents by question text
- `POST /api/questions/from-filter` — save a sidebar filter as a new question once it's matched a document

## Database changes
No schema changes — FAISS indexes are separate files on disk
(`database/faiss_documents.index`, `database/faiss_answers.index`,
`database/faiss_questions.index`), not SQLite tables. The "Uncategorized"
group is a normal row in the existing `groups` table, created lazily on
first use.

## Create table


## 12. Expected Behavior


## Files to change
- `app.py`
- `database/db.py`
- `frontend/src/components/sidebar/SideBar.jsx`

## Files to create
- `database/vector_store.py`

## New dependencies
No new dependencies.

## Rules for implementation
  - In SideBar, search pdf documents, by filter, using vector search (faiss index).
  - When some documents are found, find whole `sentence` inside of document, where `filter` is found, and treat it as the `questions.text`. Treat the whole `paragraph` where the filter was found, or the next `paragraph`, as the `answer`
  - add these `answers` to the `answers` table
  - Then for each document, find question by `questions.text`, use exact search
  - when found 
      -- if document date is newer than correspoding question created date, recreate question
      -- else create a new question with text = `questions.text`
  


## Definition of done
- [x] Documents are searchable via FAISS vector search by question text
- [x] Sidebar candidate answers use vector search instead of SOUNDEX
- [x] Sidebar filter that matches no question falls back to a document search, and a matched document causes the filter to be saved as a new question with vector-searched candidate answers
- [x] Question search (`GET /api/questions/search`) uses FAISS vector search instead of `LIKE`, with a distance cutoff so unrelated filters still report no match
