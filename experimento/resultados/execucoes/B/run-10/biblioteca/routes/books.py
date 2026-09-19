"""Rotas relacionadas ao acervo de livros."""

from flask import Blueprint, jsonify

from ._helpers import get_json_body, get_service, parse_bool_query_param

books_bp = Blueprint("books", __name__, url_prefix="/livros")


@books_bp.post("")
def cadastrar_livro():
    dados = get_json_body()
    livro = get_service().cadastrar_livro(dados)
    return jsonify(livro.to_dict()), 201


@books_bp.get("")
def listar_livros():
    disponivel = parse_bool_query_param("disponivel")
    livros = get_service().listar_livros(disponivel=disponivel)
    return jsonify([livro.to_dict() for livro in livros]), 200


@books_bp.get("/<int:livro_id>")
def buscar_livro(livro_id: int):
    livro = get_service().buscar_livro(livro_id)
    return jsonify(livro.to_dict()), 200


@books_bp.delete("/<int:livro_id>")
def excluir_livro(livro_id: int):
    get_service().excluir_livro(livro_id)
    return "", 204
