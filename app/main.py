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


app.include_router(
    cartao_v1_router.router,
    prefix="",
    tags=["Validação Cartão"]
)

@app.get("/")
async def root():
    return {"message": f"Bem-vindo ao {settings.PROJECT_NAME} - Microsserviço Externo"}