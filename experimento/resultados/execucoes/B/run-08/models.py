"""Modelos de dados do sistema de biblioteca.

Todas as entidades são representadas por dataclasses simples e mantidas em
memória (não há persistência em banco de dados).
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Book:
    """Representa um livro do acervo da biblioteca."""

    id: int
    title: str
    author: str
    isbn: str
    available: bool = True


@dataclass
class User:
    """Representa um usuário cadastrado na biblioteca."""

    id: int
    name: str
    email: str
    active: bool = True
    fine_balance: float = 0.0


@dataclass
class Loan:
    """Representa um empréstimo de um livro para um usuário."""

    id: int
    book_id: int
    user_id: int
    loan_date: date
    due_date: date
    return_date: Optional[date] = None
    fine: float = 0.0

    @property
    def is_open(self) -> bool:
        """Indica se o empréstimo ainda está em aberto (não devolvido)."""
        return self.return_date is None
