# Em app/services/cobranca_service.py (Versão Refatorada)

from datetime import datetime, timezone
import stripe
from typing import List

from app.repositories.cobranca_repository import CobrancaRepository # NOVO
from app.integrations.stripe import StripeGateway
from app.models.cobranca import Cobranca
from app.core.exceptions import CartaoApiError
from app.schemas.nova_cobranca_schema import NovaCobrancaSchema

class CobrancaService:
    def __init__(self, cobranca_repo: CobrancaRepository, payment_gateway: StripeGateway):
        self.cobranca_repo = cobranca_repo
        self.payment_gateway = payment_gateway

    @staticmethod
    def _obter_payment_method_id_do_ciclista(ciclista_id: int) -> str:
        mapa_mock = {
            0: "pm_card_visa",
            1: "pm_card_visa_chargeDeclined",
        }
        payment_method_id = mapa_mock.get(ciclista_id)
        if not payment_method_id:
            raise CartaoApiError(422,"CICLISTA_SEM_CARTAO", f"Não foi encontrado um cartão para o ciclista {ciclista_id}.")
        return payment_method_id

    def criar_cobranca_na_fila(self, dados: NovaCobrancaSchema) -> Cobranca:
        hora_solicitacao = datetime.now(timezone.utc)
        nova_cobranca = self.cobranca_repo.criar(dados, hora_solicitacao)
        return self.cobranca_repo.salvar(nova_cobranca)

    def obter_por_id(self, id_cobranca: int) -> Cobranca:
        cobranca = self.cobranca_repo.obter_por_id(id_cobranca)
        if not cobranca:
            raise CartaoApiError(422,"COBRANCA_NAO_ENCONTRADA", f"Cobrança com ID {id_cobranca} não encontrada.")
        return cobranca

    def processar_pagamento_de_cobranca(self, id_cobranca: int) -> Cobranca:

        cobranca = self.obter_por_id(id_cobranca)

        try:
            payment_method_id = self._obter_payment_method_id_do_ciclista(cobranca.ciclista)
            intent = self.payment_gateway.processar_pagamento(
                valor_em_centavos=int(cobranca.valor * 100),
                payment_method_id=payment_method_id
            )
            cobranca.status = "PAGA" if intent.status == "succeeded" else "FALHA"
        except stripe.error.StripeError as e:
            cobranca.status = "FALHA"
            if isinstance(e, stripe.error.CardError):
                raise CartaoApiError(422, "CARTAO_RECUSADO", e.user_message) from e
            if isinstance(e, stripe.error.StripeError):
                raise CartaoApiError(422, "ERRO_GATEWAY", "Erro de comunicação com o provedor.") from e
            raise e
        finally:
            cobranca.horaFinalizacao = datetime.now(timezone.utc)
            # Apenas um commit ao final da operação de negócio
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

        except (CartaoApiError, stripe.error.StripeError) as e:
            return None

        return None

    def processar_cobrancas_em_fila(self) -> List[Cobranca]:
        lista_cobrancas_pendentes = self.cobranca_repo.listar_pendentes()
        lista_cobrancas_pagas = []

        for cobranca in lista_cobrancas_pendentes:
            resultado = self.tentar_cobranca_da_fila(cobranca)
            if resultado and resultado.status == "PAGA":
                lista_cobrancas_pagas.append(resultado)

        return lista_cobrancas_pagas