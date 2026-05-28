import smtplib
from email.mime.text import MIMEText

def send_email(to_email, subject, html_content):
    sender_email = "eajmd@bwrl.in"
    password = "Bwrl@2026"
    msg = MIMEText(html_content, "html")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, password)
    server.send_message(msg)
    server.quit()