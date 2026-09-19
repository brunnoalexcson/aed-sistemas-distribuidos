"""Ponto de entrada da API REST do sistema de biblioteca.

Aplicação Flask que gerencia acervo de livros, cadastro de usuários e
controle de empréstimos, com todos os dados guardados em memória
(nenhum banco de dados é utilizado). Não há autenticação nem interface
gráfica: trata-se apenas da API.
"""

from flask import Flask, jsonify

from books import books_bp
from errors import register_error_handlers
from loans import loans_bp
from users import users_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.url_map.strict_slashes = False

    register_error_handlers(app)

    app.register_blueprint(books_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(loans_bp)

    @app.get("/")
    def index():
        return (
            jsonify(
                {
                    "service": "Sistema de Biblioteca",
                    "status": "ok",
                    "endpoints": {
                        "books": "/books",
                        "users": "/users",
                        "loans": "/loans",
                    },
                }
            ),
            200,
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
