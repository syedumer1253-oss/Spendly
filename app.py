from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from database.db import get_db, init_db, seed_db
import os


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

# Initialize database on startup
with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def login_required(f):
    """Decorator to require login for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """Get the current logged-in user's data."""
    if "user_id" not in session:
        return None
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],))
    user = cursor.fetchone()
    db.close()
    return user


# ------------------------------------------------------------------ #
# Routes — Public                                                     #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        error = None

        if not name:
            error = "Name is required."
        elif not email:
            error = "Email is required."
        elif not password or len(password) < 8:
            error = "Password must be at least 8 characters."

        if not error:
            db = get_db()
            cursor = db.cursor()
            try:
                cursor.execute(
                    "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                    (name, email, generate_password_hash(password))
                )
                db.commit()
                user_id = cursor.lastrowid
                db.close()

                # Log the user in
                session["user_id"] = user_id
                return redirect(url_for("profile"))
            except Exception as e:
                error = "Email already registered." if "UNIQUE constraint failed" in str(e) else str(e)
                db.close()

        return render_template("register.html", error=error)

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        error = None

        if not email:
            error = "Email is required."
        elif not password:
            error = "Password is required."

        if not error:
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            db.close()

            if user is None or not check_password_hash(user["password_hash"], password):
                error = "Invalid email or password."

        if not error:
            session["user_id"] = user["id"]
            return redirect(url_for("profile"))

        return render_template("login.html", error=error)

    return render_template("login.html")


# ------------------------------------------------------------------ #
# Routes — Protected                                                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
@login_required
def profile():
    user = get_current_user()
    db = get_db()
    cursor = db.cursor()

    # Get expense summary
    cursor.execute("""
        SELECT category_id,
               (SELECT name FROM categories WHERE id = expenses.category_id) as category_name,
               SUM(amount) as total
        FROM expenses
        WHERE user_id = ?
        GROUP BY category_id
        ORDER BY total DESC
    """, (session["user_id"],))
    category_totals = cursor.fetchall()

    # Get recent expenses
    cursor.execute("""
        SELECT e.*, c.name as category_name
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.user_id = ?
        ORDER BY e.date DESC
        LIMIT 10
    """, (session["user_id"],))
    recent_expenses = cursor.fetchall()

    db.close()

    return render_template("profile.html", user=user, category_totals=category_totals, recent_expenses=recent_expenses)


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/expenses/add", methods=["GET", "POST"])
@login_required
def add_expense():
    db = get_db()
    cursor = db.cursor()

    # Get user's categories
    cursor.execute("SELECT id, name FROM categories WHERE user_id = ? ORDER BY name", (session["user_id"],))
    categories = cursor.fetchall()
    db.close()

    if request.method == "POST":
        category_id = request.form.get("category_id", "").strip()
        amount = request.form.get("amount", "").strip()
        date = request.form.get("date", "").strip()
        description = request.form.get("description", "").strip()

        error = None

        if not category_id:
            error = "Category is required."
        elif not amount:
            error = "Amount is required."
        elif not date:
            error = "Date is required."

        if not error:
            try:
                amount_float = float(amount)
                if amount_float <= 0:
                    error = "Amount must be greater than zero."
            except ValueError:
                error = "Amount must be a valid number."

        if not error:
            db = get_db()
            cursor = db.cursor()
            try:
                cursor.execute("""
                    INSERT INTO expenses (user_id, category_id, amount, date, description)
                    VALUES (?, ?, ?, ?, ?)
                """, (session["user_id"], category_id, amount_float, date, description or None))
                db.commit()
                db.close()
                return redirect(url_for("profile"))
            except Exception as e:
                error = str(e)
                db.close()

        return render_template("add_expense.html", categories=categories, error=error, form_data={
            "category_id": category_id,
            "amount": amount,
            "date": date,
            "description": description
        })

    return render_template("add_expense.html", categories=categories, form_data={})


@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_expense(id):
    db = get_db()
    cursor = db.cursor()

    # Get the expense — verify it belongs to the current user
    cursor.execute("""
        SELECT e.*, c.name as category_name
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.id = ? AND e.user_id = ?
    """, (id, session["user_id"]))
    expense = cursor.fetchone()

    if not expense:
        db.close()
        return "Expense not found", 404

    # Get user's categories
    cursor.execute("SELECT id, name FROM categories WHERE user_id = ? ORDER BY name", (session["user_id"],))
    categories = cursor.fetchall()
    db.close()

    if request.method == "POST":
        category_id = request.form.get("category_id", "").strip()
        amount = request.form.get("amount", "").strip()
        date = request.form.get("date", "").strip()
        description = request.form.get("description", "").strip()

        error = None

        if not category_id:
            error = "Category is required."
        elif not amount:
            error = "Amount is required."
        elif not date:
            error = "Date is required."

        if not error:
            try:
                amount_float = float(amount)
                if amount_float <= 0:
                    error = "Amount must be greater than zero."
            except ValueError:
                error = "Amount must be a valid number."

        if not error:
            db = get_db()
            cursor = db.cursor()
            try:
                cursor.execute("""
                    UPDATE expenses
                    SET category_id = ?, amount = ?, date = ?, description = ?
                    WHERE id = ? AND user_id = ?
                """, (category_id, amount_float, date, description or None, id, session["user_id"]))
                db.commit()
                db.close()
                return redirect(url_for("profile"))
            except Exception as e:
                error = str(e)
                db.close()

        return render_template("edit_expense.html", expense=expense, categories=categories, error=error, form_data={
            "category_id": category_id,
            "amount": amount,
            "date": date,
            "description": description
        })

    return render_template("edit_expense.html", expense=expense, categories=categories, form_data={})


@app.route("/expenses/<int:id>/delete", methods=["POST"])
@login_required
def delete_expense(id):
    db = get_db()
    cursor = db.cursor()

    # Verify the expense belongs to the current user
    cursor.execute("SELECT id FROM expenses WHERE id = ? AND user_id = ?", (id, session["user_id"]))
    expense = cursor.fetchone()

    if not expense:
        db.close()
        return "Expense not found", 404

    # Delete the expense
    cursor.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (id, session["user_id"]))
    db.commit()
    db.close()

    return redirect(url_for("profile"))


if __name__ == "__main__":
    app.run(debug=True, port=5001)
