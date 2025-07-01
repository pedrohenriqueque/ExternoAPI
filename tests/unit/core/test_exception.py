import pytest
import json
from unittest.mock import AsyncMock, MagicMock

# Para executar testes async com pytest, pode ser necessário o plugin: pip install pytest-asyncio

# Importações do código real da aplicação
# Supondo que o ficheiro de teste está em `tests/unit/core/test_main_handlers.py`
# e que a sua app está na raiz do projeto.
from app.main import catch_malformed_json, validation_exception_handler, cartao_api_exception_handler
from app.core.exceptions import CartaoApiError


# Importações de exceções do FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# --- Testes Unitários Puros ---

@pytest.mark.asyncio
async def test_middleware_unit_catch_malformed_json():
    """
    Testa o middleware de forma unitária, simulando uma requisição
    cujo corpo levanta um JSONDecodeError.
    """
    # Arrange
    # 1. Mock da requisição (Request)
    mock_request = MagicMock()
    mock_request.headers = {"content-type": "application/json"}
    # Simulamos que a leitura do corpo da requisição falha com um erro de JSON
    mock_request.json = AsyncMock(side_effect=json.JSONDecodeError("Erro", "doc", 0))

    # 2. Mock da função `call_next` que o middleware chamaria. Não deve ser chamada.
    mock_call_next = AsyncMock()

    # Act: Chamada direta da função do middleware
    response = await catch_malformed_json(mock_request, mock_call_next)

    # Assert
    assert isinstance(response, JSONResponse)
    assert response.status_code == 422
    expected_content = {
        "codigo": "JSON_MALFORMADO",
        "mensagem": "O corpo da requisição está com formato JSON inválido."
    }
    assert json.loads(response.body.decode()) == expected_content
    mock_call_next.assert_not_called()

@pytest.mark.asyncio
async def test_middleware_unit_valid_json_passes():
    """
    Testa o middleware de forma unitária, garantindo que ele chama
    a próxima função (`call_next`) quando a requisição é válida.
    """
    # Arrange
    mock_request = MagicMock()
    mock_request.headers = {"content-type": "application/json"}
    mock_request.json = AsyncMock(return_value={}) # Leitura bem-sucedida
    expected_response = JSONResponse(content={"status": "ok"})
    mock_call_next = AsyncMock(return_value=expected_response)

    # Act
    response = await catch_malformed_json(mock_request, mock_call_next)

    # Assert
    mock_call_next.assert_called_once_with(mock_request)
    assert response == expected_response

@pytest.mark.asyncio
async def test_validation_exception_handler_unit():
    """
    Testa o handler de RequestValidationError de forma unitária.
    """
    # Arrange
    mock_request = MagicMock()
    # O construtor de RequestValidationError requer uma lista de erros.
    validation_exc = RequestValidationError(errors=[])

    # Act
    response = await validation_exception_handler(mock_request, validation_exc)

    # Assert
    assert isinstance(response, JSONResponse)
    assert response.status_code == 422
    assert json.loads(response.body.decode()) == {
        "codigo": "ERRO_VALIDACAO",
        "mensagem": "Erro de validação no corpo da requisição.",
    }

@pytest.mark.asyncio
async def test_cartao_api_exception_handler_unit():
    """
    Testa o handler da exceção customizada CartaoApiError de forma unitária.
    """
    # Arrange
    mock_request = MagicMock()
    cartao_exc = CartaoApiError(status_code=400, codigo="ERRO_TESTE", mensagem="Erro simulado.")

    # Act
    response = await cartao_api_exception_handler(mock_request, cartao_exc)

    # Assert
    assert isinstance(response, JSONResponse)
    assert response.status_code == 400
    assert json.loads(response.body.decode()) == {
        "codigo": "ERRO_TESTE",
        "mensagem": "Erro simulado."
    }
