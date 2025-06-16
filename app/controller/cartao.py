from fastapi import APIRouter, status, Depends
from app.schemas.cartao_schema import NovoCartaoDeCreditoSchema
from app.schemas.error_schema import ErroSchema
from app.services.cartao_service import get_cartao_service, CartaoService

router = APIRouter(tags=["Externo"])

@router.post(
    "/validaCartaoDeCredito",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "Validação do cartão bem-sucedida"},
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
    return {"mensagem": "Cartão validado com sucesso"}
