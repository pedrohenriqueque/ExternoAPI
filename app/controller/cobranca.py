from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.schemas.nova_cobranca_schema import NovaCobrancaSchema
from app.core.exceptions import CartaoApiError
from app.services.cobranca_service import CobrancaService
from app.db.dependencies import get_db
from app.schemas.cobranca_schema import CobrancaSchema

router = APIRouter(prefix="/cobranca", tags=["Cobrança"])

@router.post("", response_model=CobrancaSchema, status_code=status.HTTP_201_CREATED)
def criar_cobranca(
        cobranca: NovaCobrancaSchema,
        db: Session = Depends(get_db)
):
    try:
        service = CobrancaService(db)
        nova_cobranca = service.criar_cobranca(cobranca)
        nova_cobranca = service.processar_cobranca(nova_cobranca)
        return nova_cobranca
    except Exception:
        raise CartaoApiError(422, "ERRO_CRIAR_COBRANCA", "Cobrança não foi criada.")

@router.get("/{id_cobranca}", response_model=CobrancaSchema, status_code=status.HTTP_200_OK)
def obter_cobranca(
        id_cobranca: int,
        db: Session = Depends(get_db)
):
    try:
        service = CobrancaService(db)
        cobranca = service.obter_por_id(id_cobranca)
        if not cobranca:
            raise CartaoApiError(404, "COBRANCA_NAO_ENCONTRADA", "Cobrança não encontrada.")
        return cobranca
    except Exception:
        raise CartaoApiError(422, "ERRO_OBTER_COBRANCA", "Erro ao buscar cobrança.")
