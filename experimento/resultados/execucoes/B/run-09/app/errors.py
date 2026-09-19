"""Exceções customizadas e tratamento de erros da API."""

from flask import jsonify


class ErroApi(Exception):
    """Classe base para erros de negócio da API."""

    status_code = 400

    def __init__(self, mensagem: str, status_code: int = None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        if status_code is not None:
            self.status_code = status_code


class NaoEncontrado(ErroApi):
    """Recurso não encontrado (HTTP 404)."""

    status_code = 404


class RequisicaoInvalida(ErroApi):
    """Dados de entrada inválidos ou incompletos (HTTP 400)."""

    status_code = 400


class ConflitoRegraNegocio(ErroApi):
    """Violação de uma regra de negócio (HTTP 409)."""

    status_code = 409


def registrar_tratadores_erro(app):
    @app.errorhandler(ErroApi)
    def tratar_erro_api(erro: ErroApi):
        resposta = jsonify({"erro": erro.mensagem})
        resposta.status_code = erro.status_code
        return resposta

    @app.errorhandler(404)
    def tratar_404(_erro):
        resposta = jsonify({"erro": "Recurso não encontrado."})
        resposta.status_code = 404
        return resposta

    @app.errorhandler(405)
    def tratar_405(_erro):
        resposta = jsonify({"erro": "Método não permitido para este recurso."})
        resposta.status_code = 405
        return resposta

    @app.errorhandler(500)
    def tratar_500(_erro):
        resposta = jsonify({"erro": "Erro interno do servidor."})
        resposta.status_code = 500
        return resposta
