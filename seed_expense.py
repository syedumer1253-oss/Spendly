#!/usr/bin/env python3
"""
Script to seed realistic expenses for a user across past months.
Usage: python seed_expense.py <user_id> <count> <months>
Example: python seed_expense.py 2 5 3
"""

import sys
import random
from datetime import datetime, timedelta
from database.db import get_db


# Category definitions with realistic Indian amounts (₹) and descriptions
CATEGORIES_CONFIG = {
    "Food": {
        "amounts": (50, 800),
        "descriptions": [
            "Lunch at restaurant", "Dinner with friends", "Groceries", "Coffee and snacks",
            "Cafe breakfast", "Food delivery", "Biryani dinner", "Street food",
            "Bakery items", "Tea and samosas", "Sweets", "Ice cream"
        ],
        "weight": 4  # Most common
    },
    "Transport": {
        "amounts": (20, 500),
        "descriptions": [
            "Auto ride", "Bus fare", "Taxi", "Fuel", "Metro card recharge",
            "Train ticket", "Bike repair", "Car maintenance", "Parking"
        ],
        "weight": 3
    },
    "Bills": {
        "amounts": (200, 3000),
        "descriptions": [
            "Electricity bill", "Water bill", "Internet bill", "Phone bill",
            "Gas bill", "Insurance", "Rent payment"
        ],
        "weight": 2
    },
    "Health": {
        "amounts": (100, 2000),
        "descriptions": [
            "Doctor consultation", "Medicine purchase", "Gym membership",
            "Lab test", "Dental checkup", "Hospital visit", "Medical supplies"
        ],
        "weight": 1
    },
    "Entertainment": {
        "amounts": (100, 1500),
        "descriptions": [
            "Movie tickets", "Concert tickets", "Streaming subscription",
            "Gaming purchase", "Book purchase", "Sports event"
        ],
        "weight": 1
    },
    "Shopping": {
        "amounts": (200, 5000),
        "descriptions": [
            "New shoes", "Clothing", "Electronics", "Home decor",
            "Gifts", "Accessories", "Furniture", "Bags"
        ],
        "weight": 2
    },
    "Other": {
        "amounts": (50, 1000),
        "descriptions": [
            "Miscellaneous", "Donation", "Tips", "Personal care",
            "Hobbies", "Repairs"
        ],
        "weight": 1
    }
}


def parse_arguments():
    """Parse command-line arguments."""
    if len(sys.argv) != 4:
        print("Usage: /seed-expense <user_id> <count> <months>")
        print("Example: /seed-expense 1 50 6")
        sys.exit(1)

    try:
        user_id = int(sys.argv[1])
        count = int(sys.argv[2])
        months = int(sys.argv[3])
    except ValueError:
        print("Usage: /seed-expense <user_id> <count> <months>")
        print("Example: /seed-expense 1 50 6")
        sys.exit(1)

    return user_id, count, months


def verify_user_exists(user_id):
    """Verify user exists in database."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    db.close()

    if not user:
        print(f"No user found with id {user_id}.")
        sys.exit(1)


def get_user_categories(user_id):
    """Get all category IDs for the user."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, name FROM categories WHERE user_id = ?", (user_id,))
    categories = cursor.fetchall()
    db.close()

    return {row["name"]: row["id"] for row in categories}


def generate_expenses(user_id, count, months, category_ids):
    """Generate random expenses."""
    expenses = []

    # Build weighted category list
    weighted_categories = []
    for category_name, config in CATEGORIES_CONFIG.items():
        if category_name in category_ids:
            weighted_categories.extend([category_name] * config["weight"])

    # Generate date range
    today = datetime.now()
    start_date = today - timedelta(days=30 * months)

    for _ in range(count):
        # Random date within the past N months
        random_days_back = random.randint(0, (today - start_date).days)
        expense_date = today - timedelta(days=random_days_back)

        # Pick random category
        category_name = random.choice(weighted_categories)
        category_id = category_ids[category_name]

        # Generate amount
        min_amount, max_amount = CATEGORIES_CONFIG[category_name]["amounts"]
        amount = round(random.uniform(min_amount, max_amount), 2)

        # Pick random description
        description = random.choice(CATEGORIES_CONFIG[category_name]["descriptions"])

        expenses.append({
            "user_id": user_id,
            "category_id": category_id,
            "amount": amount,
            "date": expense_date.strftime("%Y-%m-%d"),
            "description": description,
            "category_name": category_name
        })

    return sorted(expenses, key=lambda x: x["date"])


def insert_expenses(expenses):
    """Insert all expenses in a single transaction."""
    db = get_db()
    cursor = db.cursor()

    try:
        for expense in expenses:
            cursor.execute("""
                INSERT INTO expenses (user_id, category_id, amount, date, description)
                VALUES (?, ?, ?, ?, ?)
            """, (
                expense["user_id"],
                expense["category_id"],
                expense["amount"],
                expense["date"],
                expense["description"]
            ))

        db.commit()
        db.close()
        return True
    except Exception as e:
        db.rollback()
        db.close()
        print(f"[ERROR] Failed to insert expenses: {e}")
        return False


if __name__ == "__main__":
    # Step 1: Parse arguments
    user_id, count, months = parse_arguments()

    # Step 2: Verify user exists
    verify_user_exists(user_id)

    # Step 3: Get user's categories
    category_ids = get_user_categories(user_id)

    if not category_ids:
        print(f"No categories found for user {user_id}.")
        sys.exit(1)

    # Generate expenses
    expenses = generate_expenses(user_id, count, months, category_ids)

    # Insert expenses
    if insert_expenses(expenses):
        # Step 4: Confirm
        date_range = f"{expenses[0]['date']} to {expenses[-1]['date']}"
        print(f"[OK] Inserted {len(expenses)} expenses")
        print(f"Date range: {date_range}")
        print(f"\nSample (first 5 records):")
        print("-" * 70)

        for i, exp in enumerate(expenses[:5], 1):
            print(f"{i}. {exp['date']} | {exp['category_name']:15} | ₹{exp['amount']:8.2f} | {exp['description']}")

        print("-" * 70)
    else:
        sys.exit(1)
