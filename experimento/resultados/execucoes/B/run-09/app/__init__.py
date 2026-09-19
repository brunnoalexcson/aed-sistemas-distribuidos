"""Fábrica da aplicação Flask do sistema de biblioteca."""

from flask import Flask, jsonify

from app.errors import registrar_tratadores_erro


def criar_app() -> Flask:
    app = Flask(__name__)

    registrar_tratadores_erro(app)

    from app.routes.livros import bp_livros
    from app.routes.usuarios import bp_usuarios
    from app.routes.emprestimos import bp_emprestimos

    app.register_blueprint(bp_livros)
    app.register_blueprint(bp_usuarios)
    app.register_blueprint(bp_emprestimos)

    @app.get("/")
    def raiz():
        return jsonify(
            {
                "servico": "API de biblioteca",
                "status": "online",
                "recursos": ["/livros", "/usuarios", "/emprestimos"],
            }
        ), 200

    return app
