# app/main.py
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.api.v1.endpoints import cartao as cartao_v1_router

from app.core.config import settings
from app.core.exceptions import CartaoApiError
from app.api.v1.schemas.error_schema import ErroSchema

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

@app.exception_handler(CartaoApiError)
async def cartao_api_exception_handler(request: Request, exc: CartaoApiError):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErroSchema(codigo=exc.codigo, mensagem=exc.mensagem).model_dump()
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    for error in exc.errors():
        loc = error.get("loc", ()) # Ex: ('body', 'numero')
        error_type = error.get("type", "") # Ex: 'payment_card_number_luhn'

        # Condição específica para erro de validação do número do cartão
        if (len(loc) > 1 and
                loc[0] == "body" and
                loc[1] == "numero" and
                ("payment_card_number" in error_type or "luhn" in error_type)): # Checa por tipos comuns de erro de cartão

            # Se for, retorna o ErroSchema customizado
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=jsonable_encoder(ErroSchema(
                    codigo="422", # Código específico para este erro
                    mensagem="Numero de Cartão Invalido"
                ))
            )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": jsonable_encoder(exc.errors())} # Formato padrão do FastAPI
    )
# Inclui os routers

app.include_router(
    cartao_v1_router.router,
    prefix="",
    tags=["Validação Cartão"]
)

@app.get("/")
async def root():
    return {"message": f"Bem-vindo ao {settings.PROJECT_NAME} - Microsserviço Externo"}