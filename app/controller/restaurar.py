from fastapi import APIRouter, status, Response


# A importação agora fica no topo do arquivo
from app.db.seed import restaurar_dados_iniciais

router = APIRouter()

@router.get(
    "/restaurarBanco",
    tags=["Externo"],
    status_code=status.HTTP_200_OK,
    summary="Restaura o banco de dados para os dados iniciais."
)
def restaurar_banco():
    restaurar_dados_iniciais()
    return Response(status_code=status.HTTP_200_OK)

@router.get(
    "/restaurarDados",
    tags=["Externo"],
    status_code=status.HTTP_200_OK,
    summary="Restaura o banco de dados para os dados iniciais."
)
def restaurar_banco():
    restaurar_dados_iniciais()
    return Response(status_code=status.HTTP_200_OK)