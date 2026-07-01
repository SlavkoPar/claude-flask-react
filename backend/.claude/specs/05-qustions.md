# Spec: Groups with Questions

## Overview
 For Groups maintenance, at `frontend` implement route `/groups`, as the protected route. 
 Create react component `Group` with CRUD operations for `groups`. 
 At `backend` implement coresponding end points. 
 One `Group` can have many child `groups`


## Depends on
- Step 1: Database setup (schema must exist)
- Step 2: google-authentication (user accounts must be creatable)


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


## 12. Expected Behavior


## Templates

## Files to change
- `app.py` 


## Files to create

## New dependencies
No new dependencies. 

## Error Handling Expectations

- Inserting group with invalid `user_id` → should fail (foreign key constraint)

### `Group` react component` 
- Create `GroupList` and `GroupRow` React components. Inside `GroupRow` use `GroupList` component
- Renders all groups as a **tree** nested by `parent_id`, ordered by name.
- Every group item has 5px top/bottom padding.
- Each row shows an expand/collapse toggle when it has child groups.
  <!-- - On the current user's own rows: -->
  - On the current row:
  - a `group` with **no questions** shows an `add group` link
    (`/groups/add?parent=<id>`, which pre-selects the parent)
  - a group with **no child groups** shows an `add question` link
    (to the group edit page's Questions section)
  - plus `Edit` and `Delete` 
  <!-- (owner-scoped, from Steps 8–9) -->
- The "Groups" navbar link is present.
- Filter `groups` by name, and parent group

## Rules for implementation
- create SQL tables
- import rows from `database/import/groups.json` and `database/import/questions.json`
    - All linked to the demo user (`user_id = 1`)
    - Preserve each group's explicit `id`
    - Insert parents before children so foreign keys resolve

- for each group row 
   - which has no questions, enable button for adding of child groups, text `add group`
   - enable button for expand and collapse of the child groups
   - which has no child groups, enable button for adding of questions
   - replace `q' with image `/static/Q.png'
- one group can have many questions
- count num_of_questions
- put link groups in base
- filter groups by name
- set top and bottom paddings, for every group item,  to 5px
- in `templates/groups/group_edit.html` implement section `Questions` for maintenance of questions (add, edit, delete)
- make `Questions` section always visible
- put 'Add Question' button to the top of the `Questions` section
- put 'Questions' section inside of group form, before 'Save Changes' button
- for question row display `num_of_Fixed` field with text `clicks to Fixed` 

-- Open Modal when click od "Edit Question" 
-- Modal width: 60% height: 80%
-- keep vertical scroll position after update


## Definition of done
- [ ]  Groups imported from `database/import/groups.json`
- [ ] Visiting `/groups` without being logged in redirects to `/login`
