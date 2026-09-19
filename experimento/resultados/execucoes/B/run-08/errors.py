"""Exceções da API e utilitário de registro do tratamento de erros no Flask."""

from flask import jsonify


class ApiError(Exception):
    """Erro genérico da API, associado a um código de status HTTP."""

    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class NotFoundError(ApiError):
    """Recurso solicitado não existe (HTTP 404)."""

    def __init__(self, message: str) -> None:
        super().__init__(message, 404)


class ValidationError(ApiError):
    """Dados de entrada inválidos ou incompletos (HTTP 400)."""

    def __init__(self, message: str) -> None:
        super().__init__(message, 400)


class ConflictError(ApiError):
    """Operação viola alguma regra de negócio (HTTP 409)."""

    def __init__(self, message: str) -> None:
        super().__init__(message, 409)


def register_error_handlers(app) -> None:
    """Registra os handlers de erro padronizados da API no app Flask."""

    @app.errorhandler(ApiError)
    def handle_api_error(error: ApiError):
        return jsonify({"erro": error.message}), error.status_code

    @app.errorhandler(404)
    def handle_not_found(_error):
        return jsonify({"erro": "recurso não encontrado"}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(_error):
        return jsonify({"erro": "método não permitido para este recurso"}), 405

    @app.errorhandler(500)
    def handle_internal_error(_error):
        return jsonify({"erro": "erro interno do servidor"}), 500
