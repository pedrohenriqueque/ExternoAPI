from pydantic import BaseModel

class ErroSchema(BaseModel):
    codigo: str
    mensagem: str