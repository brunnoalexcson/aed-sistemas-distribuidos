"""Rotas HTTP (Blueprint Flask) da API da biblioteca."""

from flask import Blueprint, jsonify, request

from .erros import RequisicaoInvalida
from .servicos import ServicoDeBiblioteca


def _corpo_json() -> dict:
    dados = request.get_json(silent=True)
    if dados is None or not isinstance(dados, dict):
        raise RequisicaoInvalida("O corpo da requisição deve ser um JSON válido.")
    return dados


def _parametro_booleano(valor) -> bool:
    if valor is None:
        return False
    return str(valor).strip().lower() in ("1", "true", "sim", "yes")


def criar_blueprint(servico: ServicoDeBiblioteca) -> Blueprint:
    bp = Blueprint("biblioteca", __name__)

    # ------------------------------------------------------------------
    # Livros
    # ------------------------------------------------------------------
    @bp.route("/livros", methods=["POST"])
    def cadastrar_livro():
        dados = _corpo_json()
        livro = servico.cadastrar_livro(
            titulo=dados.get("titulo"),
            autor=dados.get("autor"),
            isbn=dados.get("isbn"),
        )
        return jsonify(livro.to_dict()), 201

    @bp.route("/livros", methods=["GET"])
    def listar_livros():
        livros = servico.listar_livros()
        return jsonify([livro.to_dict() for livro in livros]), 200

    @bp.route("/livros/<livro_id>", methods=["GET"])
    def buscar_livro(livro_id):
        livro = servico.buscar_livro(livro_id)
        return jsonify(livro.to_dict()), 200

    @bp.route("/livros/<livro_id>", methods=["DELETE"])
    def excluir_livro(livro_id):
        servico.excluir_livro(livro_id)
        return "", 204

    # ------------------------------------------------------------------
    # Usuários
    # ------------------------------------------------------------------
    @bp.route("/usuarios", methods=["POST"])
    def cadastrar_usuario():
        dados = _corpo_json()
        usuario = servico.cadastrar_usuario(
            nome=dados.get("nome"),
            email=dados.get("email"),
        )
        return jsonify(usuario.to_dict()), 201

    @bp.route("/usuarios", methods=["GET"])
    def listar_usuarios():
        usuarios = servico.listar_usuarios()
        return jsonify([usuario.to_dict() for usuario in usuarios]), 200

    @bp.route("/usuarios/<usuario_id>", methods=["GET"])
    def buscar_usuario(usuario_id):
        usuario = servico.buscar_usuario(usuario_id)
        return jsonify(usuario.to_dict()), 200

    @bp.route("/usuarios/<usuario_id>/emprestimos", methods=["GET"])
    def listar_emprestimos_do_usuario(usuario_id):
        apenas_em_aberto = _parametro_booleano(request.args.get("em_aberto"))
        emprestimos = servico.listar_emprestimos_do_usuario(usuario_id, apenas_em_aberto)
        return jsonify([emprestimo.to_dict() for emprestimo in emprestimos]), 200

    @bp.route("/usuarios/<usuario_id>/pagamentos-multa", methods=["POST"])
    def pagar_multa(usuario_id):
        usuario, valor_pago = servico.registrar_pagamento_multa(usuario_id)
        return (
            jsonify(
                {
                    "usuario": usuario.to_dict(),
                    "valor_pago": round(valor_pago, 2),
                }
            ),
            200,
        )

    # ------------------------------------------------------------------
    # Empréstimos
    # ------------------------------------------------------------------
    @bp.route("/emprestimos", methods=["POST"])
    def registrar_emprestimo():
        dados = _corpo_json()
        emprestimo = servico.registrar_emprestimo(
            usuario_id=dados.get("usuario_id"),
            livro_id=dados.get("livro_id"),
        )
        return jsonify(emprestimo.to_dict()), 201

    @bp.route("/emprestimos/<emprestimo_id>", methods=["GET"])
    def buscar_emprestimo(emprestimo_id):
        emprestimo = servico.buscar_emprestimo(emprestimo_id)
        return jsonify(emprestimo.to_dict()), 200

    @bp.route("/emprestimos/<emprestimo_id>/devolucao", methods=["POST"])
    def registrar_devolucao(emprestimo_id):
        emprestimo = servico.registrar_devolucao(emprestimo_id)
        return jsonify(emprestimo.to_dict()), 200

    return bp
