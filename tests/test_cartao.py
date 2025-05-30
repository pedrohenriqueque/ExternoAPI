from fastapi.testclient import TestClient
from fastapi import status # Importar 'status' para usar códigos HTTP nomeados
from app.main import app # Importar a instância 'app' do seu app/main.py

# Criar um cliente de teste para sua aplicação FastAPI
client = TestClient(app)

# --- Payloads de exemplo para os testes ---
payload_cartao_valido = {
    "nomeTitular": "Pedro Valido Testador",
    "numero": "1234567890123456",
    "validade": "12/28",  # MM/YY futuro
    "cvv": "123"
}

payload_cartao_simulado_invalido = { # Para ser rejeitado pela lógica de serviço
    "nomeTitular": "Pedro Rejeitado Teste",
    "numero": "9876543210980000", # Termina em 0000 para simular falha
    "validade": "11/27",
    "cvv": "321"
}

payload_cartao_formato_cvv_invalido = { # Para falhar na validação Pydantic
    "nomeTitular": "Pedro Formato Errado CVV",
    "numero": "1111222233334444",
    "validade": "10/29",
    "cvv": "abc" # CVV com letras, inválido pelo pattern \d{3,4}
}

payload_cartao_data_expirada = { # Para falhar na validação Pydantic (custom validator)
    "nomeTitular": "Pedro Cartao Expirado",
    "numero": "3333444455556666",
    "validade": "12/20", # MM/YY passado
    "cvv": "789"
}

payload_cartao_campo_faltando = { # Para falhar na validação Pydantic
    "nomeTitular": "Pedro Incompleto",
    # "numero": "1111222233334444", # Campo 'numero' faltando
    "validade": "09/26",
    "cvv": "456"
}

# --- Testes ---

def test_validar_cartao_sucesso_retorna_204_no_content():
    """
    Testa a validação de um cartão válido, esperando 204 No Content.
    """
    response = client.post("/validaCartaoDeCredito", json=payload_cartao_valido)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content == b'' # Verifica se o corpo da resposta está vazio

def test_validar_cartao_simulado_invalido_retorna_422_com_erro_customizado():
    """
    Testa um cartão que é considerado inválido pela lógica de serviço (simulação),
    esperando 422 com o formato de erro customizado.
    """
    response = client.post("/validaCartaoDeCredito", json=payload_cartao_simulado_invalido)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    expected_error_body = {
        "codigo": "DADOS_INVALIDOS",
        "mensagem": "Cartão de crédito inválido ou recusado."
    }
    assert response.json() == expected_error_body

def test_validar_cartao_formato_cvv_invalido_retorna_422_erro_pydantic():
    """
    Testa um cartão com formato de CVV inválido, esperando 422 com o erro de validação do Pydantic/FastAPI.
    """
    response = client.post("/validaCartaoDeCredito", json=payload_cartao_formato_cvv_invalido)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_data = response.json()
    # O erro de validação do Pydantic/FastAPI vem dentro de uma chave "detail" e é uma lista
    assert "detail" in response_data
    assert isinstance(response_data["detail"], list)
    assert len(response_data["detail"]) > 0
    # Verifica se o erro é sobre o campo 'cvv'
    assert any(err["loc"] == ["body", "cvv"] and "string_pattern_mismatch" in err["type"] for err in response_data["detail"])

def test_validar_cartao_data_expirada_retorna_422_erro_pydantic():
    """
    Testa um cartão com data de validade expirada (validação customizada no Pydantic),
    esperando 422 com o erro de validação do Pydantic/FastAPI.
    """
    response = client.post("/validaCartaoDeCredito", json=payload_cartao_data_expirada)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_data = response.json()
    assert "detail" in response_data
    assert isinstance(response_data["detail"], list)
    assert len(response_data["detail"]) > 0
    # Verifica se o erro é sobre o campo 'validade' e a mensagem específica
    assert any(
        err["loc"] == ["body", "validade"] and "Cartão de crédito expirado (MM/YY)" in err["msg"]
        for err in response_data["detail"]
    )

def test_validar_cartao_campo_obrigatorio_faltando_retorna_422_erro_pydantic():
    """
    Testa uma requisição com um campo obrigatório faltando (número do cartão),
    esperando 422 com o erro de validação do Pydantic/FastAPI.
    """
    response = client.post("//validaCartaoDeCredito", json=payload_cartao_campo_faltando)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_data = response.json()
    assert "detail" in response_data
    assert isinstance(response_data["detail"], list)
    assert len(response_data["detail"]) > 0
    # Verifica se o erro é sobre o campo 'numero' estar faltando
    assert any(err["loc"] == ["body", "numero"] and err["type"] == "missing" for err in response_data["detail"])