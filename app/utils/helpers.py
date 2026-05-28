from app import mysql

def get_user_email(username):
    cur = mysql.connection.cursor()
    cur.execute("SELECT email FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    return user['email'] if user else None