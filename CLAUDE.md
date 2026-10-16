# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running & Development

**Start the application:**
```bash
python app.py
```
The app runs on `http://localhost:5001` in debug mode.

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Initialize/reset the database:**
```bash
python database/db.py
```
This creates tables and seeds sample data. The database file is stored at `database/expenses.db`.

**Running tests:**
```bash
pytest
```
The project uses pytest and pytest-flask. Currently no test files exist; add tests to the root directory as `test_*.py` or `*_test.py`.

## Architecture

This is a Flask web application for tracking personal expenses with user authentication.

**Core Components:**

- **app.py**: Main Flask application containing all routes and business logic
  - Public routes: landing, terms, privacy, register, login
  - Protected routes: profile, logout, expense CRUD operations
  - Authentication uses session cookies with `@login_required` decorator
  - Password hashing via werkzeug

- **database/db.py**: SQLite database layer
  - `get_db()`: Returns a connection with row_factory and foreign keys enabled
  - `init_db()`: Creates three tables (users, categories, expenses) idempotently
  - `seed_db()`: Populates sample data for development

- **Templates** (Jinja2): HTML pages in `templates/` directory
  - `base.html`: Base layout with navigation
  - Auth pages: `login.html`, `register.html`
  - Expense pages: `profile.html` (dashboard), `add_expense.html`, `edit_expense.html`
  - Static pages: `landing.html`, `terms.html`, `privacy.html`

- **Static assets**: CSS and JavaScript in `static/` directory

**Database Schema:**

- **users**: id, name, email (unique), password_hash, created_at
- **categories**: id, user_id, name, created_at (user-scoped)
- **expenses**: id, user_id, category_id, amount, date, description, created_at (user-scoped)
- Foreign key constraints enabled; categories and expenses cascade delete with users

**Key Patterns:**

- User data isolation: all queries filter by `session["user_id"]`
- Form validation: required fields checked in routes before DB operations
- Error handling: exceptions caught and displayed to users (e.g., duplicate email on registration)
- Database connections: opened and closed per request (not pooled)

## Development Notes

- The app uses Flask sessions backed by the secret key in `app.secret_key` (set via `SECRET_KEY` env var, defaults to "dev-secret-key-change-in-production")
- Database initialization runs automatically on app startup
- All database queries use parameterized queries to prevent SQL injection
- Amount validation ensures expenses are greater than zero
- Date and description fields are optional on expense entries
