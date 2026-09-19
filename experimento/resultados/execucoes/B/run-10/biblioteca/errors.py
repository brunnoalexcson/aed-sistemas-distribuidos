"""Exceções de domínio e tratadores de erro HTTP da API.

As rotas levantam as exceções definidas aqui sempre que uma regra de
negócio é violada ou um recurso não é encontrado. O Flask então converte
essas exceções em respostas JSON com o código HTTP apropriado.
"""

from flask import Flask, jsonify


class ErroDeAplicacao(Exception):
    """Classe base para erros de negócio da aplicação."""

    status_code = 400

    def __init__(self, mensagem: str):
        super().__init__(mensagem)
        self.mensagem = mensagem


class ErroDeValidacao(ErroDeAplicacao):
    """Dados de entrada inválidos ou incompletos (HTTP 400)."""

    status_code = 400


class RecursoNaoEncontrado(ErroDeAplicacao):
    """Recurso solicitado não existe (HTTP 404)."""

    status_code = 404


class ConflitoDeRegra(ErroDeAplicacao):
    """Ação viola uma regra de negócio do domínio (HTTP 409)."""

    status_code = 409


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ErroDeAplicacao)
    def handle_erro_de_aplicacao(erro: ErroDeAplicacao):
        response = jsonify({"erro": erro.mensagem})
        response.status_code = erro.status_code
        return response

    @app.errorhandler(404)
    def handle_not_found(_erro):
        response = jsonify({"erro": "Recurso ou rota não encontrada."})
        response.status_code = 404
        return response

    @app.errorhandler(405)
    def handle_method_not_allowed(_erro):
        response = jsonify({"erro": "Método HTTP não permitido para esta rota."})
        response.status_code = 405
        return response

    @app.errorhandler(Exception)
    def handle_generic_exception(erro: Exception):
        if isinstance(erro, ErroDeAplicacao):
            return handle_erro_de_aplicacao(erro)
        response = jsonify({"erro": "Erro interno do servidor.", "detalhe": str(erro)})
        response.status_code = 500
        return response
