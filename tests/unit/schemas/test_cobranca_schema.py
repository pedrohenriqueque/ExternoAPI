import pytest
from pydantic import ValidationError
from datetime import datetime

# Supondo que os seus schemas estão em app/schemas/
# Para que os testes funcionem, execute o pytest a partir da raiz do projeto.
from app.schemas.nova_cobranca_schema import NovaCobrancaSchema
from app.schemas.cobranca_schema import CobrancaSchema


# --- Testes para NovaCobrancaSchema ---

def test_nova_cobranca_schema_sucesso():
    """
    Testa a criação bem-sucedida de um NovaCobrancaSchema com dados válidos.
    """
    dados_validos = {"valor": 99.99, "ciclista": 1}
    try:
        cobranca = NovaCobrancaSchema(**dados_validos)
        assert cobranca.valor == 99.99
        assert cobranca.ciclista == 1
    except ValidationError as e:
        pytest.fail(f"A validação falhou inesperadamente com dados válidos: {e}")


@pytest.mark.parametrize("valor_invalido", [0, -10.50, 5.999])
def test_nova_cobranca_schema_falha_valor_invalido(valor_invalido):
    """
    Testa se NovaCobrancaSchema falha com valores inválidos (menor ou igual a zero, ou não múltiplo de 0.01).
    """
    dados_invalidos = {"valor": valor_invalido, "ciclista": 2}
    with pytest.raises(ValidationError):
        NovaCobrancaSchema(**dados_invalidos)


# --- Testes para CobrancaSchema ---

def test_cobranca_schema_sucesso():
    """
    Testa a criação bem-sucedida de um CobrancaSchema com dados válidos.
    """
    dados_validos = {
        "id": 100,
        "status": "PAGA",
        "valor": 25.50,
        "ciclista": 3,
        "horaSolicitacao": datetime.now(),
        "horaFinalizacao": datetime.now()
    }
    try:
        cobranca = CobrancaSchema(**dados_validos)
        assert cobranca.id == 100
        assert cobranca.status == "PAGA"
        assert cobranca.valor == 25.50
    except ValidationError as e:
        pytest.fail(f"A validação falhou inesperadamente com dados válidos: {e}")


def test_cobranca_schema_sucesso_com_hora_finalizacao_nula():
    """
    Testa a criação bem-sucedida de um CobrancaSchema quando horaFinalizacao é explicitamente None.
    """
    # CORREÇÃO: O erro `ValidationError: Field required` indica que o campo `horaFinalizacao`
    # deve estar presente nos dados de entrada, mesmo que seu valor seja nulo.
    # Para um campo ser verdadeiramente opcional (poder ser omitido), ele precisa de um valor padrão
    # no schema, como: `horaFinalizacao: Optional[datetime] = None`.
    dados_validos = {
        "id": 101,
        "status": "PENDENTE",
        "valor": 10.00,
        "ciclista": 4,
        "horaSolicitacao": datetime.now(),
        "horaFinalizacao": None  # Fornecendo o campo explicitamente como None
    }
    try:
        cobranca = CobrancaSchema(**dados_validos)
        assert cobranca.status == "PENDENTE"
        assert cobranca.horaFinalizacao is None
    except ValidationError as e:
        pytest.fail(f"A validação falhou inesperadamente com dados válidos: {e}")


def test_cobranca_schema_falha_status_invalido():
    """
    Testa se CobrancaSchema falha quando um valor de status inválido é fornecido.
    """
    dados_invalidos = {
        "id": 102,
        "status": "EM_PROCESSAMENTO",  # Status inválido
        "valor": 5.00,
        "ciclista": 5,
        "horaSolicitacao": datetime.now(),
        "horaFinalizacao": None # CORREÇÃO: O campo é obrigatório, então fornecemos None
    }
    with pytest.raises(ValidationError) as exc_info:
        CobrancaSchema(**dados_invalidos)

    # Opcional: verificar a mensagem de erro para garantir que a falha foi no campo certo
    assert "Input should be 'PENDENTE', 'PAGA', 'FALHA', 'CANCELADA' or 'OCUPADA'" in str(exc_info.value)