from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback-secret")


# Database connection
def get_db():
    conn = sqlite3.connect(
        "database.db",
        timeout=10,
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    return conn


# Create tables
with get_db() as db:
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            user_id INTEGER
        )
    """)

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            db = get_db()
            db.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            db.commit()
            return redirect("/login")

        except sqlite3.IntegrityError:
            error = "Username already exists"

        finally:
            db.close()

    return render_template("register.html", error=error)


# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()

        if user:
            session["user_id"] = user["id"]
            return redirect("/dashboard")

    return render_template("login.html")

# ---------------- DASHBOARD (READ) ----------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    notes = db.execute(
        "SELECT * FROM notes WHERE user_id=?",
        (session["user_id"],)
    ).fetchall()

    return render_template("dashboard.html", notes=notes)

# ---------------- ADD NOTE (CREATE) ----------------
@app.route("/add", methods=["GET", "POST"])
def add_note():
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        db = get_db()
        db.execute(
            "INSERT INTO notes (title, content, user_id) VALUES (?, ?, ?)",
            (title, content, session["user_id"])
        )
        db.commit()
        return redirect("/dashboard")

    return render_template("add_note.html")

# ---------------- EDIT NOTE (UPDATE) ----------------
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_note(id):
    db = get_db()

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        db.execute(
            "UPDATE notes SET title=?, content=? WHERE id=?",
            (title, content, id)
        )
        db.commit()
        return redirect("/dashboard")

    note = db.execute("SELECT * FROM notes WHERE id=?", (id,)).fetchone()
    return render_template("edit_note.html", note=note)

# ---------------- DELETE NOTE ----------------
@app.route("/delete/<int:id>")
def delete_note(id):
    db = get_db()
    db.execute("DELETE FROM notes WHERE id=?", (id,))
    db.commit()
    return redirect("/dashboard")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")



import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
