from app.models.cobranca import Cobranca
from app.db.session import SessionLocal
from datetime import datetime, timezone


def restaurar_dados_iniciais():
    db = SessionLocal()

    try:
        # Remove todas as cobranças existentes
        db.query(Cobranca).delete()

        # Lista de exemplos
        exemplos = [
            Cobranca(ciclista=0, valor=49.90, status="PENDENTE", horaSolicitacao=datetime.now(timezone.utc)),  # Deve passar (pm_card_visa)
            Cobranca(ciclista=1, valor=75.00, status="PENDENTE", horaSolicitacao=datetime.now(timezone.utc)),  # Deve falhar (pm_card_visa_chargeDeclined)
            Cobranca(ciclista=0, valor=29.99, status="PENDENTE", horaSolicitacao=datetime.now(timezone.utc)),
            Cobranca(ciclista=1, valor=150.00, status="PENDENTE", horaSolicitacao=datetime.now(timezone.utc)),
        ]

        # Inserção em lote
        db.add_all(exemplos)
        db.commit()

    finally:
        db.close()
