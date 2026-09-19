"""API REST do sistema de biblioteca do bairro.

Funcionalidades cobertas:
  - Cadastro de livros (título, autor, ISBN) e usuários (nome, e-mail).
  - Listagem e busca de livros; exclusão de livros (bloqueada se o livro
    estiver emprestado no momento).
  - Registro de empréstimos, com prazo de devolução de 14 dias, respeitando
    as regras de negócio:
      * usuário só pode ter no máximo 3 empréstimos em aberto simultaneamente;
      * usuário inativo não pode pegar livro emprestado;
      * usuário com multa pendente não pode pegar livro emprestado;
      * o livro precisa estar disponível.
  - Registro de devolução, liberando o livro e calculando multa de R$ 1,50
    por dia de atraso, que fica pendente na conta do usuário.
  - Pagamento de multa, zerando a pendência do usuário.
  - Consulta dos empréstimos de um usuário, com filtro para os que estão
    em aberto.

Toda a persistência é feita em memória (não há banco de dados). O sistema
não possui autenticação nem interface gráfica: é apenas a API.
"""

from datetime import date, timedelta

from flask import Flask, jsonify, request

from errors import ConflictError, NotFoundError, ValidationError, register_error_handlers
from models import Book, Loan, User
from storage import storage

app = Flask(__name__)
register_error_handlers(app)

# Regras de negócio / parâmetros do sistema.
LOAN_PERIOD_DAYS = 14
FINE_PER_DAY = 1.50
MAX_LOANS_PER_USER = 3


# ---------------------------------------------------------------------------
# Funções auxiliares de validação e serialização
# ---------------------------------------------------------------------------

def _require_json_body() -> dict:
    data = request.get_json(silent=True)
    if data is None or not isinstance(data, dict):
        raise ValidationError("o corpo da requisição deve ser um JSON válido")
    return data


def _require_string_field(data: dict, field_name: str) -> str:
    value = data.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(
            f"o campo '{field_name}' é obrigatório e deve ser uma string não vazia"
        )
    return value.strip()


def _parse_bool_query_param(raw_value):
    if raw_value is None:
        return None
    return raw_value.strip().lower() in ("true", "1", "sim")


def parse_id_param(raw_value: str, label: str) -> int:
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        raise ValidationError(f"{label} deve ser um número inteiro")


def serialize_book(book: Book) -> dict:
    return {
        "id": book.id,
        "titulo": book.title,
        "autor": book.author,
        "isbn": book.isbn,
        "disponivel": book.available,
    }


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "nome": user.name,
        "email": user.email,
        "ativo": user.active,
        "multa_pendente": round(user.fine_balance, 2),
    }


def serialize_loan(loan: Loan) -> dict:
    return {
        "id": loan.id,
        "livro_id": loan.book_id,
        "usuario_id": loan.user_id,
        "data_emprestimo": loan.loan_date.isoformat(),
        "data_prevista_devolucao": loan.due_date.isoformat(),
        "data_devolucao": loan.return_date.isoformat() if loan.return_date else None,
        "multa_aplicada": round(loan.fine, 2),
        "em_aberto": loan.is_open,
    }


def get_book_or_404(book_id: int) -> Book:
    book = storage.books.get(book_id)
    if book is None:
        raise NotFoundError(f"livro com id {book_id} não encontrado")
    return book


def get_user_or_404(user_id: int) -> User:
    user = storage.users.get(user_id)
    if user is None:
        raise NotFoundError(f"usuário com id {user_id} não encontrado")
    return user


def get_loan_or_404(loan_id: int) -> Loan:
    loan = storage.loans.get(loan_id)
    if loan is None:
        raise NotFoundError(f"empréstimo com id {loan_id} não encontrado")
    return loan


# ---------------------------------------------------------------------------
# Rota de saúde / raiz
# ---------------------------------------------------------------------------

@app.route("/", methods=["GET"])
def raiz():
    return jsonify({"servico": "API da biblioteca", "status": "ok"}), 200


# ---------------------------------------------------------------------------
# Livros
# ---------------------------------------------------------------------------

@app.route("/livros", methods=["POST"])
def criar_livro():
    data = _require_json_body()
    titulo = _require_string_field(data, "titulo")
    autor = _require_string_field(data, "autor")
    isbn = _require_string_field(data, "isbn")

    book_id = storage.next_book_id()
    book = Book(id=book_id, title=titulo, author=autor, isbn=isbn, available=True)
    storage.books[book_id] = book
    return jsonify(serialize_book(book)), 201


@app.route("/livros", methods=["GET"])
def listar_livros():
    disponivel = _parse_bool_query_param(request.args.get("disponivel"))
    books = list(storage.books.values())
    if disponivel is not None:
        books = [b for b in books if b.available == disponivel]
    books.sort(key=lambda b: b.id)
    return jsonify([serialize_book(b) for b in books]), 200


@app.route("/livros/<livro_id>", methods=["GET"])
def buscar_livro(livro_id):
    book_id = parse_id_param(livro_id, "o id do livro")
    book = get_book_or_404(book_id)
    return jsonify(serialize_book(book)), 200


@app.route("/livros/<livro_id>", methods=["DELETE"])
def excluir_livro(livro_id):
    book_id = parse_id_param(livro_id, "o id do livro")
    book = get_book_or_404(book_id)

    if not book.available:
        raise ConflictError(
            "não é possível excluir um livro que está emprestado no momento"
        )

    del storage.books[book_id]
    return "", 204


