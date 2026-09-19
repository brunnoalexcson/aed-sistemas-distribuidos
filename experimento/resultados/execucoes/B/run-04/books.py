"""Rotas relacionadas ao acervo de livros da biblioteca."""

from flask import Blueprint, jsonify, request

from errors import ConflictError, NotFoundError, ValidationError
from models import Book, storage

books_bp = Blueprint("books", __name__, url_prefix="/books")


def _validate_book_payload(data: dict) -> None:
    if not isinstance(data, dict):
        raise ValidationError("Corpo da requisição deve ser um JSON válido.")
    for field_name in ("title", "author", "isbn"):
        value = data.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(
                f"O campo '{field_name}' é obrigatório e não pode ser vazio."
            )


def get_book_or_404(book_id: int) -> Book:
    book = storage.books.get(book_id)
    if book is None:
        raise NotFoundError(f"Livro com id {book_id} não encontrado.")
    return book


@books_bp.post("")
def create_book():
    """Cadastra um novo livro no acervo (título, autor e ISBN)."""
    data = request.get_json(silent=True) or {}
    _validate_book_payload(data)

    book_id = storage.next_book_id()
    book = Book(
        id=book_id,
        title=data["title"].strip(),
        author=data["author"].strip(),
        isbn=data["isbn"].strip(),
    )
    storage.books[book_id] = book
    return jsonify(book.to_dict()), 201


@books_bp.get("")
def list_books():
    """Lista todos os livros do acervo."""
    books = sorted(storage.books.values(), key=lambda b: b.id)
    return jsonify([book.to_dict() for book in books]), 200


@books_bp.get("/<int:book_id>")
def get_book(book_id: int):
    """Busca um livro específico pelo id."""
    book = get_book_or_404(book_id)
    return jsonify(book.to_dict()), 200


@books_bp.delete("/<int:book_id>")
def delete_book(book_id: int):
    """Exclui um livro do acervo, desde que ele não esteja emprestado."""
    book = get_book_or_404(book_id)
    if not book.available:
        raise ConflictError(
            "Não é possível excluir um livro que está emprestado no momento."
        )
    del storage.books[book_id]
    return "", 204
