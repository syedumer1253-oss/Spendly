#!/usr/bin/env python3
"""
Test script for registration functionality.
Tests all scenarios from the implementation plan.
"""

import requests
from database.db import get_db

BASE_URL = "http://127.0.0.1:5001"

def get_user_count():
    """Get total user count in database."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM users")
    count = cursor.fetchone()["count"]
    db.close()
    return count

def email_exists(email):
    """Check if email exists in database."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    result = cursor.fetchone()
    db.close()
    return result is not None

def get_user_password_hash(email):
    """Get password hash for a user."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE email = ?", (email,))
    result = cursor.fetchone()
    db.close()
    return result["password_hash"] if result else None

def test_1_happy_path():
    """Test 1: Successful Registration"""
    print("\n" + "="*70)
    print("TEST 1: Happy Path (Successful Registration)")
    print("="*70)

    session = requests.Session()

    # Get registration form
    resp = session.get(f"{BASE_URL}/register")
    assert resp.status_code == 200, f"GET /register failed: {resp.status_code}"
    assert "Create your account" in resp.text, "Registration form not found"
    print("[OK] Registration form displays correctly")

    # Register new user
    initial_count = get_user_count()
    data = {
        "name": "Test User One",
        "email": "testuser1@example.com",
        "password": "password123",
        "confirm_password": "password123"
    }
    resp = session.post(f"{BASE_URL}/register", data=data, allow_redirects=False)

    # Should redirect to profile (302)
    assert resp.status_code == 302, f"Expected redirect, got {resp.status_code}"
    assert resp.headers.get("Location") == "/profile", f"Wrong redirect: {resp.headers.get('Location')}"
    print("[OK] Redirects to /profile on success")

    # Check user was created
    assert get_user_count() == initial_count + 1, "User not created in database"
    print("[OK] User created in database")

    # Check email is unique
    assert email_exists("testuser1@example.com"), "Email not found in database"
    print("[OK] Email stored correctly")

    # Check password is hashed
    pwd_hash = get_user_password_hash("testuser1@example.com")
    assert pwd_hash != "password123", "Password not hashed (stored plaintext!)"
    assert pwd_hash.startswith(("pbkdf2:sha256$", "scrypt:")), f"Password hash format wrong: {pwd_hash[:20]}"
    print("[OK] Password properly hashed")

    print("\n[PASS] TEST 1 PASSED\n")

def test_2_validation_failures():
    """Test 2: Validation Failures"""
    print("="*70)
    print("TEST 2: Validation Failures")
    print("="*70)

    session = requests.Session()

    # Test 2a: Empty fields
    print("\nTest 2a: Empty fields")
    resp = session.post(f"{BASE_URL}/register", data={
        "name": "", "email": "", "password": "", "confirm_password": ""
    })
    assert resp.status_code == 200, "Should re-render form"
    assert "Name is required" in resp.text, "Missing name validation"
    print("[OK] Empty name validation works")

    # Test 2b: Missing email
    resp = session.post(f"{BASE_URL}/register", data={
        "name": "Test", "email": "", "password": "pass123456", "confirm_password": "pass123456"
    })
    assert "Email is required" in resp.text, "Missing email validation"
    print("[OK] Empty email validation works")

    # Test 2c: Password too short
    resp = session.post(f"{BASE_URL}/register", data={
        "name": "Test", "email": "test@example.com", "password": "short", "confirm_password": "short"
    })
    assert "Password must be at least 8 characters" in resp.text, "Password length validation"
    print("[OK] Password minimum 8 characters validation works")

    # Test 2d: Passwords do not match
    resp = session.post(f"{BASE_URL}/register", data={
        "name": "Test", "email": "test2@example.com", "password": "password123", "confirm_password": "different123"
    })
    assert "Passwords do not match" in resp.text, "Password mismatch validation"
    print("[OK] Password mismatch validation works")

    # Test 2e: Whitespace-only input
    resp = session.post(f"{BASE_URL}/register", data={
        "name": "   ", "email": "test@example.com", "password": "password123", "confirm_password": "password123"
    })
    assert "Name is required" in resp.text, "Whitespace trimming not working"
    print("[OK] Whitespace trimming works")

    print("\n[PASS] TEST 2 PASSED\n")

def test_3_duplicate_email():
    """Test 3: Duplicate Email"""
    print("="*70)
    print("TEST 3: Duplicate Email")
    print("="*70)

    session = requests.Session()

    # Register first user
    data = {
        "name": "Duplicate Test",
        "email": "duplicate@example.com",
        "password": "password123",
        "confirm_password": "password123"
    }
    resp1 = session.post(f"{BASE_URL}/register", data=data, allow_redirects=False)
    assert resp1.status_code == 302, f"First registration should succeed, got {resp1.status_code}"
    print("[OK] First registration successful")

    # Try to register with same email
    session2 = requests.Session()
    resp2 = session2.post(f"{BASE_URL}/register", data=data)
    assert resp2.status_code == 200, "Should re-render form with error"
    assert "Email already registered" in resp2.text, "Missing duplicate email error"
    print("[OK] Duplicate email rejected with appropriate message")

    # Verify only one user was created
    count = 0
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE email = ?", ("duplicate@example.com",))
    count = cursor.fetchone()["count"]
    db.close()
    assert count == 1, f"Expected 1 user, found {count}"
    print("[OK] Only one user created (no duplicates)")

    print("\n[PASS] TEST 3 PASSED\n")

def test_4_navbar_registration_link():
    """Test 4: Navbar Registration Link"""
    print("="*70)
    print("TEST 4: Navbar Registration Link")
    print("="*70)

    session = requests.Session()

    # Get landing page (not logged in)
    resp = session.get(f"{BASE_URL}/")
    assert "Get started" in resp.text, "Registration link missing from navbar"
    assert 'href="/register"' in resp.text or 'url_for(\'register\')' in resp.text, "Register link not pointing to /register"
    print("[OK] Registration link ('Get started') visible when logged out")

    # Get profile page (needs login first)
    # Register a new user
    data = {
        "name": "Navbar Test",
        "email": "navbartest@example.com",
        "password": "password123",
        "confirm_password": "password123"
    }
    session.post(f"{BASE_URL}/register", data=data, allow_redirects=True)

    # Check profile page doesn't show registration link
    resp = session.get(f"{BASE_URL}/profile")
    assert "Get started" not in resp.text, "Registration link should not show when logged in"
    assert "Sign out" in resp.text, "Should show sign out when logged in"
    print("[OK] Registration link hidden when logged in")

    print("\n[PASS] TEST 4 PASSED\n")

def test_5_form_styling():
    """Test 5: Form Styling Consistency"""
    print("="*70)
    print("TEST 5: Form Styling Consistency")
    print("="*70)

    session = requests.Session()

    # Get register form
    resp = session.get(f"{BASE_URL}/register")
    html = resp.text

    # Check for CSS class references
    assert "auth-section" in html, "Missing auth-section class"
    assert "auth-container" in html, "Missing auth-container class"
    assert "form-input" in html, "Missing form-input class"
    assert "btn-submit" in html, "Missing btn-submit class"
    print("✓ Form uses consistent CSS classes")

    # Check for error styling
    assert "auth-error" in html, "Missing error styling"
    print("✓ Error display styling present")

    # Check form extends base.html
    assert "navbar" in html, "Navbar not in page (not extending base.html?)"
    assert "footer" in html, "Footer not in page (not extending base.html?)"
    print("✓ Template extends base.html correctly")

    print("\n✅ TEST 5 PASSED\n")

if __name__ == "__main__":
    print("\n" + "="*70)
    print("REGISTRATION IMPLEMENTATION TESTS")
    print("="*70)

    try:
        test_1_happy_path()
        test_2_validation_failures()
        test_3_duplicate_email()
        test_4_navbar_registration_link()
        test_5_form_styling()

        print("="*70)
        print("✅ ALL TESTS PASSED")
        print("="*70)
        print("\nRegistration feature is fully implemented and working!")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        exit(1)
