import logging
import os
from datetime import datetime
from flask import render_template
from app import create_app
from app.services.report_service import prepare_user_reports
from app.services.email_service import send_email
from app.utils.helpers import get_user_email

# --- UPDATED LOG PATH ---
LOG_FILE = "/home/administrator/task/log/task_report.log"

# Ensure the directory exists programmatically
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app = create_app()

def run_daily_report():
    with app.app_context():
        logging.info("--- Cron Job Started ---")
        print(f"[{datetime.now()}] Job started...")
        
        try:
            users = prepare_user_reports()
            
            if not users:
                logging.warning("No tasks found to report today.")
                return

            for user in users:
                username = user.get('assigned_to')
                email = get_user_email(username)

                if not email:
                    logging.warning(f"Skipping {username}: No email found.")
                    continue

                html = render_template("emails/task_report.html", data=user)
                send_email(email, "Daily Task Report", html)
                
                logging.info(f"Successfully sent report to {username} ({email})")
                print(f"Sent to {username}")

            logging.info("--- Cron Job Finished Successfully ---")

        except Exception as e:
            logging.error(f"FATAL ERROR: {str(e)}")
            print(f"Error: {e}")

if __name__ == "__main__":
    run_daily_report()