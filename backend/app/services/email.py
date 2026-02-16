import os
import logging
from typing import List, Dict, Any
from app.models.domain import VotingSession
try:
    import resend
except ImportError:
    resend = None

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.api_key = os.environ.get("RESEND_API_KEY")
        self.from_email = os.environ.get("FROM_EMAIL", "onboarding@resend.dev") # Default Resend testing email
        
        if self.api_key and resend:
            resend.api_key = self.api_key
        else:
            logger.warning("RESEND_API_KEY not found or resend package not installed. Email service disabled.")

    async def notify_session_start(self, session_id: str, theme_name: str, participants: List[Dict[str, Any]]):
        """
        Sends an email to all participants that a new session has started.
        """
        if not self.api_key or not resend:
            logger.info(f"Mocking email send for session {session_id}. Would send to {len(participants)} people.")
            return

        subject = f"Stemsessie gestart: {theme_name}"
        
        # Deduplicate emails and filter invalid ones
        unique_emails = {p["email"] for p in participants if p.get("email")}
        
        if not unique_emails:
            logger.warning("No valid email addresses found for notification.")
            return

        # Simple HTML Template (can be expanded later)
        html_content = f"""
        <h1>De stemsessie is gestart!</h1>
        <p>Er is een nieuwe stemsessie gestart voor het thema: <strong>{theme_name}</strong>.</p>
        <p>Je kunt nu inloggen en deelnemen.</p>
        <br>
        <p><em>Dit is een geautomatiseerd bericht vanuit Valor.</em></p>
        """

        # Resend allows bulk sending or individual. For now, we loop or use bcc to respect privacy.
        # Ideally, send individual strings for personalization, but bcc is safer for MVP to avoid leaking emails if not careful.
        # Let's send individually to ensure deliverability and avoid "undisclosed-recipients" spam flags.
        
        count = 0
        for email in unique_emails:
            try:
                r = resend.Emails.send({
                    "from": self.from_email,
                    "to": email,
                    "subject": subject,
                    "html": html_content
                })
                count += 1
            except Exception as e:
                logger.error(f"Failed to send email to {email}: {e}")

        logger.info(f"Sent {count} session start emails.")
