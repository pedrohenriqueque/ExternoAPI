# app/api/v1/endpoints/cartao.py
from fastapi import APIRouter, status, Body, Response
# Certifique-se que os imports dos seus schemas estão corretos conforme os nomes dos seus arquivos
from app.api.v1.schemas.cartao_schema import NovoCartaoDeCreditoSchema # ou o nome que você deu ao arquivo/classe
from app.api.v1.schemas.error_schema import ErroSchema # ou o nome que você deu ao arquivo/classe
from app.services.cartao_service import cartao_service_instance # ou o nome que você deu ao arquivo/instância
from app.core.exceptions import CartaoApiError

router = APIRouter()

@router.post(
    "/validaCartaoDeCredito",  # <--- CERTIFIQUE-SE QUE ESTÁ EXATAMENTE ASSIM
    summary="Valida um cartão de crédito",
    status_code=status.HTTP_204_NO_CONTENT, # Se você quer 204 para sucesso sem corpo
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
    valido = await cartao_service_instance.validar_cartao_simulado(cartao_data)

    if not valido:
        raise CartaoApiError(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            codigo="DADOS_INVALIDOS",
            mensagem="Cartão de crédito inválido ou recusado."
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)