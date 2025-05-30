from app.api.v1.schemas.cartao_schema import NovoCartaoDeCreditoSchema

class CartaoService:
    async def validar_cartao_simulado(self, dados_cartao: NovoCartaoDeCreditoSchema) -> bool:
        """
        Simula a validação de um cartão de crédito.
        Em um cenário real, aqui você chamaria um SDK de gateway de pagamento.
        """
        print(f"Simulando validação para o cartão terminado em: {dados_cartao.numero[-4:]}")
        print(f"Nome do Titular: {dados_cartao.nomeTitular}")
        print(f"Validade: {dados_cartao.validade}")
        print(f"CVV: {dados_cartao.cvv}")

        # Lógica de simulação simples:
        # Por exemplo, recusar cartões terminados em "0000" para simular falha.
        if dados_cartao.numero.endswith("0000"):
            print("Simulação: Cartão REJEITADO (termina em 0000)")
            return False # Simula cartão inválido

        # Poderia adicionar outras lógicas, como verificar o CVV com base no número, etc.
        print("Simulação: Cartão ACEITO")
        return True # Simula cartão válido

cartao_service_instance = CartaoService()