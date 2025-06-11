import os
import stripe
from dotenv import load_dotenv
from app.schemas.cartao_schema import NovoCartaoDeCreditoSchema
from app.core.exceptions import CartaoApiError

# --- Configuração ---
# Garanta que esta configuração seja executada quando sua aplicação iniciar.
load_dotenv()
stripe.api_key = os.getenv("STRIPE_API_KEY")

if not stripe.api_key:
    raise RuntimeError("Chave da API da Stripe não encontrada. Verifique seu arquivo .env")


class CartaoService:
    """
    Serviço que utiliza o schema inteligente para validar um cartão de crédito.
    A lógica de manipulação de dados de validade foi removida daqui, pois
    o schema agora cuida disso.
    """
    async def validar_cartao(self, dados_cartao: NovoCartaoDeCreditoSchema) -> None:
        """
        Valida um cartão de crédito utilizando os dados já processados pelo schema.
        """
        try:
            # --- PASSO 1: Criar um PaymentMethod ---
            # Usamos diretamente os campos exp_mes e exp_ano que o schema preparou.
            # O serviço não precisa saber como a string "validade" foi processada.
            print("Criando PaymentMethod a partir de dados brutos... (ALERTA PCI)")
            print(dados_cartao)
            print(dados_cartao.exp_mes)
            print(dados_cartao.exp_ano)
            payment_method = stripe.PaymentMethod.create(
                type="card",
                card={
                    "number": dados_cartao.numero,
                    "exp_month": dados_cartao.exp_mes,
                    "exp_year": dados_cartao.exp_ano,
                    "cvc": dados_cartao.cvv,
                },
            )

            # --- PASSO 2: Validar com SetupIntent (lógica inalterada) ---
            print(f"Validando o PaymentMethod {payment_method.id} com um SetupIntent...")
            setup_intent = stripe.SetupIntent.create(
                payment_method=payment_method.id,
                confirm=True,
                usage="off_session"
            )

            if setup_intent.status != 'succeeded':
                failure_reason = setup_intent.last_setup_error.message if setup_intent.last_setup_error else "O cartão foi recusado."
                raise CartaoApiError(422, "CARTAO_RECUSADO", failure_reason)

            print(f"Cartão associado ao PaymentMethod {payment_method.id} validado com sucesso.")

        except stripe.error.CardError as e:
            print(f"Stripe retornou um erro de cartão: {e.user_message}")
            raise CartaoApiError(422, "CARTAO_RECUSADO", e.user_message)
        except stripe.error.StripeError as e:
            print(f"Stripe retornou um erro de API: {e}")
            raise CartaoApiError(503, "ERRO_GATEWAY", "Erro de comunicação com o provedor de pagamento.")
        except Exception as e:
            # Esta exceção agora só pegaria erros inesperados no próprio serviço,
            # não mais erros de validação de formato.
            print(f"Ocorreu um erro inesperado: {e}")
            raise CartaoApiError(500, "ERRO_INTERNO", "Erro inesperado ao validar o cartão.")

# Instância única do serviço para ser usada pelo seu endpoint
cartao_service_instance = CartaoService()