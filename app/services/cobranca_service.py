
from datetime import datetime, timezone
import stripe
from typing import List

from app.clients.aluguel_client import AluguelMicroserviceClient
from app.repositories.cobranca_repository import CobrancaRepository
from app.integrations.stripe import StripeGateway
from app.models.cobranca import Cobranca
from app.core.exceptions import CartaoApiError
from app.schemas.nova_cobranca_schema import NovaCobrancaSchema
from app.services.email_service import EmailService


class CobrancaService:
    def __init__(self, cobranca_repo: CobrancaRepository, payment_gateway: StripeGateway, email_service: EmailService, aluguel_client: AluguelMicroserviceClient):
        self.cobranca_repo = cobranca_repo
        self.payment_gateway = payment_gateway
        self.email_service = email_service
        self.aluguel_client = aluguel_client


    def _obter_payment_method_id_do_ciclista(self, ciclista_id: int) -> str:
        cartao = self.aluguel_client.get_cartao_de_credito(ciclista_id)
        if not cartao:
            raise CartaoApiError(422,"CICLISTA_SEM_CARTAO", f"Não foi encontrado um cartão para o ciclista {ciclista_id}.")

        # Simulação: Se a API retornou um cartão, consideramos válido para o Stripe
        return "pm_card_visa"

    def _obter_email_do_ciclista(self, ciclista_id: int) -> str | None:
        ciclista = self.aluguel_client.get_ciclista(ciclista_id)
        if not ciclista or not ciclista.get("email"):
            return None
        return ciclista["email"]

    def criar_cobranca_na_fila(self, dados: NovaCobrancaSchema) -> Cobranca:
        hora_solicitacao = datetime.now(timezone.utc)
        nova_cobranca = self.cobranca_repo.criar(dados, hora_solicitacao)
        return self.cobranca_repo.salvar(nova_cobranca)

    def obter_por_id(self, id_cobranca: int) -> Cobranca:
        cobranca = self.cobranca_repo.obter_por_id(id_cobranca)
        if not cobranca:
            raise CartaoApiError(404,"COBRANCA_NAO_ENCONTRADA", f"Cobrança com ID {id_cobranca} não encontrada.")
        return cobranca

    def processar_pagamento_de_cobranca(self, id_cobranca: int) -> Cobranca:

        cobranca = self.obter_por_id(id_cobranca)

        try:
            payment_method_id = self._obter_payment_method_id_do_ciclista(cobranca.ciclista)
            intent = self.payment_gateway.processar_pagamento(
                valor_em_centavos=int(cobranca.valor * 100),
                payment_method_id=payment_method_id
            )
            # Sucesso: A chamada ao gateway não lançou exceção.
            cobranca.status = "PAGA" if intent.status == 'succeeded' else "FALHA"

        except CartaoApiError:
            cobranca.status = "FALHA"
        finally:
            cobranca.horaFinalizacao = datetime.now(timezone.utc)
            self.cobranca_repo.salvar(cobranca)

        return cobranca

    def tentar_cobranca_da_fila(self, cobranca: Cobranca) -> Cobranca | None:
        try:
            payment_method_id = self._obter_payment_method_id_do_ciclista(cobranca.ciclista)
            intent = self.payment_gateway.processar_pagamento(
                valor_em_centavos=int(cobranca.valor * 100),
                payment_method_id=payment_method_id
            )

            if intent.status == "succeeded":
                cobranca.status = "PAGA"
                cobranca.horaFinalizacao = datetime.now(timezone.utc)
                return self.cobranca_repo.salvar(cobranca)

        except (CartaoApiError, stripe.error.StripeError):
            return None

        return None

    def _processar_pagamentos_da_fila(self) -> List[Cobranca]:
        print("Iniciando processamento de pagamentos em fila...")
        lista_cobrancas_pendentes = self.cobranca_repo.listar_pendentes()
        lista_cobrancas_pagas = []
        for cobranca in lista_cobrancas_pendentes:
            resultado = self.tentar_cobranca_da_fila(cobranca)
            if resultado and resultado.status == "PAGA":
                lista_cobrancas_pagas.append(resultado)
        print(f"{len(lista_cobrancas_pagas)} cobranças foram pagas com sucesso.")
        return lista_cobrancas_pagas

    def _enviar_notificacoes_de_pagamento(self, cobrancas_pagas: List[Cobranca]) -> None:

        print(f"Iniciando envio de {len(cobrancas_pagas)} notificações...")
        for cobranca in cobrancas_pagas:
            try:
                destinatario = self._obter_email_do_ciclista(cobranca.ciclista)
                if destinatario:
                    self.email_service.enviar_confirmacao_pagamento(cobranca, destinatario)
            except Exception as e:
                print(f"ALERTA: A notificação para a cobrança {cobranca.id} falhou. Erro: {e}")
        print("Envio de notificações concluído.")

    def processar_cobrancas_em_fila(self) -> List[Cobranca]:

        # Etapa 1: Processar os pagamentos
        cobrancas_pagas = self._processar_pagamentos_da_fila()

        # Etapa 2: Enviar as notificações para os pagamentos bem-sucedidos
        if cobrancas_pagas:
            self._enviar_notificacoes_de_pagamento(cobrancas_pagas)

        # Retorna o resultado da operação principal
        return cobrancas_pagas
