# Spec: Google Authentication

## Overview
Implement user registration, so new visitors can create a Q&A account. 

After registration validate input, hashe the password, and insert a new row into the `users` table. This is the entry point for all authenticated features that follow.

## Depends on
- Step 01 — Database setup (`users` table, `get_db()`)

## Routes

## Database changes
No new tables or columns. The existing `users` table (id, name, email, password_hash, created_at) covers all requirements.

A new DB helper must be added to `database/db.py`:
- `create_user(name, email, password)` — hashes the password with `werkzeug`, inserts a row into `users`, returns the new user's `id`. Raises `sqlite3.IntegrityError` if the email is already taken (UNIQUE constraint).

## Templates

## Files to change
- `database/db.py` — add `create_user()` helper

## Files to create
None.

## New dependencies

## Rules for implementation
- implement `google authentication`
- `app.secret_key` must be set in `app.py` for `flash()` to work (use a hardcoded dev string for now)
- Server-side validation must check:
  1. All fields are non-empty
  2. `password == confirm_password`
  3. Email is not already registered (catch `sqlite3.IntegrityError`)
- On any validation failure, re-render the form with a flashed error message — do not redirect
- Use `abort(405)` if an unsupported HTTP method reaches the route
- Use CSS variables — never hardcode hex values
- Use `url_for()` for every internal link — never hardcode URLs

## Definition of done
- [ ] Submitting with mismatched passwords re-renders the form with an error message, no DB insert
- [ ] Submitting with an already-registered email re-renders the form with "Email already registered" error
- [ ] Submitting with any empty field re-renders the form with a validation error
- [ ] Password is stored as a hash — never plaintext — verifiable by inspecting `my.db`
- [ ] No duplicate user is created on repeated valid submissions with the same email
