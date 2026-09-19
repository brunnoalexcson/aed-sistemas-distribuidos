"""Exceções customizadas usadas para sinalizar erros de negócio da API.

Cada exceção carrega o código HTTP que deve ser retornado ao cliente,
permitindo que a camada de rotas trate os erros de forma centralizada.
"""


class ErroApi(Exception):
    """Erro genérico da API, com código de status HTTP associado."""

    status_code = 400

    def __init__(self, mensagem: str, status_code: int = None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        if status_code is not None:
            self.status_code = status_code

    def to_dict(self) -> dict:
        return {"erro": self.mensagem}


class NaoEncontrado(ErroApi):
    """Recurso solicitado não existe (HTTP 404)."""

    status_code = 404


class RequisicaoInvalida(ErroApi):
    """Dados de entrada ausentes ou inválidos (HTTP 400)."""

    status_code = 400


class ConflitoDeRegra(ErroApi):
    """Violação de alguma regra de negócio (HTTP 409)."""

    status_code = 409
