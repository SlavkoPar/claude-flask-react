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
> - **2026-07-13 addendum** — the paragraph-extraction rule below (find the
>   filter inside matched documents, turn the surrounding paragraph pair into
>   answers, find-or-create the question by exact text, assign per document
>   date) had been left unimplemented; `create_question_from_filter` only
>   created a bare question and relied on the generic answers-table vector
>   search. It's now implemented in `db.py`:
>   `find_question_by_text` does the exact-text lookup (create only on miss);
>   `_documents_matching_filter` re-runs the FAISS document search but
>   returns full rows (content + created_at) sorted ascending by date;
>   `_document_full_text`/`_document_paragraphs` normalize a document's text
>   into paragraphs — PDF-derived `content` is the JSON `{"pages": [...]}`
>   blob so pages are joined and, since `pypdf`-extracted text has no blank
>   lines, "paragraph" falls back to one paragraph per line when no blank-line
>   breaks exist (there's no reliable sentence boundary either, so "whole
>   sentence" is read as "paragraph containing the filter substring,
>   case-insensitive"); `_filter_paragraph_matches` pairs each matching
>   paragraph with the one after it, per the "also the next paragraph" rule;
>   `_get_or_create_answer_from_paragraph` inserts it as an answer (deduped by
>   exact `description` match, `short_desc` truncated to 80 chars); and the
>   document-date-vs-question-date comparison uses plain string comparison,
>   safe since both columns share SQLite's `datetime('now')` format. Answers
>   are only auto-*assigned* (via `assign_answer`, deduped against
>   `question_answers`) when the document is newer than the question — for a
>   brand-new question that's never true at creation time, so its extracted
>   answers still surface to the user through the pre-existing vector-search
>   candidate-answers path instead of an explicit assignment.
> - **2026-07-14 addendum** — added the "filter found in description only"
>   rule: `create_question_from_filter` now falls back to using a matched
>   document's whole content as the answer when `_filter_paragraph_matches`
>   finds nothing in the content but the filter text is a substring of the
>   document's `description` (e.g. a filter that names the document's topic
>   without appearing verbatim in its extracted text). `_documents_matching_filter`
>   now also selects `description` to support this check.
> - **2026-07-15 addendum** — reworked `create_question_from_filter` per the
>   revised rule text: the question is no longer created from the raw sidebar
>   filter text up front. Instead, for each matched document (still oldest
>   first), a new `_extract_sentence(text, filter_text)` finds the `sentence`
>   around the filter's first occurrence — bounded by a period, a newline, or
>   the document's start/end (extracted from the description instead when the
>   filter was only found there). That `sentence` is the exact-text
>   find-or-create key for the question, and the find-or-create + assignment
>   both happen per document rather than once upfront: a brand-new question
>   gets its document's extracted answers assigned immediately (no more
>   waiting for a later "newer document" to trigger the first assignment), an
>   existing one only when this document is newer than its `modified_at`. If
>   a filter matches multiple documents, each can resolve to a different
>   question (different documents legitimately contain different sentences);
>   the function returns the last document's question, or `None` if the
>   filter wasn't found verbatim (content or description) in any matched
>   document. `POST /api/questions/from-filter` now returns 404 in that `None`
>   case instead of `null` with a 201.


> For document search (GET /api/documents/search?q=), I use semantic vector search, not keyword matching: The query text is embedded with the all-MiniLM-L6-v2 sentence-transformers model (384-dim vector, normalized).

> That vector is compared against a FAISS IndexIDMap(IndexFlatL2) — a flat (brute-force, exact) index storing one embedding per document, keyed by the document's own SQLite id.

> FAISS returns the k nearest neighbors by L2 (Euclidean) distance, so results are ranked by meaning/similarity rather than shared words — e.g. "remote control not working" correctly matched the "SBB remote controller troubleshooting guide" document even though none of those words appear verbatim in its description.

> This replaced the old LIKE '%...%' / SOUNDEX-style matching used elsewhere in the app (e.g. get_answers(name=...) still uses plain LIKE, and the sidebar's old candidate-answer matching used SOUNDEX before I swapped it for the same FAISS approach). It's brute-force exact search (no approximate/quantized index like IVF or HNSW), which is fine at this dataset size — it'd be worth revisiting only if the document/answer counts grew into the tens of thousands.

## Overview

## Depends on
- Step 7: Documents
- Step 9: Sidebar

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
  - Add app.logger to app.py, log to debug console, add logs to  end points: /api/questions/question_id/candidate-answers, /api/questions/from-filter, api/questions/search
  - In SideBar, use filter and search description or content of `pdf` documents, using vector search. Start search after at least 3 chars are entered. Use faiss index. Don't remove new lines to enable `paragraph` recognition.

- Recognize `sentence` inside of document, where `filter` was found, by end point, new line or end of document. There can be multiple sentences.

  - If filter was found in `description` only, not in the `content`, create question, treat whole `content` as the `answer`, add answer and assign to question. 
  
  - else When some documents are found, recognize `paragraph` by empty line or end of doc. Treat the whole `paragraph` inside of which `sentence` was found, as the `answer`, also treat the next `paragraph` as the `answer`. There can be many paragraphs that `filter` satisfies. 

    -- If document(s) have been found,  order documents by `created_at` ascending
      --- for each `sentence` recognized in document
        ---- find question, by using `sentence`, use exact search, 
          ------ if question is not found, create a new `question` with text equal to `sentence`
          ------ else if document `created_at` is newer than correspoding `question.modified_at`
            -------- add `answers` recognized to the `answers` table, avoid duplicate
            -------- assign answers to the `question`
- In SideBar when showing `Related documents` replace `\n` and other whitespaces to corresponding html tags like `<br>`. Show 5 lines, and enable vertical scroll.
- for answer card do not show current.short_desc, just description

   
## Definition of done
- [x] Documents are searchable via FAISS vector search by question text
- [x] Sidebar candidate answers use vector search instead of SOUNDEX
- [x] Sidebar filter that matches no question falls back to a document search, and a matched document causes the filter to be saved as a new question with vector-searched candidate answers
- [x] Question search (`GET /api/questions/search`) uses FAISS vector search instead of `LIKE`, with a distance cutoff so unrelated filters still report no match
