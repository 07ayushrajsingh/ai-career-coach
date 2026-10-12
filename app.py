import os
import json
import sqlite3
from datetime import datetime

import bcrypt
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import (LoginManager, UserMixin, login_user, logout_user,
                         login_required, current_user)
from jinja2 import DictLoader
from werkzeug.utils import secure_filename

import config
import engine
import llm
from templates import TEMPLATES

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.jinja_loader = DictLoader(TEMPLATES)
app.config["MAX_CONTENT_LENGTH"] = config.MAX_UPLOAD_MB * 1024 * 1024

login_manager = LoginManager(app)
login_manager.login_view = "login"


def get_db():
    con = sqlite3.connect(config.DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    con = get_db()
    cur = con.cursor()

    cur.execute("""
        create table if not exists users (
            id integer primary key autoincrement,
            name text not null,
            email text not null unique,
            password_hash text not null,
            created_at text not null
        )
    """)

    cur.execute("""
        create table if not exists profiles (
            id integer primary key autoincrement,
            user_id integer not null,
            current_role text,
            target_role text,
            experience_years real,
            skills text,
            updated_at text,
            foreign key (user_id) references users(id)
        )
    """)

    cur.execute("""
        create table if not exists resumes (
            id integer primary key autoincrement,
            user_id integer not null,
            file_name text not null,
            raw_text text,
            parsed_data text,
            uploaded_at text not null,
            foreign key (user_id) references users(id)
        )
    """)

    cur.execute("""
        create table if not exists analysis (
            id integer primary key autoincrement,
            user_id integer not null,
            resume_id integer,
            ats_score integer,
            score_breakdown text,
            missing_skills text,
            created_at text not null,
            foreign key (user_id) references users(id)
        )
    """)

    cur.execute("""
        create table if not exists interview (
            id integer primary key autoincrement,
            user_id integer not null,
            target_role text,
            questions text,
            created_at text not null,
            foreign key (user_id) references users(id)
        )
    """)

    cur.execute("""
        create table if not exists answers (
            id integer primary key autoincrement,
            user_id integer not null,
            question text not null,
            answer text,
            score integer,
            feedback text,
            created_at text not null,
            foreign key (user_id) references users(id)
        )
    """)

    con.commit()
    con.close()


class User(UserMixin):
    def __init__(self, row):
        self.id = str(row["id"])
        self.name = row["name"]
        self.email = row["email"]


@login_manager.user_loader
def load_user(user_id):
    con = get_db()
    row = con.execute("select * from users where id = ?", (user_id,)).fetchone()
    con.close()
    if row:
        return User(row)
    return None


def get_profile(user_id):
    con = get_db()
    row = con.execute("select * from profiles where user_id = ?", (user_id,)).fetchone()
    con.close()
    return row


def get_last_resume(user_id):
    con = get_db()
    row = con.execute(
        "select * from resumes where user_id = ? order by id desc limit 1", (user_id,)
    ).fetchone()
    con.close()
    return row


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        con = get_db()
        existing = con.execute("select id from users where email = ?", (email,)).fetchone()
        if existing:
            con.close()
            flash("This email is already registered.", "danger")
            return redirect(url_for("register"))

        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        con.execute(
            "insert into users (name, email, password_hash, created_at) values (?, ?, ?, ?)",
            (name, email, pw_hash, now_str())
        )
        con.commit()
        con.close()

        flash("Account created. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        con = get_db()
        row = con.execute("select * from users where email = ?", (email,)).fetchone()
        con.close()

        if row and bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
            login_user(User(row))
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template(
        "dashboard.html",
        profile=get_profile(current_user.id),
        resume=get_last_resume(current_user.id)
    )


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    data = engine.load_data()
    roles = sorted(data["roles"].keys())

    if request.method == "POST":
        current_role = request.form.get("current_role", "").strip()
        target_role = request.form.get("target_role", "").strip()
        experience = request.form.get("experience_years", "0")
        skills = request.form.get("skills", "").strip()

        try:
            experience = float(experience)
        except ValueError:
            experience = 0

        con = get_db()
        existing = con.execute(
            "select id from profiles where user_id = ?", (current_user.id,)
        ).fetchone()

        if existing:
            con.execute("""
                update profiles
                set current_role = ?, target_role = ?, experience_years = ?,
                    skills = ?, updated_at = ?
                where user_id = ?
            """, (current_role, target_role, experience, skills, now_str(), current_user.id))
        else:
            con.execute("""
                insert into profiles
                (user_id, current_role, target_role, experience_years, skills, updated_at)
                values (?, ?, ?, ?, ?, ?)
            """, (current_user.id, current_role, target_role, experience, skills, now_str()))

        con.commit()
        con.close()

        flash("Profile saved.", "success")
        return redirect(url_for("dashboard"))

    return render_template("profile.html", profile=get_profile(current_user.id), roles=roles)


@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        file = request.files.get("resume")
        if not file or not file.filename:
            flash("Please select a file.", "danger")
            return redirect(url_for("upload"))

        name = secure_filename(file.filename)
        ext = os.path.splitext(name)[1].lower()

        if ext not in config.ALLOWED_EXT:
            flash("Only PDF and DOCX files are allowed.", "danger")
            return redirect(url_for("upload"))

        save_name = "u%s_%s" % (current_user.id, name)
        save_path = os.path.join(config.UPLOAD_DIR, save_name)
        file.save(save_path)

        try:
            raw_text, parsed = engine.parse_resume(save_path)
        except Exception as e:
            flash("Could not read this file: %s" % e, "danger")
            return redirect(url_for("upload"))

        if len(raw_text.split()) < 30:
            flash("Almost no text found. This may be a scanned resume, which is not supported.", "danger")
            return redirect(url_for("upload"))

        con = get_db()
        con.execute("""
            insert into resumes (user_id, file_name, raw_text, parsed_data, uploaded_at)
            values (?, ?, ?, ?, ?)
        """, (current_user.id, name, raw_text, json.dumps(parsed), now_str()))
        con.commit()

        # fill profile skills from resume if user has not entered any
        prof = con.execute(
            "select id, skills from profiles where user_id = ?", (current_user.id,)
        ).fetchone()
        if prof and not (prof["skills"] or "").strip() and parsed["skills"]:
            con.execute(
                "update profiles set skills = ?, updated_at = ? where id = ?",
                (", ".join(parsed["skills"]), now_str(), prof["id"])
            )
            con.commit()

        con.close()

        flash("Resume uploaded. %d skills detected." % len(parsed["skills"]), "success")
        return redirect(url_for("resume_view"))

    return render_template("upload.html", max_mb=config.MAX_UPLOAD_MB)


@app.route("/resume")
@login_required
def resume_view():
    row = get_last_resume(current_user.id)
    if not row:
        flash("No resume uploaded yet.", "danger")
        return redirect(url_for("upload"))

    parsed = json.loads(row["parsed_data"] or "{}")
    return render_template("resume_view.html", resume=row, parsed=parsed)


@app.route("/analysis")
@login_required
def analysis():
    prof = get_profile(current_user.id)
    row = get_last_resume(current_user.id)

    if not prof or not prof["target_role"]:
        flash("Please set your target role in profile first.", "danger")
        return redirect(url_for("profile"))

    if not row:
        flash("Please upload a resume first.", "danger")
        return redirect(url_for("upload"))

    parsed = json.loads(row["parsed_data"] or "{}")

    if "bullet_count" not in parsed:
        flash("Please re-upload your resume once, the analysis needs updated data.", "danger")
        return redirect(url_for("upload"))

    result = engine.run_analysis(parsed, prof["target_role"], prof["experience_years"])
    if not result:
        flash("Target role not found in data file.", "danger")
        return redirect(url_for("profile"))

    con = get_db()
    con.execute("""
        insert into analysis
        (user_id, resume_id, ats_score, score_breakdown, missing_skills, created_at)
        values (?, ?, ?, ?, ?, ?)
    """, (current_user.id, row["id"], result["ats"]["total"],
          json.dumps(result["ats"]["breakdown"]),
          json.dumps(result["gap"]["must_missing"] + result["gap"]["good_missing"]),
          now_str()))
    con.commit()
    con.close()

    return render_template("analysis.html", resume=row, profile=prof, result=result)


def get_interview(user_id):
    con = get_db()
    row = con.execute(
        "select * from interview where user_id = ? order by id desc limit 1", (user_id,)
    ).fetchone()
    con.close()
    return row


@app.route("/interview")
@login_required
def interview():
    prof = get_profile(current_user.id)
    if not prof or not prof["target_role"]:
        flash("Please set your target role in profile first.", "danger")
        return redirect(url_for("profile"))

    row = get_interview(current_user.id)
    questions = []

    if row and row["target_role"] == prof["target_role"]:
        questions = json.loads(row["questions"] or "[]")

    return render_template("interview.html", profile=prof, questions=questions)


@app.route("/interview/generate", methods=["POST"])
@login_required
def interview_generate():
    prof = get_profile(current_user.id)
    if not prof or not prof["target_role"]:
        flash("Please set your target role in profile first.", "danger")
        return redirect(url_for("profile"))

    skills = []
    resume = get_last_resume(current_user.id)
    if resume:
        parsed = json.loads(resume["parsed_data"] or "{}")
        skills = parsed.get("skills", [])
    elif prof["skills"]:
        skills = [s.strip() for s in prof["skills"].split(",") if s.strip()]

    try:
        questions = llm.generate_questions(prof["target_role"], prof["experience_years"], skills)
    except RuntimeError as e:
        flash(str(e), "danger")
        return redirect(url_for("interview"))

    if not questions:
        flash("Model did not return usable questions. Please try again.", "danger")
        return redirect(url_for("interview"))

    con = get_db()
    con.execute("""
        insert into interview (user_id, target_role, questions, created_at)
        values (?, ?, ?, ?)
    """, (current_user.id, prof["target_role"], json.dumps(questions), now_str()))
    con.commit()
    con.close()

    flash("%d questions generated." % len(questions), "success")
    return redirect(url_for("interview"))


@app.route("/interview/answer", methods=["POST"])
@login_required
def interview_answer():
    prof = get_profile(current_user.id)
    question = request.form.get("question", "").strip()
    answer = request.form.get("answer", "").strip()

    if not question or not answer:
        flash("Please write an answer first.", "danger")
        return redirect(url_for("interview"))

    try:
        result = llm.evaluate_answer(question, answer, prof["target_role"])
    except RuntimeError as e:
        flash(str(e), "danger")
        return redirect(url_for("interview"))

    if not result:
        flash("Model did not return usable feedback. Please try again.", "danger")
        return redirect(url_for("interview"))

    con = get_db()
    con.execute("""
        insert into answers (user_id, question, answer, score, feedback, created_at)
        values (?, ?, ?, ?, ?, ?)
    """, (current_user.id, question, answer, result["score"], json.dumps(result), now_str()))
    con.commit()
    con.close()

    row = get_interview(current_user.id)
    questions = json.loads(row["questions"] or "[]") if row else []

    return render_template(
        "interview.html", profile=prof, questions=questions,
        feedback=result, asked=question, given=answer
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)