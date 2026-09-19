"""Armazenamento em memória do sistema de biblioteca.

Não há uso de banco de dados: todos os dados vivem em dicionários em memória
enquanto o processo da aplicação estiver em execução.
"""

import itertools
from typing import Dict

from models import Book, Loan, User


class Storage:
    """Contêiner simples para os dados em memória da aplicação."""

    def __init__(self) -> None:
        self.books: Dict[int, Book] = {}
        self.users: Dict[int, User] = {}
        self.loans: Dict[int, Loan] = {}

        self._book_id_seq = itertools.count(1)
        self._user_id_seq = itertools.count(1)
        self._loan_id_seq = itertools.count(1)

    def next_book_id(self) -> int:
        return next(self._book_id_seq)

    def next_user_id(self) -> int:
        return next(self._user_id_seq)

    def next_loan_id(self) -> int:
        return next(self._loan_id_seq)


# Instância única compartilhada por toda a aplicação (estado global em memória).
storage = Storage()
