# Spec: Answers and Answer

> Status: implemented (2026-06-15). Notes on how it was built vs. this draft:
> - Tables created as `answers` and `question_answers` (SQL name; spec wrote
>   "question_answers" which isn't a valid identifier). `num_of_assigned_answers`
>   column added to `questions` and kept in sync by the query helpers.
> - `/answers` list page filters by name (server-side `q` + a `<datalist>`
>   autocomplete). Add is a page (`add_answer.html`); **Edit uses a modal**
>   (60%×80%, scroll preserved) and **Delete is inline `confirm()`** — so
>   `edit_answer.html` / `delete_answer.html` were intentionally not created
>   (same pattern as groups/questions).
> - Assignment lives on the **group edit page**: each question row shows its
>   assigned-answer count and an "Assigned answers" modal to add (from
>   unassigned, with autocomplete filter) / remove. Routes:
>   `POST /questions/<qid>/answers/assign` and
>   `POST /questions/<qid>/answers/<aid>/unassign`.
> - Global `.form-input` padding set to `0.125rem 0.875rem` per the spec; answer
>   rows get a distinct style (accent-2 colours, 0.1rem row padding).
> - Tests: `tests/test_answers.py`.

## Overview

## Depends on
- Step 1: Database setup (schema must exist)
- Step 2: google-authentication (user accounts must be creatable)
- Step 5: Questions

## Routes
- GET /answers — render the answers list page

## Database changes

## Create table
### answers

| Column | Type | Constraints |
| --- | --- | --- |
| id | INTEGER | Primary key, autoincrement |
| user_id | INTEGER | Foreign key → users.id, not null |
| short_desc | TEXT | Not null |
| description | TEXT | Nullable |
| link | TEXT | Nullable |
| created_at | TEXT | Default datetime('now') |

### question_answers

| Column | Type | Constraints |
| --- | --- | --- |
| id | INTEGER | Primary key, autoincrement |
| question_id | INTEGER | Foreign key → questions.id, not null |
| answer_id | INTEGER | Foreign key → answers.id, not null |
| clicks_to_Fixed | INTEGER | Default 0 |
| user_id | INTEGER | Foreign key → users.id, not null |
| created_at | TEXT | Default datetime('now') |




## 12. Expected Behavior



## Files to change
- `app.py` 

## Files to create
   - `model/answers/Answer.ts`
   - `model/answers/AnswerRow.ts`


   - `src/pages/Answers.jsx`
   - `src/components/answer/List.jsx`
   - `src/components/answer/Row.jsx`


## New dependencies
No new dependencies. 

- filter answers by name


## Rules for implementation

- **Modify**: add an "Answers" link to navbar, visible only when `session.user_id` is set
- import rows from `database/import/answers.json` and `database/import/question_answers.json`

- add field number of `assigned answers` in table `questions`
- for question row display number of `assigned answers`
- create section `Assigned answers` in question form
- create modal for selection of the answers which are not already assigned, Modal width: 50% height: 70%
- for answers, and aswers in modal for selection of unassigned answers,  enable autocomplete filter by name
- for answers, set top and bottom paddings to: 1px 
- give the same css styles for assigned-answers as for answers
- set top and bottom paddings to 0.1rem for all answer, question and answer rows

-- Open Modal when click od "Edit Answer" 
-- Modal width: 60% height: 80%
-- keep vertical scroll position after update

- implement CRUD operations for `Answers`
- In the answer row, put 'Edit link to short_desc
- put icon `A.png` as the first column of the answer row, justify content left
- in question edit form put section `AssignedAnswers` with its assigned answers, visible 3 rows, for rest enable vertical scroll
- for assigned answer row, put icon A.png at the start of row
- for question row allign row to the left, replace `Assigned answers:` with icon A.png
- for rows: group, question, answer, assigned-answer, replace `Delete` with `X` icon and keep to the right

- in question edit form, create button `Assign answer`, on click open modal to add assign answers from unassigned, with autocomplete filter
## Definition of done
- [ ] Visiting `/answers` without being logged in redirects to `/login`
