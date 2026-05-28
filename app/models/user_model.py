from app import mysql
from .base_model import BaseModel
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import datetime
import os
from cryptography.fernet import Fernet

# Set up security logging
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.WARNING)
handler = logging.FileHandler('security_audit.log')
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
security_logger.addHandler(handler)

# CRITICAL SECURITY: Generate encryption key for emergency password access
# In production, this should be environment variable or HSM
ENCRYPTION_KEY = os.environ.get('PASSWORD_ENCRYPTION_KEY')
if not ENCRYPTION_KEY:
    # Generate a key for development - NEVER DO THIS IN PRODUCTION
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    print("⚠️  WARNING: Using auto-generated encryption key. Set PASSWORD_ENCRYPTION_KEY environment variable in production!")
    
cipher = Fernet(ENCRYPTION_KEY.encode())


class User(BaseModel):
    table = "users"

    @classmethod
    def find_by_email(cls, email):
        cur = cls.get_cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        return cur.fetchone()
    

        # ✅ ADD HERE (INSIDE CLASS) nikhil code to get users by department for dashboard filtering
    @classmethod
    def get_by_department(cls, dept):
        cur = cls.get_cursor()
        cur.execute("""
            SELECT * FROM users
            WHERE department = %s AND status = 1
        """, (dept,))
        return cur.fetchall()




    @classmethod
    def find_by_username(cls, username):
        cur = cls.get_cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        return cur.fetchone()

    @classmethod
    def find_by_username_or_email(cls, identifier):
        cur = cls.get_cursor()
        cur.execute(
            "SELECT * FROM users WHERE username = %s OR email = %s LIMIT 1",
            (identifier, identifier)
        )
        return cur.fetchone()

    @classmethod
    def reveal_password_admin_only(cls, user_id, admin_user_id, admin_username, reason="Emergency password access"):
        """
        EXTREMELY DANGEROUS - ONLY FOR EMERGENCY USE IN DEVELOPMENT
        Temporarily reveals plain text password for a user - ADMIN ONLY with full audit logging
        
        Args:
            user_id: ID of user whose password to reveal
            admin_user_id: ID of admin performing this action
            admin_username: Username of admin performing this action
            reason: Reason for accessing password (logged)
            
        Returns:
            dict: {'success': bool, 'password': str or None, 'error': str or None}
        """
        try:
            # Get target user
            target_user = cls.find_by_id(user_id)
            if not target_user:
                security_logger.warning(f"FAILED PASSWORD REVEAL: User {user_id} not found - Admin: {admin_username} ({admin_user_id})")
                return {'success': False, 'password': None, 'error': 'User not found'}
            
            # Get admin user to verify they exist and are admin
            admin_user = cls.find_by_id(admin_user_id)
            if not admin_user or admin_user['role'] != 'admin':
                security_logger.critical(f"SECURITY BREACH ATTEMPT: Non-admin {admin_username} ({admin_user_id}) attempted password reveal for user {user_id}")
                return {'success': False, 'password': None, 'error': 'Unauthorized access'}
            
            # CRITICAL SECURITY: Check if encrypted password exists
            if 'encrypted_password' not in target_user or not target_user['encrypted_password']:
                security_logger.critical(
                    f"PASSWORD REVEAL IMPOSSIBLE: No encrypted password stored for user {user_id} "
                    f"(passwords were hashed, not encrypted). Admin: {admin_username} ({admin_user_id})"
                )
                return {
                    'success': False, 
                    'password': None, 
                    'error': 'Password was hashed (irreversible). Cannot reveal original password.',
                    'solution': 'Use password reset to generate a new temporary password.'
                }
            
            # Attempt to decrypt password
            try:
                decrypted_password = cipher.decrypt(target_user['encrypted_password'].encode()).decode()
            except Exception as decrypt_error:
                security_logger.critical(
                    f"PASSWORD DECRYPTION FAILED: {str(decrypt_error)} - User {user_id} - Admin: {admin_username} ({admin_user_id})"
                )
                return {
                    'success': False, 
                    'password': None, 
                    'error': f'Decryption failed: {str(decrypt_error)}'
                }
            
            # CRITICAL SECURITY LOGGING - This is a massive security violation
            security_logger.critical(
                f"🚨 PASSWORD REVEALED - CRITICAL SECURITY EVENT: "
                f"Admin: {admin_username} ({admin_user_id}) "
                f"revealed password for user: {target_user['username']} ({user_id}) "
                f"Reason: {reason} "
                f"Password Length: {len(decrypted_password)} characters "
                f"Timestamp: {datetime.datetime.now()}"
            )
            
            return {
                'success': True, 
                'password': decrypted_password, 
                'warning': 'This password has been revealed and logged. This violates security best practices.'
            }
            
        except Exception as e:
            security_logger.critical(f"PASSWORD REVEAL SYSTEM ERROR: {str(e)} - Admin: {admin_username} ({admin_user_id}) - Target: {user_id}")
            return {'success': False, 'password': None, 'error': f'System error: {str(e)}'}
    @classmethod
    def create(cls, name, username, email, password, role='user', department=None):
        cur = cls.get_cursor()
        hashed = generate_password_hash(password)
        
        # CRITICAL SECURITY RISK: Attempt to store encrypted password for emergency access
        # This should NEVER be done in production systems
        try:
            encrypted_password = cipher.encrypt(password.encode()).decode()
            cur.execute("""
                INSERT INTO users (name, username, email, password, encrypted_password, role, department, status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 1, NOW(), NOW())
            """, (name, username, email, hashed, encrypted_password, role, department))
        except Exception:
            # Fallback if encrypted_password column doesn't exist
            security_logger.warning("encrypted_password column not found - passwords will be hashed only (irreversible)")
            cur.execute("""
                INSERT INTO users (name, username, email, password, role, department, status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, 1, NOW(), NOW())
            """, (name, username, email, hashed, role, department))
        
        mysql.connection.commit()
        return cur.lastrowid
    
    @staticmethod
    def verify_password(stored_hash, plain_password):
        return check_password_hash(stored_hash, plain_password)

    @classmethod
    def reset_password(cls, user_id, new_password):
        """Reset user password - for admin use only"""
        cur = cls.get_cursor()
        hashed = generate_password_hash(new_password)
        cur.execute("""
            UPDATE users 
            SET password = %s, updated_at = NOW() 
            WHERE id = %s
        """, (hashed, user_id))
        mysql.connection.commit()
        return cur.rowcount > 0

    @staticmethod
    def generate_temp_password(length=12):
        """Generate a secure temporary password"""
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    @classmethod
    def get_total_count(cls):
        cur = cls.get_cursor()
        cur.execute("SELECT COUNT(*) as total FROM users")
        result = cur.fetchone()
        return result['total'] if result else 0

    @classmethod
    def all_with_details(cls):
        cur = cls.get_cursor()
        try:
            # Try to select with encrypted_password column
            cur.execute("""
                SELECT id, name, username, email, department, role, status, password, 
                       encrypted_password, created_at, updated_at
                FROM users 
                ORDER BY created_at DESC
            """)
        except Exception:
            # Fallback if encrypted_password column doesn't exist
            cur.execute("""
                SELECT id, name, username, email, department, role, status, password, 
                       NULL as encrypted_password, created_at, updated_at
                FROM users 
                ORDER BY created_at DESC
            """)
        return cur.fetchall()

