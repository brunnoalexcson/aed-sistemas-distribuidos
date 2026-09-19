"""Rotas relacionadas ao cadastro de usuários e às suas multas/empréstimos."""

from flask import Blueprint, jsonify

from ._helpers import get_json_body, get_service, parse_bool_query_param

users_bp = Blueprint("users", __name__, url_prefix="/usuarios")


@users_bp.post("")
def cadastrar_usuario():
    dados = get_json_body()
    usuario = get_service().cadastrar_usuario(dados)
    return jsonify(usuario.to_dict()), 201


@users_bp.get("")
def listar_usuarios():
    usuarios = get_service().listar_usuarios()
    return jsonify([usuario.to_dict() for usuario in usuarios]), 200


@users_bp.get("/<int:usuario_id>")
def buscar_usuario(usuario_id: int):
    usuario = get_service().buscar_usuario(usuario_id)
    return jsonify(usuario.to_dict()), 200


@users_bp.patch("/<int:usuario_id>")
def atualizar_usuario(usuario_id: int):
    dados = get_json_body()
    usuario = get_service().atualizar_usuario(usuario_id, dados)
    return jsonify(usuario.to_dict()), 200


@users_bp.get("/<int:usuario_id>/emprestimos")
def listar_emprestimos_do_usuario(usuario_id: int):
    em_aberto = parse_bool_query_param("em_aberto")
    emprestimos = get_service().listar_emprestimos_do_usuario(usuario_id, em_aberto=em_aberto)
    return jsonify([emprestimo.to_dict() for emprestimo in emprestimos]), 200


@users_bp.post("/<int:usuario_id>/pagamentos")
def registrar_pagamento_multa(usuario_id: int):
    usuario = get_service().registrar_pagamento_multa(usuario_id)
    return jsonify(usuario.to_dict()), 200
