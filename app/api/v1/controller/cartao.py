# app/api/v1/controller/cartao.py
from fastapi import APIRouter, status, Body, Response
from app.api.v1.schemas.cartao_schema import NovoCartaoDeCreditoSchema # ou o nome que você deu ao arquivo/classe
from app.api.v1.schemas.error_schema import ErroSchema # ou o nome que você deu ao arquivo/classe
from app.services.cartao_service import cartao_service_instance # ou o nome que você deu ao arquivo/instância
from app.core.exceptions import CartaoApiError

router = APIRouter()

@router.post(
    "/validaCartaoDeCredito",  #
    summary="Valida um cartão de crédito",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Validação do cartão bem-sucedida (sem conteúdo de resposta)"
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Dados Inválidos ou Cartão Recusado",
            "model": ErroSchema
        }
    }
)

async def validar_cartao_de_credito(
        cartao_data: NovoCartaoDeCreditoSchema = Body(...)
):
    await cartao_service_instance.validar_cartao(cartao_data)
    return Response(status_code=status.HTTP_204_NO_CONTENT)