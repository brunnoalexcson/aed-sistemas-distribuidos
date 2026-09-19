"""Modelos de dados e repositório em memória do sistema de biblioteca."""

from dataclasses import dataclass
from datetime import date
from itertools import count
from typing import Dict, Optional

# Regras de negócio da biblioteca
LOAN_PERIOD_DAYS = 14
MAX_LOANS_PER_USER = 3
FINE_PER_DAY_LATE = 1.50


@dataclass
class Book:
    id: int
    title: str
    author: str
    isbn: str
    available: bool = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "isbn": self.isbn,
            "available": self.available,
        }


@dataclass
class User:
    id: int
    name: str
    email: str
    active: bool = True
    fine_balance: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "active": self.active,
            "fine_balance": round(self.fine_balance, 2),
        }


@dataclass
class Loan:
    id: int
    book_id: int
    user_id: int
    loan_date: date
    due_date: date
    return_date: Optional[date] = None
    fine_amount: float = 0.0

    @property
    def status(self) -> str:
        return "returned" if self.return_date is not None else "open"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "book_id": self.book_id,
            "user_id": self.user_id,
            "loan_date": self.loan_date.isoformat(),
            "due_date": self.due_date.isoformat(),
            "return_date": self.return_date.isoformat() if self.return_date else None,
            "fine_amount": round(self.fine_amount, 2),
            "status": self.status,
        }


class Storage:
    """Repositório em memória para livros, usuários e empréstimos.

    Não há persistência em banco de dados: todos os dados vivem apenas
    enquanto o processo da aplicação estiver em execução.
    """

    def __init__(self) -> None:
        self.books: Dict[int, Book] = {}
        self.users: Dict[int, User] = {}
        self.loans: Dict[int, Loan] = {}
        self._book_ids = count(1)
        self._user_ids = count(1)
        self._loan_ids = count(1)

    def next_book_id(self) -> int:
        return next(self._book_ids)

    def next_user_id(self) -> int:
        return next(self._user_ids)

    def next_loan_id(self) -> int:
        return next(self._loan_ids)


# Instância única de armazenamento compartilhada por toda a aplicação.
storage = Storage()
