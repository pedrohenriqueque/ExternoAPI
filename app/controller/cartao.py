from fastapi import APIRouter, status, Depends, Response
from app.schemas.cartao_schema import NovoCartaoDeCreditoSchema
from app.schemas.error_schema import ErroSchema
from app.services.cartao_service import get_cartao_service, CartaoService

router = APIRouter(tags=["Externo"])

@router.post(
    "/validaCartaoDeCredito",
    summary="Valida os dados de um cartão de crédito",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Validação do cartão bem-sucedida. Nenhum conteúdo é retornado."
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Dados Inválidos ou Cartão Recusado",
            "model": ErroSchema
        }
    }
)
def validar_cartao(
        dados: NovoCartaoDeCreditoSchema,
        service: CartaoService = Depends(get_cartao_service)
):
    service.validar_cartao(dados)

    return Response(status_code=status.HTTP_200_OK)