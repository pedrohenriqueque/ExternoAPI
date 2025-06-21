# app/services/cartao_service.py
from app.integrations.stripe import StripeGateway

from app.schemas.cartao_schema import NovoCartaoDeCreditoSchema
import os
import stripe
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.getenv("STRIPE_API_KEY")



class CartaoService:
    def __init__(self, stripe_gateway: StripeGateway):
        self.gateway = stripe_gateway

    def validar_cartao(self, dados_cartao: NovoCartaoDeCreditoSchema) -> None:
            self.gateway.validar_cartao(dados_cartao.numero)

def get_cartao_service() -> CartaoService:
    gateway = StripeGateway()
    return CartaoService(gateway)
