from app.models.cobranca import Cobranca
from app.db.session import SessionLocal



def restaurar_dados_iniciais():
    db = SessionLocal()

    try:
        # Remove todas as cobranças existentes
        db.query(Cobranca).delete()
        db.commit()

    finally:
        db.close()
