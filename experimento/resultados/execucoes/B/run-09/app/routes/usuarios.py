"""Rotas relacionadas ao cadastro de usuários, seus empréstimos e multas."""

from flask import Blueprint, jsonify, request

from app import services
from app.errors import RequisicaoInvalida

bp_usuarios = Blueprint("usuarios", __name__, url_prefix="/usuarios")


@bp_usuarios.post("")
def criar_usuario():
    dados = request.get_json(silent=True)
    if dados is None:
        raise RequisicaoInvalida("Corpo da requisição deve ser um JSON válido.")
    usuario = services.criar_usuario(dados)
    return jsonify(usuario.to_dict()), 201


@bp_usuarios.get("")
def listar_usuarios():
    usuarios = services.listar_usuarios()
    return jsonify([usuario.to_dict() for usuario in usuarios]), 200


@bp_usuarios.get("/<int:usuario_id>")
def buscar_usuario(usuario_id):
    usuario = services.buscar_usuario(usuario_id)
    return jsonify(usuario.to_dict()), 200


@bp_usuarios.patch("/<int:usuario_id>")
def atualizar_usuario(usuario_id):
    dados = request.get_json(silent=True)
    if dados is None:
        raise RequisicaoInvalida("Corpo da requisição deve ser um JSON válido.")
    usuario = services.atualizar_usuario(usuario_id, dados)
    return jsonify(usuario.to_dict()), 200


@bp_usuarios.get("/<int:usuario_id>/emprestimos")
def listar_emprestimos_do_usuario(usuario_id):
    apenas_em_aberto = request.args.get("em_aberto", "").lower() in ("true", "1", "sim")
    emprestimos = services.listar_emprestimos_do_usuario(usuario_id, apenas_em_aberto=apenas_em_aberto)
    return jsonify([emprestimo.to_dict() for emprestimo in emprestimos]), 200


@bp_usuarios.post("/<int:usuario_id>/multas/pagamento")
def pagar_multa(usuario_id):
    resultado = services.pagar_multa(usuario_id)
    return jsonify(resultado), 200
