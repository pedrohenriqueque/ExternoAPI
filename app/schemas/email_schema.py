from pydantic import BaseModel, field_validator
from pydantic_core.core_schema import ValidationInfo

from app.core.exceptions import CartaoApiError

class EmailRequest(BaseModel):
    destinatario: str
    assunto: str
    mensagem: str

    @field_validator('assunto', 'mensagem')
    def nao_pode_estar_vazio(cls, v, info: ValidationInfo):
        if not v or not v.strip():
            raise CartaoApiError(422,"FORMATO_INCORRETO",f"O campo '{info.field_name}' não pode estar vazio.")
        return v

    @field_validator('destinatario')
    def validar_email(cls, v):
        email = v

        if not email:
            raise CartaoApiError(404, "DESTINATARIO_INVALIDO", "O campo 'destinatario' é obrigatório.")

        if "@" not in email or email.startswith("@") or email.endswith("@"):
            raise CartaoApiError(404, "DESTINATARIO_INVALIDO", "O campo 'destinatario' deve conter um '@' válido.")

        if "." not in email.split("@")[-1]:
            raise CartaoApiError(404, "DESTINATARIO_INVALIDO", "O domínio do e-mail está incompleto (ex: 'gmail.com').")

        return email
