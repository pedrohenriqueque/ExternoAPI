from datetime import datetime, timezone
import stripe
from sqlalchemy.orm import Session


from app.models.cobranca import Cobranca
from app.core.exceptions import CartaoApiError
from typing import Optional
import os

from app.schemas.nova_cobranca_schema import NovaCobrancaSchema

stripe.api_key = os.getenv("STRIPE_API_KEY")

class CobrancaService:
    def __init__(self, db: Session):
        self.db = db

    def criar_cobranca(self, dados: NovaCobrancaSchema) -> Cobranca:
        cobranca_schema = Cobranca(
            ciclista=dados.ciclista,
            valor=dados.valor,
            status="PENDENTE",
        )
        self.db.add(cobranca_schema)
        self.db.commit()
        self.db.refresh(cobranca_schema)
        return cobranca_schema

    def processar_cobranca(self, cobranca: Cobranca) -> Cobranca:
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(cobranca.valor * 100),
                currency="brl",
                payment_method="pm_card_visa_chargeDeclined",
                confirm=True,
                off_session=True,
                capture_method="automatic"
            )

            if intent.status == "succeeded":
                cobranca.status = "PAGA"
            else:
                cobranca.status = "FALHA"

        except stripe.error.CardError as e:
            cobranca.status = "FALHA"
            raise CartaoApiError(422, "CARTAO_RECUSADO", e.user_message)

        except Exception:
            cobranca.status = "FALHA"
            raise CartaoApiError(422, "ERRO_COBRANCA", "Erro ao processar a cobrança.")

        now = datetime.now(timezone.utc).replace(microsecond=0)
        cobranca.horaFinalizacao = now
        self.db.commit()
        self.db.refresh(cobranca)
        return cobranca

    def obter_por_id(self, id_cobranca: int) -> Optional[Cobranca]:
        return self.db.query(Cobranca).filter(Cobranca.id == id_cobranca).first()

    def incluir_na_fila(self, dados: NovaCobrancaSchema) -> Cobranca:
            nova_cobranca = Cobranca(
                ciclista=dados.ciclista,
                valor=dados.valor,
                status="PENDENTE",
                horaSolicitacao=datetime.now()
            )
            self.db.add(nova_cobranca)
            self.db.commit()
            self.db.refresh(nova_cobranca)
            return nova_cobranca

    def processar_cobrancas_em_fila(self):
        cobrancas_pendentes = self.db.query(Cobranca).filter_by(status="PENDENTE").all()
        cobrancas_processadas = []

        for cobranca in cobrancas_pendentes:
            try:
                cobranca_processada = self.processar_cobranca(cobranca)
                cobrancas_processadas.append(cobranca_processada)
            except Exception:
                continue

        return cobrancas_processadas
