import pytest
import unittest
from unittest.mock import patch, MagicMock

from app.integrations.email import EmailClient
from app.core.exceptions import CartaoApiError

@patch.dict('os.environ', {
    'SENDGRID_API_KEY': 'TEST_API_KEY',
    'EMAIL_REMETENTE': 'remetente@teste.com'
})
@patch('sendgrid.SendGridAPIClient')
class TestEmailClient(unittest.TestCase):

    def test_enviar_email_sucesso(self, mock_sendgrid_client):

        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_sendgrid_client.return_value.send.return_value = mock_response

        client = EmailClient()

        # Act
        try:
            client.enviar_email("dest@example.com", "Assunto", "Mensagem")
        except CartaoApiError:
            self.fail("A função 'enviar_email' levantou CartaoApiError inesperadamente.")

        # Assert
        # Verifica se o cliente do SendGrid foi chamado
        mock_sendgrid_client.return_value.send.assert_called_once()

        # Acessa o primeiro argumento da chamada a 'send' (o objeto Mail)
        sent_mail = mock_sendgrid_client.return_value.send.call_args[0][0]
        mail_json = sent_mail.get()

        self.assertEqual(mail_json['from']['email'], 'remetente@teste.com')
        self.assertEqual(mail_json['personalizations'][0]['to'][0]['email'], 'dest@example.com')
        self.assertEqual(mail_json['subject'], 'Assunto')
        self.assertEqual(mail_json['content'][0]['value'], 'Mensagem')

    def test_enviar_email_falha_na_api(self, mock_sendgrid_client):
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 422 # Código de erro
        mock_sendgrid_client.return_value.send.return_value = mock_response

        client = EmailClient()

        # Act & Assert
        with self.assertRaises(CartaoApiError) as context:
            client.enviar_email("dest@example.com", "Assunto", "Mensagem")

        self.assertEqual(context.exception.status_code, 422)
        self.assertEqual(context.exception.codigo, "FALHA_ENVIO_EMAIL")
        self.assertEqual(context.exception.mensagem, "Houve um erro no envio do email")
