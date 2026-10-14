import sqlite3
from pathlib import Path
import os
from werkzeug.security import generate_password_hash


DATABASE_PATH = Path(__file__).parent.parent / "spendly.db"


def get_db():
    """Returns a SQLite connection with row_factory and foreign keys enabled."""
    db = sqlite3.connect(str(DATABASE_PATH))
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def init_db():
    """Creates all tables using CREATE TABLE IF NOT EXISTS."""
    db = get_db()
    cursor = db.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Categories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)

    # Expenses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            date DATE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE SET NULL
        )
    """)

    db.commit()
    db.close()


def seed_db():
    """Inserts sample data for development."""
    db = get_db()
    cursor = db.cursor()

    # Check if sample data already exists
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        db.close()
        return

    # Insert sample user
    cursor.execute("""
        INSERT INTO users (name, email, password_hash)
        VALUES (?, ?, ?)
    """, ("Demo User", "demo@spendly.com", generate_password_hash("demo123")))

    user_id = cursor.lastrowid

    # Insert sample categories
    categories = ["Bills", "Food", "Health", "Transport", "Entertainment", "Shopping", "Other"]
    for category_name in categories:
        cursor.execute("""
            INSERT INTO categories (user_id, name)
            VALUES (?, ?)
        """, (user_id, category_name))

    # Get category IDs for sample expenses
    cursor.execute("SELECT id FROM categories WHERE user_id = ?", (user_id,))
    category_ids = [row[0] for row in cursor.fetchall()]

    # Insert sample expenses
    sample_expenses = [
        (user_id, category_ids[0], 4500.00, "2026-10-01", "Electricity bill"),
        (user_id, category_ids[1], 850.00, "2026-10-02", "Lunch at cafe"),
        (user_id, category_ids[2], 1200.00, "2026-10-03", "Doctor consultation"),
        (user_id, category_ids[3], 500.00, "2026-10-04", "Auto fare"),
        (user_id, category_ids[1], 450.00, "2026-10-05", "Dinner"),
        (user_id, category_ids[4], 1500.00, "2026-10-06", "Movie tickets"),
        (user_id, category_ids[5], 2000.00, "2026-10-07", "New shoes"),
        (user_id, category_ids[2], 500.00, "2026-10-08", "Gym membership"),
    ]

    for expense in sample_expenses:
        cursor.execute("""
            INSERT INTO expenses (user_id, category_id, amount, date, description)
            VALUES (?, ?, ?, ?, ?)
        """, expense)

    db.commit()
    db.close()


if __name__ == "__main__":
    # Initialize database and seed with sample data
    init_db()
    seed_db()
    print("[OK] Database initialized at:", DATABASE_PATH)
