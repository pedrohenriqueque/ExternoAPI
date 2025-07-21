import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

# Assumindo que os componentes estão nestes caminhos
from app.services.cobranca_service import CobrancaService
from app.repositories.cobranca_repository import CobrancaRepository
from app.integrations.stripe import StripeGateway
from app.services.email_service import EmailService
from app.models.cobranca import Cobranca
from app.core.exceptions import CartaoApiError
# Importar o AluguelClient (ou seu mock)
from app.clients.aluguel_client import AluguelMicroserviceClient # Assumindo este caminho

# Import real do Stripe para usar suas classes de exceção
import stripe

class TestCobrancaService:
    """
    Testa o CobrancaService, com foco em validar o comportamento da implementação fornecida,
    incluindo o tratamento de erros e fluxos de fila.
    """

    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        """Cria um mock para a CobrancaRepository."""
        mock = MagicMock(spec=CobrancaRepository)
        mock.salvar.side_effect = lambda cobranca: cobranca
        return mock

    @pytest.fixture
    def mock_gateway(self) -> MagicMock:
        """Cria um mock para a StripeGateway."""
        return MagicMock(spec=StripeGateway)

    @pytest.fixture
    def mock_email_service(self) -> MagicMock:
        """Cria um mock para o EmailService."""
        return MagicMock(spec=EmailService)

    @pytest.fixture
    def mock_aluguel_client(self) -> MagicMock:
        """NOVO: Cria um mock para o AluguelClient."""
        return MagicMock(spec=AluguelMicroserviceClient)

    @pytest.fixture
    def cobranca_service(self, mock_repo: MagicMock, mock_gateway: MagicMock, mock_email_service: MagicMock, mock_aluguel_client: MagicMock) -> CobrancaService:
        """Instancia o serviço com as dependências mockadas."""
        return CobrancaService(
            cobranca_repo=mock_repo,
            payment_gateway=mock_gateway,
            email_service=mock_email_service,
            aluguel_client=mock_aluguel_client # NOVO: Passando o mock para o construtor
        )

    # --- Testes para processar_pagamento_de_cobranca ---


    @patch.object(CobrancaService, '_obter_payment_method_id_do_ciclista', side_effect=CartaoApiError(422, "CICLISTA_SEM_CARTAO", "..."))
    def test_processar_pagamento_falha_ciclista_sem_cartao(self, mock_get_card, cobranca_service, mock_repo):
        """Testa a falha quando o ciclista não tem cartão (CartaoApiError é capturado)."""
        cobranca = Cobranca(id=1, ciclista=99, valor=100.0, status="PENDENTE")
        mock_repo.obter_por_id.return_value = cobranca

        resultado = cobranca_service.processar_pagamento_de_cobranca(1)

        assert resultado.status == "FALHA"
        assert resultado.horaFinalizacao is not None
        mock_repo.salvar.assert_called_once()
        saved_cobranca = mock_repo.salvar.call_args[0][0]
        assert saved_cobranca.status == "FALHA"

    @patch.object(CobrancaService, '_obter_payment_method_id_do_ciclista', return_value="pm_card_visa")
    def test_processar_pagamento_falha_status_intent(self, mock_get_card, cobranca_service, mock_repo, mock_gateway):
        """Testa a falha quando o intent do Stripe retorna um status de falha."""
        cobranca = Cobranca(id=1, ciclista=1, valor=100.0, status="PENDENTE")
        mock_repo.obter_por_id.return_value = cobranca
        intent_falha = MagicMock(status="failed")
        mock_gateway.processar_pagamento.return_value = intent_falha

        resultado = cobranca_service.processar_pagamento_de_cobranca(1)

        assert resultado.status == "FALHA"
        assert resultado.horaFinalizacao is not None # Adicionado
        mock_repo.salvar.assert_called_once()

    @patch.object(CobrancaService, '_obter_payment_method_id_do_ciclista', return_value="pm_card_visa")
    def test_processar_pagamento_falha_excecao_gateway(self, mock_get_card, cobranca_service, mock_repo, mock_gateway):
        """Testa que uma exceção CartaoApiError do gateway é capturada pelo serviço."""
        cobranca = Cobranca(id=1, ciclista=1, valor=100.0, status="PENDENTE")
        mock_repo.obter_por_id.return_value = cobranca
        gateway_error = CartaoApiError(422, "CARTAO_RECUSADO", "O Cartão foi recusado")
        mock_gateway.processar_pagamento.side_effect = gateway_error

        resultado = cobranca_service.processar_pagamento_de_cobranca(1)

        assert resultado.status == "FALHA"
        assert resultado.horaFinalizacao is not None # Adicionado
        mock_repo.salvar.assert_called_once()

    # --- NOVOS TESTES PARA CASOS DE BORDA ---

    def test_processar_pagamento_cobranca_nao_encontrada(self, cobranca_service, mock_repo):
        """NOVO: Testa o caso em que a cobrança com o ID fornecido não existe."""
        mock_repo.obter_por_id.return_value = None

        with pytest.raises(CartaoApiError) as exc_info:
            cobranca_service.processar_pagamento_de_cobranca(999)

        assert exc_info.value.status_code == 404
        assert exc_info.value.codigo == "COBRANCA_NAO_ENCONTRADA"

    @patch.object(CobrancaService, '_obter_payment_method_id_do_ciclista', return_value="pm_card_visa")
    @pytest.mark.parametrize("status_existente", ["PAGA", "FALHA"])
    def test_processar_pagamento_cobranca_ja_processada(self, mock_get_card, cobranca_service, mock_repo, mock_gateway, status_existente):
        """
        NOVO: Testa o comportamento atual onde uma cobrança já finalizada é processada novamente.
        NOTA: O comportamento ideal seria retornar a cobrança sem reprocessar. Este teste
        valida a lógica como está implementada.
        """
        cobranca = Cobranca(id=1, ciclista=1, valor=100.0, status=status_existente)
        mock_repo.obter_por_id.return_value = cobranca
        intent_sucesso = MagicMock(status="succeeded")
        mock_gateway.processar_pagamento.return_value = intent_sucesso

        resultado = cobranca_service.processar_pagamento_de_cobranca(1)

        # Valida o comportamento atual: ele tenta processar de novo.
        mock_gateway.processar_pagamento.assert_called_once()
        # Valida o comportamento atual: ele salva de novo no `finally`.
        mock_repo.salvar.assert_called_once()
        # O status será sobrescrito para PAGA, independentemente do status anterior.
        assert resultado.status == "PAGA"
        assert resultado.horaFinalizacao is not None # Adicionado

    # --- Testes para a Fila ---

    @patch.object(CobrancaService, '_obter_payment_method_id_do_ciclista', return_value="pm_card_visa")
    def test_tentar_cobranca_da_fila_sucesso(self, mock_get_card, cobranca_service, mock_repo, mock_gateway):
        """Testa o caminho feliz de um item da fila."""
        cobranca = Cobranca(id=1, ciclista=1, valor=100.0, status="PENDENTE")
        intent_sucesso = MagicMock(status="succeeded")
        mock_gateway.processar_pagamento.return_value = intent_sucesso

        resultado = cobranca_service.tentar_cobranca_da_fila(cobranca)

        assert resultado is not None
        assert resultado.status == "PAGA"
        assert resultado.horaFinalizacao is not None # Adicionado
        mock_repo.salvar.assert_called_once_with(resultado)

    @patch.object(CobrancaService, '_obter_payment_method_id_do_ciclista', return_value="pm_card_visa")
    def test_tentar_cobranca_da_fila_falha_gateway_retorna_none(self, mock_get_card, cobranca_service, mock_gateway, mock_repo):
        cobranca = Cobranca(id=1, ciclista=1, valor=100.0, status="PENDENTE")
        mock_gateway.processar_pagamento.side_effect = stripe.error.StripeError("API Error")

        resultado = cobranca_service.tentar_cobranca_da_fila(cobranca)

        # Comportamento atual: retorna None e não salva.
        # Sugestão de melhoria: marcar como FALHA e salvar.
        assert resultado is None
        mock_repo.salvar.assert_not_called()

    @patch.object(CobrancaService, '_obter_email_do_ciclista')
    @patch.object(CobrancaService, '_obter_payment_method_id_do_ciclista')
    def test_processar_cobrancas_em_fila_completo(self, mock_get_card, mock_get_email, cobranca_service, mock_repo, mock_gateway, mock_email_service):
        """Testa o processamento da fila com sucesso, falha e verifica o envio de e-mails."""
        cobranca_sucesso = Cobranca(id=1, ciclista=1, valor=100.0, status="PENDENTE")
        cobranca_falha = Cobranca(id=2, ciclista=2, valor=50.0, status="PENDENTE")
        cobranca_sem_email = Cobranca(id=3, ciclista=3, valor=25.0, status="PENDENTE")

        mock_repo.listar_pendentes.return_value = [cobranca_sucesso, cobranca_falha, cobranca_sem_email]

        intent_sucesso = MagicMock(status="succeeded")
        mock_gateway.processar_pagamento.side_effect = [
            intent_sucesso,
            stripe.error.StripeError("Error"),
            intent_sucesso
        ]
        mock_get_email.side_effect = ["pedrohenriqueque@gmail.com", None]

        resultados = cobranca_service.processar_cobrancas_em_fila()

        assert len(resultados) == 2
        assert resultados[0].id == 1 and resultados[0].status == "PAGA"
        assert resultados[1].id == 3 and resultados[1].status == "PAGA"
        assert mock_gateway.processar_pagamento.call_count == 3
        assert mock_repo.salvar.call_count == 2
        assert mock_get_email.call_count == 2
        mock_email_service.enviar_confirmacao_pagamento.assert_called_once_with(
            cobranca_sucesso,
            "pedrohenriqueque@gmail.com"
        )

    def test_processar_cobrancas_em_fila_vazia(self, cobranca_service, mock_repo, mock_gateway):
        """NOVO: Testa o comportamento quando não há cobranças pendentes na fila."""
        mock_repo.listar_pendentes.return_value = []

        resultados = cobranca_service.processar_cobrancas_em_fila()

        mock_gateway.processar_pagamento.assert_not_called()
        assert resultados == []
