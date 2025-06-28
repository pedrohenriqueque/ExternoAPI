# Em app/repositories/cobranca_repository.py

from sqlalchemy.orm import Session
from typing import List
from app.models.cobranca import Cobranca
from app.schemas.nova_cobranca_schema import NovaCobrancaSchema

class CobrancaRepository:
    def __init__(self, db: Session):
        self.db = db

    def criar(self, dados: NovaCobrancaSchema, hora_solicitacao) -> Cobranca:
        cobranca_db = Cobranca(
            ciclista=dados.ciclista,
            valor=dados.valor,
            status="PENDENTE",
            horaSolicitacao=hora_solicitacao
        )
        self.db.add(cobranca_db)
        return cobranca_db

    def obter_por_id(self, id_cobranca: int) -> Cobranca | None:
        return self.db.query(Cobranca).filter(Cobranca.id == id_cobranca).first()

    def listar_pendentes(self) -> List[Cobranca]:
        return self.db.query(Cobranca).filter_by(status="PENDENTE").all()

    def salvar(self, cobranca: Cobranca) -> Cobranca:
        self.db.add(cobranca)
        self.db.commit()
        self.db.refresh(cobranca)
        return cobranca