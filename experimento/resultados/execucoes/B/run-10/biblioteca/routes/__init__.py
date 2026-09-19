"""Reúne e expõe todos os blueprints de rotas da API."""

from .books import books_bp
from .users import users_bp
from .loans import loans_bp

__all__ = ["books_bp", "users_bp", "loans_bp"]
