# Spec: Questions

## Overview
 One `Group` can have many `questions`. Show them in `Questions` section of `Group` form.
 Inside of section `Questions`, enable CRUD operations for `questions`.


## Depends on
- Step 1: Database setup (schema must exist)
- Step 2: google-authentication (user accounts must be creatable)
- Step 4: Groups


## Database changes

## Create table

### questions

| Column | Type | Constraints |
| --- | --- | --- |
| id | INTEGER | Primary key, autoincrement |
| user_id | INTEGER | Foreign key → users.id, not null |
| group_id | INTEGER | Foreign key → group.id, not null |
| text | TEXT | Not null |
| description | TEXT | Nullable |
| created_at | TEXT | Default datetime('now') |

## Update table `groups`
- add column `num_of_questions` | INTEGER | Default 0

## 12. Expected Behavior


## Files to change
- `app.py` 


## Files to create

## New dependencies
No new dependencies. 

## Error Handling Expectations

- Inserting question with invalid `user_id` → should fail (foreign key constraint)


## Rules for implementation
- import rows from `database/import/questions.json`
    - All linked to the demo user (`user_id = 1`)
    - Preserve each group's explicit `id`
    - Insert parents before children so foreign keys resolve


  - On the current `group` row:
  - `group row` with **no questions** shows an `add group` link
    (`/groups/add?parent=<id>`, which pre-selects the parent)
  - `group row` with **no child groups** shows an `add question` link
  - link `Edit` to `question.text`
  - link `Delete` question

- for each `group` row 
   - show `num_of_questions` with icon `/src/assets/Q.png'
- count num_of_questions, after add or delete question
- in `Group Form` implement section `Questions` for maintenance of questions (add, edit, delete)
- make `Questions` section always visible
- put `Add Question` button to the top of the `Questions` section
- after adding, edititng or deleting a `question`, refresh section`Questions` only, do not reload the Group, do not navigate `groups`
- put 'Questions' section inside of `group` form, before 'Save Changes' button
- for question row put icon Q.png at the start of row

-- Open Modal when click od "Edit Question" 
-- Modal width: 60% height: 80%
-- keep vertical scroll position after update


## Definition of done
- [ ]  Questions imported
