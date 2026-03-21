# ELEC0138 Resilient Security — Hospital Web App Demo

This project is a Flask-based hospital patient management system built for the ELEC0138 Security and Privacy coursework. It simulates a connected healthcare environment with intentional vulnerabilities for attack demonstration (Coursework 1) and a secure fixed version as the defensive prototype (Coursework 2).

## Branches

| Branch | Purpose |
|---|---|
| `master` | Vulnerable app — Coursework 1 attack demonstrations |
| `secure` | Fixed app — Coursework 2 defensive prototype |

**Switch between branches:**
```bash
git checkout master   # vulnerable version (CW1)
git checkout secure   # fixed version (CW2)
```

> After switching branches, always re-run `python init_db.py` and `python generate_data.py`.

---

## Project Structure

```text
elec0138-resilient-security-webapp/
├── app/
│   ├── __init__.py
│   ├── app.py                  # Main Flask application
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
│   └── hospital_demo.sql       # Schema definition
├── scripts/
│   ├── test_sqli_login.py      # SQL injection attack demo
│   └── test_bruteforce_login.py# Brute force attack demo
├── generate_data.py            # Synthetic patient data generator (Faker + ICD-10)
├── query_logs.py               # Print login audit log in a readable table
├── init_db.py                  # Database initialisation script
├── requirements.txt
└── README.md
```

---

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

5. Generate 100 synthetic patients with ICD-10 records:

```bash
python generate_data.py
```

6. Run the application:

```bash
python -m flask --app app.app run --debug
```

7. Open your browser at `http://127.0.0.1:5000`

---

## Database

After running both scripts the database contains:

| Table | Records |
|---|---|
| patients | 100 synthetic |
| doctors | 5 |
| medical_records | ~200 |
| users | 106 (1 admin + 5 doctors + 100 patients) |
| login_logs | grows with each login attempt |

Synthetic patients use realistic UK names, dates of birth, and real **ICD-10 diagnosis codes** (e.g., `[I10] Essential hypertension`, `[F32.1] Moderate depressive episode`) generated via the Faker library.

---

## Sample Users

| Role | Username | Password | Name |
|---|---|---|---|
| Admin | `admin1` | `admin123` | — |
| Doctor | `cartera` | `doctor123` | Dr. Amelia Carter (Cardiology) |
| Doctor | `shahd` | `doctor123` | Dr. Daniel Shah (General Medicine) |
| Doctor | `nairp` | `doctor123` | Dr. Priya Nair (Respiratory) |
| Doctor | `obrienj` | `doctor123` | Dr. James O'Brien (Mental Health) |
| Doctor | `zhangm` | `doctor123` | Dr. Mei Zhang (Orthopaedics) |
| Patient | *(generated)* | `patient123` | Run `generate_data.py` to see all 100 |

> On the `secure` branch all passwords are stored as scrypt hashes — the plaintext above is only for reference.

---

## Coursework 1 — Intentional Vulnerabilities (`master` branch)

| Vulnerability | Location | CWE |
|---|---|---|
| SQL Injection | `app.py` login query | CWE-89 |
| No rate limiting / account lockout | `/login` route | CWE-307 |
| Plaintext password storage | `users` table | CWE-256 |
| No CAPTCHA | Login/register forms | — |

### Attack Demonstration Scripts

Run the Flask app first, then in a separate terminal:

```bash
# SQL injection — bypasses login without a password
python scripts/test_sqli_login.py

# Brute force — iterates a password list with no lockout
python scripts/test_bruteforce_login.py
```

---

## Coursework 2 — Security Fixes (`secure` branch)

| Fix | Detail |
|---|---|
| Parameterized queries | SQL injection payload returns `401` — attack neutralised |
| Password hashing | All passwords stored as scrypt hashes via Werkzeug |
| Rate limiting | Max 5 login attempts per minute per IP (Flask-Limiter) |
| Account lockout | Blocked after 10 consecutive failed attempts |
| Secure session | Random `SECRET_KEY`, `HttpOnly` + `SameSite=Strict` cookies |

---

## Audit Log

Every login attempt is recorded in `login_logs` with timestamp, IP, success/failure, and SQL injection flags.

To view the log:

```bash
python query_logs.py
```

---

## Resetting the Database

```bash
python init_db.py          # recreate schema + admin user
python generate_data.py    # add 100 synthetic patients + doctor accounts
```
