"""Pacote da API REST do Sistema de Biblioteca.

Expõe a função `create_app`, responsável por montar a aplicação Flask,
registrar as rotas (blueprints) e os tratadores de erro, e inicializar
o armazenamento em memória usado por toda a aplicação.
"""

from flask import Flask

from .storage import Storage
from .services import LibraryService
from .errors import register_error_handlers
from .routes import books_bp, users_bp, loans_bp


def create_app() -> Flask:
    """Cria e configura a aplicação Flask.

    Todo o estado (livros, usuários e empréstimos) é mantido em memória,
    através de uma instância de `Storage` e de `LibraryService` associadas
    à aplicação (`app.extensions`). Não há persistência em banco de dados.
    """
    app = Flask(__name__)
    app.url_map.strict_slashes = False

    storage = Storage()
    service = LibraryService(storage)

    # Disponibiliza o serviço para as rotas através do contexto da app.
    app.extensions["library_service"] = service

    app.register_blueprint(books_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(loans_bp)

    register_error_handlers(app)

    @app.get("/")
    def index():
        return {
            "servico": "Sistema de Biblioteca",
            "status": "ok",
            "recursos": ["/livros", "/usuarios", "/emprestimos"],
        }

    return app
