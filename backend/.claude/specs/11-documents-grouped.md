# Spec: Documents Grouped

> Status: implemented (2026-07-10). Notes on how it was built vs. this draft:
> - `documents.group_id` was added as a nullable `INTEGER REFERENCES groups(id)`
>   rather than `NOT NULL` — SQLite can't retrofit a `NOT NULL` foreign key
>   onto a table with existing rows via `ALTER TABLE`. Pre-existing documents
>   (and the seeded ones from `documents.json`, which also predate grouping)
>   are backfilled by `backfill_document_groups()` into an "Uncategorized"
>   root group — the same one `10-vector-search.md`'s sidebar-filter feature
>   already creates on demand — keyed by each document's own `user_id`.
>   Application-level validation (`_parse_document_payload` in `app.py`)
>   requires a real `group_id` for every create/update going forward, the
>   same way question creation already requires one.
> - `GET /api/documents` gained an optional `group_id` filter (same convention
>   as `GET /api/groups`'s `parent_id`) and now also returns `group_id` +
>   `group_name` (via a `LEFT JOIN groups`) on every row, ordered by group
>   name then description, so the frontend can bucket a single flat response
>   into per-group sections instead of needing one request per group.
> - Grouping/collapse-expand is client-side only: `components/document/List.jsx`
>   fetches the (already group-sorted) flat list and buckets it into sections;
>   a new `components/document/GroupSection.jsx` renders each bucket as a
>   collapsible header (reusing the same folder icon and collapse/expand
>   toggle pattern as `components/group/Row.jsx`'s own tree), defaulting to
>   expanded, with that group's `Row`s nested inside when open.
> - The "documentGroup icon" rule was read as the icon on that new
>   group-header row (a "document group" row), not on each individual
>   document row — `Row.jsx` itself is unchanged. It reuses the existing
>   `assets/folder.svg` rather than introducing a new icon with no design
>   spec.
> - "Filter documents by description, and group": `pages/Documents.jsx` now
>   has both the existing description autocomplete and a `Form.Select`
>   populated from `/api/groups/options` (the same flat options endpoint
>   `Groups.jsx`/`Group.jsx` already use), passed down as `group_id`.
> - `DocumentForm.jsx` (Add) and `DocumentModal.jsx` (Edit/View) both gained a
>   required "Group" select using the same `/api/groups/options` data; the
>   modal disables it in read-only mode instead of using `readOnly` (which
>   doesn't apply to `<select>`).

## Overview

## Depends on
- Step 10: vector search
- Step 9: Documents
- Step 6: Answers

## Routes
- GET /documents — render the documents list page, grouped by group

## Database changes
- add field to `documents`
   group_id | INTEGER | Foreign key → groups.id (nullable at the DB level for
   pre-existing rows; required by the application for all new/updated
   documents) |

## Create table


## 12. Expected Behavior


## Files to change
- `app.py`
- `database/db.py`
- `frontend/src/pages/Documents.jsx`
- `frontend/src/pages/DocumentForm.jsx`
- `frontend/src/components/document/List.jsx`
- `frontend/src/components/document/DocumentModal.jsx`
- `frontend/src/model/documents/Document.ts`
- `frontend/src/model/documents/DocumentRow.ts`
- `frontend/src/scss/custom.scss`

## Files to create
- `frontend/src/components/document/GroupSection.jsx`

## New dependencies
No new dependencies.

## Rules for implementation

- filter documents by description, and group
- enable grouping of documents by group
- at the document row, add icon documentGroup
- enable collapse/expand button

## Definition of done
- [x] Visiting `/documents` without being logged in redirects to `/login`
- [x] Documents list is grouped by group, each group collapsible/expandable (default expanded)
- [x] Documents can be filtered by description and by group at the same time
- [x] Adding/editing a document requires selecting a group
- [x] Pre-existing documents (from before grouping) are auto-filed under "Uncategorized"
