# Em app/api/v1/cobranca_router.py

from fastapi import APIRouter, Depends, status
from typing import List

# Schemas para validação e serialização de dados
from app.schemas.nova_cobranca_schema import NovaCobrancaSchema
from app.schemas.cobranca_schema import CobrancaSchema
from app.schemas.error_schema import ErroSchema

# A camada de serviço que contém a lógica de negócio
from app.services.cobranca_service import CobrancaService

# A função centralizada que sabe como construir o serviço
from app.core.dependencies import get_cobranca_service


router = APIRouter(tags=["Externo"])


# --- ENDPOINTS ---

@router.post(
    "/cobranca",
    response_model=CobrancaSchema,
    summary="Realizar cobrança",
    status_code=status.HTTP_200_OK,
    responses={
        "200": {"description": "Cobrança solicitada", "model": CobrancaSchema},
        "422": {"description": "Dados Inválidos", "model": ErroSchema},
    }
)
def realizar_cobranca(
        cobranca_data: NovaCobrancaSchema,
        service: CobrancaService = Depends(get_cobranca_service)
):

    nova_cobranca = service.criar_cobranca_na_fila(cobranca_data)
    cobranca_processada = service.processar_pagamento_de_cobranca(nova_cobranca.id)
    return cobranca_processada


@router.post(
    "/filaCobranca",
    response_model=CobrancaSchema,
    summary="Inclui cobrança na fila de cobrança",
    status_code=status.HTTP_200_OK,
    responses={
        "200": {"description": "Cobrança incluida na fila", "model": CobrancaSchema},
        "422": {"description": "Dados Inválidos", "model": ErroSchema}
    }
)
def colocar_cobranca_na_fila(
        cobranca_data: NovaCobrancaSchema,
        service: CobrancaService = Depends(get_cobranca_service)
):
    return service.criar_cobranca_na_fila(cobranca_data)


@router.get(
    "/cobranca/{id_cobranca}",
    response_model=CobrancaSchema,
    summary="Obter cobrança",
    status_code=status.HTTP_200_OK,
    responses={
        "200": {"description": "Cobrança", "model": CobrancaSchema},
        "404": {"description": "Não encontrado", "model": ErroSchema}
    }
)
def obter_cobranca(
        id_cobranca: int,
        service: CobrancaService = Depends(get_cobranca_service)
):
    return service.obter_por_id(id_cobranca)


@router.post(
    "/processaCobrancasEmFila",
    response_model=List[CobrancaSchema],
    summary="Processa todas as cobranças na fila",
    status_code=status.HTTP_200_OK,
    responses={
        "200": {"description": "Processamento concluído", "model": List[CobrancaSchema]},
        "422": {"description": "Dados Inválidos", "model": ErroSchema}
    }
)
def processar_fila(
        service: CobrancaService = Depends(get_cobranca_service)
):

    return service.processar_cobrancas_em_fila()