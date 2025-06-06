import stripe
from app.api.v1.schemas.cartao_schema import NovoCartaoDeCreditoSchema
from app.core.exceptions import CartaoApiError

stripe.api_key = "sk_test_51RWQ3aCsgOR6s2Dtnnkx5Ifs52oDuskSc7KpODbfkaUDMuSeYXS8ig0wMfoIsz96snJY3mcWi2xiE1N1a6CTsI6C00ZUnmXM3b"

class CartaoService:
    async def validar_cartao(self, dados: NovoCartaoDeCreditoSchema) -> None:
        try:

            payment_method_id = "pm_card_visa"

            intent = stripe.PaymentIntent.create(
                amount=400,
                currency="brl",
                payment_method=payment_method_id,
                confirm=True,
                off_session=True,
                capture_method="automatic"
            )

            print(f"Stripe status: {intent.status}")
            if intent.status != "succeeded":
                raise CartaoApiError(422, "CARTAO_RECUSADO", "O cartão foi recusado.")

        except stripe.error.CardError as e:
            raise CartaoApiError(422, "CARTAO_RECUSADO", e.user_message)
        except Exception:
            raise CartaoApiError(422, "ERRO_VALIDACAO", "Erro inesperado ao validar o cartão.")

cartao_service_instance = CartaoService()