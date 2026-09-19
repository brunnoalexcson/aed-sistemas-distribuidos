"""Rotas relacionadas ao cadastro de usuários e seus empréstimos."""

from flask import Blueprint, jsonify, request

from errors import NotFoundError, ValidationError
from models import User, storage

users_bp = Blueprint("users", __name__, url_prefix="/users")


def _validate_user_payload(data: dict) -> None:
    if not isinstance(data, dict):
        raise ValidationError("Corpo da requisição deve ser um JSON válido.")
    for field_name in ("name", "email"):
        value = data.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(
                f"O campo '{field_name}' é obrigatório e não pode ser vazio."
            )


def get_user_or_404(user_id: int) -> User:
    user = storage.users.get(user_id)
    if user is None:
        raise NotFoundError(f"Usuário com id {user_id} não encontrado.")
    return user


@users_bp.post("")
def create_user():
    """Cadastra um novo usuário (nome e e-mail)."""
    data = request.get_json(silent=True) or {}
    _validate_user_payload(data)

    user_id = storage.next_user_id()
    user = User(
        id=user_id,
        name=data["name"].strip(),
        email=data["email"].strip(),
    )
    storage.users[user_id] = user
    return jsonify(user.to_dict()), 201


@users_bp.get("")
def list_users():
    """Lista todos os usuários cadastrados."""
    users = sorted(storage.users.values(), key=lambda u: u.id)
    return jsonify([user.to_dict() for user in users]), 200


@users_bp.get("/<int:user_id>")
def get_user(user_id: int):
    """Busca um usuário específico pelo id."""
    user = get_user_or_404(user_id)
    return jsonify(user.to_dict()), 200


@users_bp.patch("/<int:user_id>")
def update_user(user_id: int):
    """Atualiza dados cadastrais do usuário, incluindo ativar/inativar."""
    user = get_user_or_404(user_id)
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        raise ValidationError("Corpo da requisição deve ser um JSON válido.")

    if "name" in data:
        if not isinstance(data["name"], str) or not data["name"].strip():
            raise ValidationError("O campo 'name' não pode ser vazio.")
        user.name = data["name"].strip()

    if "email" in data:
        if not isinstance(data["email"], str) or not data["email"].strip():
            raise ValidationError("O campo 'email' não pode ser vazio.")
        user.email = data["email"].strip()

    if "active" in data:
        if not isinstance(data["active"], bool):
            raise ValidationError("O campo 'active' deve ser um booleano.")
        user.active = data["active"]

    return jsonify(user.to_dict()), 200


@users_bp.get("/<int:user_id>/loans")
def list_user_loans(user_id: int):
    """Lista os empréstimos de um usuário, com filtro opcional por status.

    Use o parâmetro de query `status=open` para ver somente os
    empréstimos ainda em aberto, ou `status=returned` para os já
    devolvidos.
    """
    get_user_or_404(user_id)

    status_filter = request.args.get("status")
    loans = [loan for loan in storage.loans.values() if loan.user_id == user_id]

    if status_filter:
        status_filter = status_filter.strip().lower()
        if status_filter not in ("open", "returned"):
            raise ValidationError("O parâmetro 'status' deve ser 'open' ou 'returned'.")
        loans = [loan for loan in loans if loan.status == status_filter]

    loans.sort(key=lambda loan: loan.id)
    return jsonify([loan.to_dict() for loan in loans]), 200


@users_bp.post("/<int:user_id>/pay_fine")
def pay_fine(user_id: int):
    """Registra o pagamento da multa do usuário, zerando a pendência."""
    user = get_user_or_404(user_id)
    user.fine_balance = 0.0
    return jsonify(user.to_dict()), 200
