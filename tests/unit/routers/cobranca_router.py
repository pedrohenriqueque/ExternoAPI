import pytest
from unittest.mock import MagicMock
import json
from fastapi import Request

# Supondo que os componentes estejam nestes caminhos
from app.controller.cobranca import (
    realizar_cobranca,
    colocar_cobranca_na_fila,
    obter_cobranca,
    processar_fila
)
from app.services.cobranca_service import CobrancaService
from app.schemas.nova_cobranca_schema import NovaCobrancaSchema
from app.models.cobranca import Cobranca
from app.core.exceptions import CartaoApiError
# Importa o handler de exceção do main.py
from app.main import cartao_api_exception_handler


@pytest.mark.asyncio
class TestCobrancaRouter:
    """
    Testa a camada de router para a funcionalidade de Cobrança,
    verificando a lógica da rota e o tratamento de exceções.
    """

    @pytest.fixture
    def mock_cobranca_service(self) -> MagicMock:
        """Cria um mock para o CobrancaService."""
        return MagicMock(spec=CobrancaService)

    async def test_realizar_cobranca_sucesso(self, mock_cobranca_service: MagicMock):
        """
        Testa o fluxo de sucesso do endpoint 'realizar_cobranca'.
        """
        # Arrange
        dados_cobranca = NovaCobrancaSchema(ciclista=1, valor=100.0)
        cobranca_na_fila = Cobranca(id=1, status="PENDENTE")
        cobranca_processada_final = Cobranca(id=1, status="PAGA")

        mock_cobranca_service.criar_cobranca_na_fila.return_value = cobranca_na_fila
        mock_cobranca_service.processar_pagamento_de_cobranca.return_value = cobranca_processada_final

        # Act
        response = realizar_cobranca(cobranca_data=dados_cobranca, service=mock_cobranca_service)

        # Assert
        mock_cobranca_service.criar_cobranca_na_fila.assert_called_once_with(dados_cobranca)
        mock_cobranca_service.processar_pagamento_de_cobranca.assert_called_once_with(cobranca_na_fila.id)
        assert response is cobranca_processada_final

    async def test_realizar_cobranca_falha_servico_e_handler(self, mock_cobranca_service: MagicMock):
        """
        Testa o fluxo de falha do endpoint 'realizar_cobranca' e o tratamento pelo handler.
        """
        # Arrange
        dados_cobranca = NovaCobrancaSchema(ciclista=1, valor=100.0)
        cobranca_na_fila = Cobranca(id=1, status="PENDENTE")
        expected_error = CartaoApiError(422, "PAGAMENTO_FALHOU", "O pagamento não pôde ser processado.")

        mock_cobranca_service.criar_cobranca_na_fila.return_value = cobranca_na_fila
        mock_cobranca_service.processar_pagamento_de_cobranca.side_effect = expected_error
        mock_request = MagicMock(spec=Request)

        # Act
        try:
            realizar_cobranca(cobranca_data=dados_cobranca, service=mock_cobranca_service)
            pytest.fail("CartaoApiError não foi levantada pela função do router")
        except CartaoApiError as e:
            # Simula o handler do FastAPI a capturar a exceção
            response = await cartao_api_exception_handler(mock_request, e)

        # Assert
        assert response.status_code == 422
        response_body = json.loads(response.body.decode())
        assert response_body["codigo"] == "PAGAMENTO_FALHOU"
        assert response_body["mensagem"] == "O pagamento não pôde ser processado."

    async def test_colocar_cobranca_na_fila_sucesso(self, mock_cobranca_service: MagicMock):
        """
        Testa o fluxo de sucesso do endpoint 'colocar_cobranca_na_fila'.
        """
        # Arrange
        dados_cobranca = NovaCobrancaSchema(ciclista=2, valor=50.0)
        cobranca_criada = Cobranca(id=2, status="PENDENTE")
        mock_cobranca_service.criar_cobranca_na_fila.return_value = cobranca_criada

        # Act
        response = colocar_cobranca_na_fila(cobranca_data=dados_cobranca, service=mock_cobranca_service)

        # Assert
        mock_cobranca_service.criar_cobranca_na_fila.assert_called_once_with(dados_cobranca)
        assert response is cobranca_criada

    async def test_obter_cobranca_sucesso(self, mock_cobranca_service: MagicMock):
        """
        Testa o fluxo de sucesso do endpoint 'obter_cobranca'.
        """
        # Arrange
        id_cobranca = 42
        cobranca_existente = Cobranca(id=id_cobranca, status="PAGA")
        mock_cobranca_service.obter_por_id.return_value = cobranca_existente

        # Act
        response = obter_cobranca(id_cobranca=id_cobranca, service=mock_cobranca_service)

        # Assert
        mock_cobranca_service.obter_por_id.assert_called_once_with(id_cobranca)
        assert response is cobranca_existente

    async def test_obter_cobranca_falha_servico_e_handler(self, mock_cobranca_service: MagicMock):
        """
        Testa se o router propaga a exceção e se o handler a captura corretamente.
        """
        # Arrange
        id_cobranca = 999
        expected_error = CartaoApiError(404, "NAO_ENCONTRADO", "Cobrança não encontrada")
        mock_cobranca_service.obter_por_id.side_effect = expected_error
        mock_request = MagicMock(spec=Request)

        # Act
        try:
            obter_cobranca(id_cobranca=id_cobranca, service=mock_cobranca_service)
            pytest.fail("CartaoApiError não foi levantada pela função do router")
        except CartaoApiError as e:
            # Simula o handler do FastAPI a capturar a exceção
            response = await cartao_api_exception_handler(mock_request, e)

        # Assert
        assert response.status_code == 404
        response_body = json.loads(response.body.decode())
        assert response_body["codigo"] == "NAO_ENCONTRADO"
        assert response_body["mensagem"] == "Cobrança não encontrada"

    async def test_processar_fila_sucesso(self, mock_cobranca_service: MagicMock):
        """
        Testa o fluxo de sucesso do endpoint 'processar_fila'.
        """
        # Arrange
        cobrancas_processadas = [Cobranca(id=1, status="PAGA"), Cobranca(id=2, status="PAGA")]
        mock_cobranca_service.processar_cobrancas_em_fila.return_value = cobrancas_processadas

        # Act
        response = processar_fila(service=mock_cobranca_service)

        # Assert
        mock_cobranca_service.processar_cobrancas_em_fila.assert_called_once()
        assert response is cobrancas_processadas
