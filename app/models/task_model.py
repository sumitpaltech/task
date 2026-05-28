from app import mysql
from .base_model import BaseModel

class Task(BaseModel):
    table = "task_tracker"

    @classmethod
    def all_with_user_paginated(cls, limit=20, offset=0):
        cur = cls.get_cursor()
        cur.execute("""
            SELECT 
                task_tracker.*, 
                COALESCE(users.name, task_tracker.assigned_to) as assigned_to_name
            FROM task_tracker
            LEFT JOIN users ON task_tracker.assigned_to = users.username
            ORDER BY task_tracker.created_at DESC
            LIMIT %s OFFSET %s
        """, (limit, offset))
        return cur.fetchall()
    
    
    
    @classmethod
    def by_user_paginated(cls, user_email, limit=20, offset=0):
        cur = cls.get_cursor()
        cur.execute("""
            SELECT * FROM task_tracker 
            WHERE assigned_to = %s 
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, [user_email, limit, offset])
        return cur.fetchall()
    

    
    @classmethod
    def get_by_user(cls, username):
        cur = cls.get_cursor()
        cur.execute("SELECT * FROM task_tracker WHERE assigned_to = %s", (username,))
        return cur.fetchall()
    

    

    




    @classmethod
    def by_department_paginated(cls, department, limit=20, offset=0):
        cur = cls.get_cursor()
        cur.execute("""
            SELECT 
                task_tracker.*, 
                COALESCE(users.name, task_tracker.assigned_to) as assigned_to_name
            FROM task_tracker
            LEFT JOIN users ON task_tracker.assigned_to = users.username
            WHERE task_tracker.department = %s
            ORDER BY task_tracker.created_at DESC
            LIMIT %s OFFSET %s
        """, [department, limit, offset])
        return cur.fetchall()
    
    @classmethod
    def count_all(cls):
        cur = cls.get_cursor()
        cur.execute("SELECT COUNT(*) as total FROM task_tracker")
        result = cur.fetchone()
        return result['total'] if result else 0
    
    @classmethod
    def count_by_user(cls, user_email):
        cur = cls.get_cursor()
        cur.execute("SELECT COUNT(*) as total FROM task_tracker WHERE assigned_to = %s", [user_email])
        result = cur.fetchone()
        return result['total'] if result else 0
    
    @classmethod
    def count_by_department(cls, department):
        cur = cls.get_cursor()
        cur.execute("SELECT COUNT(*) as total FROM task_tracker WHERE department = %s", [department])
        result = cur.fetchone()
        return result['total'] if result else 0

    @classmethod
    def get_total_count(cls):
        cur = cls.get_cursor()
        cur.execute("SELECT COUNT(*) as total FROM task_tracker")
        result = cur.fetchone()
        return result['total'] if result else 0

    @classmethod
    def get_status_count(cls, status):
        cur = cls.get_cursor()
        cur.execute("SELECT COUNT(*) as total FROM task_tracker WHERE status = %s", [status])
        result = cur.fetchone()
        return result['total'] if result else 0

    @classmethod
    def get_recent_tasks(cls, limit=10):
        cur = cls.get_cursor()
        cur.execute("""
            SELECT 
                task_tracker.*, 
                COALESCE(users.name, task_tracker.assigned_to) as assigned_to_name
            FROM task_tracker
            LEFT JOIN users ON task_tracker.assigned_to = users.username
            ORDER BY task_tracker.created_at DESC
            LIMIT %s
        """, [limit])
        return cur.fetchall()

    @classmethod
    def get_user_tasks(cls, user_id, limit=10):
        cur = cls.get_cursor()
        cur.execute("""
            SELECT * FROM task_tracker 
            WHERE assigned_to = (SELECT username FROM users WHERE id = %s)
            ORDER BY created_at DESC
            LIMIT %s
        """, [user_id, limit])
        return cur.fetchall()

    @classmethod
    def create(cls, data):
        """
        Fixed Indentation and added all fields matching your Excel sheet.
        """
        cur = cls.get_cursor()
        sql = """
            INSERT INTO task_tracker (
                title, description, category, department, assigned_to, user_mail,
                team_member, priority, start_date, due_date, completion_date, 
                status, remarks, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        values = (
            data.get('title'), 
            data.get('description'), 
            data.get('category'), 
            data.get('department'),
            data.get('assigned_to'),
            data.get('user_mail'),
            data.get('team_member'),
            data.get('priority'), 
            data.get('start_date'), 
            data.get('due_date'),
            data.get('completion_date'),
            data.get('status', 'pending'), 
            data.get('remarks')
        )
        cur.execute(sql, values)
        mysql.connection.commit()
        return cur.lastrowid

    @classmethod
    def update(cls, id, data):
        cur = cls.get_cursor()
        sql = """
            UPDATE task_tracker SET 
                title=%s, description=%s, category=%s, department=%s, 
                assigned_to=%s, user_mail=%s, team_member=%s, priority=%s, status=%s, 
                start_date=%s, due_date=%s, completion_date=%s, remarks=%s, 
                updated_at=NOW()
            WHERE id=%s
        """
        values = (
            data.get('title'), 
            data.get('description'), 
            data.get('category'),
            data.get('department'), 
            data.get('assigned_to'),
            data.get('user_mail'),
            data.get('team_member'), 
            data.get('priority'),
            data.get('status'), 
            data.get('start_date'),
            data.get('due_date'),
            data.get('completion_date'),
            data.get('remarks'),
            id
        )
        cur.execute(sql, values)
        mysql.connection.commit()
        return cur.rowcount

    @classmethod
    def delete(cls, id):
        cur = cls.get_cursor()
        cur.execute("DELETE FROM task_tracker WHERE id = %s", (id,))
        mysql.connection.commit()
        return cur.rowcount

    @classmethod
    def update_file_attachment(cls, id, filename):
        """Set file_attachment to a single file"""
        cur = cls.get_cursor()
        cur.execute("""
            UPDATE task_tracker 
            SET file_attachment = %s, updated_at = NOW()
            WHERE id = %s
        """, (filename, id))
        mysql.connection.commit()
        return cur.rowcount

    @classmethod
    def add_file_attachment(cls, id, filename):
        """Append a new file to existing file_attachment (semicolon-separated)"""
        cur = cls.get_cursor()
        # Get current attachments
        cur.execute("SELECT file_attachment FROM task_tracker WHERE id = %s", (id,))
        result = cur.fetchone()
        current_files = result['file_attachment'] if result and result['file_attachment'] else ''
        
        # Append new file
        if current_files.strip():
            new_files = f"{current_files};{filename}"
        else:
            new_files = filename
        
        # Update
        cur.execute("""
            UPDATE task_tracker 
            SET file_attachment = %s, updated_at = NOW()
            WHERE id = %s
        """, (new_files, id))
        mysql.connection.commit()
        return cur.rowcount

    @classmethod
    def find(cls, id):
        cur = cls.get_cursor()
        cur.execute("SELECT * FROM task_tracker WHERE id = %s", (id,))
        return cur.fetchone()

    @classmethod
    def count_by_status(cls, assigned_to_value):
        cur = cls.get_cursor()
        cur.execute("""
            SELECT status, COUNT(*) as total
            FROM task_tracker 
            WHERE assigned_to = %s
            GROUP BY status
        """, (assigned_to_value,))
        return cur.fetchall()
    
    @classmethod
    def find_with_user(cls, id):
        """Finds a task by ID and includes the user name and email from the users table"""
        cur = cls.get_cursor()
        cur.execute("""
            SELECT task_tracker.*, users.name AS user_name, users.email AS assigned_email
            FROM task_tracker
            LEFT JOIN users ON task_tracker.assigned_to = users.username
            WHERE task_tracker.id = %s
        """, (id,))
        return cur.fetchone()
    
    @classmethod
    def count_all_statuses(cls):
        """Get task counts for all users (Admin view)"""
        cur = cls.get_cursor()
        cur.execute("""
            SELECT status, COUNT(*) as total
            FROM task_tracker 
            GROUP BY status
        """)
        return cur.fetchall()
    
    @classmethod
    def by_department(cls, department_name):
        """Find tasks matching a specific department"""
        cur = cls.get_cursor()
        cur.execute("SELECT * FROM task_tracker WHERE department = %s", [department_name])
        return cur.fetchall()

    @classmethod
    def count_by_department_status(cls, department_name):
        """Get status stats for a specific department"""
        cur = cls.get_cursor()
        cur.execute("""
            SELECT status, COUNT(*) as total
            FROM task_tracker 
            WHERE department = %s
            GROUP BY status
        """, (department_name,))
        return cur.fetchall()
    
    @classmethod
    def filter_all_paginated(cls, filters, limit, offset):
        cur = cls.get_cursor()

        query = """
            SELECT 
                task_tracker.*, 
                COALESCE(users.name, task_tracker.assigned_to) as assigned_to_name
            FROM task_tracker
            LEFT JOIN users ON task_tracker.assigned_to = users.username
            WHERE 1=1
        """

        params = []

        if filters.get("title"):
            query += " AND task_tracker.title LIKE %s"
            params.append(f"%{filters['title']}%")

        if filters.get("assigned_to"):
            query += " AND task_tracker.assigned_to = %s"
            params.append(filters["assigned_to"])

        if filters.get("department"):
            query += " AND task_tracker.department = %s"
            params.append(filters["department"])

        if filters.get("status"):
            query += " AND task_tracker.status = %s"
            params.append(filters["status"])

        if filters.get("priority"):
            query += " AND task_tracker.priority = %s"
            params.append(filters["priority"])

        query += " ORDER BY task_tracker.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cur.execute(query, params)
        return cur.fetchall()
    
    @classmethod
    def count_filtered(cls, filters):
        cur = cls.get_cursor()

        query = "SELECT COUNT(*) as total FROM task_tracker WHERE 1=1"
        params = []

        if filters.get("title"):
            query += " AND title LIKE %s"
            params.append(f"%{filters['title']}%")

        if filters.get("assigned_to"):
            query += " AND assigned_to = %s"
            params.append(filters["assigned_to"])

        if filters.get("department"):
            query += " AND department = %s"
            params.append(filters["department"])

        if filters.get("status"):
            query += " AND status = %s"
            params.append(filters["status"])

        if filters.get("priority"):
            query += " AND priority = %s"
            params.append(filters["priority"])

        cur.execute(query, params)
        return cur.fetchone()['total']
    
    @classmethod
    def get_filtered_status_summary(cls, filters):
        cur = cls.get_cursor()

        query = "SELECT status, COUNT(*) as total FROM task_tracker WHERE 1=1"
        params = []

        if filters.get("title"):
            query += " AND title LIKE %s"
            params.append(f"%{filters['title']}%")

        if filters.get("assigned_to"):
            query += " AND task_tracker.assigned_to LIKE %s"
            params.append(f"%{filters['assigned_to']}%")

        if filters.get("department"):
            query += " AND task_tracker.department LIKE %s"
            params.append(f"%{filters['department']}%")

        if filters.get("status"):
            query += " AND status = %s"
            params.append(filters["status"])

        if filters.get("priority"):
            query += " AND priority = %s"
            params.append(filters["priority"])

        if filters.get("start_date"):
            query += " AND task_tracker.due_date >= %s"
            params.append(filters["start_date"])

        if filters.get("end_date"):
            query += " AND task_tracker.due_date <= %s"
            params.append(filters["end_date"])

        query += " GROUP BY status"

        cur.execute(query, params)
        return cur.fetchall()
    
    @classmethod
    def get_distinct_departments(cls):
        cur = cls.get_cursor()
        cur.execute("SELECT DISTINCT department FROM task_tracker WHERE department IS NOT NULL")
        return [row['department'] for row in cur.fetchall()]

    @classmethod
    def get_distinct_assigned_users(cls):
        cur = cls.get_cursor()
        cur.execute("""
            SELECT DISTINCT assigned_to FROM task_tracker 
            WHERE assigned_to IS NOT NULL
        """)
        return [row['assigned_to'] for row in cur.fetchall()]

    @classmethod
    def get_distinct_status(cls):
        cur = cls.get_cursor()
        cur.execute("SELECT DISTINCT status FROM task_tracker")
        return [row['status'] for row in cur.fetchall()]

    @classmethod
    def get_distinct_priority(cls):
        cur = cls.get_cursor()
        cur.execute("SELECT DISTINCT priority FROM task_tracker")
        return [row['priority'] for row in cur.fetchall()]
    
    @classmethod
    def employee_all_data(cls,username):
        cur = cls.get_cursor()
        cur.execute("""
            SELECT 
            task_tracker.*,
            COALESCE(users.name, task_tracker.assigned_to) AS employee_name,
            users.email AS employee_email,
            users.department AS employee_department
        FROM task_tracker
        LEFT JOIN users ON task_tracker.assigned_to = users.username
        WHERE task_tracker.assigned_to = %s
        ORDER BY task_tracker.created_at DESC
        """, (username,))
        return cur.fetchall()
    


    @classmethod
    def get_user_task_summary_with_pending(cls):
        cur = cls.get_cursor()

        # Summary
        cur.execute("""
            SELECT 
                assigned_to,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status != 'completed' THEN 1 ELSE 0 END) as pending
            FROM task_tracker
            GROUP BY assigned_to
        """)
        
        users = cur.fetchall()
        result = []

        for user in users:
            assigned_to = user['assigned_to']

            # Pending tasks
            cur.execute("""
                SELECT title, due_date 
                FROM task_tracker
                WHERE assigned_to = %s AND status != 'completed'
                ORDER BY due_date ASC
            """, (assigned_to,))
            
            pending_tasks = cur.fetchall()

            total = user['total']
            completed = user['completed']
            pending = user['pending']

            result.append({
                "assigned_to": assigned_to,
                "total": total,
                "completed": completed,
                "pending": pending,
                "completed_pct": round((completed / total * 100), 2) if total else 0,
                "pending_pct": round((pending / total * 100), 2) if total else 0,
                "pending_tasks": pending_tasks
            })

        return result
    # ================================
    # nikhil code - user wise task stats for department dashboard charts
    # ================================
    @classmethod
    def get_department_user_stats(cls, department):
        cur = cls.get_cursor()

        cur.execute("""
            SELECT 
                assigned_to,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled
            FROM task_tracker
            WHERE department = %s
            GROUP BY assigned_to
        """, (department,))

        rows = cur.fetchall()

        result = {}

        for r in rows:
            result[r['assigned_to']] = {
                "total": int(r['total'] or 0),
                "completed": int(r['completed'] or 0),
                "pending": int(r['pending'] or 0),
                "in_progress": int(r['in_progress'] or 0),
                "cancelled": int(r['cancelled'] or 0)
            }

        return result


    # ================================
    # nikhil code - get unique users in a department (task based)
    # ================================
    @classmethod
    def get_department_users(cls, department):
        cur = cls.get_cursor()

        cur.execute("""
            SELECT DISTINCT assigned_to AS username
            FROM task_tracker
            WHERE department = %s
            AND assigned_to IS NOT NULL
            AND assigned_to != ''
        """, (department,))

        return cur.fetchall()


    # ================================
    # nikhil code - get department users with email (from task table)
    # ================================
    @classmethod
    def get_department_users_with_details(cls, department):
        cur = cls.get_cursor()

        cur.execute("""
            SELECT 
                assigned_to as username,
                MAX(user_mail) as email
            FROM task_tracker
            WHERE department = %s
            AND assigned_to IS NOT NULL
            AND assigned_to != ''
            GROUP BY assigned_to
        """, (department,))

        return cur.fetchall()

    # ================================
    # nikhil code - full task list for a user (task tracker table)
    # ================================
    @classmethod
    def employee_all_data(cls, username):
        cur = cls.get_cursor()

        cur.execute("""
            SELECT *
            FROM task_tracker
            WHERE assigned_to = %s
            ORDER BY created_at DESC
        """, (username,))

        return cur.fetchall()


    # ================================
    # nikhil code - user task summary (dashboard stats)
    # ================================
    @classmethod
    def get_user_summary(cls, username):
        cur = cls.get_cursor()

        cur.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status!='completed' THEN 1 ELSE 0 END) as pending
            FROM task_tracker
            WHERE assigned_to = %s
        """, (username,))

        return cur.fetchone()
