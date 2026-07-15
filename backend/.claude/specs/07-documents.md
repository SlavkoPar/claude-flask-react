# Spec: Documents

> Status: implemented (2026-07-07). Notes on how it was built vs. this draft:
> - Added `pypdf` as a real dependency despite the "No new dependencies" line
>   below — PDF-to-text extraction isn't feasible with the stdlib, and the
>   "enable upload of pdf, convert it to text" rule overrides it (same kind of
>   draft/rules mismatch as in `06-answers.md`).
> - `POST /api/documents/extract-pdf` accepts a multipart PDF upload and
>   returns a JSON string — `{"filename", "pages": [...]}`, one entry per
>   PDF page — which fills the `Content` textarea (still a plain `TEXT`
>   column; it just holds JSON when the source was a PDF). It stays editable
>   before save. The uploaded file itself is kept in memory client-side and
>   re-sent as part of the final `multipart/form-data` `POST`/`PUT
>   /api/documents`, which stores it in new `documents.pdf_filename`/
>   `pdf_data` (BLOB) columns — so both the original PDF and its
>   JSON-converted/edited text are persisted, per the updated rule. Editing a
>   document without re-uploading a PDF leaves the stored one untouched.
>   `GET /api/documents/<id>/pdf` streams it back out; the modal shows a
>   "Download original PDF" link when one is stored.
> - Ownership: `documents.user_id` is enforced server-side — `PUT`/`DELETE`
>   return 403 for non-creators. The list is visible to every logged-in user;
>   `Row.jsx` only renders the delete `X` for the creator, and clicking a
>   description always opens `DocumentModal` (read-only for non-creators,
>   editable for the creator).
> - `GET /api/documents` omits `content` (can be large); the modal fetches
>   the full record by id on open.
> - Icon: no `Doc.png` asset existed, so `assets/Doc.svg` was added, following
>   the same pattern as `A.png`/`Q.png`.
> - Filter uses the same `name` query param convention as groups/answers
>   (filters by `description`, despite the param name).
> - Add is a page (`DocumentForm.jsx`); Edit/View uses a modal (60%×80%,
>   scroll position preserved) — same split as answers/groups.

## Overview

## Depends on
- Step 2: google-authentication (user accounts must be creatable)
- Step 6: Answers

## Routes
- GET /documents — render the documents list page

## Database changes

## Create table
### documents

| Column | Type | Constraints |
| --- | --- | --- |
| id | INTEGER | Primary key, autoincrement |
| user_id | INTEGER | Foreign key → users.id, not null |
| group_id | INTEGER | Foreign key → groups.id, not null |
| description | TEXT | Not null |
| content | TEXT | Not null |
| link | TEXT | Nullable |
| pdf_filename | TEXT | null |
| has_pdf | BOOLEAN | Default 0 |
| created_at | TEXT | Default datetime('now') |

## 12. Expected Behavior


## Files to change
- `app.py` 

## Files to create
   - `src/pages/Documents.jsx`

   - `model/documents/Document.ts`
   - `model/documents/DocumentRow.ts`

   - `src/components/document/List.jsx`
   - `src/components/document/Row.jsx`


## New dependencies
No new dependencies. 


## Rules for implementation



- **Modify**: add an "Documents" link to navbar, visible only when `session.user_id` is set
- import rows from `database/import/documents.json`

- make autocomplete filter documents by description, and group
- enable grouping of documents by group
- at the document row, add icon documentGroup
- enable collapse/expand button
- make documents visible for all the users, but only creator can modify or delete its document
- for documents, set top and bottom paddings to: 1px 
- set top and bottom paddings to 0.08rem for all  document rows

-- Open Modal when click od "Edit Document" 
-- Modal width: 60% height: 80%
-- keep vertical scroll position after update

- in `Document` form, enable upload of `pdf` document, store it to the separate folder at server, convert it to text fromat and store to `Content` field of document
- implement CRUD operations for `Documents`
- In the document row, put 'Edit link to short_desc
- put icon `Doc` as the first column of the document row, justify content left
- for rows of document, replace `Delete` with `X` icon and keep to the right
- make document content 3 rows height, with enabled vertical scroll

## Definition of done
- [x] Visiting `/documents` without being logged in redirects to `/login`
