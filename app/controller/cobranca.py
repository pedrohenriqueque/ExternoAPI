from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

# Importações necessárias do seu projeto
from app.services.cobranca_service import CobrancaService
from app.integrations.stripe import StripeGateway
from app.schemas.nova_cobranca_schema import NovaCobrancaSchema
from app.schemas.cobranca_schema import CobrancaSchema
from app.schemas.error_schema import ErroSchema # Import ErroSchema
from app.db.dependencies import get_db
from app.core.exceptions import CartaoApiError

router = APIRouter(tags=["Externo"])

# --- CAMADA DE INJEÇÃO DE DEPENDÊNCIA  ---


def get_payment_gateway() -> StripeGateway:
    return StripeGateway()

def get_cobranca_service(
        db: Session = Depends(get_db),
        payment_gateway: StripeGateway = Depends(get_payment_gateway)
) -> CobrancaService:
    return CobrancaService(db=db, payment_gateway=payment_gateway)


# --- ENDPOINTS  ---

@router.post(
    "/cobranca",
    response_model=CobrancaSchema,
    summary="Realizar cobrança",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Cobrança solicitada",
            "model": CobrancaSchema
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Dados Inválidos",
            "model": ErroSchema # Or List[ErroSchema]
        }
    }
)
def realizar_cobranca(
        cobranca: NovaCobrancaSchema,
        service: CobrancaService = Depends(get_cobranca_service)
):
    try:
        nova_cobranca = service.criar_cobranca(cobranca)
        cobranca_processada = service.processar_cobranca(nova_cobranca)
        return cobranca_processada
    except Exception:
        raise CartaoApiError(422, "ERRO_CRIAR_COBRANCA", "Cobrança não foi criada.")


@router.post(
    "/processaCobrancasEmFila",
    response_model=List[CobrancaSchema],
    summary="Processa todas as cobranças atrasadas colocadas em fila previamente.",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Processamento concluído com sucesso",
            "model": List[CobrancaSchema]
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Dados Inválidos",
            "model": ErroSchema
        }
    }
)
def processar_fila(
        service: CobrancaService = Depends(get_cobranca_service)
):
    try:
        cobrancas_processadas = service.processar_cobrancas_em_fila()
        return cobrancas_processadas
    except Exception:
        raise CartaoApiError(422, "ERRO_PROCESSAR_FILA", "Fila não foi processada")


@router.post(
    "/filaCobranca",
    response_model=CobrancaSchema,
    summary="Inclui cobrança na fila de cobrança. Cobranças na fila serão cobradas de tempos em tempos.",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Cobrança Incluida",
            "model": CobrancaSchema
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Dados Inválidos",
            "model": ErroSchema
        }
    }
)
def colocar_cobranca_na_fila(
        cobranca: NovaCobrancaSchema,
        service: CobrancaService = Depends(get_cobranca_service)
):

    try:
        nova_cobranca = service.criar_cobranca(cobranca)
        return nova_cobranca
    except Exception:
        raise CartaoApiError(422, "ERRO_ADICIONAR_FILA", "Erro ao adicionar cobrança à fila.")


@router.get(
    "/cobranca/{id_cobranca}",
    response_model=CobrancaSchema,
    summary="Obter cobrança",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Cobrança",
            "model": CobrancaSchema
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Não encontrado",
            "model": ErroSchema
        }
    }
)
def obter_cobranca(
        id_cobranca: int,
        service: CobrancaService = Depends(get_cobranca_service)
):

    cobranca = service.obter_por_id(id_cobranca)
    if not cobranca:
        raise CartaoApiError(404, "COBRANCA_NAO_ENCONTRADA", "Cobrança não encontrada")
    return cobranca