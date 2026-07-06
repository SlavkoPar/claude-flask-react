# Spec: Groups

## Overview
 One `Group` can have many child `groups`
 For Groups maintenance, at `frontend` implement route `/groups`, as the protected route, 
 create jsx page `src/pages/Groups.jsx`, and link to it
 Create react component `Group` for CRUD operations for `/groups`. 
 At `backend` implement coresponding end points. 


## Depends on
- Step 1: Database setup (schema must exist)
- Step 2: google-authentication (user accounts must be creatable)


## Database changes

## Create table `groups`

### groups

| Column | Type | Constraints |
| --- | --- | --- |
| id | INTEGER | Primary key, autoincrement |
| parent_id | INTEGER | Foreign key → groups.id |
| user_id | INTEGER | Foreign key → users.id, not null |
| name | TEXT | Not null |
| description | TEXT | Nullable |
| has_child_groups | BOOLEAN | Default False 
| created_at | TEXT | Default datetime('now') |


## 12. Expected Behavior

## Files to change
- `app.py` 


## Files to create
- `src/pages/Groups.jsx`
- `src/components/group/Group.jsx`
- `src/components/group/List.jsx`
- `src/components/group/Row.jsx`

## New dependencies
No new dependencies. 

## Error Handling Expectations

- Inserting group with invalid `user_id` → should fail (foreign key constraint)

## Rules for implementation
  ### backend
  #### import rows from `database/import/groups.json`
      - All linked to the demo user (`user_id = 1`)
      - Preserve each group's explicit `id`
      - Insert parents before children so foreign keys resolve

  #### Validation rules for Group Form, for POST and PUT:
    - `name`: required, non-blank after `strip()`
    - `parent_id`: blank → `None`; otherwise must be the id of one of the groups, else an error
    - `description`: optional; `strip()`; store `None` if blank
    - On any validation error, return the message and the submitted values pre-filled
  
  ### frontend
  - put link `Groups` to navbar
  - Filter `groups` by name, and parent group
  - set top and bottom paddings, for every group item,  to 1px
  - remove btn-link from buttons
  - create and use scss classes for tree 
  - move links `add group` and `delete` to the right end of row
  - for `Group` form create section `Questions` always visible
  - put `folder` icon at the start of `group` row, color gray, margin-left: 5px

  - create page `src/pages/Groups.jsx`
  - create javascript model `src/model/Group.ts`
  - create javascript model `src/model/GroupRow.ts` with fields: `id`, `name`, `description`, `has_child_groups`

  - Create groups `List` and `Row` React components. Inside of `Row` use `List` component.
  - Render all groups as a **tree** nested by `parent_id`, ordered by name.
  - show all groups regardless of creator
  -- only author can delete group that he/she created
  - use model `GroupRow` for group row
  - Every group's item has 5px top/bottom padding.
  - Each row show an expand/collapse icon, to toggle when its child groups.
  - On the current row:
    -- a `group` with **no questions** shows an `add group` link
      (`/groups/add?parent=<id>`, which pre-selects the parent)
    -- `edit link` attach to name
    -- `has_child_groups` relate to `expand` icon
    -- show button `Delete` 
    -- update `has_child_groups` afer add or update group


  #### for each group row 
  - which has no questions, enable button for adding of child groups, text `add group`
  - enable button for expand and collapse of the child groups
  - which has no child groups, enable button for adding of questions

  
 
## Definition of done
- [ ] Groups imported from `database/import/groups.json`
- [ ] Visiting `/groups` without being logged in redirects to `/login`
