# Flask Coursework Demo

This project is a minimal Flask web application for a local academic cybersecurity demo. It includes:

- user registration
- user login
- logout
- user dashboard
- admin dashboard
- SQLite database with seeded sample users

This version is intentionally insecure for local academic demonstration only. It must never be deployed to a real environment.

## Project Structure

```text
Playground/
|-- app/
|   |-- __init__.py
|   |-- app.py
|   |-- static/
|   |   `-- style.css
|   `-- templates/
|       |-- admin.html
|       |-- base.html
|       |-- dashboard.html
|       |-- index.html
|       |-- login.html
|       `-- register.html
|-- instance/
|   `-- demo.db
|-- init_db.py
|-- requirements.txt
`-- README.md
```

## Setup

1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Initialize the database:

```powershell
python init_db.py
```

4. Run the application:

```powershell
python -m flask --app app.app run --debug
```

5. Open your browser:

```text
http://127.0.0.1:5000
```

## Sample Users

- Normal user: `student` / `password123`
- Admin user: `admin` / `admin`

## Notes For Coursework

- The app is intentionally minimal and keeps everything local with SQLite.
- The login flow is intentionally vulnerable to SQL injection for classroom demonstration and report discussion.
- There is no rate limiting or account lockout, which makes it suitable for discussing brute-force risk in a local test environment.
- There is no CAPTCHA, so repeated login attempts can be automated very easily.
- Passwords are stored in plaintext and seeded with weak demo credentials so you can show why weak password choices matter.
- These insecure choices are deliberate for a local-only coursework exercise and must never be copied into production systems.

## Script Testing

The login endpoint accepts regular form posts for the browser UI and also supports JSON requests for scripts.

Example success or failure test:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/login?format=json `
  -ContentType "application/json" `
  -Body '{"username":"student","password":"password123"}'
```

Failed logins return HTTP `401` with a JSON body containing `success: false`.

## Local Demo Scripts

Two local-only testing scripts are included in [scripts](/c:/Users/35562/OneDrive/文档/Playground/scripts):

- [test_sqli_login.py](/c:/Users/35562/OneDrive/文档/Playground/scripts/test_sqli_login.py) demonstrates the intentional SQL injection login weakness.
- [test_bruteforce_login.py](/c:/Users/35562/OneDrive/文档/Playground/scripts/test_bruteforce_login.py) demonstrates repeated automated login attempts against the intentionally weak login flow.

Usage:

```powershell
python scripts/test_sqli_login.py
python scripts/test_bruteforce_login.py
```

These scripts are intentionally scoped to the local coursework app on `http://127.0.0.1:5000` and are not written as general-purpose tools.

## Resetting The Demo Database

If you want to recreate the seeded users, run:

```powershell
python init_db.py
```
