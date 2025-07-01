import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.services.email_service import EmailService
from app.models.cobranca import Cobranca # Supondo que a classe Cobranca esteja neste local

class TestEmailService(unittest.TestCase):

    @patch('app.services.email_service.EmailClient')
    def test_enviar_chama_cliente_com_argumentos_corretos(self, mock_email_client):

        # Arrange
        service = EmailService()
        # Injetando o mock no cliente da instância do serviço
        service.client = mock_email_client.return_value

        destinatario = "teste@example.com"
        assunto = "Assunto Teste"
        mensagem = "Mensagem Teste"

        # Act
        service.enviar(destinatario, assunto, mensagem)

        # Assert
        service.client.enviar_email.assert_called_once_with(destinatario, assunto, mensagem)

    @patch('app.services.email_service.EmailClient')
    def test_enviar_confirmacao_pagamento_formata_e_envia_email(self, mock_email_client):

        # Arrange
        service = EmailService()
        service.client = mock_email_client.return_value

        # Criando um mock para o objeto Cobranca
        mock_cobranca = MagicMock(spec=Cobranca)
        mock_cobranca.id = 123
        mock_cobranca.valor = 150.75
        mock_cobranca.status = "PAGO"
        mock_cobranca.horaFinalizacao = datetime(2023, 10, 27, 14, 30)

        destinatario = "cliente@example.com"

        assunto_esperado = "Confirmação de Pagamento Recebido - Cobrança #123"
        mensagem_esperada = (
            "Olá!\n\n"
            "Confirmamos o recebimento do seu pagamento no valor de R$ 150.75.\n\n"
            "Detalhes da Cobrança:\n"
            "ID: 123\n"
            "Status: PAGO\n"
            "Data de Finalização: 27/10/2023 14:30\n\n"
            "Obrigado!"
        )

        # Act
        service.enviar_confirmacao_pagamento(mock_cobranca, destinatario)

        # Assert
        service.client.enviar_email.assert_called_once_with(
            destinatario, assunto_esperado, mensagem_esperada
        )

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)