"""Ponto de entrada da API REST do sistema de biblioteca.

Aplicação Flask sem autenticação, sem interface gráfica e sem banco de
dados: todos os dados são mantidos em memória (ver storage.py) e são
perdidos quando o processo é encerrado.
"""
from flask import Flask, jsonify

from routes import bp


def criar_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(bp)

    @app.errorhandler(404)
    def nao_encontrado(_erro):
        return jsonify({"erro": "Recurso não encontrado."}), 404

    @app.errorhandler(405)
    def metodo_nao_permitido(_erro):
        return jsonify({"erro": "Método não permitido para este recurso."}), 405

    @app.errorhandler(400)
    def requisicao_invalida(_erro):
        return jsonify({"erro": "Requisição inválida."}), 400

    @app.errorhandler(500)
    def erro_interno(_erro):
        return jsonify({"erro": "Erro interno do servidor."}), 500

    return app


app = criar_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
