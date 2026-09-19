"""Exceções da API e tratamento centralizado de erros HTTP."""

from flask import jsonify


class ApiError(Exception):
    """Erro genérico da API, convertido em uma resposta HTTP com JSON."""

    status_code = 400

    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class ValidationError(ApiError):
    """Dados de entrada ausentes ou inválidos (HTTP 400)."""

    status_code = 400


class NotFoundError(ApiError):
    """Recurso (livro, usuário ou empréstimo) inexistente (HTTP 404)."""

    status_code = 404


class ConflictError(ApiError):
    """Violação de regra de negócio (HTTP 409)."""

    status_code = 409


def register_error_handlers(app) -> None:
    @app.errorhandler(ApiError)
    def handle_api_error(error: ApiError):
        response = jsonify({"error": error.message})
        response.status_code = error.status_code
        return response

    @app.errorhandler(404)
    def handle_404(error):
        return jsonify({"error": "Recurso não encontrado."}), 404

    @app.errorhandler(405)
    def handle_405(error):
        return jsonify({"error": "Método não permitido para este recurso."}), 405

    @app.errorhandler(500)
    def handle_500(error):
        return jsonify({"error": "Erro interno do servidor."}), 500
