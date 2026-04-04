# ELEC0138 Resilient Security — Hospital Web App Demo

This project is a Flask-based hospital patient management system built for the ELEC0138 Security and Privacy coursework. It simulates a connected healthcare environment with intentional vulnerabilities for attack demonstration (Coursework 1) and a multi-layered defensive prototype (Coursework 2).

## Branches

| Branch | Purpose |
|---|---|
| `master` | Vulnerable app — Coursework 1 attack demonstrations |
| `secure` | Fixed app — Coursework 2 multi-layered defense system |

**Switch between branches:**
```bash
git checkout master   # vulnerable version (CW1)
git checkout secure   # fixed version (CW2)
```

> After switching branches, always re-run `python init_db.py` and `python generate_data.py`.

---

> **Warning:** The `master` branch is intentionally insecure for local academic demonstration only. It must never be deployed to a real environment.

## Project Structure

```text
elec0138-resilient-security-webapp/
├── app/
│   ├── __init__.py
│   ├── app.py                  # Main Flask application (intentionally vulnerable on master)
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
| Patient | `wood-youngg` | `patient123` | Run `generate_data.py` to see all 100 |

---

## Intentional Vulnerabilities (Coursework 1)

The `master` branch contains the following intentional security weaknesses for CW1 attack demonstration:

| Vulnerability | Location | CWE |
|---|---|---|
| SQL Injection | `app.py` login query — user input concatenated directly into SQL | CWE-89 |
| No rate limiting / account lockout | `/login` route has no throttling or lockout | CWE-307 |
| Plaintext password storage | `users` table stores raw passwords | CWE-256 |
| No CAPTCHA | Login/register forms have no bot protection | — |
| Hardcoded `SECRET_KEY` | Session cookies can be forged | CWE-798 |

### Attack Demonstration Scripts

Run the Flask app first, then in a separate terminal:

```bash
# SQL injection — bypasses login without a password
python scripts/test_sqli_login.py

# Brute force — iterates a password list with no lockout
python scripts/test_bruteforce_login.py
```

Both scripts target `http://127.0.0.1:5000` only and are scoped to this local demo.

Every login attempt (success or failure) is recorded in the `login_logs` table with timestamp, IP address, and an automatic flag for SQL injection patterns.

---

## Audit Log

To inspect login attempts after running the attack scripts:

```bash
python query_logs.py
```

This prints all entries in the `login_logs` table as a formatted table showing ID, timestamp, username, IP address, success/failure, role, and any flagged notes (e.g. SQL injection detected).

---

## Coursework 2 — Multi-Layered Defense System (`secure` branch)

Switch to the `secure` branch (`git checkout secure`) for the full defensive prototype. See the `secure` branch README for detailed documentation of all four defense layers:

| Layer | Features |
|---|---|
| **1. Access Controls & Auth** | Parameterized queries, password hashing, rate limiting (3/min), account lockout, TOTP-based MFA, session timeout |
| **2. Data Security & Encryption** | AES-256 field-level encryption for patient data and medical records at rest |
| **3. Network Protection & Monitoring** | Rule-based IDS with brute-force / SQLi / locked-account detection, security alerts dashboard |
| **4. Session Hardening** | HttpOnly + SameSite cookies, random SECRET_KEY, 15-min inactivity timeout |

---

## Resetting the Database

```bash
python init_db.py          # recreate schema + admin user
python generate_data.py    # add 100 synthetic patients + doctor accounts
```
