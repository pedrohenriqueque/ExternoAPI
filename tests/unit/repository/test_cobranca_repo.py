import pytest
from unittest.mock import MagicMock
from datetime import datetime

# Supondo que os componentes estejam nestes caminhos
from app.repositories.cobranca_repository import CobrancaRepository
from app.models.cobranca import Cobranca
from app.schemas.nova_cobranca_schema import NovaCobrancaSchema

class TestCobrancaRepository:
    """
    Testa a camada de repositório para a entidade Cobranca,
    baseado na implementação fornecida.
    """

    @pytest.fixture
    def mock_db_session(self) -> MagicMock:
        """Cria um mock para a sessão do banco de dados (SQLAlchemy Session)."""
        return MagicMock()

    @pytest.fixture
    def cobranca_repository(self, mock_db_session: MagicMock) -> CobrancaRepository:
        """Instancia o repositório com a sessão mockada."""
        return CobrancaRepository(db=mock_db_session)

    def test_criar_cobranca(self, cobranca_repository: CobrancaRepository, mock_db_session: MagicMock):

        # Arrange
        dados_nova_cobranca = NovaCobrancaSchema(ciclista=1, valor=150.75)
        hora_solicitacao = datetime.now()

        # Act
        cobranca_criada = cobranca_repository.criar(dados_nova_cobranca, hora_solicitacao)

        # Assert
        # Verifica se o objeto foi criado com os dados corretos
        assert cobranca_criada.ciclista == dados_nova_cobranca.ciclista
        assert cobranca_criada.valor == dados_nova_cobranca.valor
        assert cobranca_criada.status == "PENDENTE"
        assert cobranca_criada.horaSolicitacao == hora_solicitacao

        # Verifica se o objeto foi adicionado à sessão
        mock_db_session.add.assert_called_once_with(cobranca_criada)

        mock_db_session.commit.assert_not_called()

    def test_obter_por_id(self, cobranca_repository: CobrancaRepository, mock_db_session: MagicMock):

        # Arrange
        cobranca_id = 42
        # Configura a cadeia de chamadas do mock da query
        mock_query = mock_db_session.query.return_value
        mock_filtered_query = mock_query.filter.return_value

        # Act
        cobranca_repository.obter_por_id(cobranca_id)

        # Assert
        mock_db_session.query.assert_called_once_with(Cobranca)
        # Verifica se o filtro foi chamado com a condição correta
        mock_query.filter.assert_called_once()
        filter_arg = mock_query.filter.call_args[0][0]
        assert str(filter_arg) == str(Cobranca.id == cobranca_id)
        mock_filtered_query.first.assert_called_once()

    def test_listar_pendentes(self, cobranca_repository: CobrancaRepository, mock_db_session: MagicMock):

        # Arrange
        mock_query = mock_db_session.query.return_value
        mock_filtered_query = mock_query.filter_by.return_value

        # Act
        cobranca_repository.listar_pendentes()

        # Assert
        mock_db_session.query.assert_called_once_with(Cobranca)
        mock_query.filter_by.assert_called_once_with(status="PENDENTE")
        mock_filtered_query.all.assert_called_once()

    def test_salvar_cobranca(self, cobranca_repository: CobrancaRepository, mock_db_session: MagicMock):

        # Arrange
        cobranca_para_salvar = Cobranca(id=1, ciclista=1, valor=100.0, status="PAGA")

        # Act
        resultado = cobranca_repository.salvar(cobranca_para_salvar)

        # Assert
        mock_db_session.add.assert_called_once_with(cobranca_para_salvar)
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(cobranca_para_salvar)
        assert resultado is cobranca_para_salvar

