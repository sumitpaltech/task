from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models import User
from app.middleware import login_required, guest_only

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/login", methods=["GET", "POST"])
@guest_only
def login():
    if request.method == "POST":
        login_value = request.form.get("username_or_email", "").strip()
        password = request.form.get("password", "")

        user = User.find_by_username_or_email(login_value)
        
        if user and User.verify_password(user["password"], password):
            session["user_id"]    = user["id"]
            session["user_name"]  = user["name"]
            session["username"]   = user["username"]
            session["email"]      = user["email"]

            role_value = user.get("role", "user") or "user"
            session["role"]       = role_value.strip().lower()
            session["department"] = user.get("department")

            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for("dashboard.index"))

        flash("Invalid username/email or password.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
@login_required
def register():
    # Only admin can register new users
    if session.get("role") != "admin":
        flash("Access denied. Only administrators can register new users.", "danger")
        return redirect(url_for("dashboard.index"))
    
    if request.method == "POST":
        name       = request.form.get("name", "").strip()
        username   = request.form.get("username", "").strip()
        email      = request.form.get("email", "").strip()
        password   = request.form.get("password", "")
        department = request.form.get("department") # Get department from dropdown

        if not name or not username or not email or not password or not department:
            flash("All fields including Username and Department are required.", "danger")
            return render_template("auth/register.html")

        if User.find_by_username(username):
            flash("Username already taken.", "danger")
            return render_template("auth/register.html")

        user_id = User.create(name, username, email, password, role='user', department=department)
        
        session["user_id"]    = user_id
        session["user_name"]  = name
        session["username"]   = username
        session["email"]      = email
        session["role"]       = "user"
        session["department"] = department
        
        flash("Account created successfully!", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("auth/register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    # Clear all session data (removes role and department)
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("auth.login"))