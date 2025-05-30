from pydantic import BaseModel, constr, field_validator
from datetime import date # Usaremos date para validade, conforme spec.
import re

class NovoCartaoDeCreditoSchema(BaseModel):
    nomeTitular: str
    numero: constr(pattern=r'^\d+$') # A spec diz pattern: \d+
    validade: str  # A spec diz format: date. Vamos validar o formato 'MM/YY' ou 'YYYY-MM-DD'
    cvv: constr(pattern=r'^\d{3,4}$') # A spec diz pattern: \d{3,4}

    @field_validator('nomeTitular')
    @classmethod
    def nome_titular_nao_vazio(cls, value):
        if not value.strip():
            raise ValueError('Nome do titular não pode ser vazio')
        return value

    @field_validator('validade')
    @classmethod
    def validar_formato_e_data_validade(cls, value):
        # Tenta MM/YY ou MM/YYYY
        if re.match(r"^(0[1-9]|1[0-2])\/(\d{2}|\d{4})$", value):
            mes_str, ano_str = value.split('/')
            mes = int(mes_str)
            ano = int(ano_str)
            if len(ano_str) == 2:
                ano += 2000 # Assume século 21 para anos com 2 dígitos

            from datetime import datetime
            hoje = datetime.now()
            # Cartão é válido se expira no último dia do mês de validade
            # Consideramos que o cartão expira após o mês indicado
            if ano < hoje.year or (ano == hoje.year and mes < hoje.month):
                raise ValueError("Cartão de crédito expirado (MM/YY)")
            return value # Retorna o valor original se válido
        # Tenta YYYY-MM-DD
        try:
            data_validade_obj = date.fromisoformat(value)
            # Validação se a data é futura (simplificado)
            if data_validade_obj < date.today():
                raise ValueError("Cartão de crédito expirado (YYYY-MM-DD)")
            return value
        except ValueError:
            raise ValueError("Formato de validade inválido. Use MM/YY, MM/YYYY ou YYYY-MM-DD.")