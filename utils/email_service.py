import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

class EmailService:
    @staticmethod
    def send_email(to_email, subject, body, is_html=True):
        """
        Sends an email. Uses Mock (Console Print) if SMTP env vars are not set.
        """
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = os.getenv('SMTP_PORT', 587)
        smtp_user = os.getenv('SMTP_USER')
        smtp_password = os.getenv('SMTP_PASSWORD')
        
        # Mock Mode
        if not smtp_server or not smtp_user:
            print(f"\n[MOCK EMAIL SERVICE] ----------------------------------------")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(f"Time: {datetime.now()}")
            print(f"Body (Preview): {body[:200]}..." if len(body) > 200 else f"Body: {body}")
            print(f"-----------------------------------------------------------\n")
            return True

        # Real SMTP Mode
        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html' if is_html else 'plain'))

            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            text = msg.as_string()
            server.sendmail(smtp_user, to_email, text)
            server.quit()
            print(f"Email sent successfully to {to_email}")
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    @staticmethod
    def send_status_update(candidate_name, candidate_email, new_status, job_title, candidate_id=None, base_url=None):
        subject = f"Application Update: {job_title}"
        
        if new_status == 'Offer' and candidate_id and base_url:
            # Offer Letter Template
            accept_link = f"{base_url}offer/respond/{candidate_id}/accept"
            reject_link = f"{base_url}offer/respond/{candidate_id}/reject"
            
            body = f"""
            <h3>Congratulations {candidate_name}!</h3>
            <p>We are pleased to offer you the position of <strong>{job_title}</strong> at NexGen ATS.</p>
            <p>We were impressed with your skills and experience.</p>
            <br>
            <p><strong>Please let us know your decision:</strong></p>
            <p>
                <a href="{accept_link}" style="background-color: #10b981; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px;">Accept Offer</a>
                <a href="{reject_link}" style="background-color: #ef4444; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Decline Offer</a>
            </p>
            <br>
            <p>Best Regards,<br>NexGen Hiring Team</p>
            """
        else:
            # Standard Update
            body = f"""
            <h3>Hello {candidate_name},</h3>
            <p>Your application for the position of <strong>{job_title}</strong> has been updated.</p>
            <p><strong>New Status: {new_status}</strong></p>
            <p>Log in to your dashboard to view more details.</p>
            <br>
            <p>Best Regards,<br>NexGen ATS Team</p>
            """
            
        return EmailService.send_email(candidate_email, subject, body)

    @staticmethod
    def send_interview_invite(candidate_name, candidate_email, date_time, location, notes):
        subject = f"Interview Invitation - NexGen ATS"
        body = f"""
        <h3>Hello {candidate_name},</h3>
        <p>You have been invited for an interview.</p>
        <ul>
            <li><strong>Date & Time:</strong> {date_time}</li>
            <li><strong>Location/Link:</strong> {location}</li>
        </ul>
        <p><strong>Notes:</strong> {notes}</p>
        <br>
        <p>Please confirm your availability.</p>
        <p>Best Regards,<br>NexGen Recruitment Team</p>
        """
        return EmailService.send_email(candidate_email, subject, body)