# ---------------------------------------------------------------------------
# Usuários
# ---------------------------------------------------------------------------

@app.route("/usuarios", methods=["POST"])
def criar_usuario():
    data = _require_json_body()
    nome = _require_string_field(data, "nome")
    email = _require_string_field(data, "email")

    if "@" not in email:
        raise ValidationError("o campo 'email' deve conter um e-mail válido")

    user_id = storage.next_user_id()
    user = User(id=user_id, name=nome, email=email, active=True, fine_balance=0.0)
    storage.users[user_id] = user
    return jsonify(serialize_user(user)), 201


@app.route("/usuarios", methods=["GET"])
def listar_usuarios():
    users = sorted(storage.users.values(), key=lambda u: u.id)
    return jsonify([serialize_user(u) for u in users]), 200


@app.route("/usuarios/<usuario_id>", methods=["GET"])
def buscar_usuario(usuario_id):
    user_id = parse_id_param(usuario_id, "o id do usuário")
    user = get_user_or_404(user_id)
    return jsonify(serialize_user(user)), 200


@app.route("/usuarios/<usuario_id>/emprestimos", methods=["GET"])
def listar_emprestimos_usuario(usuario_id):
    user_id = parse_id_param(usuario_id, "o id do usuário")
    get_user_or_404(user_id)

    em_aberto = _parse_bool_query_param(request.args.get("em_aberto"))
    loans = [loan for loan in storage.loans.values() if loan.user_id == user_id]
    if em_aberto is not None:
        loans = [loan for loan in loans if loan.is_open == em_aberto]
    loans.sort(key=lambda loan: loan.id)
    return jsonify([serialize_loan(loan) for loan in loans]), 200


@app.route("/usuarios/<usuario_id>/pagamento-multa", methods=["POST"])
def pagar_multa(usuario_id):
    user_id = parse_id_param(usuario_id, "o id do usuário")
    user = get_user_or_404(user_id)

    if user.fine_balance <= 0:
        raise ConflictError("usuário não possui multa pendente")

    user.fine_balance = 0.0
    return jsonify(serialize_user(user)), 200


# ---------------------------------------------------------------------------
# Empréstimos
# ---------------------------------------------------------------------------

@app.route("/emprestimos", methods=["POST"])
def criar_emprestimo():
    data = _require_json_body()

    livro_id_raw = data.get("livro_id")
    usuario_id_raw = data.get("usuario_id")
    if livro_id_raw is None or usuario_id_raw is None:
        raise ValidationError(
            "os campos 'livro_id' e 'usuario_id' são obrigatórios"
        )

    try:
        book_id = int(livro_id_raw)
        user_id = int(usuario_id_raw)
    except (TypeError, ValueError):
        raise ValidationError("'livro_id' e 'usuario_id' devem ser números inteiros")

    book = get_book_or_404(book_id)
    user = get_user_or_404(user_id)

    if not user.active:
        raise ConflictError("usuário inativo não pode pegar livro emprestado")

    if user.fine_balance > 0:
        raise ConflictError(
            "usuário com multa pendente não pode pegar livro emprestado até quitá-la"
        )

    open_loans_count = sum(
        1 for loan in storage.loans.values() if loan.user_id == user_id and loan.is_open
    )
    if open_loans_count >= MAX_LOANS_PER_USER:
        raise ConflictError(
            f"usuário já atingiu o limite de {MAX_LOANS_PER_USER} livros "
            "emprestados simultaneamente"
        )

    if not book.available:
        raise ConflictError("livro não está disponível para empréstimo")

    today = date.today()
    loan_id = storage.next_loan_id()
    loan = Loan(
        id=loan_id,
        book_id=book_id,
        user_id=user_id,
        loan_date=today,
        due_date=today + timedelta(days=LOAN_PERIOD_DAYS),
        return_date=None,
        fine=0.0,
    )
    storage.loans[loan_id] = loan
    book.available = False

    return jsonify(serialize_loan(loan)), 201


@app.route("/emprestimos", methods=["GET"])
def listar_emprestimos():
    em_aberto = _parse_bool_query_param(request.args.get("em_aberto"))
    loans = list(storage.loans.values())
    if em_aberto is not None:
        loans = [loan for loan in loans if loan.is_open == em_aberto]
    loans.sort(key=lambda loan: loan.id)
    return jsonify([serialize_loan(loan) for loan in loans]), 200


@app.route("/emprestimos/<emprestimo_id>", methods=["GET"])
def buscar_emprestimo(emprestimo_id):
    loan_id = parse_id_param(emprestimo_id, "o id do empréstimo")
    loan = get_loan_or_404(loan_id)
    return jsonify(serialize_loan(loan)), 200


@app.route("/emprestimos/<emprestimo_id>/devolucao", methods=["POST"])
def devolver_emprestimo(emprestimo_id):
    loan_id = parse_id_param(emprestimo_id, "o id do empréstimo")
    loan = get_loan_or_404(loan_id)

    if not loan.is_open:
        raise ConflictError("este empréstimo já foi devolvido")

    today = date.today()
    loan.return_date = today

    if today > loan.due_date:
        days_late = (today - loan.due_date).days
        fine_amount = round(days_late * FINE_PER_DAY, 2)
        loan.fine = fine_amount
        user = storage.users.get(loan.user_id)
        if user is not None:
            user.fine_balance = round(user.fine_balance + fine_amount, 2)

    book = storage.books.get(loan.book_id)
    if book is not None:
        book.available = True

    return jsonify(serialize_loan(loan)), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
