"""API REST em memória para gerenciamento de uma biblioteca.

Este pacote expõe a função `create_app`, responsável por montar a aplicação
Flask com todas as rotas de livros, usuários e empréstimos, além do
tratamento centralizado de erros.
"""

from flask import Flask, jsonify

from .armazenamento import Armazenamento
from .erros import ErroDeAplicacao
from .rotas import criar_blueprint
from .servicos import ServicoDeBiblioteca


def create_app() -> Flask:
    app = Flask(__name__)
    app.url_map.strict_slashes = False

    armazenamento = Armazenamento()
    servico = ServicoDeBiblioteca(armazenamento)

    app.register_blueprint(criar_blueprint(servico))

    @app.errorhandler(ErroDeAplicacao)
    def tratar_erro_de_aplicacao(erro: ErroDeAplicacao):
        resposta = jsonify(erro.to_dict())
        resposta.status_code = erro.status_code
        return resposta

    @app.errorhandler(404)
    def tratar_nao_encontrado(_erro):
        return jsonify({"erro": "Recurso não encontrado."}), 404

    @app.errorhandler(405)
    def tratar_metodo_nao_permitido(_erro):
        return jsonify({"erro": "Método não permitido para este recurso."}), 405

    @app.errorhandler(500)
    def tratar_erro_interno(_erro):
        return jsonify({"erro": "Erro interno do servidor."}), 500

    @app.route("/", methods=["GET"])
    def raiz():
        return jsonify(
            {
                "servico": "API da Biblioteca do Bairro",
                "status": "online",
                "recursos": ["/livros", "/usuarios", "/emprestimos"],
            }
        )

    return app
