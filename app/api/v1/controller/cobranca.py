from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.schemas.nova_cobranca_schema import NovaCobrancaSchema
from app.services.cobranca_service import CobrancaService
from app.db.dependencies import get_db
from app.api.v1.schemas.cobranca_schema import CobrancaSchema

router = APIRouter(prefix="/cobranca", tags=["Cobrança"])

@router.post("/", response_model=CobrancaSchema, status_code=status.HTTP_201_CREATED)
def criar_cobranca(
        cobranca: NovaCobrancaSchema,
        db: Session = Depends(get_db)
):
    try:
        service = CobrancaService(db)
        nova_cobranca = service.criar_cobranca(cobranca)
        nova_cobranca = service.processar_cobranca(nova_cobranca)
        return nova_cobranca
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{id_cobranca}", response_model=CobrancaSchema, status_code=status.HTTP_200_OK)
def obter_cobranca(
        id_cobranca: int,
        db: Session = Depends(get_db)
):
    try:
        service = CobrancaService(db)
        cobranca = service.obter_por_id(id_cobranca)
        if not cobranca:
            raise HTTPException(status_code=404, detail="Cobrança não encontrada.")
        return cobranca
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
