import requests
from typing import Dict, Any

# A URL base do servidor de API
BASE_URL = "https://scb-api-g8jr.onrender.com/"

class AluguelMicroserviceClient:

    def get_ciclista(self, ciclista_id: int) -> Dict[str, Any]:
        try:
            response = requests.get(f"{BASE_URL}/ciclista/{ciclista_id}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None # Retorna None se o ciclista não for encontrado
            raise e

    def get_cartao_de_credito(self, ciclista_id: int) -> Dict[str, Any]:
        try:
            response = requests.get(f"{BASE_URL}/cartaoDeCredito/{ciclista_id}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None # Retorna None se o cartão não for encontrado
            raise e