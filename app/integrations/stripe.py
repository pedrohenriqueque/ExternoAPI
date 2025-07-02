import stripe
from typing import Any, Dict
from app.core.exceptions import CartaoApiError  # para lançar erros personalizados

class StripeGateway:

    @staticmethod
    def processar_pagamento(valor_em_centavos: int, payment_method_id: str) -> Any:
        try:
            return stripe.PaymentIntent.create(
                amount=valor_em_centavos,
                currency="brl",
                payment_method=payment_method_id,
                confirm=True,
                off_session=True,
                return_url="https://seu-dominio.com/cobranca-retorno"
            )
        except stripe.error.CardError:

            raise CartaoApiError(422, "CARTAO_RECUSADO", "O Cartão foi recusado")
        except stripe.error.StripeError:
            raise CartaoApiError(422, "ERRO_GATEWAY", "Ocorreu uma falha de comunicação com o provedor de pagamento.")

    @staticmethod
    def _obter_id_metodo_pagamento_teste(numero_cartao: str) -> str:
        numero_limpo = numero_cartao.replace(" ", "")
        mapa_testes: Dict[str, str] = {
            "4242424242424242": "pm_card_visa",
            "4000000000000002": "pm_card_visa_chargeDeclined",
        }
        payment_method_id = mapa_testes.get(numero_limpo)

        if not payment_method_id:
            raise CartaoApiError(422,"CARTAO_NAO_MAPEADO","Esse cartão não foi mapeado")

        return payment_method_id

    @staticmethod
    def _validar_metodo_de_pagamento_na_stripe(payment_method_id: str) -> None:
        try:
            return_url = "https://seu-dominio.com/validacao-retorno"

            stripe.SetupIntent.create(
                payment_method=payment_method_id,
                confirm=True,
                usage="off_session",
                return_url=return_url
            )

        except stripe.error.CardError:
            raise CartaoApiError(422, "CARTAO_RECUSADO", "O cartão foi recusado.")
        except stripe.error.StripeError:
            raise CartaoApiError(422, "ERRO_GATEWAY", "Erro inesperado ao validar o cartão com o provedor.")


    @staticmethod
    def validar_cartao(numero_cartao: str) -> None:

        # Etapa 1: Obter o ID a partir do número de teste
        payment_method_id = StripeGateway._obter_id_metodo_pagamento_teste(numero_cartao)

        # Etapa 2: Validar o ID com a Stripe
        StripeGateway._validar_metodo_de_pagamento_na_stripe(payment_method_id)
