# ELEC0138 Resilient Security — Hospital Web App Demo

This project is a Flask-based hospital patient management system built for the ELEC0138 Security and Privacy coursework. It simulates a connected healthcare environment with intentional vulnerabilities for attack demonstration (Coursework 1) and a foundation for implementing defensive countermeasures (Coursework 2).

> **Warning:** This application is intentionally insecure for local academic demonstration only. It must never be deployed to a real environment.

## Project Structure

```text
elec0138-resilient-security-webapp/
├── app/
│   ├── __init__.py
│   ├── app.py                  # Main Flask application (intentionally vulnerable)
│   ├── static/
│   │   └── style.css
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── login.html
│       ├── register.html
│       ├── admin_dashboard.html
│       ├── doctor_dashboard.html
│       └── patient_dashboard.html
├── instance/
│   ├── hospital_demo.db        # SQLite database (generated)
│   └── hospital_demo.sql       # Schema + seed data (incl. login_logs table)
├── scripts/
│   ├── test_sqli_login.py      # SQL injection attack demo
│   └── test_bruteforce_login.py# Brute force attack demo
├── generate_data.py            # Synthetic patient data generator (Faker + ICD-10)
├── init_db.py                  # Database initialisation script
├── requirements.txt
└── README.md
```

## Setup

1. Clone the repository:

```bash
git clone https://github.com/yaoqid/elec0138-resilient-security-webapp.git
cd elec0138-resilient-security-webapp
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1     # Windows
source .venv/bin/activate      # macOS/Linux
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Initialise the database:

```bash
python init_db.py
```

5. (Optional) Generate 100 synthetic patients with ICD-10 records:

```bash
python generate_data.py
```

6. Run the application:

```bash
python -m flask --app app.app run --debug
```

7. Open your browser at `http://127.0.0.1:5000`

## Database

After running both scripts the database contains:

| Table | Records |
|---|---|
| patients | 104 (4 seed + 100 synthetic) |
| doctors | 5 |
| medical_records | ~206 |
| users | 107 |
| login_logs | grows with each login attempt |

Synthetic patients use realistic UK names, dates of birth, and real **ICD-10 diagnosis codes** (e.g., `[I10] Essential hypertension`, `[F32.1] Moderate depressive episode`) generated via the Faker library.

## Sample Users

| Role | Username | Password |
|---|---|---|
| Admin | `admin1` | `admin123` |
| Doctor | `acarter` | `doctor123` |
| Patient | `obennett` | `patient123` |

## Intentional Vulnerabilities (Coursework 1)

| Vulnerability | Location | CWE |
|---|---|---|
| SQL Injection | `app.py` login query | CWE-89 |
| No rate limiting / account lockout | `/login` route | CWE-307 |
| Plaintext password storage | `users` table | CWE-256 |
| No CAPTCHA | Login/register forms | — |

## Attack Demonstration Scripts

Run the Flask app first, then in a separate terminal:

```bash
# SQL injection — bypasses login without a password
python scripts/test_sqli_login.py

# Brute force — iterates a password list with no lockout
python scripts/test_bruteforce_login.py
```

Both scripts target `http://127.0.0.1:5000` only and are scoped to this local demo.

Every login attempt (success or failure) is recorded in the `login_logs` table with timestamp, IP address, and an automatic flag for SQL injection patterns.

## Audit Log

To inspect login attempts after running the attack scripts:

```bash
python -c "
import sqlite3
conn = sqlite3.connect('instance/hospital_demo.db')
for row in conn.execute('SELECT timestamp, username, ip_address, success, note FROM login_logs ORDER BY log_id DESC LIMIT 20'):
    print(row)
conn.close()
"
```

## Resetting the Database

```bash
python init_db.py          # reset schema + original 7 users
python generate_data.py    # re-add 100 synthetic patients
```
