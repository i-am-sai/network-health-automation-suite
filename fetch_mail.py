import boto3
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import smtplib
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
BUCKET_NAME = "network-health-automation-reports"
RECIPIENT = os.environ.get("RECIPIENT_EMAIL")


def get_latest_report_key(bucket_name=BUCKET_NAME, prefix="reports/"):
    s3 = boto3.client("s3")
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

    objects = response.get("Contents", [])
    if not objects:
        print("No reports found in S3.")
        return None

    latest = max(objects, key=lambda obj: obj["LastModified"])
    print(f"Latest report in S3: {latest['Key']} (modified {latest['LastModified']})")
    return latest["Key"]


def build_attachment(file_bytes, filename):
    attachment = MIMEApplication(file_bytes, _subtype="json")
    attachment.add_header("Content-Disposition", "attachment", filename=filename)
    return attachment


def send_email_from_bytes(file_bytes, filename, recipient_email):
    sender_email = os.environ.get("EMAIL_SENDER")
    sender_password = os.environ.get("EMAIL_APP_PASSWORD")

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = "Network Health Suite - Daily S3 Report"
    msg.attach(MIMEText("Latest health check report from S3 attached.", "plain"))
    msg.attach(build_attachment(file_bytes, filename))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print(f"Report email sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def fetch_and_email_latest_report():
    s3_key = get_latest_report_key()
    if not s3_key:
        return False

    s3 = boto3.client("s3")
    response = s3.get_object(Bucket=BUCKET_NAME, Key=s3_key)
    file_bytes = response["Body"].read()
    filename = os.path.basename(s3_key)

    print(f"Fetched {filename} from S3 into memory ({len(file_bytes)} bytes)")

    return send_email_from_bytes(file_bytes, filename, RECIPIENT)


if __name__ == "__main__":
    fetch_and_email_latest_report()