# app/api/v1/schemas/cartao_schema.py
from pydantic import BaseModel, Field, ConfigDict, field_validator
from pydantic_extra_types.payment import PaymentCardNumber
from datetime import datetime # Certifique-se que datetime está importado aqui
import re

from starlette import status

from app.core.exceptions import CartaoApiError


class NovoCartaoDeCreditoSchema(BaseModel):
    nomeTitular: str
    numero: PaymentCardNumber
    validade: str # Recebe a string nos formatos M/YY, MM/YY, M/YYYY, MM/YYYY
    cvv: str

    @field_validator('nomeTitular')
    @classmethod
    def nome_titular_nao_vazio(cls, value: str) -> str:
        if not value.strip():
            raise CartaoApiError(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                codigo="TITULAR_VAZIO",
                mensagem="Nome do titular não pode ser vazio"
            )
        return value.strip()

    @field_validator('validade')
    @classmethod
    def validar_formatos_e_data_expiracao(cls, v: str) -> str:
        # Regex para validar M/YY, MM/YY, M/YYYY, MM/YYYY
        # Mês: 0?[1-9] (para 1-9 ou 01-09) ou 1[0-2] (para 10-12)
        # Ano: \d{2} (para YY) ou \d{4} (para YYYY)
        match = re.fullmatch(r"^(0?[1-9]|1[0-2])\/(\d{2}|\d{4})$", v)

        if not match:
            raise CartaoApiError(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                codigo="422",
                mensagem="('Formato de validade inválido. Use M/YY, MM/YY, M/YYYY ou MM/YYYY (ex: 1/26, 01/26, 1/2026, 01/2026).."
            )

        mes_str, ano_str = match.groups()
        mes = int(mes_str)

        #
        if len(ano_str) == 2:

            ano = int(ano_str) + 2000
        elif len(ano_str) == 4:
            ano = int(ano_str)
        else:

            raise CartaoApiError(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                codigo="422",
                mensagem="Formato de ano inválido na data de validade."
            )

        hoje = datetime.now()

        if ano < hoje.year:  # Ano de expiração já passou
            raise CartaoApiError(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                codigo="422",
                mensagem="Cartão de crédito expirado (ano)."
            )
        if ano == hoje.year and mes < hoje.month:  # Ano de expiração é o atual, mas o mês já passou
            raise CartaoApiError(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                codigo="422",
                mensagem="Cartão de crédito expirado (mês)."
            )

        return v #

    @field_validator('cvv')
    @classmethod
    def validar_cvv(cls, value: str) -> str:
        if not value.strip():
            raise CartaoApiError(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                codigo="CVV_VAZIO",
                mensagem="CVV não pode ser vazio"
            )
        if not value.isdigit():
            raise CartaoApiError(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                codigo="CVV_INVALIDO",
                mensagem="CVV deve conter apenas números"
            )
        if len(value) not in (3, 4):
            raise CartaoApiError(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                codigo="CVV_TAMANHO_INVALIDO",
                mensagem="CVV deve ter 3 ou 4 dígitos"
            )
        return value

    model_config = ConfigDict(
        from_attributes=True
    )

