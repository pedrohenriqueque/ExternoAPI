from pydantic import BaseModel

class EmailRequest(BaseModel):
    destinatario: str
    assunto: str
    mensagem: str