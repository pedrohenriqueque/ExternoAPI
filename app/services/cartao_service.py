from app.api.v1.schemas.cartao_schema import NovoCartaoDeCreditoSchema

class CartaoService:
    async def validar_cartao(self, dados_cartao: NovoCartaoDeCreditoSchema) -> bool:
        """
        Simula a validação de um cartão de crédito.
        Em um cenário real, aqui você chamaria um SDK de gateway de pagamento.
        """
        print(f"Simulando validação para o cartão terminado em: {dados_cartao.numero[-4:]}")
        print(f"Nome do Titular: {dados_cartao.nomeTitular}")
        print(f"Validade: {dados_cartao.validade}")
        print(f"CVV: {dados_cartao.cvv}")

        return True #

cartao_service_instance = CartaoService()