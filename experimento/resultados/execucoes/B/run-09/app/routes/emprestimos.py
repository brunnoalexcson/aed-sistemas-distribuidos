"""Rotas relacionadas ao empréstimo e devolução de livros."""

from flask import Blueprint, jsonify, request

from app import services
from app.errors import RequisicaoInvalida

bp_emprestimos = Blueprint("emprestimos", __name__, url_prefix="/emprestimos")


@bp_emprestimos.post("")
def registrar_emprestimo():
    dados = request.get_json(silent=True)
    if dados is None:
        raise RequisicaoInvalida("Corpo da requisição deve ser um JSON válido.")
    emprestimo = services.registrar_emprestimo(dados)
    return jsonify(emprestimo.to_dict()), 201


@bp_emprestimos.get("")
def listar_emprestimos():
    emprestimos = services.listar_emprestimos()
    return jsonify([emprestimo.to_dict() for emprestimo in emprestimos]), 200


@bp_emprestimos.get("/<int:emprestimo_id>")
def buscar_emprestimo(emprestimo_id):
    emprestimo = services.buscar_emprestimo(emprestimo_id)
    return jsonify(emprestimo.to_dict()), 200


@bp_emprestimos.post("/<int:emprestimo_id>/devolucao")
def registrar_devolucao(emprestimo_id):
    emprestimo = services.registrar_devolucao(emprestimo_id)
    return jsonify(emprestimo.to_dict()), 200
