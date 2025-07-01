# tests/integration/test_seed.py
import pytest
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import engine, SessionLocal
from app.db.base_class import Base
from app.db.seed import restaurar_dados_iniciais # Importa a função refatorada
from app.models.cobranca import Cobranca

@pytest.fixture(scope="function")
def db_session() -> Session:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_restaurar_dados_iniciais_apaga_dados_antigos(db_session: Session):
    # Arrange: Adiciona um dado antigo
    cobranca_antiga = Cobranca(id=999, ciclista=99, valor=1.00, status="PAGA", horaSolicitacao=datetime.now())
    db_session.add(cobranca_antiga)
    db_session.commit()
    assert db_session.query(Cobranca).count() == 1

    # Act: Chama a função passando a sessão do teste
    restaurar_dados_iniciais(db_session)

    # Assert: Verifica o resultado na mesma sessão
    assert db_session.query(Cobranca).count() == 4
    assert db_session.query(Cobranca).filter_by(id=999).first() is None