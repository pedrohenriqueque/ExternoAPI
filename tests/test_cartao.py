from fastapi.testclient import TestClient
from fastapi import status # Importar 'status' para usar códigos HTTP nomeados
from app.main import app # Importar a instância 'app' do seu app/main.py

# Criar um cliente de teste para sua aplicação FastAPI
client = TestClient(app)

# --- Payloads de exemplo para os testes ---
payload_cartao_valido = {
    "nomeTitular": "Pedro Valido Testador",
    "numero": "374912479705018",
    "validade": "12/28",  # MM/YY futuro
    "cvv": "123"
}

payload_cartao_invalido = { # Para ser rejeitado pela lógica de serviço
    "nomeTitular": "Pedro Rejeitado Teste",
    "numero": "4514167286457082",
    "validade": "11/27",
    "cvv": "321"
}

payload_cartao_formato_cvv_invalido = { # Para falhar na validação Pydantic
    "nomeTitular": "Pedro Formato Errado CVV",
    "numero": "374912479705018",
    "validade": "10/29",
    "cvv": "abc" # CVV com letras, inválido pelo pattern \d{3,4}
}

payload_cartao_data_expirada = { # Para falhar na validação Pydantic (custom validator)
    "nomeTitular": "Pedro Cartao Expirado",
    "numero": "374912479705018",
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

def test_validar_cartao_numero_luhn_invalido_retorna_422_formato_customizado():
    response = client.post("/validaCartaoDeCredito", json=payload_cartao_invalido)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # A mensagem exata pode depender da biblioteca PaymentCardNumber para este input específico
    # Pode ser 'Card number is not luhn valid' ou algo sobre a bandeira
    # Você pode precisar rodar uma vez para ver a mensagem exata do 'msg' e ajustar aqui
    expected_error_message_substring = "Card number is not luhn valid" # Ou outra mensagem que PaymentCardNumber retorne
    # para este número inválido.

    actual_response_json = response.json()

    assert actual_response_json["codigo"] == "NUMERO_CARTAO_INVALIDO"
    # Verifica se a substring esperada está na mensagem (mais flexível que uma correspondência exata)
    assert expected_error_message_substring in actual_response_json["mensagem"]
    # Ou, para correspondência exata se você souber a mensagem:
    # assert actual_response_json["mensagem"] == f"O número do cartão fornecido é inválido: {expected_error_message_substring}"


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
    response = client.post("/validaCartaoDeCredito", json=payload_cartao_campo_faltando)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_data = response.json()
    assert "detail" in response_data
    assert isinstance(response_data["detail"], list)
    assert len(response_data["detail"]) > 0
    # Verifica se o erro é sobre o campo 'numero' estar faltando
    assert any(err["loc"] == ["body", "numero"] and err["type"] == "missing" for err in response_data["detail"])