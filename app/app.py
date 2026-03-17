from functools import wraps
import sqlite3
from pathlib import Path

from flask import Flask, flash, g, redirect, render_template, request, session, url_for
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = BASE_DIR / "instance" / "demo.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "coursework-demo-secret-key"
app.config["DATABASE"] = DATABASE


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


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Admin access is required.")
            return redirect(url_for("dashboard"))
        return view(*args, **kwargs)

    return wrapped_view


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

        if not username or not password:
            flash("Username and password are required.")
            return render_template("register.html")

        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
                (username, password, 0),
            )
            db.commit()
        except sqlite3.IntegrityError:
            flash("That username already exists.")
            return render_template("register.html")

        flash("Registration successful. Please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        db = get_db()
        # Intentionally vulnerable login query for local coursework demonstration only.
        # This is insecure because untrusted user input is concatenated directly into SQL,
        # which allows attackers to change the logic of the query with SQL injection.
        # Never use this pattern in production code.
        query = (
            "SELECT id, username, is_admin FROM users "
            f"WHERE username = '{username}' AND password = '{password}'"
        )
        user = db.execute(query).fetchone()

        if user is None:
            flash("Invalid username or password.")
            return render_template("login.html")

        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["is_admin"] = bool(user["is_admin"])
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
    return render_template("dashboard.html")


@app.route("/admin")
@login_required
@admin_required
def admin_dashboard():
    users = get_db().execute(
        "SELECT id, username, is_admin FROM users ORDER BY username"
    ).fetchall()
    return render_template("admin.html", users=users)


if __name__ == "__main__":
    app.run(debug=True)
