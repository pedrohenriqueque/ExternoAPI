import pytest
from datetime import datetime

from app.api.v1.schemas.cartao_schema import NovoCartaoDeCreditoSchema
from app.core.exceptions import CartaoApiError


@pytest.fixture
def dados_base():
    return {
        "nomeTitular": "João da Silva",
        "numero": "4111111111111111",  # Número válido simulado (VISA)
        "cvv": "123"
    }

def validade_futura(formato="MM/YY"):
    hoje = datetime.now()
    mes = hoje.month
    ano = hoje.year + 1

    if formato == "M/YY":
        return f"{mes}/{str(ano)[-2:]}"
    elif formato == "MM/YY":
        return f"{mes:02d}/{str(ano)[-2:]}"
    elif formato == "M/YYYY":
        return f"{mes}/{ano}"
    elif formato == "MM/YYYY":
        return f"{mes:02d}/{ano}"
    return ""

# --- Casos de sucesso ---
@pytest.mark.parametrize("formato", ["M/YY", "MM/YY", "M/YYYY", "MM/YYYY"])
def test_cartao_valido_com_varios_formatos(dados_base, formato):
    dados_base["validade"] = validade_futura(formato)
    cartao = NovoCartaoDeCreditoSchema(**dados_base)
    assert cartao.nomeTitular == dados_base["nomeTitular"].strip()
    assert cartao.validade == dados_base["validade"]
    assert cartao.numero == "4111111111111111"
    assert cartao.cvv == "123"

# --- Nome do titular vazio ---
def test_nome_titular_vazio_lanca_excecao(dados_base):
    dados_base["nomeTitular"] = "   "
    dados_base["validade"] = validade_futura()
    with pytest.raises(CartaoApiError) as excinfo:
        NovoCartaoDeCreditoSchema(**dados_base)
    assert excinfo.value.codigo == "TITULAR_VAZIO"

# --- Validade com formato inválido ---
@pytest.mark.parametrize("invalido", [
    "13/26", "00/2026", "1-26", "02-20", "2//2026", "aa/2026", "1/20ab"
])
def test_validade_com_formato_invalido(dados_base, invalido):
    dados_base["validade"] = invalido
    with pytest.raises(CartaoApiError) as excinfo:
        NovoCartaoDeCreditoSchema(**dados_base)
    assert "Formato de validade inválido" in excinfo.value.mensagem

# --- Cartão expirado por ano ---
def test_cartao_expirado_por_ano(dados_base):
    ano_passado = datetime.now().year - 1
    dados_base["validade"] = f"12/{str(ano_passado)[-2:]}"
    with pytest.raises(CartaoApiError) as excinfo:
        NovoCartaoDeCreditoSchema(**dados_base)
    assert "Cartão de crédito expirado (ano)" in excinfo.value.mensagem

# --- Cartão expirado por mês ---
def test_cartao_expirado_por_mes(dados_base):
    hoje = datetime.now()
    if hoje.month == 1:
        mes = 12
        ano = hoje.year - 1
    else:
        mes = hoje.month - 1
        ano = hoje.year

    dados_base["validade"] = f"{mes:02d}/{str(ano)[-2:]}"
    with pytest.raises(CartaoApiError) as excinfo:
        NovoCartaoDeCreditoSchema(**dados_base)
    assert "Cartão de crédito expirado (mês)" in excinfo.value.mensagem

# --- CVVs inválidos ---
@pytest.mark.parametrize("cvv", ["12", "12345", "abc", "", "12a"])
def test_cvv_invalido(dados_base, cvv):
    dados_base["validade"] = validade_futura()
    dados_base["cvv"] = cvv
    with pytest.raises(CartaoApiError) as excinfo:
        NovoCartaoDeCreditoSchema(**dados_base)
    assert excinfo.value.codigo in ["CVV_VAZIO", "CVV_INVALIDO", "CVV_TAMANHO_INVALIDO"]

# --- Números de cartão inválidos ---
@pytest.mark.parametrize("numero_invalido", [
    "",                       # vazio
    "4111 1111 1111 111",     # incompleto
    "abcd1234abcd5678",       # letras
    "4111111111111121",       # falha no algoritmo de Luhn
    "0000000000000000",       # não passa no Luhn
    "1234567890123456"        # estrutura válida, mas inválido no Luhn
])
def test_numero_cartao_invalido(dados_base, numero_invalido):
    dados_base["validade"] = validade_futura()
    dados_base["numero"] = numero_invalido
    with pytest.raises(CartaoApiError) as excinfo:
        NovoCartaoDeCreditoSchema(**dados_base)
    assert excinfo.value.codigo == "NUMERO_INVALIDO"
