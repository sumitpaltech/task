from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from app.models.task_model import Task
from app.models.user_model import User
from app.middleware.auth_middleware import login_required

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

# ✅ SINGLE SOURCE OF TRUTH
DEPARTMENT_HEADS = {
    "IT": "Bala",
    "Business Intelligence": "Mayank Sir",
    "Data Analyst": "Mayank Sir",
    "Accounts": "KanhaiyaLal",
    "Marketing": "Divya",
    "Tender": "Divya",
    "Technical": "Devendra",
    "Sales & Marketing": "Divya",
    "Supply Chain Management": "Divya",
    "Services": "Divya",
    "New Project": "Bibhu",
    "Digital Marketing": "Divya",
    "Ecommerce": "Mayank Sir",
    "Dispatch": "Mayank Sir",
    "Costing": "Mayank Sir",
    "HR": "Mayank Sir",
    "Zoho": "Sadique",
}

def is_user_dept_head(username, department):
    if not username or not department:
        return False
    return DEPARTMENT_HEADS.get(department) == username


# =========================
# USERS (ADMIN ONLY)
# =========================
@dashboard_bp.route("/users")
@login_required
def users():
    if session.get("role") != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("dashboard.index"))

    users = User.all_with_details()
    return render_template("dashboard/users.html", users=users)


# =========================
# DASHBOARD
# =========================
@dashboard_bp.route("/")
@login_required
def index():
    user_id = session.get("user_id")
    user_role = session.get("role", "user")
    user_department = session.get("department")
    user_name = session.get("username")

    # =========================
    # 1. ROLE BASED STATS
    # =========================
    if user_role == 'admin':
        stats = {
            'total_tasks': Task.get_total_count(),
            'pending_tasks': Task.get_status_count('pending'),
            'completed_tasks': Task.get_status_count('completed'),
            'in_progress_tasks': Task.get_status_count('in_progress'),
            'total_users': User.get_total_count(),
        }

        chart_data = {
            'pending': Task.get_status_count('pending'),
            'completed': Task.get_status_count('completed'),
            'in_progress': Task.get_status_count('in_progress'),
            'cancelled': Task.get_status_count('cancelled'),
        }

    elif is_user_dept_head(user_name, user_department):
        counts = Task.count_by_department_status(user_department)
        status_map = {i['status'].strip().lower(): i['total'] for i in counts}

        stats = {
            'total_tasks': Task.count_by_department(user_department),
            'pending_tasks': status_map.get('pending', 0),
            'completed_tasks': status_map.get('completed', 0),
            'in_progress_tasks': status_map.get('in_progress', 0),
            'total_users': None,
        }

        chart_data = status_map

    else:
        counts = Task.count_by_status(user_name)
        status_map = {i['status'].strip().lower(): i['total'] for i in counts}

        stats = {
            'total_tasks': Task.count_by_user(user_name),
            'pending_tasks': status_map.get('pending', 0),
            'completed_tasks': status_map.get('completed', 0),
            'in_progress_tasks': status_map.get('in_progress', 0),
            'total_users': None,
        }

        chart_data = status_map

    # =========================
    # 2. RECENT TASKS
    # =========================
    if user_role == 'admin':
        recent_tasks = Task.get_recent_tasks(10)

    elif is_user_dept_head(user_name, user_department):
        recent_tasks = Task.by_department_paginated(user_department, 10, 0)

    else:
        recent_tasks = Task.get_user_tasks(user_id, 10)

    # =========================
    # 3. DEPARTMENT STATS (STRICT MAPPING)
    # =========================
    dept_stats = {}
    
    # Define order clearly
    if user_role == 'admin':
        depts_to_process = list(DEPARTMENT_HEADS.keys())
    elif is_user_dept_head(user_name, user_department):
        depts_to_process = [user_department]
    else:
        depts_to_process = []

    for dept in depts_to_process:
        counts = Task.count_by_department_status(dept)
        status_map = {i['status'].strip().lower(): i['total'] for i in counts}

        # Calculate total based on ALL statuses found
        actual_total = sum(status_map.values())

        dept_stats[dept] = {
            "pending": status_map.get("pending", 0),
            "completed": status_map.get("completed", 0),
            "in_progress": status_map.get("in_progress", 0),
            "cancelled": status_map.get("cancelled", 0),
            "total": actual_total
        }

    # =========================
    # 4. FINAL RENDER
    # =========================
    return render_template(
        "dashboard/index.html",
        stats=stats,
        chart_data=chart_data,
        dept_stats=dept_stats,
        recent_tasks=recent_tasks,
        user_role=user_role,
        user_department=user_department
    )

@dashboard_bp.route("/department/<dept>")
@login_required
def department_view(dept):

    # ✅ USERS FROM TASK TABLE ONLY
    users = Task.get_department_users_with_details(dept)

    # department tasks
    tasks = Task.by_department(dept)

    # department summary
    counts = Task.count_by_department_status(dept)
    status_map = {i['status'].strip().lower(): i['total'] for i in counts}

    dept_stats = {
        dept: {
            "pending": status_map.get("pending", 0),
            "completed": status_map.get("completed", 0),
            "in_progress": status_map.get("in_progress", 0),
            "cancelled": status_map.get("cancelled", 0),
            "total": sum(status_map.values())
        }
    }

    # ✅ USER STATS FROM TASK TABLE ONLY
    user_stats = Task.get_department_user_stats(dept)

    return render_template(
        "dashboard/department.html",
        dept=dept,
        users=users,
        tasks=tasks,
        dept_stats=dept_stats,
        user_stats=user_stats
    )

@dashboard_bp.route("/user/<username>")
@login_required
def user_tasks(username):
    tasks = Task.employee_all_data(username)

    return render_template(
        "dashboard/user_tasks.html",
        username=username,
        tasks=tasks
    )