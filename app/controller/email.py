from fastapi import APIRouter, status
from app.schemas.email_schema import EmailRequest
from app.services.email_service import EmailService

router = APIRouter(prefix="/enviarEmail", tags=["Email"])

@router.post("", status_code=status.HTTP_204_NO_CONTENT)
def enviar_email(request: EmailRequest):
    EmailService().enviar(
        destinatario=request.destinatario,
        assunto=request.assunto,
        mensagem=request.mensagem
    )