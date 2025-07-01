import pytest
from pydantic import ValidationError

from app.schemas.email_schema import EmailRequest
from app.core.exceptions import CartaoApiError

# Testes para o validador 'nao_pode_estar_vazio'
@pytest.mark.parametrize("campo", ["assunto", "mensagem"])
@pytest.mark.parametrize("valor_invalido", ["", "   "])
def test_nao_pode_estar_vazio_com_dados_invalidos(campo, valor_invalido):

    dados = {"destinatario": "valido@email.com", "assunto": "Assunto", "mensagem": "Mensagem"}
    dados[campo] = valor_invalido

    with pytest.raises(CartaoApiError) as exc_info:
        EmailRequest(**dados)

    assert exc_info.value.status_code == 422
    assert exc_info.value.codigo == "FORMATO_INCORRETO"
    assert exc_info.value.mensagem == f"O campo '{campo}' não pode estar vazio."

# Testes para o validador 'validar_email' (destinatario)
def test_validar_email_obrigatorio():
    """
    Verifica se a validação falha quando 'destinatario' está vazio.
    """
    with pytest.raises(CartaoApiError) as exc_info:
        EmailRequest(destinatario="", assunto="a", mensagem="b")

    assert exc_info.value.status_code == 404
    assert exc_info.value.codigo == "DESTINATARIO_INVALIDO"
    assert "O campo 'destinatario' é obrigatório" in exc_info.value.mensagem

@pytest.mark.parametrize("email_invalido", [
    "emailsemarroba.com",
    "@dominio.com",
    "email@",
    "email@dominio_sem_ponto"
])
def test_validar_email_formato_invalido(email_invalido):

    mensagem_esperada = {
        "emailsemarroba.com": "O campo 'destinatario' deve conter um '@' válido.",
        "@dominio.com": "O campo 'destinatario' deve conter um '@' válido.",
        "email@": "O campo 'destinatario' deve conter um '@' válido.",
        "email@dominio_sem_ponto": "O domínio do e-mail está incompleto (ex: 'gmail.com')."
    }[email_invalido]

    with pytest.raises(CartaoApiError) as exc_info:
        EmailRequest(destinatario=email_invalido, assunto="a", mensagem="b")

    assert exc_info.value.status_code == 404
    assert exc_info.value.codigo == "DESTINATARIO_INVALIDO"
    assert mensagem_esperada in exc_info.value.mensagem

def test_email_request_com_dados_validos():
    """
    Verifica se o modelo é criado com sucesso quando todos os dados são válidos.
    """
    dados = {
        "destinatario": "usuario@dominio.com.br",
        "assunto": "  Assunto Válido  ",
        "mensagem": "   Mensagem Válida   "
    }

    try:
        request = EmailRequest(**dados)
        # O Pydantic realiza o strip nos campos validados
        assert request.destinatario == "usuario@dominio.com.br"
        assert request.assunto == "Assunto Válido"
        assert request.mensagem == "Mensagem Válida"
    except ValidationError as e:
        pytest.fail(f"A validação falhou inesperadamente: {e}")