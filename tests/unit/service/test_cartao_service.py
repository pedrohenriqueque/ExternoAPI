import pytest
from unittest.mock import MagicMock, patch

# --- Importações do Código Real da Aplicação ---
# Para que isto funcione, execute o pytest a partir da raiz do seu projeto,
# garantindo que a pasta `app` esteja no python path.
from app.services.cartao_service import CartaoService, get_cartao_service
from app.integrations.stripe import StripeGateway
from app.schemas.cartao_schema import NovoCartaoDeCreditoSchema
from app.core.exceptions import CartaoApiError


# --- Início dos Testes Unitários ---

def test_validar_cartao_chama_gateway_com_numero_correto():

    # Arrange
    # Criamos um mock do gateway. O `spec` garante que o mock
    # tem a mesma "forma" da classe real, ajudando a evitar erros.
    mock_gateway = MagicMock(spec=StripeGateway)

    # Instanciamos o SERVIÇO REAL com o nosso gateway FALSO.
    cartao_service = CartaoService(stripe_gateway=mock_gateway)

    # CORREÇÃO: Usamos os nomes de campo exatos que o schema espera (camelCase).
    dados_cartao = NovoCartaoDeCreditoSchema(
        numero="4242424242424242",
        cvv="123",
        nomeTitular="JOAO DA SILVA", # Corrigido para camelCase
        validade="12/2030"           # Corrigido para campo único
    )

    cartao_service.validar_cartao(dados_cartao)



    # e com o argumento correto (o número do cartão).
    mock_gateway.validar_cartao.assert_called_once_with("4242424242424242")


def test_validar_cartao_propaga_excecao_do_gateway():
    """
    Testa se o serviço propaga corretamente a exceção
    CartaoApiError quando o gateway a lança.
    """
    # Arrange
    mock_gateway = MagicMock(spec=StripeGateway)
    # Configuramos o mock para, em vez de executar, lançar uma exceção.
    erro_esperado = CartaoApiError(422, "CARTAO_RECUSADO", "O cartão foi recusado.")
    mock_gateway.validar_cartao.side_effect = erro_esperado

    cartao_service = CartaoService(stripe_gateway=mock_gateway)

    # CORREÇÃO: Usamos os nomes de campo exatos que o schema espera (camelCase).
    dados_cartao = NovoCartaoDeCreditoSchema(
        numero="4000000000000002",
        cvv="456",
        nomeTitular="MARIA PEREIRA", # Corrigido para camelCase
        validade="11/2028"           # Corrigido para campo único
    )

    # Act & Assert
    # Usamos pytest.raises para verificar se o código lança a exceção esperada.
    with pytest.raises(CartaoApiError) as exc_info:
        cartao_service.validar_cartao(dados_cartao)

    # Verificamos se a exceção capturada é exatamente a que o mock deveria lançar.
    assert exc_info.value is erro_esperado
    assert exc_info.value.codigo == "CARTAO_RECUSADO"


# O patch deve apontar para onde o objeto é USADO.
# A função `get_cartao_service` está no módulo `app.services.cartao_service`
# e é lá que ela usa `StripeGateway`.
@patch('app.services.cartao_service.StripeGateway')
def test_get_cartao_service_cria_servico_com_gateway(MockStripeGateway):
    """
    Testa se a factory get_cartao_service constrói e retorna
    uma instância de CartaoService, que por sua vez contém uma instância de StripeGateway.
    """
    # Arrange
    mock_instancia_gateway = MagicMock()
    MockStripeGateway.return_value = mock_instancia_gateway

    # Act
    # Chamamos a função REAL, importada do nosso código da aplicação.
    servico = get_cartao_service()

    # Assert
    # 1. Verifica se o construtor `StripeGateway()` foi chamado uma vez.
    MockStripeGateway.assert_called_once()

    # 2. Verifica se o objeto retornado é do tipo CartaoService.
    assert isinstance(servico, CartaoService)

    # 3. Verifica se o serviço contém a instância do gateway que o mock criou.
    assert servico.gateway is mock_instancia_gateway
