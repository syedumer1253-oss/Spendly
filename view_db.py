#!/usr/bin/env python3
"""
View database contents in table format.
"""

from database.db import get_db
from tabulate import tabulate


def view_users():
    """Display users table."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, name, email, created_at FROM users")
    users = cursor.fetchall()
    db.close()

    if users:
        print("\n" + "="*80)
        print("USERS TABLE")
        print("="*80)
        headers = ["ID", "Name", "Email", "Created At"]
        rows = [[u["id"], u["name"], u["email"], u["created_at"]] for u in users]
        print(tabulate(rows, headers=headers, tablefmt="grid"))
    else:
        print("\nNo users found.")


def view_categories():
    """Display categories table."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT c.id, c.user_id, u.name as user_name, c.name, c.created_at
        FROM categories c
        JOIN users u ON c.user_id = u.id
        ORDER BY c.user_id, c.name
    """)
    categories = cursor.fetchall()
    db.close()

    if categories:
        print("\n" + "="*80)
        print("CATEGORIES TABLE")
        print("="*80)
        headers = ["ID", "User ID", "User Name", "Category", "Created At"]
        rows = [[c["id"], c["user_id"], c["user_name"], c["name"], c["created_at"]] for c in categories]
        print(tabulate(rows, headers=headers, tablefmt="grid"))
    else:
        print("\nNo categories found.")


def view_expenses():
    """Display expenses table."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT e.id, e.user_id, u.name as user_name, e.category_id, c.name as category,
               e.amount, e.date, e.description, e.created_at
        FROM expenses e
        JOIN users u ON e.user_id = u.id
        JOIN categories c ON e.category_id = c.id
        ORDER BY e.user_id, e.date DESC
    """)
    expenses = cursor.fetchall()
    db.close()

    if expenses:
        print("\n" + "="*80)
        print("EXPENSES TABLE")
        print("="*80)
        headers = ["ID", "User ID", "User", "Cat ID", "Category", "Amount (₹)", "Date", "Description", "Created At"]
        rows = [
            [
                e["id"],
                e["user_id"],
                e["user_name"],
                e["category_id"],
                e["category"],
                f"₹{e['amount']:.2f}",
                e["date"],
                e["description"][:30] if e["description"] else "—",
                e["created_at"]
            ]
            for e in expenses
        ]
        print(tabulate(rows, headers=headers, tablefmt="grid"))
    else:
        print("\nNo expenses found.")


def view_summary():
    """Display summary statistics."""
    db = get_db()
    cursor = db.cursor()

    # User count
    cursor.execute("SELECT COUNT(*) as count FROM users")
    user_count = cursor.fetchone()["count"]

    # Category count
    cursor.execute("SELECT COUNT(*) as count FROM categories")
    category_count = cursor.fetchone()["count"]

    # Expense count
    cursor.execute("SELECT COUNT(*) as count FROM expenses")
    expense_count = cursor.fetchone()["count"]

    # Total expense amount
    cursor.execute("SELECT SUM(amount) as total FROM expenses")
    total_amount = cursor.fetchone()["total"] or 0

    db.close()

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total Users:      {user_count}")
    print(f"Total Categories: {category_count}")
    print(f"Total Expenses:   {expense_count}")
    print(f"Total Amount:     ₹{total_amount:.2f}")


if __name__ == "__main__":
    view_summary()
    view_users()
    view_categories()
    view_expenses()
    print("\n")
