import os
import sendgrid
from sendgrid.helpers.mail import Mail

from app.core.exceptions import CartaoApiError


class EmailClient:
    def __init__(self):
        self.api_key = os.getenv("SENDGRID_API_KEY")
        self.remetente = os.getenv("EMAIL_REMETENTE")
        self.sg = sendgrid.SendGridAPIClient(api_key=self.api_key)

    def enviar_email(self, destinatario: str, assunto: str, mensagem: str):
        email = Mail(
            from_email=self.remetente,
            to_emails=destinatario,
            subject=assunto,
            plain_text_content=mensagem
        )
        response = self.sg.send(email)

        if not (200 <= response.status_code < 300):
            raise CartaoApiError(422,"","")
