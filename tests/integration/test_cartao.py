from fastapi.testclient import TestClient
from app.main import app
from datetime import datetime

client = TestClient(app)

# --- Utilitário ---
def validade_futura():
    hoje = datetime.now()
    return f"{hoje.month:02d}/{str(hoje.year + 1)[-2:]}"

# --- Teste de sucesso ---
def test_validacao_cartao_valido():
    response = client.post("/validaCartaoDeCredito", json={
        "nomeTitular": "João da Silva",
        "numero": "4111111111111111",
        "validade": validade_futura(),
        "cvv": "123"
    })
    assert response.status_code == 204


# --- Testes de erro ---

# Nome vazio
def test_nome_titular_vazio():
    response = client.post("/validaCartaoDeCredito", json={
        "nomeTitular": " ",
        "numero": "4111111111111111",
        "validade": validade_futura(),
        "cvv": "123"
    })
    assert response.status_code == 422
    assert response.json()["codigo"] == "TITULAR_VAZIO"

# CVV inválidos
import pytest
@pytest.mark.parametrize("cvv", ["12", "12345", "abc", "", "12a"])
def test_cartao_cvv_invalido(cvv):
    response = client.post("/validaCartaoDeCredito", json={
        "nomeTitular": "João da Silva",
        "numero": "4111111111111111",
        "validade": validade_futura(),
        "cvv": cvv
    })
    assert response.status_code == 422
    assert response.json()["codigo"].startswith("CVV")

# Validade inválida
@pytest.mark.parametrize("validade", [
    "13/26", "00/2026", "1-26", "02-20", "2//2026", "aa/2026", "1/20ab"
])
def test_cartao_validade_invalida(validade):
    response = client.post("/validaCartaoDeCredito", json={
        "nomeTitular": "João da Silva",
        "numero": "4111111111111111",
        "validade": validade,
        "cvv": "123"
    })
    assert response.status_code == 422
    assert response.json()["codigo"] == "VALIDADE_INVALIDA"

# Validade expirada
def test_cartao_expirado():
    response = client.post("/validaCartaoDeCredito", json={
        "nomeTitular": "João da Silva",
        "numero": "4111111111111111",
        "validade": "01/22",
        "cvv": "123"
    })
    assert response.status_code == 422
    assert response.json()["codigo"] == "CARTAO_EXPIRADO"

# Número inválido
@pytest.mark.parametrize("numero", [
    "", "abcd1234", "0000000000000000", "4111111111111121", "1234567890123456"
])
def test_cartao_numero_invalido(numero):
    response = client.post("/validaCartaoDeCredito", json={
        "nomeTitular": "João da Silva",
        "numero": numero,
        "validade": validade_futura(),
        "cvv": "123"
    })
    assert response.status_code == 422
    assert response.json()["codigo"] == "NUMERO_INVALIDO"
