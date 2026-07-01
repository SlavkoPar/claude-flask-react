# Spec: Groups with Questions

## Overview
 One `Group` can have many child `groups`
 For Groups maintenance, at `frontend` implement route `/groups`, as the protected route. 
 Create react component `Group` with CRUD operations for `groups`. 
 At `backend` implement coresponding end points. 


## Depends on
- Step 1: Database setup (schema must exist)
- Step 2: google-authentication (user accounts must be creatable)


## Database changes

## Create table


### groups

| Column | Type | Constraints |
| --- | --- | --- |
| id | INTEGER | Primary key, autoincrement |
| parent_id | INTEGER | Foreign key → groups.id |
| user_id | INTEGER | Foreign key → users.id, not null |
| name | TEXT | Not null |
| description | TEXT | Nullable |
| num_of_questions | INTEGER | Default 0 |
| created_at | TEXT | Default datetime('now') |


## 12. Expected Behavior


## Templates

## Files to change
- `app.py` 


## Files to create
- `src/components/group/GroupList.jsx`
- `src/components/group/GroupRow.jsx`
- `src/pages/Groups.js`

## New dependencies
No new dependencies. 

## Error Handling Expectations

- Inserting group with invalid `user_id` → should fail (foreign key constraint)



## Rules for implementation
  ### backend
  #### create SQL table
  #### import rows from `database/import/groups.json`
      - All linked to the demo user (`user_id = 1`)
      - Preserve each group's explicit `id`
      - Insert parents before children so foreign keys resolve

  #### Validation rules for POST and PUT:
    - `name`: required, non-blank after `strip()`
    - `parent_id`: blank → `None`; otherwise must be the id of one of the groups, else an error
    - `description`: optional; `strip()`; store `None` if blank
    - On any validation error, return the message and the
      submitted values pre-filled
  
  ### frontend
  - one `group` can have many questions
  - count num_of_questions
  - put link `Groups` to navbar
  - Filter `groups` by name, and parent group
  - set top and bottom paddings, for every group item,  to 5px
  - for `Group` form create section `Questions`  always visible

  - create page `src/pages/Groups.jsx`
  - create javascript model `src/model/Group.ts`
  - create javascript model `src/model/GroupRow.ts` with fields: `id`, `name`, `description`, `num_of_questions`

  - Create `GroupList` and `GroupRow` React components. Inside `GroupRow` use `GroupList` component.
  - Render all groups as a **tree** nested by `parent_id`, ordered by name.
  - use model `GroupRow` for group row
  - Every group's item has 5px top/bottom padding.
  - Each row shows an expand/collapse toggle when it has child groups.
  - On the current row:
    -- a `group` with **no questions** shows an `add group` link
      (`/groups/add?parent=<id>`, which pre-selects the parent)
    -- a group with **no child groups** shows an `add question` link
      (to the group edit page's Questions section)
    -- `edit link` attach to name
    -- show button `Delete` 


  #### for each group row 
  - which has no questions, enable button for adding of child groups, text `add group`
  - enable button for expand and collapse of the child groups
  - which has no child groups, enable button for adding of questions

  
 
## Definition of done
- [ ]  Groups imported from `database/import/groups.json`
- [ ] Visiting `/groups` without being logged in redirects to `/login`
