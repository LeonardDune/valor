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

    async def send_invitation_email(self, email: str, inviter_name: str, entity_name: str, redirect_url: str):
        """
        Sends an invitation email to an existing user via Resend.
        """
        if not self.api_key or not resend:
            logger.info(f"Mocking invite email to {email} for {entity_name} from {inviter_name}")
            return

        subject = f"Je bent uitgenodigd voor: {entity_name}"
        
        html_content = f"""
        <h1>Je hebt een uitnodiging ontvangen!</h1>
        <p><strong>{inviter_name}</strong> heeft je uitgenodigd om deel te nemen aan <strong>{entity_name}</strong> op Valor.</p>
        <p>Klik op de onderstaande knop om de uitnodiging te bekijken en te accepteren:</p>
        <br>
        <a href="{redirect_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">Uitnodiging Bekijken</a>
        <br><br>
        <p><em>Dit is een geautomatiseerd bericht vanuit Valor.</em></p>
        """

        try:
            r = resend.Emails.send({
                "from": self.from_email,
                "to": email,
                "subject": subject,
                "html": html_content
            })
            logger.info(f"Sent invitation email to {email} successfully.")
        except Exception as e:
            logger.error(f"Failed to send invitation email to {email}: {e}")
