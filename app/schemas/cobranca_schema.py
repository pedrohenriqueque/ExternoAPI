from typing import Optional, Literal
from datetime import datetime
from app.schemas.nova_cobranca_schema import NovaCobrancaSchema


class CobrancaSchema(NovaCobrancaSchema):
    id: int
    status: Literal["PENDENTE", "PAGA", "FALHA", "CANCELADA", "OCUPADA"]
    horaSolicitacao: datetime
    horaFinalizacao: Optional[datetime]