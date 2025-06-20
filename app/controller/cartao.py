from fastapi import APIRouter, status, Depends, Response
from app.schemas.cartao_schema import NovoCartaoDeCreditoSchema
from app.schemas.error_schema import ErroSchema
from app.services.cartao_service import get_cartao_service, CartaoService

router = APIRouter(tags=["Externo"])

@router.post(
    "/valida-cartao-de-credito",
    summary="Valida os dados de um cartão de crédito",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Validação do cartão bem-sucedida. Nenhum conteúdo é retornado."
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Dados Inválidos ou Cartão Recusado",
            "model": ErroSchema
        }
    }
)
async def validar_cartao(
        dados: NovoCartaoDeCreditoSchema,
        service: CartaoService = Depends(get_cartao_service)
):
    await service.validar_cartao(dados)

    return Response(status_code=status.HTTP_204_NO_CONTENT)