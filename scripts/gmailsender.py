import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv

load_dotenv()

def send_email(subject, body, receiver):
    sender   = os.getenv("GMAIL_SENDER")
    password = os.getenv("GMAIL_APP_PASSWORD")

    message = MIMEMultipart()
    message["From"]    = sender
    message["To"]      = receiver
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    receivers_list = [email.strip() for email in receiver.split(",")]

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, receivers_list, message.as_string())
        print(f"  [Email] Sent to {receivers_list} for {subject}")

def run_email_agent():
    print(f"\n[Email Agent] Starting...")
    
    # We fetch the exact Supabase string you placed in .env
    db_url = os.getenv("DATABASE_URL") 
    
    if not db_url:
        print("[!] DATABASE_URL not found in .env. Checking local defaults...")
        db_url = "dbname=mu_hive user=postgres password=postgres host=localhost"

    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        # 1. Fetch the IG to Email mappings right out of Postgres
        cursor.execute("SELECT ig, email FROM ig_mails")
        ig_email_records = cursor.fetchall()

        if not ig_email_records:
            print("[Email Agent] No email mappings found in the 'ig_mails' table.")

        for record in ig_email_records:
            ig = record['ig']
            email = record['email']

            # 2. Fetch scraped events for this specific IG
            # Postgres: The JSON wrapper extracts 'summary' from the data column
            cursor.execute(
                "SELECT id, data->>'summary' as summary FROM scraped_data WHERE ig = %s AND status = 'scraped'",
                (ig,)
            )
            events = cursor.fetchall()

            if not events:
                print(f"  [{ig}] No events, skipping.")
                continue

            # Join summaries together
            body = "\n\n".join([str(e['summary']) for e in events if e['summary']])

            # Send Email
            send_email(
                subject=f"{ig.title()} Events Digest",
                body=body,
                receiver=email
            )

            # 3. Mark them as sent so we don't spam!
            event_ids = tuple([e['id'] for e in events])
            if event_ids:
                cursor.execute(
                    "UPDATE scraped_data SET status = 'mail sent' WHERE id IN %s",
                    (event_ids,)
                )

    except Exception as e:
        print(f"[Email Agent] PostgreSQL Error: {e}")
    finally:
        if 'cursor' in locals(): 
            cursor.close()
        if 'conn' in locals(): 
            conn.close()

    print("[Email Agent] Done.")

if __name__ == "__main__":
    run_email_agent()