#!/usr/bin/env python3
"""
Script to generate and insert a realistic random Indian user into the database.
"""

import random
from datetime import datetime
from werkzeug.security import generate_password_hash
from database.db import get_db

# Realistic Indian names across different regions
FIRST_NAMES = [
    "Rahul", "Priya", "Arjun", "Ananya", "Vikram", "Neha", "Amit", "Shreya",
    "Rohan", "Divya", "Karan", "Anjali", "Sanjay", "Ritika", "Akshay", "Pooja",
    "Nikhil", "Tanvi", "Varun", "Aisha", "Ravi", "Meera", "Aditya", "Kavya",
    "Suresh", "Geeta", "Aman", "Nisha", "Abhishek", "Sneha", "Manish", "Isha"
]

LAST_NAMES = [
    "Sharma", "Singh", "Patel", "Kumar", "Gupta", "Verma", "Mishra", "Joshi",
    "Reddy", "Iyer", "Nair", "Menon", "Desai", "Rao", "Chopra", "Kapoor",
    "Malhotra", "Saxena", "Bhat", "Naidu", "Pandey", "Srivastava", "Trivedi", "Agarwal"
]

def generate_random_user():
    """Generate a random Indian user."""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    name = f"{first_name} {last_name}"

    # Generate email with random suffix
    email_base = f"{first_name.lower()}.{last_name.lower()}"
    random_suffix = random.randint(10, 999)
    email = f"{email_base}{random_suffix}@gmail.com"

    # Hash password
    password_hash = generate_password_hash("password123")

    # Current timestamp
    created_at = datetime.now().isoformat()

    return name, email, password_hash, created_at


def email_exists(email):
    """Check if email already exists in the database."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    result = cursor.fetchone()
    db.close()
    return result is not None


def insert_user(name, email, password_hash):
    """Insert user into the database."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO users (name, email, password_hash)
        VALUES (?, ?, ?)
    """, (name, email, password_hash))

    user_id = cursor.lastrowid
    db.commit()
    db.close()

    return user_id


if __name__ == "__main__":
    # Generate random user until we get a unique email
    max_attempts = 10
    attempt = 0

    while attempt < max_attempts:
        name, email, password_hash, created_at = generate_random_user()

        if not email_exists(email):
            # Insert the user
            user_id = insert_user(name, email, password_hash)

            # Print confirmation
            print(f"[OK] User created successfully:")
            print(f"  ID:    {user_id}")
            print(f"  Name:  {name}")
            print(f"  Email: {email}")
            break

        attempt += 1
    else:
        print(f"[ERROR] Failed to generate unique email after {max_attempts} attempts")
