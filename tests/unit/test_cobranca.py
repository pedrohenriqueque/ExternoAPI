import pytest
from unittest.mock import MagicMock, patch, ANY


from app.services import email_service
# Importações do código real da aplicação
from app.services.cobranca_service import CobrancaService
from app.repositories.cobranca_repository import CobrancaRepository
from app.integrations.stripe import StripeGateway
from app.services.email_service import EmailService
from app.models.cobranca import Cobranca
from app.schemas.nova_cobranca_schema import NovaCobrancaSchema
from app.core.exceptions import CartaoApiError

# Import real do Stripe para usar suas classes de exceção
import stripe


class TestCobrancaServiceStaticMethods:
    """Testa os métodos estáticos isoladamente."""

    def test_obter_payment_method_id_do_ciclista_sucesso(self):
        result = CobrancaService._obter_payment_method_id_do_ciclista(0)
        assert result == "pm_card_visa"

    def test_obter_payment_method_id_do_ciclista_falha(self):
        with pytest.raises(CartaoApiError) as exc_info:
            CobrancaService._obter_payment_method_id_do_ciclista(99) # ID não mapeado
        assert exc_info.value.codigo == "CICLISTA_SEM_CARTAO"

    def test_obter_email_do_ciclista_sucesso(self):
        result = CobrancaService._obter_email_do_ciclista(0)
        assert result == "pedrohenriqueque@gmail.com"

    def test_obter_email_do_ciclista_nao_encontrado(self):
        result = CobrancaService._obter_email_do_ciclista(99) # ID não mapeado
        assert result is None


class TestCobrancaService:
    """Testa a lógica de negócio principal do CobrancaService."""

    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        mock = MagicMock(spec=CobrancaRepository)
        mock.salvar.side_effect = lambda cobranca: cobranca
        return mock

    @pytest.fixture
    def mock_gateway(self) -> MagicMock:
        return MagicMock(spec=StripeGateway)

    @pytest.fixture
    def mock_email_service(self) -> MagicMock:
        return MagicMock(spec=EmailService)

    @pytest.fixture
    def cobranca_service(self, mock_repo, mock_gateway, mock_email_service) -> CobrancaService:
        return CobrancaService(
            cobranca_repo=mock_repo,
            payment_gateway=mock_gateway,
            email_service=email_service
        )

    # --- Testes para métodos CRUD básicos ---

    def test_criar_cobranca_na_fila(self, cobranca_service, mock_repo):
        # Arrange
        dados = NovaCobrancaSchema(valor=50.0, ciclista=1)

        # Act
        cobranca_service.criar_cobranca_na_fila(dados)

        # Assert
        mock_repo.criar.assert_called_once_with(dados, ANY)
        mock_repo.salvar.assert_called_once()

    def test_obter_por_id_sucesso(self, cobranca_service, mock_repo):
        # Arrange
        mock_repo.obter_por_id.return_value = Cobranca(id=1)

        # Act
        resultado = cobranca_service.obter_por_id(1)

        # Assert
        mock_repo.obter_por_id.assert_called_once_with(1)
        assert resultado.id == 1

    def test_obter_por_id_nao_encontrada(self, cobranca_service, mock_repo):
        # Arrange
        mock_repo.obter_por_id.return_value = None

        # Act & Assert
        with pytest.raises(CartaoApiError) as exc_info:
            cobranca_service.obter_por_id(999)
        assert exc_info.value.codigo == "COBRANCA_NAO_ENCONTRADA"

    # --- Testes para processar_pagamento_de_cobranca ---

    @patch.object(CobrancaService, '_obter_payment_method_id_do_ciclista', return_value="pm_card_visa")
    def test_processar_pagamento_sucesso(self, mock_get_card, cobranca_service, mock_repo, mock_gateway):
        # Arrange
        cobranca = Cobranca(id=1, ciclista=1, valor=100.0, status="PENDENTE")
        mock_repo.obter_por_id.return_value = cobranca
        mock_gateway.processar_pagamento.return_value = MagicMock(status="succeeded")

        # Act
        resultado = cobranca_service.processar_pagamento_de_cobranca(1)

        # Assert
        mock_get_card.assert_called_once_with(1)
        mock_gateway.processar_pagamento.assert_called_once()
        mock_repo.salvar.assert_called_once()
        assert resultado.status == "PAGA"

    @patch.object(CobrancaService, '_obter_payment_method_id_do_ciclista')
    def test_processar_pagamento_falha_gateway(self, mock_get_card, cobranca_service, mock_repo, mock_gateway):
        # Arrange
        cobranca = Cobranca(id=1, ciclista=1, valor=100.0, status="PENDENTE")
        mock_repo.obter_por_id.return_value = cobranca
        mock_gateway.processar_pagamento.side_effect = CartaoApiError(422, "ERRO_GATEWAY", "...")

        # Act
        resultado = cobranca_service.processar_pagamento_de_cobranca(1)

        # Assert
        assert resultado.status == "FALHA"
        assert resultado.horaFinalizacao is not None
        mock_repo.salvar.assert_called_once()

    # --- Testes para a Fila ---

    @patch.object(CobrancaService, '_obter_payment_method_id_do_ciclista', return_value="pm_card_visa")
    def test_tentar_cobranca_da_fila_falha_intent_status(self, mock_get_card, cobranca_service, mock_repo, mock_gateway):
        # Arrange
        cobranca = Cobranca(id=1, ciclista=1, valor=100.0, status="PENDENTE")
        mock_gateway.processar_pagamento.return_value = MagicMock(status="failed")

        # Act
        resultado = cobranca_service.tentar_cobranca_da_fila(cobranca)

        # Assert
        assert resultado is None
        mock_repo.salvar.assert_not_called()

    @patch.object(CobrancaService, 'tentar_cobranca_da_fila', side_effect=[None, None])
    def test_processar_cobrancas_em_fila_sem_sucesso(self, mock_tentar_cobranca, cobranca_service, mock_repo, mock_email_service):
        # Arrange
        mock_repo.listar_pendentes.return_value = [Cobranca(id=1), Cobranca(id=2)]

        # Act
        resultados = cobranca_service.processar_cobrancas_em_fila()

        # Assert
        assert resultados == []
        assert mock_tentar_cobranca.call_count == 2
        mock_email_service.enviar_confirmacao_pagamento.assert_not_called()




