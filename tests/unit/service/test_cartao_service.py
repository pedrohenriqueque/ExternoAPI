import pytest
from unittest.mock import MagicMock, patch

# Import real do Stripe para usar suas classes de exceção
import stripe

# --- Importações do Código Real da Aplicação ---
# Garanta que o pytest seja executado da raiz do projeto.
from app.integrations.stripe import StripeGateway
from app.core.exceptions import CartaoApiError
from app.services.cartao_service import CartaoService, get_cartao_service
from app.schemas.cartao_schema import NovoCartaoDeCreditoSchema

# --- Testes para a Lógica de Negócio do CartaoService ---

class TestCartaoService:
    """Testa a lógica de negócio principal do CartaoService."""

    def test_validar_cartao_chama_gateway_com_numero_correto(self):
        mock_gateway = MagicMock(spec=StripeGateway)
        cartao_service = CartaoService(stripe_gateway=mock_gateway)
        dados_cartao = NovoCartaoDeCreditoSchema(
            numero="4242424242424242",
            cvv="123",
            nomeTitular="JOAO DA SILVA",
            validade="12/2030"
        )

        cartao_service.validar_cartao(dados_cartao)

        mock_gateway.validar_cartao.assert_called_once_with("4242424242424242")

    def test_validar_cartao_propaga_excecao_do_gateway(self):
        """Testa se o serviço propaga a exceção CartaoApiError quando o gateway a lança."""
        mock_gateway = MagicMock(spec=StripeGateway)
        erro_esperado = CartaoApiError(422, "CARTAO_RECUSADO", "O cartão foi recusado.")
        mock_gateway.validar_cartao.side_effect = erro_esperado
        cartao_service = CartaoService(stripe_gateway=mock_gateway)
        dados_cartao = NovoCartaoDeCreditoSchema(
            numero="4000000000000002",
            cvv="456",
            nomeTitular="MARIA PEREIRA",
            validade="11/2028"
        )

        with pytest.raises(CartaoApiError) as exc_info:
            cartao_service.validar_cartao(dados_cartao)

        assert exc_info.value is erro_esperado
        assert exc_info.value.codigo == "CARTAO_RECUSADO"


# --- Testes para a Factory do CartaoService ---

# O patch deve apontar para onde o objeto é USADO.
@patch('app.services.cartao_service.StripeGateway')
def test_get_cartao_service_cria_servico_com_gateway(MockStripeGateway):
    """
    Testa se a factory get_cartao_service constrói e retorna
    uma instância de CartaoService, que por sua vez contém uma instância de StripeGateway.
    """
    mock_instancia_gateway = MagicMock()
    MockStripeGateway.return_value = mock_instancia_gateway

    servico = get_cartao_service()

    MockStripeGateway.assert_called_once()
    assert isinstance(servico, CartaoService)
    assert servico.gateway is mock_instancia_gateway
