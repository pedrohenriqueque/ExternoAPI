from app.integrations.email import EmailClient
from app.models.cobranca import Cobranca


class EmailService:
    def __init__(self):
        self.client = EmailClient()

    def enviar(self, destinatario: str, assunto: str, mensagem: str):
        self.client.enviar_email(destinatario, assunto, mensagem)

    def enviar_confirmacao_pagamento(self, cobranca: Cobranca, destinatario: str):
        assunto = f"Confirmação de Pagamento Recebido - Cobrança #{cobranca.id}"
        mensagem = (
            f"Olá!\n\n"
            f"Confirmamos o recebimento do seu pagamento no valor de R$ {cobranca.valor:.2f}.\n\n"
            f"Detalhes da Cobrança:\n"
            f"ID: {cobranca.id}\n"
            f"Status: {cobranca.status}\n"
            f"Data de Finalização: {cobranca.horaFinalizacao.strftime('%d/%m/%Y %H:%M')}\n\n"
            "Obrigado!"
        )
        self.enviar(destinatario, assunto, mensagem)