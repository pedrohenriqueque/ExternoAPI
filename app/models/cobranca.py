from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.sql import func
from app.db.base_class import Base

class Cobranca(Base):
    __tablename__ = "cobrancas"

    id = Column(Integer, primary_key=True, index=True)
    ciclista = Column(Integer, nullable=False)
    valor = Column(Float, nullable=False)
    status = Column(String(20), nullable=False, index=True)  # PENDENTE, PAGA, FALHA etc
    horaSolicitacao = Column(DateTime(timezone=True), server_default=func.now())
    horaFinalizacao = Column(DateTime(timezone=True), nullable=True)