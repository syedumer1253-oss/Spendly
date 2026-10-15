# Spec: Registration

  ## Overview

  Implement user registration with validation, password hashing, and automatic login.

  Users create an account by providing name, email, and password. The system validates inputs, hashes the password with werkzeug, creates a user record, and logs the user in automatically on success the user shows a success message and then redirected to the login pages.
  Registration is the entry point for new users into Spendly.

  ---

  ## Depends on

  - Step 1 — Database Setup (users table, password hashing utilities)
  ---

  ## Routes

  - `GET /register` — Display registration form — public
  - `POST /register` — Handle registration form submission — public

  ---

  ## Database changes

  No new tables or columns. Uses existing `users` table with id, name, email (unique), password_hash, created_at.

  ---

  ## Templates

  **Create:**
  - `templates/register.html` — Registration form

  **Modify:**
  - `templates/base.html` — Add registration link in navbar

  ---

  ## Files to change

  - `app.py` — Add registration route and handler
  - `templates/base.html` — Update navbar

  ---

  ## Files to create

  - `templates/register.html` — Registration form template

  ---

  ## New dependencies

  None. Uses werkzeug.security (already installed).

  ---

  ## Rules for implementation

  - Parameterized queries only (? placeholders)
  - Password hashed with werkzeug.security.generate_password_hash()
  - Email uniqueness via UNIQUE constraint
  - Session-based auth: set session["user_id"]
  - Redirect to /profile after success
  - All templates extend base.html
  - Use CSS variables only

  ---

  ## Definition of done

  - [ ] Registration form displays correctly
  - [ ] All inputs validated (required fields, password min 8 chars)
  - [ ] Duplicate email rejected
  - [ ] Password hashed in database
  - [ ] User auto-logged in after registration
  - [ ] Redirects to /profile on success
  - [ ] Styling consistent with app

