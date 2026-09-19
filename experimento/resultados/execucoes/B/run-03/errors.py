"""Erros customizados da API da biblioteca.

Todos os erros de negócio e de validação são representados por ApiError
(ou subclasses), que carregam o código de status HTTP apropriado e uma
mensagem amigável, para serem convertidos em respostas JSON consistentes
pelo error handler registrado em app.py.
"""


class ApiError(Exception):
    """Erro genérico da API, com status HTTP e mensagem associados."""

    status_code = 400

    def __init__(self, message: str, status_code: int = None, payload: dict = None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self) -> dict:
        body = dict(self.payload or {})
        body["erro"] = self.message
        return body


class ValidationError(ApiError):
    """Dados de entrada inválidos ou ausentes (HTTP 400)."""

    status_code = 400


class NotFoundError(ApiError):
    """Recurso solicitado não existe (HTTP 404)."""

    status_code = 404


class ConflictError(ApiError):
    """Violação de regra de negócio (HTTP 409)."""

    status_code = 409
