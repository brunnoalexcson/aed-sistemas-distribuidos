"""API REST do sistema de biblioteca do bairro.

Aplicação Flask, sem autenticação e sem interface gráfica, com todos os
dados mantidos em memória (não há banco de dados). Execute com:

    python app.py

O servidor sobe em http://0.0.0.0:5000/
"""
from flask import Flask, jsonify, request

import services
from errors import register_error_handlers

app = Flask(__name__)
register_error_handlers(app)


@app.get("/")
def index():
    return jsonify({"service": "Sistema de Biblioteca", "status": "ok"}), 200


# ---------------------------------------------------------------------------
# Livros
# ---------------------------------------------------------------------------
@app.post("/books")
def create_book():
    book = services.create_book(request.get_json(silent=True) or {})
    return jsonify(book.to_dict()), 201


@app.get("/books")
def list_books():
    books = services.list_books()
    return jsonify([book.to_dict() for book in books]), 200


@app.get("/books/<int:book_id>")
def get_book(book_id):
    book = services.get_book(book_id)
    return jsonify(book.to_dict()), 200


@app.delete("/books/<int:book_id>")
def delete_book(book_id):
    services.delete_book(book_id)
    return "", 204


# ---------------------------------------------------------------------------
# Usuários
# ---------------------------------------------------------------------------
@app.post("/users")
def create_user():
    user = services.create_user(request.get_json(silent=True) or {})
    return jsonify(user.to_dict()), 201


@app.get("/users")
def list_users():
    users = services.list_users()
    return jsonify([user.to_dict() for user in users]), 200


@app.get("/users/<int:user_id>")
def get_user(user_id):
    user = services.get_user(user_id)
    return jsonify(user.to_dict()), 200


@app.patch("/users/<int:user_id>")
def update_user(user_id):
    user = services.update_user(user_id, request.get_json(silent=True) or {})
    return jsonify(user.to_dict()), 200


@app.post("/users/<int:user_id>/pay-fine")
def pay_fine(user_id):
    user = services.pay_fine(user_id)
    return jsonify(user.to_dict()), 200


@app.get("/users/<int:user_id>/loans")
def list_user_loans(user_id):
    status = request.args.get("status")
    loans = services.list_user_loans(user_id, status=status)
    return jsonify([loan.to_dict() for loan in loans]), 200


# ---------------------------------------------------------------------------
# Empréstimos
# ---------------------------------------------------------------------------
@app.post("/loans")
def create_loan():
    loan = services.create_loan(request.get_json(silent=True) or {})
    return jsonify(loan.to_dict()), 201


@app.get("/loans")
def list_loans():
    loans = services.list_loans()
    return jsonify([loan.to_dict() for loan in loans]), 200


@app.get("/loans/<int:loan_id>")
def get_loan(loan_id):
    loan = services.get_loan(loan_id)
    return jsonify(loan.to_dict()), 200


@app.post("/loans/<int:loan_id>/return")
def return_loan(loan_id):
    loan = services.return_loan(loan_id)
    return jsonify(loan.to_dict()), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
