"""Armazenamento em memória para livros, usuários e empréstimos.

Não há persistência em banco de dados: todos os dados vivem apenas
enquanto o processo da aplicação estiver em execução.
"""
import threading
from typing import Dict, List, Optional

from models import Book, Loan, User


class InMemoryStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._books: Dict[int, Book] = {}
        self._users: Dict[int, User] = {}
        self._loans: Dict[int, Loan] = {}
        self._next_book_id = 1
        self._next_user_id = 1
        self._next_loan_id = 1

    # ---------- Books ----------
    def add_book(self, title: str, author: str, isbn: str) -> Book:
        with self._lock:
            book = Book(id=self._next_book_id, title=title, author=author, isbn=isbn)
            self._books[book.id] = book
            self._next_book_id += 1
            return book

    def get_book(self, book_id: int) -> Optional[Book]:
        return self._books.get(book_id)

    def list_books(self) -> List[Book]:
        return list(self._books.values())

    def delete_book(self, book_id: int) -> None:
        with self._lock:
            self._books.pop(book_id, None)

    # ---------- Users ----------
    def add_user(self, name: str, email: str) -> User:
        with self._lock:
            user = User(id=self._next_user_id, name=name, email=email)
            self._users[user.id] = user
            self._next_user_id += 1
            return user

    def get_user(self, user_id: int) -> Optional[User]:
        return self._users.get(user_id)

    def list_users(self) -> List[User]:
        return list(self._users.values())

    # ---------- Loans ----------
    def add_loan(self, book_id: int, user_id: int, loan_date, due_date) -> Loan:
        with self._lock:
            loan = Loan(
                id=self._next_loan_id,
                book_id=book_id,
                user_id=user_id,
                loan_date=loan_date,
                due_date=due_date,
            )
            self._loans[loan.id] = loan
            self._next_loan_id += 1
            return loan

    def get_loan(self, loan_id: int) -> Optional[Loan]:
        return self._loans.get(loan_id)

    def list_loans(self) -> List[Loan]:
        return list(self._loans.values())

    def list_loans_by_user(self, user_id: int) -> List[Loan]:
        return [loan for loan in self._loans.values() if loan.user_id == user_id]

    def list_loans_by_book(self, book_id: int) -> List[Loan]:
        return [loan for loan in self._loans.values() if loan.book_id == book_id]


# Instância única compartilhada por toda a aplicação.
store = InMemoryStore()
