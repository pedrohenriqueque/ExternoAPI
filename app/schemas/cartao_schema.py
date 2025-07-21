from pydantic import BaseModel,ConfigDict, field_validator
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
