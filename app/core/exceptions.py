class CartaoApiError(Exception):
    def __init__(self, status_code: int, codigo: str, mensagem: str):
        self.status_code = status_code
        self.codigo = codigo
        self.mensagem = mensagem