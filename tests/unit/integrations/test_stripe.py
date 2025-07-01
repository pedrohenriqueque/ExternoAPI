import pytest
from unittest.mock import patch, MagicMock
import stripe

# Supondo que os componentes estejam nestes caminhos
from app.integrations.stripe import StripeGateway
from app.core.exceptions import CartaoApiError

# Mock da classe de exceção base do Stripe para os testes
# Isso evita a necessidade de ter a biblioteca stripe instalada no ambiente de teste
# se você mockar todas as chamadas.
stripe.error = MagicMock()
stripe.error.CardError = type('CardError', (Exception,), {})
stripe.error.StripeError = type('StripeError', (Exception,), {})


class TestStripeGateway:
    """
    Testa a camada de integração com o gateway de pagamento Stripe.
    """

    @patch('stripe.PaymentIntent')
    def test_processar_pagamento_sucesso(self, mock_payment_intent_class: MagicMock):
        """
        Testa o fluxo de sucesso ao processar um pagamento.
        """
        # Arrange
        valor_em_centavos = 25000  # R$ 250,00
        payment_method_id = "pm_card_visa"
        mock_intent_criado = MagicMock(status="succeeded")
        mock_payment_intent_class.create.return_value = mock_intent_criado

        # Act
        resultado = StripeGateway.processar_pagamento(valor_em_centavos, payment_method_id)

        # Assert
        mock_payment_intent_class.create.assert_called_once_with(
            amount=valor_em_centavos,
            currency="brl",
            payment_method=payment_method_id,
            confirm=True,
            off_session=True,
            return_url="https://seu-dominio.com/cobranca-retorno"
        )
        assert resultado is mock_intent_criado

    @patch('stripe.PaymentIntent.create', side_effect=stripe.error.CardError)
    def test_processar_pagamento_falha_cartao_recusado(self, _mock_create: MagicMock):
        """
        Testa se CartaoApiError é levantado quando o cartão é recusado.
        """
        # Act & Assert
        with pytest.raises(CartaoApiError) as exc_info:
            StripeGateway.processar_pagamento(1000, "pm_card_visa_chargeDeclined")

        assert exc_info.value.status_code == 422
        assert exc_info.value.codigo == "CARTAO_RECUSADO"
        assert exc_info.value.mensagem == "O Cartão foi recusado"

    @patch('stripe.PaymentIntent.create', side_effect=stripe.error.StripeError)
    def test_processar_pagamento_falha_generica_stripe(self, _mock_create: MagicMock):
        """
        Testa se CartaoApiError é levantado para outros erros da API do Stripe.
        """
        # Act & Assert
        with pytest.raises(CartaoApiError) as exc_info:
            StripeGateway.processar_pagamento(1000, "pm_card_visa")

        assert exc_info.value.status_code == 422
        assert exc_info.value.codigo == "ERRO_GATEWAY"
        assert exc_info.value.mensagem == "Ocorreu uma falha de comunicação com o provedor de pagamento."

    def test_validar_cartao_nao_mapeado(self):
        """
        Testa a validação de um número de cartão de teste que não está no mapa.
        """
        # Arrange
        numero_cartao_invalido = "1234567890123456"

        # Act & Assert
        with pytest.raises(CartaoApiError) as exc_info:
            StripeGateway.validar_cartao(numero_cartao_invalido)

        assert exc_info.value.status_code == 422
        assert exc_info.value.codigo == "CARTAO_NAO_MAPEADO"
        assert exc_info.value.mensagem == "Esse cartão não foi mapeado"

    @patch('stripe.SetupIntent')
    def test_validar_cartao_sucesso(self, mock_setup_intent_class: MagicMock):
        """
        Testa o fluxo de sucesso da validação de um cartão.
        """
        # Arrange
        numero_cartao_valido = "4242424242424242"  # pm_card_visa
        # Não precisa retornar nada, apenas não levantar exceção
        mock_setup_intent_class.create.return_value = None

        # Act
        try:
            StripeGateway.validar_cartao(numero_cartao_valido)
        except CartaoApiError:
            pytest.fail("A validação de cartão levantou um CartaoApiError inesperadamente.")

        # Assert
        mock_setup_intent_class.create.assert_called_once_with(
            payment_method="pm_card_visa",
            confirm=True,
            usage="off_session",
            return_url="https://seu-dominio.com/validacao-retorno"
        )

    @patch('stripe.SetupIntent.create', side_effect=stripe.error.CardError)
    def test_validar_cartao_recusado_pela_stripe(self, _mock_create: MagicMock):
        """
        Testa a falha quando a validação do SetupIntent na Stripe recusa o cartão.
        """
        # Arrange
        numero_cartao_recusado = "4000000000000002"  # pm_card_visa_chargeDeclined

        # Act & Assert
        with pytest.raises(CartaoApiError) as exc_info:
            StripeGateway.validar_cartao(numero_cartao_recusado)

        assert exc_info.value.status_code == 422
        assert exc_info.value.codigo == "CARTAO_RECUSADO"
        assert exc_info.value.mensagem == "O cartão foi recusado."
