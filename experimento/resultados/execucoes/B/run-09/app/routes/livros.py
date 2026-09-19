"""Rotas relacionadas ao acervo de livros."""

from flask import Blueprint, jsonify, request

from app import services
from app.errors import RequisicaoInvalida

bp_livros = Blueprint("livros", __name__, url_prefix="/livros")


@bp_livros.post("")
def criar_livro():
    dados = request.get_json(silent=True)
    if dados is None:
        raise RequisicaoInvalida("Corpo da requisição deve ser um JSON válido.")
    livro = services.criar_livro(dados)
    return jsonify(livro.to_dict()), 201


@bp_livros.get("")
def listar_livros():
    livros = services.listar_livros()
    return jsonify([livro.to_dict() for livro in livros]), 200


@bp_livros.get("/<int:livro_id>")
def buscar_livro(livro_id):
    livro = services.buscar_livro(livro_id)
    return jsonify(livro.to_dict()), 200


@bp_livros.delete("/<int:livro_id>")
def excluir_livro(livro_id):
    services.excluir_livro(livro_id)
    return "", 204
