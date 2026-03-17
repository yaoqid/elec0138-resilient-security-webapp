# Flask Coursework Demo

This project is a minimal Flask web application for a local academic cybersecurity demo based on a hospital records environment. It includes:

- user registration
- user login
- logout
- user dashboard
- admin dashboard
- SQLite database created from a hospital records SQL script

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
|       |-- admin_dashboard.html
|       |-- base.html
|       |-- doctor_dashboard.html
|       |-- index.html
|       |-- login.html
|       |-- patient_dashboard.html
|       `-- register.html
|-- instance/
|   |-- hospital_demo.db
|   `-- hospital_demo.sql
|-- scripts/
|   |-- test_bruteforce_login.py
|   `-- test_sqli_login.py
|-- init_db.py
|-- requirements.txt
`-- README.md
```

## Setup

1. Clone the repository:

```powershell
git clone https://github.com/yaoqid/elec0138-resilient-security-webapp.git
cd Playground
```

2. Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
pip install -r requirements.txt
```

4. Initialize the database:

```powershell
python init_db.py
```

5. Run the application:

```powershell
python -m flask --app app.app run --debug
```

6. Open your browser:

```text
http://127.0.0.1:5000
```

## Sample Users

- Admin user: `admin1` / `admin123`
- Doctor user: `acarter` / `doctor123`
- Patient user: `obennett` / `patient123`

## Notes For Coursework

- The app is intentionally minimal and keeps everything local with SQLite.
- The login flow is intentionally vulnerable to SQL injection for classroom demonstration and report discussion.
- There is no rate limiting or account lockout, which makes it suitable for discussing brute-force risk in a local test environment.
- There is no CAPTCHA, so repeated login attempts can be automated very easily.
- Passwords are stored in plaintext in the `users` table and medical records are visible through role-based dashboards.
- These insecure choices are deliberate for a local-only coursework exercise and must never be copied into production systems.

## Script Testing

The login endpoint accepts regular form posts for the browser UI and also supports JSON requests for scripts.

Example success or failure test:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/login?format=json `
  -ContentType "application/json" `
  -Body '{"username":"obennett","password":"patient123"}'
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
