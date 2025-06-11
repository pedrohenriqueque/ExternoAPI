from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.schemas.cobranca_schema import CobrancaSchema
from app.schemas.nova_cobranca_schema import NovaCobrancaSchema
from app.core.exceptions import CartaoApiError
from app.services.cobranca_service import CobrancaService
from app.db.dependencies import get_db

router = APIRouter(prefix="/filaCobranca", tags=["Externo"])

@router.post("/", response_model=CobrancaSchema, status_code=status.HTTP_200_OK)
def incluir_na_fila(
        nova_cobranca: NovaCobrancaSchema,
        db: Session = Depends(get_db)
):
    try:
        service = CobrancaService(db)
        cobranca = service.incluir_na_fila(nova_cobranca)
        return cobranca
    except Exception:
        raise CartaoApiError(422, "ERRO_INCLUIR_FILA", "Não foi possível incluir a cobrança na fila.")
