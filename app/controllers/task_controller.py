import pandas as pd
import numpy as np
import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file
from werkzeug.utils import secure_filename
from app.models.task_model import Task
from app.middleware.auth_middleware import login_required

# File upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xlsx', 'xls', 'jpg', 'jpeg', 'png', 'txt', 'zip'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_path(filename):
    """Get safe file path"""
    return os.path.join(UPLOAD_FOLDER, secure_filename(filename))

# --- NEW: DEPARTMENT HEAD MAPPING ---
# Update this dictionary with the actual usernames from your 'users' table
DEPARTMENT_HEADS = {         
    "Admin": "Sumit",
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
    """Checks if the given username is the head of the specified department."""
    if not username or not department:
        return False
    return DEPARTMENT_HEADS.get(department) == username


task_bp = Blueprint("task", __name__, url_prefix="/tasks")

def is_authorized(task):
    """
    Logic:
    1. Admin: Access everything.
    2. Dept Head: Access all tasks in their specific department.
    3. User: Access ONLY tasks assigned to their username.
    """
    if not task:
        return False

    user_role = (session.get("role") or "").strip().lower()
    user_dept = session.get("department")
    user_name = session.get("username") or session.get("user_name")

    # 1. Admin bypass
    if user_role == 'admin':
        return True

    # 2. Check if user is the designated Head of this task's department
    if is_user_dept_head(user_name, task.get("department")):
        return True

    # 3. Standard User: Only their own tasks
    return task.get("assigned_to") == user_name


@task_bp.route("/")
@login_required
def index():
    """GET /tasks — list tasks based on specific visibility rules"""
    user_name = session.get("username") or session.get("user_name")
    user_role = (session.get("role") or "").strip().lower()
    user_dept = session.get("department")
  
    # --- FILTER INPUTS ---
    title_filter = request.args.get("title", "").strip()
    assigned_filter = request.args.get("assigned_to", "").strip()
    dept_filter = request.args.get("department", "").strip()
    status_filter = request.args.get("status", "").strip()
    priority_filter = request.args.get("priority", "").strip()

    # Pagination
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    # --- FILTER OBJECT ---
    filters = {
        "title": title_filter,
        "assigned_to": assigned_filter,
        "department": dept_filter,
        "status": status_filter,
        "priority": priority_filter
    }

    if user_role == 'admin':
        tasks = Task.filter_all_paginated(filters, per_page, offset)
        total_tasks = Task.count_filtered(filters)
        stats = Task.get_filtered_status_summary(filters)

    elif is_user_dept_head(user_name, user_dept):
        filters["department"] = user_dept
        tasks = Task.filter_all_paginated(filters, per_page, offset)
        total_tasks = Task.count_filtered(filters)
        stats = Task.get_filtered_status_summary(filters)

    else:
        filters["assigned_to"] = user_name
        tasks = Task.filter_all_paginated(filters, per_page, offset)
        total_tasks = Task.count_filtered(filters)
        stats = Task.get_filtered_status_summary(filters)

    status_map = {s['status']: s['total'] for s in stats}

    completed = status_map.get('completed', 0)
    pending = status_map.get('pending', 0)
    in_progress = status_map.get('in_progress', 0)

    total = total_tasks

    summary = {
        "total": total,
        "completed": completed,
        "pending": pending,
        "in_progress": in_progress,
        "completed_pct": round((completed / total * 100), 2) if total else 0,
        "pending_pct": round((pending / total * 100), 2) if total else 0,
        "in_progress_pct": round((in_progress / total * 100), 2) if total else 0,
    }
        
    # Calculate pagination info (Keep this as is)
    total_pages = (total_tasks + per_page - 1) // per_page
    pagination = {
        'page': page,
        'per_page': per_page,
        'total_tasks': total_tasks,
        'total_pages': total_pages,
        'has_next': page < total_pages,
        'has_prev': page > 1,
        'next_page': page + 1 if page < total_pages else None,
        'prev_page': page - 1 if page > 1 else None
    }
    departments = Task.get_distinct_departments()
    users = Task.get_distinct_assigned_users()
    statuses = Task.get_distinct_status()
    priorities = Task.get_distinct_priority()

    return render_template(
        "tasks/index.html",
        tasks=tasks,
        stats=stats,
        pagination=pagination,
        summary=summary,
        departments=departments,
        users=users,
        statuses=statuses,
        priorities=priorities
    )

@task_bp.route("/store", methods=["POST"])
@login_required
def store():
    """POST /tasks/store — save new task"""
    user_role = (session.get("role") or "").strip().lower()
    
    data = {
        "title": request.form.get("title", "").strip(),
        "description": request.form.get("description", "").strip(),
        "category": request.form.get("category", "General"),
        "department": request.form.get("department", "").strip(),
        "assigned_to": request.form.get("assigned_to", "").strip() if user_role == 'admin' else session.get("username"),
        "user_mail": request.form.get("user_mail", "").strip() if user_role == 'admin' else session.get("email"),
        "team_member": request.form.get("team_member", "").strip(),
        "priority": request.form.get("priority", "medium"),
        "start_date": request.form.get("start_date") or None,
        "due_date": request.form.get("due_date") or None,
        "completion_date": request.form.get("completion_date") or None,
        "status": request.form.get("status", "pending"),
        "remarks": request.form.get("remarks", "").strip()
    }

    if not data["title"]:
        flash("Title is required.", "danger")
        return redirect(url_for("task.create"))

    Task.create(data)
    flash("Task created successfully!", "success")
    return redirect(url_for("task.index"))


@task_bp.route("/<int:id>", methods=["GET"])
@login_required
def show(id):
    """GET /tasks/<id> — view single task"""
    task = Task.find_with_user(id)
    if not is_authorized(task):
        flash("Task not found.", "danger")
        return redirect(url_for("task.index"))
    return render_template("tasks/show.html", task=task)


@task_bp.route("/<int:id>/update", methods=["POST"])
@login_required
def update(id):
    """POST /tasks/<id>/update — save task changes"""
    task = Task.find(id)
    if not is_authorized(task):
        flash("Task not found.", "danger")
        return redirect(url_for("task.index"))

    user_role = (session.get("role") or "").strip().lower()

    title       = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    status      = request.form.get("status", "pending")
    priority    = request.form.get("priority", "medium")
    category    = request.form.get("category", "General")
    department  = request.form.get("department", "").strip()
    assigned_to = request.form.get("assigned_to", "").strip() if user_role == 'admin' else task.get("assigned_to")
    user_mail   = request.form.get("user_mail", "").strip() if user_role == 'admin' else task.get("user_mail")
    team_member = request.form.get("team_member", "").strip()
    remarks     = request.form.get("remarks", "").strip()

    # Dates: only admin can change
    start_date = request.form.get("start_date") or None if user_role == 'admin' else task.get("start_date")
    due_date = request.form.get("due_date") or None if user_role == 'admin' else task.get("due_date")
    completion_date = request.form.get("completion_date") or None if user_role == 'admin' else task.get("completion_date")

    if not title:
        flash("Title is required.", "danger")
        return redirect(url_for("task.edit", id=id))

    update_data = {
        "title": title,
        "description": description,
        "category": category,
        "department": department,
        "assigned_to": assigned_to,
        "user_mail": user_mail,
        "team_member": team_member,
        "priority": priority,
        "status": status,
        "start_date": start_date,
        "due_date": due_date,
        "completion_date": completion_date,
        "remarks": remarks
    }
    
    # Handle file upload
    file_attachment = None
    if 'file_upload' in request.files:
        file = request.files['file_upload']
        if file and file.filename and allowed_file(file.filename):
            file_data = file.read()
            if len(file_data) > MAX_FILE_SIZE:
                flash("File size exceeds 10 MB limit.", "danger")
                return redirect(url_for("task.edit", id=id))
            
            filename = secure_filename(f"task_{id}_{file.filename}")
            filepath = get_file_path(filename)
            with open(filepath, 'wb') as f:
                f.write(file_data)
            file_attachment = filename

    Task.update(id, update_data)
    
    if file_attachment:
        Task.update_file_attachment(id, file_attachment)
        flash("Task and file updated successfully!", "success")
    else:
        flash("Task updated successfully!", "success")
    
    return redirect(url_for("task.index"))


@task_bp.route("/create", methods=["GET"])
@login_required
def create():
    """GET /tasks/create — show create form"""
    return render_template("tasks/create.html")


@task_bp.route("/<int:id>/edit", methods=["GET"])
@login_required
def edit(id):
    """GET /tasks/<id>/edit — show the edit form"""
    task = Task.find(id)
    if not is_authorized(task):
        flash("Task not found.", "danger")
        return redirect(url_for("task.index"))
    
    return render_template("tasks/edit.html", task=task)


@task_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete(id):
    """POST /tasks/<id>/delete — remove a task"""
    task = Task.find(id)
    
    if not is_authorized(task):
        flash("Task not found or unauthorized.", "danger")
        return redirect(url_for("task.index"))

    Task.delete(id)
    flash("Task deleted successfully!", "success")
    return redirect(url_for("task.index"))


@task_bp.route("/<int:id>/upload_file_index", methods=["POST"])
@login_required
def upload_file_index(id):
    """POST /tasks/<id>/upload_file_index — upload file to task from index page"""
    task = Task.find(id)
    
    if not is_authorized(task):
        flash("Task not found or unauthorized.", "danger")
        return redirect(url_for("task.index"))
    
    if 'file_upload' not in request.files:
        flash("No file selected.", "danger")
        return redirect(url_for("task.index"))
    
    file = request.files['file_upload']
    if not file or not file.filename:
        flash("No file selected.", "danger")
        return redirect(url_for("task.index"))
    
    if not allowed_file(file.filename):
        flash("File type not allowed. Allowed: PDF, Word, Excel, Images, TXT, ZIP", "danger")
        return redirect(url_for("task.index"))
    
    file_data = file.read()
    if len(file_data) > MAX_FILE_SIZE:
        flash("File size exceeds 10 MB limit.", "danger")
        return redirect(url_for("task.index"))
    
    filename = secure_filename(f"task_{id}_{file.filename}")
    filepath = get_file_path(filename)
    
    with open(filepath, 'wb') as f:
        f.write(file_data)
    
    Task.add_file_attachment(id, filename)
    flash("File uploaded successfully!", "success")
    
    return redirect(url_for("task.index"))


@task_bp.route("/<int:id>/upload_file", methods=["POST"])
@login_required
def upload_file(id):
    """POST /tasks/<id>/upload_file — upload file to task"""
    task = Task.find(id)
    
    if not is_authorized(task):
        flash("Task not found or unauthorized.", "danger")
        return redirect(url_for("task.show", id=id))
    
    if 'file_upload' not in request.files:
        flash("No file selected.", "danger")
        return redirect(url_for("task.show", id=id))
    
    file = request.files['file_upload']
    if not file or not file.filename:
        flash("No file selected.", "danger")
        return redirect(url_for("task.show", id=id))
    
    if not allowed_file(file.filename):
        flash("File type not allowed. Allowed: PDF, Word, Excel, Images, TXT, ZIP", "danger")
        return redirect(url_for("task.show", id=id))
    
    file_data = file.read()
    if len(file_data) > MAX_FILE_SIZE:
        flash("File size exceeds 10 MB limit.", "danger")
        return redirect(url_for("task.show", id=id))
    
    filename = secure_filename(f"task_{id}_{file.filename}")
    filepath = get_file_path(filename)
    
    with open(filepath, 'wb') as f:
        f.write(file_data)
    
    Task.add_file_attachment(id, filename)
    flash("File uploaded successfully!", "success")
    
    return redirect(url_for("task.show", id=id))


@task_bp.route("/download_file/<filename>", methods=["GET"])
@login_required
def download_file(filename):
    """GET /tasks/download_file/<filename> — download or view task file"""
    try:
        filepath = get_file_path(filename)
        
        if not os.path.exists(filepath):
            flash("File not found.", "danger")
            return redirect(url_for("task.index"))
        
        if not os.path.abspath(filepath).startswith(os.path.abspath(UPLOAD_FOLDER)):
            flash("Invalid file.", "danger")
            return redirect(url_for("task.index"))
        
        # Determine if file should be viewed inline or downloaded
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        inline_types = {'pdf', 'jpg', 'jpeg', 'png', 'gif', 'txt'}
        
        if ext in inline_types:
            return send_file(filepath, as_attachment=False)
        else:
            return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        flash(f"Error accessing file: {str(e)}", "danger")
        return redirect(url_for("task.index"))


@task_bp.route("/import", methods=["POST"])
@login_required
def import_excel():
    """POST /tasks/import — bulk import tasks from Excel"""
    file = request.files.get('file')
    if not file or file.filename == '':
        flash("Please select a file.", "danger")
        return redirect(url_for("task.index"))

    try:
        df = pd.read_excel(file, skiprows=0)
        
        df = df.replace({np.nan: None})
        df = df.where(pd.notnull(df), None)
        count = 0
        
        for _, row in df.iterrows():
            cols = list(row)

            task_data = {
                "title": str(cols[0]).strip() if cols[0] else None,
                "description": str(cols[1]).strip() if cols[1] else None,
                "category": str(cols[2]).strip() if cols[2] else None,
                "department": str(cols[3]).strip() if cols[3] else None,
                "assigned_to": str(cols[4]).strip() if cols[4] else None,
                "user_mail": str(cols[6]).strip() if cols[6] else None,
                "team_member": str(cols[5]).strip() if cols[5] else None,
                "priority": str(cols[7] or "medium").strip().lower(),
                "start_date": cols[8],
                "due_date": cols[9],
                "completion_date": cols[10],
                "status": str(cols[11] or "pending").strip().lower().replace(" ", "_"),
                "remarks": str(cols[12]).strip() if cols[12] else None
            }
            
            cleaned_data = {k: (None if (isinstance(v, float) and np.isnan(v)) else v) for k, v in task_data.items()}

            Task.create(cleaned_data)
            count += 1

        flash(f"Successfully imported {count} tasks!", "success")
        
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        flash(f"Import failed: {str(e)}", "danger")

    return redirect(url_for("task.index"))
