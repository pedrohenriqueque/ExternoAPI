# app/main.py
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError

from fastapi.responses import JSONResponse
import json  # ✅ Aqui está a correção
from app.core.config import settings
from app.core.exceptions import CartaoApiError
from app.db.base_class import Base
from app.db.session import engine

from app.controller import cobranca as cobranca_v1_router
from app.controller import email as email_v1_router, cartao as cartao_v1_router , restaurar as restaurar_v1_router
from app.schemas.error_schema import ErroSchema

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

@app.middleware("http")
async def catch_malformed_json(request: Request, call_next):
    if request.headers.get("content-type") == "application/json":
        try:
            await request.json()
        except json.JSONDecodeError:
            return JSONResponse(
                status_code=422,
                content={
                    "codigo": "JSON_MALFORMADO",
                    "mensagem": "O corpo da requisição está com formato JSON inválido."
                }
            )
    return await call_next(request)

# Handler: erros de validação de dados (ex: tipo errado, campo ausente etc.)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "codigo": "ERRO_VALIDACAO",
            "mensagem": "Erro de validação no corpo da requisição.",
        }
    )

@app.exception_handler(CartaoApiError)
async def cartao_api_exception_handler(request: Request, exc: CartaoApiError):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErroSchema(codigo=exc.codigo, mensagem=exc.mensagem).model_dump()
    )


app.include_router(
    cartao_v1_router.router,
)

app.include_router(
    cobranca_v1_router.router,
)

app.include_router(
    email_v1_router.router,
)
app.include_router(
    restaurar_v1_router.router,
)