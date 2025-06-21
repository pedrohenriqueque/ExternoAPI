import stripe
from typing import Any
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
        except (stripe.error.CardError, stripe.error.StripeError) as e:
            print(f"Gateway Error: {e}")
            raise e

    @staticmethod
    def validar_cartao(numero_cartao: str) -> None:
        numero_limpo = numero_cartao.replace(" ", "")
        mapa_testes = {
            "4242424242424242": "pm_card_visa",
            "4000000000000002": "pm_card_visa_chargeDeclined",
        }
        payment_method_id = mapa_testes.get(numero_limpo)

        if not payment_method_id:
            raise CartaoApiError(422, "CARTAO_DE_TESTE_NAO_MAPEADO",
                                 "Este serviço aceita apenas números de cartão de teste pré-definidos (ex: 4242...).")

        try:
            setup_intent = stripe.SetupIntent.create(
                payment_method=payment_method_id,
                confirm=True,
                usage="off_session",
                return_url="https://seu-dominio.com/validacao-retorno"
            )

            if setup_intent.status not in ['succeeded', 'requires_action']:
                failure_reason = setup_intent.last_setup_error.message if setup_intent.last_setup_error else "O cartão foi recusado."
                raise CartaoApiError(422, "CARTAO_RECUSADO", failure_reason)

        except stripe.error.CardError:
            raise CartaoApiError(422, "CARTAO_RECUSADO", "Cartão foi Recusado")
        except Exception as e:
            print(f"Erro inesperado na validação do cartão: {e}")
            raise CartaoApiError(422, "ERRO_INTERNO", "Erro inesperado ao validar o cartão.")
