import base64
import io
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps
import sqlite3
from pathlib import Path

import pyotp
import qrcode
from flask import (
    Flask, flash, g, jsonify, redirect, render_template,
    request, session, url_for, send_file,
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import check_password_hash, generate_password_hash

from app.encryption import encrypt_field, decrypt_field

# ---------------------------------------------------------------------------
# App configuration
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = BASE_DIR / "instance" / "hospital_demo.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = secrets.token_hex(32)
app.config["DATABASE"] = DATABASE

# --- Layer 1a: Secure session configuration ---
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=15)

# --- Layer 1b: Rate limiting ---
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)

MAX_FAILED_ATTEMPTS = 10

# --- Layer 3: IDS thresholds ---
IDS_FAILED_LOGIN_THRESHOLD = 5       # failures from one IP in 10 min
IDS_SQLI_PATTERN_KEYWORDS = ("'", "--", ";", "/*", "OR ", "or ", "UNION", "union", "DROP", "drop")


# ===== Helpers =====

def wants_json_response():
    return request.is_json or request.args.get("format") == "json"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ===== Layer 3: Intrusion Detection System (IDS) =====

def ids_check_login(username, ip):
    """Analyse login_logs for suspicious activity and raise security alerts."""
    db = get_db()

    # Rule 1: Multiple failed logins from the same IP in the last 10 minutes
    ten_min_ago = (datetime.now(timezone.utc) - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
    row = db.execute(
        """
        SELECT COUNT(*) FROM login_logs
        WHERE ip_address = ? AND success = 0 AND timestamp >= ?
        """,
        (ip, ten_min_ago),
    ).fetchone()
    if row and row[0] >= IDS_FAILED_LOGIN_THRESHOLD:
        _raise_alert(
            alert_type="brute_force",
            severity="high",
            source_ip=ip,
            username=username,
            description=(
                f"Brute-force suspected: {row[0]} failed login attempts from "
                f"IP {ip} in the last 10 minutes."
            ),
        )

    # Rule 2: SQL injection patterns in username
    if any(kw in username for kw in IDS_SQLI_PATTERN_KEYWORDS):
        _raise_alert(
            alert_type="sqli_attempt",
            severity="critical",
            source_ip=ip,
            username=username,
            description=(
                f"SQL injection pattern detected in login username: {username!r}"
            ),
        )

    # Rule 3: Login attempt on a locked account
    if get_failed_attempts(username) >= MAX_FAILED_ATTEMPTS:
        _raise_alert(
            alert_type="locked_account_probe",
            severity="medium",
            source_ip=ip,
            username=username,
            description=(
                f"Login attempt on locked account '{username}' from IP {ip}."
            ),
        )


def _raise_alert(*, alert_type, severity, source_ip, username, description):
    """Insert a security alert into the database."""
    try:
        db = get_db()
        db.execute(
            """
            INSERT INTO security_alerts
                (timestamp, alert_type, severity, source_ip, username, description)
            VALUES (datetime('now'), ?, ?, ?, ?, ?)
            """,
            (alert_type, severity, source_ip, username, description),
        )
        db.commit()
    except Exception:
        pass


# ===== Audit logging =====

def log_login_attempt(username, success, role="unknown"):
    outcome = "SUCCESS" if success else "FAILURE"
    print(f"[LOGIN {outcome}] username={username!r} role={role}")
    try:
        ip = request.remote_addr or "unknown"
        note = None
        if any(c in username for c in ("'", "--", ";", "/*", "OR ", "or ")):
            note = "Possible SQL injection attempt (blocked by parameterized query)"
        db = get_db()
        db.execute(
            """
            INSERT INTO login_logs (timestamp, username, ip_address, success, role, note)
            VALUES (datetime('now'), ?, ?, ?, ?, ?)
            """,
            (username, ip, 1 if success else 0, role, note),
        )
        db.commit()
    except Exception:
        pass


# ===== Auth decorators =====

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if session.get("user_id") is None:
            flash("Please log in first.")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped_view


def role_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            if session.get("role") not in allowed_roles:
                flash("You do not have permission to access that page.")
                return redirect(url_for("dashboard"))
            return view(*args, **kwargs)
        return wrapped_view
    return decorator


def get_failed_attempts(username):
    """Count consecutive failed login attempts for a username."""
    db = get_db()
    row = db.execute(
        """
        SELECT COUNT(*) FROM login_logs
        WHERE username = ?
          AND success = 0
          AND log_id > COALESCE(
              (SELECT MAX(log_id) FROM login_logs WHERE username = ? AND success = 1),
              0
          )
        """,
        (username, username),
    ).fetchone()
    return row[0] if row else 0


# ===== Layer 2: Encryption helpers for templates =====

def decrypt_row(row, *fields):
    """Return a dict copy of a sqlite3.Row with selected fields decrypted."""
    d = dict(row)
    for f in fields:
        d[f] = decrypt_field(d.get(f))
    return d


# ===== Session timeout middleware =====

@app.before_request
def enforce_session_timeout():
    """Auto-logout after 15 minutes of inactivity."""
    session.permanent = True
    now = datetime.now(timezone.utc).timestamp()
    last = session.get("_last_active")
    if last and (now - last) > 15 * 60:
        session.clear()
        flash("Session expired due to inactivity. Please log in again.")
        return redirect(url_for("login"))
    if session.get("user_id"):
        session["_last_active"] = now


def fetch_user_profile(role, linked_id):
    db = get_db()
    if role == "doctor":
        return db.execute(
            "SELECT doctor_id, full_name, department, email FROM doctors WHERE doctor_id = ?",
            (linked_id,),
        ).fetchone()
    if role == "patient":
        row = db.execute(
            """
            SELECT patient_id, full_name, date_of_birth, gender, phone, email
            FROM patients WHERE patient_id = ?
            """,
            (linked_id,),
        ).fetchone()
        if row:
            return decrypt_row(row, "phone", "email")
    return None


# ===== Routes =====

@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        full_name = request.form.get("full_name", "").strip()
        date_of_birth = request.form.get("date_of_birth", "").strip()
        gender = request.form.get("gender", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()

        if not all([username, password, full_name, date_of_birth, gender, email]):
            flash("All required fields must be completed.")
            return render_template("register.html")

        hashed_password = generate_password_hash(password)

        # Layer 2: Encrypt sensitive fields before storage
        encrypted_phone = encrypt_field(phone) if phone else None
        encrypted_email = encrypt_field(email)

        db = get_db()
        try:
            cursor = db.execute(
                """
                INSERT INTO patients (full_name, date_of_birth, gender, phone, email)
                VALUES (?, ?, ?, ?, ?)
                """,
                (full_name, date_of_birth, gender, encrypted_phone, encrypted_email),
            )
            patient_id = cursor.lastrowid
            db.execute(
                """
                INSERT INTO users (username, password, role, linked_id)
                VALUES (?, ?, 'patient', ?)
                """,
                (username, hashed_password, patient_id),
            )
            db.commit()
        except sqlite3.IntegrityError:
            db.rollback()
            flash("That username or email already exists.")
            return render_template("register.html")

        flash("Patient registration successful. Please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("3 per minute")
def login():
    if request.method == "POST":
        if request.is_json:
            payload = request.get_json(silent=True) or {}
            username = str(payload.get("username", "")).strip()
            password = str(payload.get("password", ""))
        else:
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")

        ip = request.remote_addr or "unknown"

        # Layer 3: IDS check before processing
        ids_check_login(username, ip)

        # Account lockout check
        if get_failed_attempts(username) >= MAX_FAILED_ATTEMPTS:
            log_login_attempt(username, success=False, role="locked")
            msg = "Account locked due to too many failed attempts. Contact an administrator."
            if wants_json_response():
                return jsonify({"success": False, "message": msg}), 403
            flash(msg)
            return render_template("login.html"), 403

        db = get_db()

        # Parameterized query (prevents SQL injection)
        user = db.execute(
            "SELECT user_id, username, password, role, linked_id, totp_secret, mfa_enabled FROM users WHERE username = ?",
            (username,),
        ).fetchone()

        # Password hashing check
        if user is None or not check_password_hash(user["password"], password):
            log_login_attempt(username, success=False)
            if wants_json_response():
                return jsonify({"success": False, "message": "Invalid username or password."}), 401
            flash("Invalid username or password.")
            return render_template("login.html"), 401

        # Layer 1c: MFA check — if MFA is enabled, redirect to verification page
        if user["mfa_enabled"]:
            session["_mfa_user_id"] = user["user_id"]
            session["_mfa_pending"] = True
            return redirect(url_for("mfa_verify"))

        # Complete login (no MFA)
        _complete_login(user)

        if wants_json_response():
            return jsonify(
                {
                    "success": True,
                    "message": "Login successful.",
                    "username": user["username"],
                    "role": user["role"],
                }
            )

        flash("Login successful.")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


def _complete_login(user):
    """Finalise session after successful authentication (password + optional MFA)."""
    session.clear()
    session.permanent = True
    session["user_id"] = user["user_id"]
    session["username"] = user["username"]
    session["role"] = user["role"]
    session["linked_id"] = user["linked_id"]
    session["_last_active"] = datetime.now(timezone.utc).timestamp()
    log_login_attempt(user["username"], success=True, role=user["role"])


# ===== Layer 1c: MFA routes =====

@app.route("/mfa/verify", methods=["GET", "POST"])
def mfa_verify():
    if not session.get("_mfa_pending"):
        return redirect(url_for("login"))

    if request.method == "POST":
        code = request.form.get("code", "").strip()
        db = get_db()
        user = db.execute(
            "SELECT user_id, username, role, linked_id, totp_secret FROM users WHERE user_id = ?",
            (session["_mfa_user_id"],),
        ).fetchone()

        if user and pyotp.TOTP(user["totp_secret"]).verify(code, valid_window=1):
            session.pop("_mfa_pending", None)
            session.pop("_mfa_user_id", None)
            _complete_login(user)
            flash("Login successful.")
            return redirect(url_for("dashboard"))

        flash("Invalid MFA code. Please try again.")

    return render_template("mfa_verify.html")


@app.route("/mfa/setup", methods=["GET", "POST"])
@login_required
def mfa_setup():
    db = get_db()
    user = db.execute(
        "SELECT user_id, username, mfa_enabled, totp_secret FROM users WHERE user_id = ?",
        (session["user_id"],),
    ).fetchone()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "enable":
            code = request.form.get("code", "").strip()
            totp_secret = session.get("_setup_totp_secret")
            if totp_secret and pyotp.TOTP(totp_secret).verify(code, valid_window=1):
                db.execute(
                    "UPDATE users SET totp_secret = ?, mfa_enabled = 1 WHERE user_id = ?",
                    (totp_secret, session["user_id"]),
                )
                db.commit()
                session.pop("_setup_totp_secret", None)
                flash("MFA enabled successfully.")
                return redirect(url_for("dashboard"))
            flash("Invalid code. Please scan the QR code and try again.")

        elif action == "disable":
            db.execute(
                "UPDATE users SET totp_secret = NULL, mfa_enabled = 0 WHERE user_id = ?",
                (session["user_id"],),
            )
            db.commit()
            flash("MFA has been disabled.")
            return redirect(url_for("dashboard"))

    # Generate a new TOTP secret for setup
    totp_secret = pyotp.random_base32()
    session["_setup_totp_secret"] = totp_secret
    totp = pyotp.TOTP(totp_secret)
    provisioning_uri = totp.provisioning_uri(
        name=user["username"],
        issuer_name="Hospital Records Demo",
    )

    return render_template(
        "mfa_setup.html",
        mfa_enabled=user["mfa_enabled"],
        provisioning_uri=provisioning_uri,
        totp_secret=totp_secret,
    )


@app.route("/mfa/qrcode")
@login_required
def mfa_qrcode():
    """Serve the MFA QR code as a PNG image."""
    totp_secret = session.get("_setup_totp_secret")
    if not totp_secret:
        return "", 404
    user = get_db().execute(
        "SELECT username FROM users WHERE user_id = ?", (session["user_id"],)
    ).fetchone()
    uri = pyotp.TOTP(totp_secret).provisioning_uri(
        name=user["username"], issuer_name="Hospital Records Demo"
    )
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


# ===== Main routes =====

@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    role = session.get("role")
    if role == "admin":
        return redirect(url_for("admin_dashboard"))
    if role == "doctor":
        return redirect(url_for("doctor_dashboard"))
    return redirect(url_for("patient_dashboard"))


@app.route("/admin")
@login_required
@role_required("admin")
def admin_dashboard():
    db = get_db()
    users = db.execute(
        "SELECT user_id, username, role, linked_id, mfa_enabled FROM users ORDER BY role, username"
    ).fetchall()
    patients_raw = db.execute(
        """
        SELECT patient_id, full_name, date_of_birth, gender, phone, email
        FROM patients ORDER BY full_name
        """
    ).fetchall()
    # Layer 2: Decrypt sensitive fields for display
    patients = [decrypt_row(p, "phone", "email") for p in patients_raw]

    doctors = db.execute(
        "SELECT doctor_id, full_name, department, email FROM doctors ORDER BY full_name"
    ).fetchall()
    records_raw = db.execute(
        """
        SELECT mr.record_id, p.full_name AS patient_name, d.full_name AS doctor_name,
               mr.diagnosis, mr.treatment, mr.notes, mr.last_updated
        FROM medical_records mr
        JOIN patients p ON p.patient_id = mr.patient_id
        JOIN doctors d ON d.doctor_id = mr.doctor_id
        ORDER BY mr.last_updated DESC
        """
    ).fetchall()
    records = [decrypt_row(r, "diagnosis", "treatment", "notes") for r in records_raw]

    # Layer 3: Security alerts for admin
    alerts = db.execute(
        """
        SELECT alert_id, timestamp, alert_type, severity, source_ip, username, description, resolved
        FROM security_alerts ORDER BY timestamp DESC LIMIT 50
        """
    ).fetchall()

    return render_template(
        "admin_dashboard.html",
        users=users,
        patients=patients,
        doctors=doctors,
        records=records,
        alerts=alerts,
    )


@app.route("/doctor")
@login_required
@role_required("doctor")
def doctor_dashboard():
    doctor = fetch_user_profile("doctor", session.get("linked_id"))
    records_raw = get_db().execute(
        """
        SELECT mr.record_id, p.full_name AS patient_name, mr.diagnosis, mr.treatment,
               mr.notes, mr.last_updated
        FROM medical_records mr
        JOIN patients p ON p.patient_id = mr.patient_id
        WHERE mr.doctor_id = ?
        ORDER BY mr.last_updated DESC
        """,
        (session.get("linked_id"),),
    ).fetchall()
    records = [decrypt_row(r, "diagnosis", "treatment", "notes") for r in records_raw]
    return render_template("doctor_dashboard.html", doctor=doctor, records=records)


@app.route("/patient")
@login_required
@role_required("patient")
def patient_dashboard():
    patient = fetch_user_profile("patient", session.get("linked_id"))
    records_raw = get_db().execute(
        """
        SELECT mr.record_id, d.full_name AS doctor_name, d.department, mr.diagnosis,
               mr.treatment, mr.notes, mr.last_updated
        FROM medical_records mr
        JOIN doctors d ON d.doctor_id = mr.doctor_id
        WHERE mr.patient_id = ?
        ORDER BY mr.last_updated DESC
        """,
        (session.get("linked_id"),),
    ).fetchall()
    records = [decrypt_row(r, "diagnosis", "treatment", "notes") for r in records_raw]
    return render_template("patient_dashboard.html", patient=patient, records=records)


if __name__ == "__main__":
    app.run(debug=True)
