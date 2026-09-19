"""Rotas relacionadas ao controle de empréstimos de livros."""

from flask import Blueprint, jsonify

from ._helpers import get_json_body, get_service, parse_bool_query_param

loans_bp = Blueprint("loans", __name__, url_prefix="/emprestimos")


@loans_bp.post("")
def registrar_emprestimo():
    dados = get_json_body()
    emprestimo = get_service().registrar_emprestimo(dados)
    return jsonify(emprestimo.to_dict()), 201


@loans_bp.get("")
def listar_emprestimos():
    em_aberto = parse_bool_query_param("em_aberto")
    emprestimos = get_service().listar_emprestimos(em_aberto=em_aberto)
    return jsonify([emprestimo.to_dict() for emprestimo in emprestimos]), 200


@loans_bp.get("/<int:emprestimo_id>")
def buscar_emprestimo(emprestimo_id: int):
    emprestimo = get_service().buscar_emprestimo(emprestimo_id)
    return jsonify(emprestimo.to_dict()), 200


@loans_bp.post("/<int:emprestimo_id>/devolucao")
def registrar_devolucao(emprestimo_id: int):
    emprestimo = get_service().registrar_devolucao(emprestimo_id)
    return jsonify(emprestimo.to_dict()), 200
