from pydantic import BaseModel, Field, ConfigDict, field_validator  #
from pydantic_extra_types.payment import PaymentCardNumber


class NovoCartaoDeCreditoSchema(BaseModel):
    nomeTitular: str
    numero: PaymentCardNumber
    validade: str
    cvv: str = Field(pattern=r"^\d{3,4}$", min_length=3, max_length=4)

    # Validador para validade se for string "MM/YY"
    @field_validator('validade')
    @classmethod
    def validar_data_validade_str(cls, value: str) -> str:

        import re
        from datetime import date, datetime
        if re.match(r"^(0[1-9]|1[0-2])\/(\d{2})$", value): # Formato MM/YY
            mes_str, ano_str = value.split('/')
            mes = int(mes_str)
            ano = int(ano_str) + 2000
            hoje = datetime.now()
            if ano < hoje.year or (ano == hoje.year and mes < hoje.month):
                raise ValueError("Cartão de crédito expirado (MM/YY)")
            return value
        raise ValueError("Formato de validade inválido. Use MM/YY.")


    model_config = ConfigDict(
        from_attributes=True  # Permite criar o modelo a partir de atributos de objeto (ex: ORM)
    )


