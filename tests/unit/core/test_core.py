import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

# --- Importações do Código Real da Aplicação ---
# Esta é a correção principal: importar o código real que será testado.
# Para que isto funcione, o pytest deve ser executado a partir da raiz do projeto.
from app.core.dependencies import get_db, get_cobranca_repository, get_cobranca_service
from app.repositories.cobranca_repository import CobrancaRepository
from app.integrations.stripe import StripeGateway
from app.services.email_service import EmailService
from app.services.cobranca_service import CobrancaService


# --- Testes Unitários ---

# O patch deve apontar para onde 'SessionLocal' é USADO, ou seja, dentro do módulo de dependências.
@patch('app.core.dependencies.SessionLocal')
def test_get_db(MockSessionLocal):
    """
    Testa a dependência get_db para garantir que ela cria, fornece (yield) e fecha uma sessão.
    """
    # Arrange
    mock_session = MagicMock(spec=Session)
    # Configura o callable MockSessionLocal para retornar nossa sessão mockada quando for chamado.
    MockSessionLocal.return_value = mock_session

    # Act
    # O `get_db` é um gerador, então precisamos iterar sobre ele para executar o código.
    db_generator = get_db()
    yielded_db = next(db_generator)

    # Assert: Verifica se a sessão foi criada e fornecida.
    MockSessionLocal.assert_called_once()
    assert yielded_db is mock_session

    # Assert: Verifica se a sessão foi fechada após o gerador ser esgotado.
    with pytest.raises(StopIteration):
        next(db_generator)

    mock_session.close.assert_called_once()


def test_get_cobranca_repository():
    """
    Testa se a dependência get_cobranca_repository instancia o repositório corretamente.
    """
    # Arrange
    mock_db_session = MagicMock(spec=Session)

    # Act
    repository = get_cobranca_repository(db=mock_db_session)

    # Assert
    assert isinstance(repository, CobrancaRepository)
    assert repository.db is mock_db_session


def test_get_cobranca_service():
    """
    Testa se a dependência get_cobranca_service instancia o serviço corretamente.
    """
    # Arrange
    mock_repo = MagicMock(spec=CobrancaRepository)
    mock_gateway = MagicMock(spec=StripeGateway)
    mock_email_svc = MagicMock(spec=EmailService)

    # Act
    # Chamamos a função diretamente com os mocks. O `Depends` do FastAPI
    # é apenas um marcador e não é executado em um teste unitário.
    service = get_cobranca_service(
        repo=mock_repo,
        gateway=mock_gateway,
        email_svc=mock_email_svc
    )

    # Assert
    assert isinstance(service, CobrancaService)
    # Verifica se as dependências foram injetadas corretamente no serviço.
    assert service.cobranca_repo is mock_repo
    assert service.payment_gateway is mock_gateway
    assert service.email_service is mock_email_svc
