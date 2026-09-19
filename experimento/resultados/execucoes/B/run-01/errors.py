"""Exceções customizadas e tratamento de erros da API."""
from flask import jsonify


class ApiError(Exception):
    """Erro base da API. Carrega uma mensagem e um código de status HTTP."""

    status_code = 400

    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class NotFoundError(ApiError):
    """Recurso solicitado não existe (HTTP 404)."""

    status_code = 404


class ValidationError(ApiError):
    """Dados de entrada inválidos ou incompletos (HTTP 400)."""

    status_code = 400


class ConflictError(ApiError):
    """Violação de uma regra de negócio (HTTP 409)."""

    status_code = 409


def register_error_handlers(app):
    """Registra os handlers de erro na aplicação Flask."""

    @app.errorhandler(ApiError)
    def handle_api_error(error: ApiError):
        response = jsonify({"error": error.message})
        response.status_code = error.status_code
        return response

    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({"error": "Recurso não encontrado."}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        return jsonify({"error": "Método não permitido para este recurso."}), 405

    @app.errorhandler(400)
    def handle_bad_request(error):
        return jsonify({"error": "Requisição inválida."}), 400

    @app.errorhandler(500)
    def handle_internal_error(error):
        return jsonify({"error": "Erro interno do servidor."}), 500
