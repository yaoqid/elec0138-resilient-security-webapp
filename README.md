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

## Project Structure

```text
elec0138-resilient-security-webapp/
├── app/
│   ├── __init__.py
│   ├── app.py                  # Main Flask application
│   ├── encryption.py           # AES-256 field-level encryption module (CW2)
│   ├── static/
│   │   └── style.css
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── login.html
│       ├── register.html
│       ├── admin_dashboard.html
│       ├── doctor_dashboard.html
│       ├── patient_dashboard.html
│       ├── mfa_setup.html       # TOTP MFA setup page (CW2)
│       └── mfa_verify.html      # TOTP MFA verification page (CW2)
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
| security_alerts | populated by the IDS on suspicious activity (CW2) |

Synthetic patients use realistic UK names, dates of birth, and real **ICD-10 diagnosis codes** (e.g., `[I10] Essential hypertension`, `[F32.1] Moderate depressive episode`) generated via the Faker library.

On the `secure` branch, sensitive patient fields (phone, email) and medical record fields (diagnosis, treatment, notes) are **encrypted at rest** using AES-256.

---

## Sample Users

| Role | Username | Password (`master`) | Password (`secure`) | Name |
|---|---|---|---|---|
| Admin | `admin1` | `admin123` | `Sec#Admin2026!` | — |
| Doctor | `cartera` | `doctor123` | `Doc$Secure2026!` | Dr. Amelia Carter (Cardiology) |
| Doctor | `shahd` | `doctor123` | `Doc$Secure2026!` | Dr. Daniel Shah (General Medicine) |
| Doctor | `nairp` | `doctor123` | `Doc$Secure2026!` | Dr. Priya Nair (Respiratory) |
| Doctor | `obrienj` | `doctor123` | `Doc$Secure2026!` | Dr. James O'Brien (Mental Health) |
| Doctor | `zhangm` | `doctor123` | `Doc$Secure2026!` | Dr. Mei Zhang (Orthopaedics) |
| Patient | *(generated)* | `patient123` | `Pat#Health2026!` | Run `generate_data.py` to see all 100 |

> On the `secure` branch all passwords are stored as scrypt hashes and are strong enough to resist brute force attacks.

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

## Coursework 2 — Multi-Layered Defense System (`secure` branch)

### Layer 1: Access Controls & Authentication

| Fix | Detail |
|---|---|
| Parameterized queries | SQL injection payload returns `401` — attack neutralised |
| Password hashing | All passwords stored as scrypt hashes via Werkzeug |
| Rate limiting | Max 3 login attempts per minute per IP (Flask-Limiter) |
| Account lockout | Blocked after 10 consecutive failed attempts |
| TOTP-based MFA | Users can enable two-factor authentication via `/mfa/setup` using Google Authenticator or any TOTP app. QR code provided for easy setup. |
| Session timeout | Auto-logout after 15 minutes of inactivity |
| Secure session cookies | Random `SECRET_KEY`, `HttpOnly` + `SameSite=Strict` cookies |

### Layer 2: Data Security & Encryption

| Fix | Detail |
|---|---|
| AES-256 field-level encryption | Sensitive patient data (phone, email) and medical records (diagnosis, treatment, notes) are encrypted at rest using the `cryptography` library |
| PBKDF2 key derivation | Encryption key derived from a master secret using PBKDF2-HMAC-SHA256 with 480,000 iterations |
| Key management | Encryption key stored outside the database (env var or auto-generated key file, excluded from git) |
| Decrypt on display only | Data is decrypted only when an authorised user views their dashboard |

### Layer 3: Network Protection & Monitoring (IDS)

| Fix | Detail |
|---|---|
| Brute-force detection | Flags 5+ failed login attempts from the same IP within 10 minutes |
| SQL injection detection | Detects SQLi patterns in login usernames and raises critical alerts |
| Locked account probing | Alerts when someone attempts to log in to an already-locked account |
| Security alerts dashboard | Admin panel displays all IDS alerts with severity badges (critical / high / medium / low) |
| Audit logging | Every login attempt recorded with timestamp, IP, success/failure, and SQLi flags |

### Layer 4: Session Hardening

| Fix | Detail |
|---|---|
| `HttpOnly` cookies | Prevents client-side JavaScript from accessing session cookies |
| `SameSite=Strict` | Prevents CSRF attacks via cross-site request forgery |
| 15-minute inactivity timeout | Enforced server-side via `before_request` middleware |
| Random `SECRET_KEY` | Generated fresh on each app start, preventing session forgery |

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
