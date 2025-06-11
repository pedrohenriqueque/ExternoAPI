from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.dependencies import get_db
from app.services.cobranca_service import CobrancaService
from app.schemas.cobranca_schema import CobrancaSchema
from typing import List

router = APIRouter(prefix="/processaCobrancasEmFila", tags=["Cobrança"])

@router.post("", response_model=List[CobrancaSchema], status_code=status.HTTP_200_OK)
def processar_cobrancas_em_fila(db: Session = Depends(get_db)):
    service = CobrancaService(db)
    cobrancas_processadas = service.processar_cobrancas_em_fila()
    return cobrancas_processadas
