from app.integrations.email import EmailClient

class EmailService:
    def __init__(self):
        self.client = EmailClient()

    def enviar(self, destinatario: str, assunto: str, mensagem: str):
        self.client.enviar_email(destinatario, assunto, mensagem)