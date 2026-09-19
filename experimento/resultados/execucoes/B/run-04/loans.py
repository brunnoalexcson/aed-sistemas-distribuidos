"""Rotas relacionadas a empréstimos e devoluções de livros."""

from datetime import date, timedelta

from flask import Blueprint, jsonify, request

from books import get_book_or_404
from errors import ConflictError, NotFoundError, ValidationError
from models import (
    FINE_PER_DAY_LATE,
    LOAN_PERIOD_DAYS,
    MAX_LOANS_PER_USER,
    Loan,
    storage,
)
from users import get_user_or_404

loans_bp = Blueprint("loans", __name__, url_prefix="/loans")


def get_loan_or_404(loan_id: int) -> Loan:
    loan = storage.loans.get(loan_id)
    if loan is None:
        raise NotFoundError(f"Empréstimo com id {loan_id} não encontrado.")
    return loan


def _count_open_loans(user_id: int) -> int:
    return sum(
        1
        for loan in storage.loans.values()
        if loan.user_id == user_id and loan.status == "open"
    )


@loans_bp.post("")
def create_loan():
    """Registra um novo empréstimo de livro para um usuário.

    Regras aplicadas:
    - o livro precisa existir e estar disponível;
    - o usuário precisa existir e estar ativo;
    - o usuário não pode ter multa pendente;
    - o usuário não pode ter mais de 3 empréstimos em aberto.
    """
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        raise ValidationError("Corpo da requisição deve ser um JSON válido.")

    book_id = data.get("book_id")
    user_id = data.get("user_id")
    if not isinstance(book_id, int) or isinstance(book_id, bool):
        raise ValidationError("O campo 'book_id' é obrigatório e deve ser um inteiro.")
    if not isinstance(user_id, int) or isinstance(user_id, bool):
        raise ValidationError("O campo 'user_id' é obrigatório e deve ser um inteiro.")

    book = get_book_or_404(book_id)
    user = get_user_or_404(user_id)

    if not book.available:
        raise ConflictError("Este livro já está emprestado no momento.")

    if not user.active:
        raise ConflictError("Usuário inativo não pode pegar livro emprestado.")

    if user.fine_balance > 0:
        raise ConflictError(
            "Usuário possui multa pendente e está impedido de pegar livros "
            "emprestados até quitá-la."
        )

    if _count_open_loans(user_id) >= MAX_LOANS_PER_USER:
        raise ConflictError(
            f"Usuário já atingiu o limite de {MAX_LOANS_PER_USER} livros "
            "emprestados ao mesmo tempo."
        )

    today = date.today()
    loan_id = storage.next_loan_id()
    loan = Loan(
        id=loan_id,
        book_id=book_id,
        user_id=user_id,
        loan_date=today,
        due_date=today + timedelta(days=LOAN_PERIOD_DAYS),
    )
    storage.loans[loan_id] = loan
    book.available = False

    return jsonify(loan.to_dict()), 201


@loans_bp.get("")
def list_loans():
    """Lista todos os empréstimos, com filtro opcional por status."""
    status_filter = request.args.get("status")
    loans = list(storage.loans.values())

    if status_filter:
        status_filter = status_filter.strip().lower()
        if status_filter not in ("open", "returned"):
            raise ValidationError("O parâmetro 'status' deve ser 'open' ou 'returned'.")
        loans = [loan for loan in loans if loan.status == status_filter]

    loans.sort(key=lambda loan: loan.id)
    return jsonify([loan.to_dict() for loan in loans]), 200


@loans_bp.get("/<int:loan_id>")
def get_loan(loan_id: int):
    """Busca um empréstimo específico pelo id."""
    loan = get_loan_or_404(loan_id)
    return jsonify(loan.to_dict()), 200


@loans_bp.post("/<int:loan_id>/return")
def return_loan(loan_id: int):
    """Registra a devolução de um livro.

    O livro volta a ficar disponível. Se a devolução ocorrer após o
    prazo, é calculada uma multa de R$ 1,50 por dia de atraso, que fica
    pendente na conta do usuário.
    """
    loan = get_loan_or_404(loan_id)
    if loan.status == "returned":
        raise ConflictError("Este empréstimo já foi devolvido anteriormente.")

    today = date.today()
    loan.return_date = today

    days_late = (today - loan.due_date).days
    if days_late > 0:
        fine = round(days_late * FINE_PER_DAY_LATE, 2)
        loan.fine_amount = fine
        user = storage.users.get(loan.user_id)
        if user is not None:
            user.fine_balance = round(user.fine_balance + fine, 2)

    book = storage.books.get(loan.book_id)
    if book is not None:
        book.available = True

    return jsonify(loan.to_dict()), 200
