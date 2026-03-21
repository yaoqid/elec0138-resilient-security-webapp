from functools import wraps
import sqlite3
from pathlib import Path

from flask import Flask, flash, g, jsonify, redirect, render_template, request, session, url_for


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = BASE_DIR / "instance" / "hospital_demo.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "hospital-coursework-demo-secret-key"
app.config["DATABASE"] = DATABASE


def wants_json_response():
    return request.is_json or request.args.get("format") == "json"


def log_login_attempt(username, success, role="unknown"):
    outcome = "SUCCESS" if success else "FAILURE"
    print(f"[LOGIN {outcome}] username={username!r} role={role}")
    try:
        ip = request.remote_addr or "unknown"
        note = None
        # Flag obvious SQL injection attempts
        if any(c in username for c in ("'", "--", ";", "/*", "OR ", "or ")):
            note = "Possible SQL injection detected"
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
        pass  # Never let logging break the login flow


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


def fetch_user_profile(role, linked_id):
    db = get_db()
    if role == "doctor":
        return db.execute(
            "SELECT doctor_id, full_name, department, email FROM doctors WHERE doctor_id = ?",
            (linked_id,),
        ).fetchone()
    if role == "patient":
        return db.execute(
            """
            SELECT patient_id, full_name, date_of_birth, gender, phone, email
            FROM patients
            WHERE patient_id = ?
            """,
            (linked_id,),
        ).fetchone()
    return None


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

        db = get_db()
        try:
            cursor = db.execute(
                """
                INSERT INTO patients (full_name, date_of_birth, gender, phone, email)
                VALUES (?, ?, ?, ?, ?)
                """,
                (full_name, date_of_birth, gender, phone, email),
            )
            patient_id = cursor.lastrowid
            db.execute(
                """
                INSERT INTO users (username, password, role, linked_id)
                VALUES (?, ?, 'patient', ?)
                """,
                (username, password, patient_id),
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
def login():
    if request.method == "POST":
        if request.is_json:
            payload = request.get_json(silent=True) or {}
            username = str(payload.get("username", "")).strip()
            password = str(payload.get("password", ""))
        else:
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")

        db = get_db()
        # Intentionally vulnerable login query for local coursework demonstration only.
        # This is insecure because untrusted user input is concatenated directly into SQL,
        # which allows attackers to change the logic of the query with SQL injection.
        # Never use this pattern in production code.
        #
        # This route is also intentionally easy to brute-force:
        # - no rate limiting
        # - no account lockout
        # - no CAPTCHA
        # - immediate success/failure feedback
        query = (
            "SELECT user_id, username, role, linked_id FROM users "
            f"WHERE username = '{username}' AND password = '{password}'"
        )
        user = db.execute(query).fetchone()

        if user is None:
            log_login_attempt(username, success=False)
            if wants_json_response():
                return jsonify({"success": False, "message": "Invalid username or password."}), 401
            flash("Invalid username or password.")
            return render_template("login.html"), 401

        session.clear()
        session["user_id"] = user["user_id"]
        session["username"] = user["username"]
        session["role"] = user["role"]
        session["linked_id"] = user["linked_id"]
        log_login_attempt(user["username"], success=True, role=user["role"])

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
        "SELECT user_id, username, role, linked_id FROM users ORDER BY role, username"
    ).fetchall()
    patients = db.execute(
        """
        SELECT patient_id, full_name, date_of_birth, gender, phone, email
        FROM patients
        ORDER BY full_name
        """
    ).fetchall()
    doctors = db.execute(
        "SELECT doctor_id, full_name, department, email FROM doctors ORDER BY full_name"
    ).fetchall()
    records = db.execute(
        """
        SELECT mr.record_id, p.full_name AS patient_name, d.full_name AS doctor_name,
               mr.diagnosis, mr.last_updated
        FROM medical_records mr
        JOIN patients p ON p.patient_id = mr.patient_id
        JOIN doctors d ON d.doctor_id = mr.doctor_id
        ORDER BY mr.last_updated DESC
        """
    ).fetchall()
    return render_template(
        "admin_dashboard.html",
        users=users,
        patients=patients,
        doctors=doctors,
        records=records,
    )


@app.route("/doctor")
@login_required
@role_required("doctor")
def doctor_dashboard():
    doctor = fetch_user_profile("doctor", session.get("linked_id"))
    records = get_db().execute(
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
    return render_template("doctor_dashboard.html", doctor=doctor, records=records)


@app.route("/patient")
@login_required
@role_required("patient")
def patient_dashboard():
    patient = fetch_user_profile("patient", session.get("linked_id"))
    records = get_db().execute(
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
    return render_template("patient_dashboard.html", patient=patient, records=records)


if __name__ == "__main__":
    app.run(debug=True)
