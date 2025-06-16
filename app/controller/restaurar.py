from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get(
    "/restaurarBanco",
    tags=["Externo"],
    status_code=status.HTTP_200_OK,
    summary="Restaura o banco de dados para os dados iniciais." # Added summary
)
def restaurar_banco():
    try:
        # Simulação de reset do banco de dados
        from app.db.seed import restaurar_dados_iniciais
        restaurar_dados_iniciais()

        return {"mensagem": "Banco restaurado com sucesso."}
    except Exception as e:
        return JSONResponse(
            status_code=422,
            content={"erro": "FALHA_RESTAURACAO", "mensagem": str(e)}
        )