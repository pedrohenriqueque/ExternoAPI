# app/main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import CartaoApiError
from app.db.base_class import Base
from app.db.session import engine

from app.controller import cobranca as cobranca_v1_router
from app.controller import email as email_v1_router, cartao as cartao_v1_router
from app.schemas.error_schema import ErroSchema

Base.metadata.create_all(bind=engine)

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


app.include_router(
    cartao_v1_router.router,
    prefix="",
    tags=["Validação Cartão"]
)

app.include_router(
    cobranca_v1_router.router,
    prefix="",
    tags=["Cobrança"]

)

app.include_router(
    email_v1_router.router,
    prefix="",
    tags=["Email"]

)

@app.get("/")
async def root():
    return {"message": f"Bem-vindo ao {settings.PROJECT_NAME} - Microsserviço Externo"}