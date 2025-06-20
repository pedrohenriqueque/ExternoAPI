# Em app/core/dependencies.py (Versão Refinada)

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.integrations.stripe import StripeGateway
from app.repositories.cobranca_repository import CobrancaRepository
from app.services.cobranca_service import CobrancaService


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_cobranca_repository(db: Session = Depends(get_db)) -> CobrancaRepository:
    return CobrancaRepository(db=db)

def get_cobranca_service(
        repo: CobrancaRepository = Depends(get_cobranca_repository),
        gateway: StripeGateway = Depends(StripeGateway)
) -> CobrancaService:
    return CobrancaService(cobranca_repo=repo, payment_gateway=gateway)