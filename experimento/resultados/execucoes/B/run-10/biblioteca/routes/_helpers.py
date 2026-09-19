"""Funções auxiliares compartilhadas entre os blueprints de rotas."""

from typing import Optional

from flask import current_app, request

from ..errors import ErroDeValidacao
from ..services import LibraryService


def get_service() -> LibraryService:
    return current_app.extensions["library_service"]


def parse_bool_query_param(nome: str) -> Optional[bool]:
    """Lê um parâmetro de query string booleano (ex.: ?disponivel=true).

    Retorna None quando o parâmetro não foi informado, e levanta erro de
    validação caso o valor informado não seja reconhecido como booleano.
    """
    valor = request.args.get(nome)
    if valor is None:
        return None

    valor_normalizado = valor.strip().lower()
    if valor_normalizado in ("true", "1", "sim"):
        return True
    if valor_normalizado in ("false", "0", "nao", "não"):
        return False

    raise ErroDeValidacao(
        f"O parâmetro '{nome}' deve ser um valor booleano (true ou false)."
    )


def get_json_body() -> dict:
    """Obtém o corpo JSON da requisição, garantindo que seja um objeto."""
    dados = request.get_json(silent=True)
    if dados is None or not isinstance(dados, dict):
        raise ErroDeValidacao("O corpo da requisição deve ser um objeto JSON válido.")
    return dados
