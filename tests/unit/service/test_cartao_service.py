import pytest
from unittest.mock import MagicMock, patch, ANY

# Import real do Stripe para usar suas classes de exceção
import stripe

# --- Importações do Código Real da Aplicação ---
# Garanta que o pytest seja executado da raiz do projeto.
from app.services.cobranca_service import CobrancaService
from app.repositories.cobranca_repository import CobrancaRepository
from app.integrations.stripe import StripeGateway
from app.services.email_service import EmailService
from app.models.cobranca import Cobranca
from app.schemas.nova_cobranca_schema import NovaCobrancaSchema
from app.core.exceptions import CartaoApiError
from app.services.cartao_service import CartaoService, get_cartao_service
from app.schemas.cartao_schema import NovoCartaoDeCreditoSchema


# --- Testes para Métodos Estáticos do CobrancaService ---

class TestCobrancaServiceStaticMethods:
    """Testa os métodos estáticos do CobrancaService isoladamente."""

    def test_obter_payment_method_id_do_ciclista_sucesso(self):
        result = CobrancaService._obter_payment_method_id_do_ciclista(0)
        assert result == "pm_card_visa"

    def test_obter_payment_method_id_do_ciclista_falha(self):
        """Verifica se uma exceção é levantada para um ciclista sem cartão."""
        with pytest.raises(CartaoApiError) as exc_info:
            CobrancaService._obter_payment_method_id_do_ciclista(99)  # ID não mapeado
        assert exc_info.value.codigo == "CICLISTA_SEM_CARTAO"

    def test_obter_email_do_ciclista_sucesso(self):
        """Verifica se o e-mail do ciclista é retornado corretamente."""
        result = CobrancaService._obter_email_do_ciclista(0)
        assert result == "pedrohenriqueque@gmail.com"

    def test_obter_email_do_ciclista_nao_encontrado(self):
        """Verifica se None é retornado para um ciclista não mapeado."""
        result = CobrancaService._obter_email_do_ciclista(99)  # ID não mapeado
        assert result is None


# --- Testes para a Lógica de Negócio do CobrancaService ---

class TestCobrancaService:
    """Testa a lógica de negócio principal do CobrancaService."""

    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        """Fixture para o repositório de cobranças."""
        mock = MagicMock(spec=CobrancaRepository)
        # Simula o salvamento retornando o próprio objeto.
        mock.salvar.side_effect = lambda cobranca: cobranca
        return mock

    @pytest.fixture
    def mock_gateway(self) -> MagicMock:
        """Fixture para o gateway de pagamento."""
        return MagicMock(spec=StripeGateway)

    @pytest.fixture
    def mock_email_service(self) -> MagicMock:
        """Fixture para o serviço de e-mail."""
        return MagicMock(spec=EmailService)

    @pytest.fixture
    def cobranca_service(self, mock_repo, mock_gateway, mock_email_service) -> CobrancaService:
        """Fixture que monta o serviço de cobrança com todas as suas dependências mockadas."""
        return CobrancaService(
            cobranca_repo=mock_repo,
            payment_gateway=mock_gateway,
            email_service=mock_email_service # Correção: usar o mock injetado
        )

    # --- Testes para métodos CRUD básicos ---

    def test_criar_cobranca_na_fila(self, cobranca_service, mock_repo):
        """Testa se uma nova cobrança é criada com status PENDENTE."""
        dados = NovaCobrancaSchema(valor=50.0, ciclista=1)
        cobranca_service.criar_cobranca_na_fila(dados)
        mock_repo.criar.assert_called_once_with(dados, ANY)
        mock_repo.salvar.assert_called_once()

    def test_obter_por_id_sucesso(self, cobranca_service, mock_repo):
        """Testa a busca de uma cobrança existente pelo ID."""
        mock_repo.obter_por_id.return_value = Cobranca(id=1)
        resultado = cobranca_service.obter_por_id(1)
        mock_repo.obter_por_id.assert_called_once_with(1)
        assert resultado.id == 1

    def test_obter_por_id_nao_encontrada(self, cobranca_service, mock_repo):
        """Testa a busca de uma cobrança inexistente, esperando uma exceção."""
        mock_repo.obter_por_id.return_value = None
        with pytest.raises(CartaoApiError) as exc_info:
            cobranca_service.obter_por_id(999)
        assert exc_info.value.codigo == "COBRANCA_NAO_ENCONTRADA"

    # --- Testes para processar_pagamento_de_cobranca ---

    @patch.object(CobrancaService, '_obter_payment_method_id_do_ciclista', return_value="pm_card_visa")
    def test_processar_pagamento_sucesso(self, mock_get_card, cobranca_service, mock_repo, mock_gateway):
        """Testa o fluxo de sucesso do processamento de um pagamento."""
        cobranca = Cobranca(id=1, ciclista=1, valor=100.0, status="PENDENTE")
        mock_repo.obter_por_id.return_value = cobranca
        mock_gateway.processar_pagamento.return_value = MagicMock(status="succeeded")

        resultado = cobranca_service.processar_pagamento_de_cobranca(1)

        mock_get_card.assert_called_once_with(1)
        mock_gateway.processar_pagamento.assert_called_once()
        mock_repo.salvar.assert_called_once()
        assert resultado.status == "PAGA"

    @patch.object(CobrancaService, '_obter_payment_method_id_do_ciclista')
    def test_processar_pagamento_falha_gateway(self, mock_get_card, cobranca_service, mock_repo, mock_gateway):
        """Testa o fluxo de falha no gateway, atualizando o status da cobrança."""
        cobranca = Cobranca(id=1, ciclista=1, valor=100.0, status="PENDENTE")
        mock_repo.obter_por_id.return_value = cobranca
        mock_gateway.processar_pagamento.side_effect = CartaoApiError(422, "ERRO_GATEWAY", "...")

        resultado = cobranca_service.processar_pagamento_de_cobranca(1)

        assert resultado.status == "FALHA"
        assert resultado.horaFinalizacao is not None
        mock_repo.salvar.assert_called_once()

    # --- Testes para a Fila de Cobranças ---

    @patch.object(CobrancaService, '_obter_payment_method_id_do_ciclista', return_value="pm_card_visa")
    def test_tentar_cobranca_da_fila_falha_intent_status(self, mock_get_card, cobranca_service, mock_repo, mock_gateway):
        """Testa o caso onde o gateway processa mas o status final não é 'succeeded'."""
        cobranca = Cobranca(id=1, ciclista=1, valor=100.0, status="PENDENTE")
        mock_gateway.processar_pagamento.return_value = MagicMock(status="failed")

        resultado = cobranca_service.tentar_cobranca_da_fila(cobranca)

        assert resultado is None
        mock_repo.salvar.assert_not_called()

    @patch.object(CobrancaService, 'tentar_cobranca_da_fila', side_effect=[None, None])
    def test_processar_cobrancas_em_fila_sem_sucesso(self, mock_tentar_cobranca, cobranca_service, mock_repo, mock_email_service):
        """Testa o processamento da fila onde nenhuma cobrança é bem-sucedida."""
        mock_repo.listar_pendentes.return_value = [Cobranca(id=1), Cobranca(id=2)]

        resultados = cobranca_service.processar_cobrancas_em_fila()

        assert resultados == []
        assert mock_tentar_cobranca.call_count == 2
        mock_email_service.enviar_confirmacao_pagamento.assert_not_called()


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
