"""
Local-only brute-force demonstration for the coursework Flask app.

This script is intentionally limited to:
- the demo application on http://127.0.0.1:5000
- a short hardcoded password list
- a single demo username

It exists only to show that the app has no rate limiting, lockout, or CAPTCHA.
"""

import sys
import time

import requests


LOGIN_URL = "http://127.0.0.1:5000/login?format=json"
TARGET_USERNAME = "admin1"

# Short, readable list for the coursework demo.
PASSWORD_CANDIDATES = [
    "123456",
    "password",
    "admin123",
    "letmein",
    "admin",
]


def main():
    print("Brute-Force Demo")
    print(f"Target: {LOGIN_URL}")
    print(f"Username under test: {TARGET_USERNAME}")
    print("Trying several passwords in sequence against the local demo app...\n")

    for attempt_number, candidate in enumerate(PASSWORD_CANDIDATES, start=1):
        payload = {
            "username": TARGET_USERNAME,
            "password": candidate,
        }

        print(f"Attempt {attempt_number}: testing password {candidate!r}")

        try:
            response = requests.post(LOGIN_URL, json=payload, timeout=5)
        except requests.RequestException as exc:
            print(f"Request failed: {exc}")
            print("Make sure the Flask app is running locally on http://127.0.0.1:5000.")
            sys.exit(1)

        try:
            data = response.json()
        except ValueError:
            print("The app did not return JSON. Response body:")
            print(response.text)
            sys.exit(1)

        if response.status_code == 200 and data.get("success"):
            print("Login succeeded.")
            print(f"Working password found: {candidate!r}")
            print("Result: brute-force demonstration succeeded.")
            return

        print("Login failed.")

        # Small pause keeps the terminal output readable. The application itself
        # has no rate limit, lockout, or CAPTCHA to slow these attempts down.
        time.sleep(0.2)

    print("\nResult: brute-force demonstration did not find a matching password.")
    print("Check that the seeded demo database is initialized and the app is running.")
    sys.exit(1)


if __name__ == "__main__":
    main()
