import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv()
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def send_report_email(report_path, recipient_email):
    sender_email = os.environ.get("EMAIL_SENDER")
    sender_password = os.environ.get("EMAIL_APP_PASSWORD")
    print(f"Sending report email to {recipient_email} from {sender_email} with report {report_path}")

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = "Network Health Suite - Report"

    body = "Automated health check run completed. Report attached."
    msg.attach(MIMEText(body, "plain"))

    with open(report_path, "rb") as f:
        attachment = MIMEApplication(f.read(), _subtype="json")
        attachment.add_header("Content-Disposition", "attachment", filename=os.path.basename(report_path))
        msg.attach(attachment)
    
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.set_debuglevel(1)
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print(f"Report email sent to {recipient_email}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"Authentication failed: {e}")
        return False
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False