"""Regras de negócio do sistema de biblioteca.

Concentra as validações e as regras descritas na especificação:
- cadastro de livros e usuários;
- controle de disponibilidade de livros;
- limite de 3 empréstimos ativos por usuário;
- bloqueio de usuário inativo ou com multa pendente;
- prazo de devolução de 14 dias;
- cálculo de multa de R$ 1,50 por dia de atraso;
- quitação de multas.
"""
from datetime import datetime, timedelta
from typing import List, Optional

from errors import ConflictError, NotFoundError, ValidationError
from models import Book, Loan, User
from storage import store

LOAN_PERIOD_DAYS = 14
MAX_ACTIVE_LOANS = 3
FINE_PER_DAY = 1.50


def _require_str(value, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(
            f"Campo '{field_name}' é obrigatório e deve ser um texto não vazio."
        )
    return value.strip()


def _require_int(value, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"Campo '{field_name}' é obrigatório e deve ser um número inteiro.")
    return value


# ---------- Books ----------
def create_book(data: dict) -> Book:
    if not isinstance(data, dict):
        raise ValidationError("Corpo da requisição inválido.")
    title = _require_str(data.get("title"), "title")
    author = _require_str(data.get("author"), "author")
    isbn = _require_str(data.get("isbn"), "isbn")
    return store.add_book(title=title, author=author, isbn=isbn)


def list_books() -> List[Book]:
    return store.list_books()


def get_book(book_id: int) -> Book:
    book = store.get_book(book_id)
    if book is None:
        raise NotFoundError(f"Livro com id {book_id} não encontrado.")
    return book


def delete_book(book_id: int) -> None:
    book = get_book(book_id)
    if not book.available:
        raise ConflictError(
            "Não é possível excluir um livro que está emprestado no momento."
        )
    store.delete_book(book_id)


# ---------- Users ----------
def create_user(data: dict) -> User:
    if not isinstance(data, dict):
        raise ValidationError("Corpo da requisição inválido.")
    name = _require_str(data.get("name"), "name")
    email = _require_str(data.get("email"), "email")
    return store.add_user(name=name, email=email)


def list_users() -> List[User]:
    return store.list_users()


def get_user(user_id: int) -> User:
    user = store.get_user(user_id)
    if user is None:
        raise NotFoundError(f"Usuário com id {user_id} não encontrado.")
    return user


def update_user(user_id: int, data: dict) -> User:
    user = get_user(user_id)
    if not isinstance(data, dict):
        raise ValidationError("Corpo da requisição inválido.")
    if "name" in data:
        user.name = _require_str(data.get("name"), "name")
    if "email" in data:
        user.email = _require_str(data.get("email"), "email")
    if "active" in data:
        if not isinstance(data.get("active"), bool):
            raise ValidationError("Campo 'active' deve ser um booleano.")
        user.active = data.get("active")
    return user


def pay_fine(user_id: int) -> User:
    user = get_user(user_id)
    user.pending_fine = 0.0
    return user


# ---------- Loans ----------
def create_loan(data: dict) -> Loan:
    if not isinstance(data, dict):
        raise ValidationError("Corpo da requisição inválido.")
    book_id = _require_int(data.get("book_id"), "book_id")
    user_id = _require_int(data.get("user_id"), "user_id")

    book = get_book(book_id)
    user = get_user(user_id)

    if not book.available:
        raise ConflictError("Livro indisponível para empréstimo no momento.")
    if not user.active:
        raise ConflictError("Usuário inativo não pode pegar livro emprestado.")
    if user.pending_fine > 0:
        raise ConflictError(
            "Usuário possui multa pendente e está impedido de pegar livros emprestados."
        )

    active_loans = [
        loan for loan in store.list_loans_by_user(user_id) if loan.status == "open"
    ]
    if len(active_loans) >= MAX_ACTIVE_LOANS:
        raise ConflictError(
            f"Usuário já possui o máximo de {MAX_ACTIVE_LOANS} livros emprestados."
        )

    loan_date = datetime.now()
    due_date = loan_date + timedelta(days=LOAN_PERIOD_DAYS)
    loan = store.add_loan(
        book_id=book_id, user_id=user_id, loan_date=loan_date, due_date=due_date
    )
    book.available = False
    return loan


def list_loans() -> List[Loan]:
    return store.list_loans()


def get_loan(loan_id: int) -> Loan:
    loan = store.get_loan(loan_id)
    if loan is None:
        raise NotFoundError(f"Empréstimo com id {loan_id} não encontrado.")
    return loan


def return_loan(loan_id: int) -> Loan:
    loan = get_loan(loan_id)
    if loan.status == "returned":
        raise ConflictError("Este empréstimo já foi devolvido anteriormente.")

    return_date = datetime.now()
    loan.return_date = return_date
    loan.status = "returned"

    if return_date > loan.due_date:
        days_late = (return_date.date() - loan.due_date.date()).days
        fine = round(days_late * FINE_PER_DAY, 2)
        loan.fine_amount = fine
        user = get_user(loan.user_id)
        user.pending_fine = round(user.pending_fine + fine, 2)

    book = get_book(loan.book_id)
    book.available = True
    return loan


def list_user_loans(user_id: int, status: Optional[str] = None) -> List[Loan]:
    get_user(user_id)  # garante que o usuário existe, senão levanta NotFoundError
    loans = store.list_loans_by_user(user_id)
    if status:
        if status not in ("open", "returned"):
            raise ValidationError("Parâmetro 'status' deve ser 'open' ou 'returned'.")
        loans = [loan for loan in loans if loan.status == status]
    return loans
