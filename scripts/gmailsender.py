import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
from src.db.database import Database
from src.config.ig_mails import IG_EMAILS
 
load_dotenv()

def send_email(subject, body, receiver):
    sender   = os.getenv("GMAIL_SENDER")
    password = os.getenv("GMAIL_APP_PASSWORD")

    message = MIMEMultipart()
    message["From"]    = sender
    message["To"]      = receiver
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, receiver, message.as_string())
        print(f"  [Email] Sent to {receiver} for {subject}")

def run_email_agent():
    db = Database()
    print(f"\n[Email Agent] Starting...")

    for ig, email in IG_EMAILS.items():
        events = list(db.events.find({"keyword_used": ig, "status": "scraped"}))

        if not events:
            print(f"  [{ig}] No events, skipping.")
            continue

        body = "\n\n".join([e.get("summary", "") for e in events])

        send_email(
            subject=f"{ig.title()} Events Digest",
            body=body,
            receiver=email
        )

        db.events.update_many(
            {"keyword_used": ig, "status": "scraped"},
            {"$set": {"status": "mail sent"}}
        )

    db.close()
    print("[Email Agent] Done.")

if __name__ == "__main__":
    run_email_agent() 