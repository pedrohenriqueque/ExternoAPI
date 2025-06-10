from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
import re
from app.core.exceptions import CartaoApiError


class NovoCartaoDeCreditoSchema(BaseModel):
    nomeTitular: str
    numero: str  # Agora como string
    validade: str
    cvv: str

    @field_validator('nomeTitular')
    @classmethod
    def nome_titular_nao_vazio(cls, value: str) -> str:
        if not value.strip():
            raise CartaoApiError(422, "TITULAR_VAZIO", "Nome do titular não pode ser vazio")
        return value.strip()

    @field_validator('numero')
    @classmethod
    def validar_numero_cartao(cls, value: str) -> str:
        numero = value.replace(" ", "")
        if not numero.isdigit():
            raise CartaoApiError(422, "NUMERO_INVALIDO", "Número do cartão deve conter apenas dígitos")
        if set(numero) == {"0"}:
            raise CartaoApiError(422, "NUMERO_INVALIDO", "Número do cartão não pode ser composto apenas por zeros")

        if not cls.validar_luhn(numero):
            raise CartaoApiError(422, "NUMERO_INVALIDO", "Número do cartão de crédito é inválido")

        return numero

    @staticmethod
    def validar_luhn(numero: str) -> bool:
        soma = 0
        inverter = numero[::-1]
        for i, digito in enumerate(inverter):
            n = int(digito)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            soma += n
        return soma % 10 == 0


    @field_validator('validade')
    @classmethod
    def validar_formatos_e_data_expiracao(cls, v: str) -> str:
        match = re.fullmatch(r"^(0?[1-9]|1[0-2])\/(\d{2}|\d{4})$", v)
        if not match:
            raise CartaoApiError(422, "VALIDADE_INVALIDA", "Formato de validade inválido. Use M/YY, MM/YY, M/YYYY ou MM/YYYY (ex: 1/26, 01/26, 1/2026, 01/2026).")
        mes_str, ano_str = match.groups()
        mes = int(mes_str)
        ano = int(ano_str) + 2000 if len(ano_str) == 2 else int(ano_str)

        hoje = datetime.now()
        if ano < hoje.year or (ano == hoje.year and mes < hoje.month):
            tipo = "ano" if ano < hoje.year else "mês"
            raise CartaoApiError(422, "CARTAO_EXPIRADO", f"Cartão de crédito expirado ({tipo}).")

        return v

    @field_validator('cvv')
    @classmethod
    def validar_cvv(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise CartaoApiError(422, "CVV_VAZIO", "CVV não pode ser vazio")
        if not value.isdigit():
            raise CartaoApiError(422, "CVV_INVALIDO", "CVV deve conter apenas números")
        if len(value) not in (3, 4):
            raise CartaoApiError(422, "CVV_TAMANHO_INVALIDO", "CVV deve ter 3 ou 4 dígitos")
        return value

    model_config = ConfigDict(from_attributes=True)
