from datetime import datetime, timezone
import stripe
from sqlalchemy.orm import Session
from typing import Optional, List

from app.integrations.stripe import StripeGateway
from app.models.cobranca import Cobranca
from app.core.exceptions import CartaoApiError
from app.schemas.nova_cobranca_schema import NovaCobrancaSchema


class CobrancaService:
    mapa_ciclista_para_cartao = {
        0: "pm_card_visa",
        1: "pm_card_visa_chargeDeclined",
    }

    def __init__(self, db: Session, payment_gateway: StripeGateway):
        self.db = db
        self.payment_gateway = payment_gateway

    def criar_cobranca(self, dados: NovaCobrancaSchema) -> Cobranca:
        cobranca_schema = Cobranca(
            ciclista=dados.ciclista,
            valor=dados.valor,
            status="PENDENTE",
            horaSolicitacao=datetime.now(timezone.utc)
        )
        self.db.add(cobranca_schema)
        self.db.commit()
        self.db.refresh(cobranca_schema)
        return cobranca_schema

    def obter_por_id(self, id_cobranca: int) -> Optional[Cobranca]:
        return self.db.query(Cobranca).filter(Cobranca.id == id_cobranca).first()

    def incluir_na_fila(self, dados: NovaCobrancaSchema) -> Cobranca:
        return self.criar_cobranca(dados)

    def tentar_processar_pagamento(self, cobranca: Cobranca) -> str:
        payment_method_id = self.mapa_ciclista_para_cartao.get(cobranca.ciclista)
        if not payment_method_id:
            raise CartaoApiError(422, "CICLISTA_SEM_CARTAO", f"Não foi encontrado um cartão para o ciclista {cobranca.ciclista}.")

        try:
            intent = self.payment_gateway.processar_pagamento(
                valor_em_centavos=int(cobranca.valor * 100),
                payment_method_id=payment_method_id
            )
            return intent.status
        except stripe.error.CardError as e:
            raise CartaoApiError(422, "CARTAO_RECUSADO", e.user_message)
        except stripe.error.StripeError:
            raise CartaoApiError(500, "ERRO_GATEWAY", "Erro de comunicação com o provedor de pagamento.")

    def processar_cobranca(self, cobranca: Cobranca) -> Cobranca:
        try:
            status = self.tentar_processar_pagamento(cobranca)
            cobranca.status = "PAGA" if status == "succeeded" else "FALHA"
        except CartaoApiError as e:
            cobranca.status = "FALHA"
            raise e
        finally:
            cobranca.horaFinalizacao = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(cobranca)

        return cobranca

    def processar_cobranca_em_fila(self, cobranca: Cobranca) -> Optional[Cobranca]:
        try:
            status = self.tentar_processar_pagamento(cobranca)
            if status == "succeeded":
                cobranca.status = "PAGA"
                cobranca.horaFinalizacao = datetime.now(timezone.utc)
                self.db.commit()
                self.db.refresh(cobranca)
                return cobranca
        except CartaoApiError:
            # Ignora erro e mantém pendente
            pass
        return None

    def processar_cobrancas_em_fila(self) -> List[Cobranca]:
        cobrancas_pendentes = self.db.query(Cobranca).filter_by(status="PENDENTE").all()
        cobrancas_processadas = []

        for cobranca in cobrancas_pendentes:
            resultado = self.processar_cobranca_em_fila(cobranca)
            if resultado:
                cobrancas_processadas.append(resultado)

        return cobrancas_processadas
