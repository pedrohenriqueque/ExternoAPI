from pydantic import BaseModel, Field

class NovaCobrancaSchema(BaseModel):
    valor: float = Field(..., gt=0, multiple_of=0.01)
    ciclista: int