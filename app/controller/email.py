from fastapi import APIRouter, status
from app.schemas.email_schema import EmailRequest
from app.schemas.error_schema import ErroSchema
from app.services.email_service import EmailService

router = APIRouter(prefix="/enviarEmail", tags=["Externo"])

@router.post(
    "",
    status_code=status.HTTP_200_OK,
    summary="Notificar via email",
    responses={
        status.HTTP_200_OK: {
            "description": "Email Enviado",
            "model": EmailRequest
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "E-mail não existe",
            "model": ErroSchema
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "E-mail com formato inválido",
            "model": ErroSchema
        }
    }
)
def enviar_email(request: EmailRequest):
    EmailService().enviar(
        destinatario=request.destinatario,
        assunto=request.assunto,
        mensagem=request.mensagem
    )