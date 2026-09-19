"""Rotas da API REST do sistema de biblioteca."""
import math
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from storage import storage

bp = Blueprint("biblioteca", __name__)

PRAZO_EMPRESTIMO_DIAS = 14
LIMITE_EMPRESTIMOS_POR_USUARIO = 3
VALOR_MULTA_POR_DIA = 1.50


def erro(mensagem: str, codigo: int):
    return jsonify({"erro": mensagem}), codigo


def texto_valido(valor) -> bool:
    return isinstance(valor, str) and valor.strip() != ""


# ==================== Livros ====================


@bp.route("/livros", methods=["POST"])
def cadastrar_livro():
    dados = request.get_json(silent=True) or {}
    titulo = dados.get("titulo")
    autor = dados.get("autor")
    isbn = dados.get("isbn")

    if not texto_valido(titulo) or not texto_valido(autor) or not texto_valido(isbn):
        return erro(
            "Os campos 'titulo', 'autor' e 'isbn' são obrigatórios e não podem "
            "ser vazios.",
            400,
        )

    livro = storage.criar_livro(titulo.strip(), autor.strip(), isbn.strip())
    return jsonify(livro.to_dict()), 201


@bp.route("/livros", methods=["GET"])
def listar_livros():
    livros = storage.listar_livros()
    return jsonify([livro.to_dict() for livro in livros]), 200


@bp.route("/livros/<int:livro_id>", methods=["GET"])
def buscar_livro(livro_id: int):
    livro = storage.obter_livro(livro_id)
    if livro is None:
        return erro("Livro não encontrado.", 404)
    return jsonify(livro.to_dict()), 200


@bp.route("/livros/<int:livro_id>", methods=["DELETE"])
def excluir_livro(livro_id: int):
    livro = storage.obter_livro(livro_id)
    if livro is None:
        return erro("Livro não encontrado.", 404)

    if not livro.disponivel:
        return erro(
            "Não é possível excluir um livro que está emprestado no momento.",
            409,
        )

    storage.remover_livro(livro_id)
    return "", 204


# ==================== Usuários ====================


@bp.route("/usuarios", methods=["POST"])
def cadastrar_usuario():
    dados = request.get_json(silent=True) or {}
    nome = dados.get("nome")
    email = dados.get("email")

    if not texto_valido(nome) or not texto_valido(email):
        return erro(
            "Os campos 'nome' e 'email' são obrigatórios e não podem ser vazios.",
            400,
        )

    if "@" not in email:
        return erro("O campo 'email' deve conter um endereço de e-mail válido.", 400)

    usuario = storage.criar_usuario(nome.strip(), email.strip())
    return jsonify(usuario.to_dict()), 201


@bp.route("/usuarios", methods=["GET"])
def listar_usuarios():
    usuarios = storage.listar_usuarios()
    return jsonify([usuario.to_dict() for usuario in usuarios]), 200


@bp.route("/usuarios/<int:usuario_id>", methods=["GET"])
def buscar_usuario(usuario_id: int):
    usuario = storage.obter_usuario(usuario_id)
    if usuario is None:
        return erro("Usuário não encontrado.", 404)
    return jsonify(usuario.to_dict()), 200


@bp.route("/usuarios/<int:usuario_id>/emprestimos", methods=["GET"])
def listar_emprestimos_do_usuario(usuario_id: int):
    usuario = storage.obter_usuario(usuario_id)
    if usuario is None:
        return erro("Usuário não encontrado.", 404)

    status = request.args.get("status")
    emprestimos = storage.emprestimos_do_usuario(usuario_id)

    if status is not None:
        status = status.strip().lower()
        if status not in ("aberto", "devolvido"):
            return erro(
                "O parâmetro 'status' deve ser 'aberto' ou 'devolvido'.", 400
            )
        emprestimos = [e for e in emprestimos if e.status == status]

    return jsonify([e.to_dict() for e in emprestimos]), 200


@bp.route("/usuarios/<int:usuario_id>/pagamentos-multa", methods=["POST"])
def pagar_multa(usuario_id: int):
    usuario = storage.obter_usuario(usuario_id)
    if usuario is None:
        return erro("Usuário não encontrado.", 404)

    valor_pago = usuario.multa_pendente
    usuario.multa_pendente = 0.0

    return (
        jsonify(
            {
                "usuario_id": usuario.id,
                "valor_pago": round(valor_pago, 2),
                "multa_pendente": usuario.multa_pendente,
            }
        ),
        200,
    )


# ==================== Empréstimos ====================


@bp.route("/emprestimos", methods=["POST"])
def registrar_emprestimo():
    dados = request.get_json(silent=True) or {}
    livro_id = dados.get("livro_id")
    usuario_id = dados.get("usuario_id")

    if not isinstance(livro_id, int) or isinstance(livro_id, bool):
        return erro("O campo 'livro_id' é obrigatório e deve ser um inteiro.", 400)
    if not isinstance(usuario_id, int) or isinstance(usuario_id, bool):
        return erro("O campo 'usuario_id' é obrigatório e deve ser um inteiro.", 400)

    livro = storage.obter_livro(livro_id)
    if livro is None:
        return erro("Livro não encontrado.", 404)

    usuario = storage.obter_usuario(usuario_id)
    if usuario is None:
        return erro("Usuário não encontrado.", 404)

    if not livro.disponivel:
        return erro("O livro não está disponível para empréstimo.", 409)

    if not usuario.ativo:
        return erro("Usuário inativo não pode pegar livro emprestado.", 409)

    if usuario.multa_pendente > 0:
        return erro(
            "Usuário com multa pendente não pode pegar livro emprestado até "
            "quitar a pendência.",
            409,
        )

    if len(storage.emprestimos_abertos_do_usuario(usuario_id)) >= LIMITE_EMPRESTIMOS_POR_USUARIO:
        return erro(
            f"Usuário já atingiu o limite de {LIMITE_EMPRESTIMOS_POR_USUARIO} "
            "livros emprestados simultaneamente.",
            409,
        )

    agora = datetime.now()
    prazo = agora + timedelta(days=PRAZO_EMPRESTIMO_DIAS)

    emprestimo = storage.criar_emprestimo(livro_id, usuario_id, agora, prazo)
    livro.disponivel = False

    return jsonify(emprestimo.to_dict()), 201


@bp.route("/emprestimos", methods=["GET"])
def listar_emprestimos():
    emprestimos = storage.listar_emprestimos()
    return jsonify([e.to_dict() for e in emprestimos]), 200


@bp.route("/emprestimos/<int:emprestimo_id>", methods=["GET"])
def buscar_emprestimo(emprestimo_id: int):
    emprestimo = storage.obter_emprestimo(emprestimo_id)
    if emprestimo is None:
        return erro("Empréstimo não encontrado.", 404)
    return jsonify(emprestimo.to_dict()), 200


@bp.route("/emprestimos/<int:emprestimo_id>/devolucao", methods=["POST"])
def devolver_emprestimo(emprestimo_id: int):
    emprestimo = storage.obter_emprestimo(emprestimo_id)
    if emprestimo is None:
        return erro("Empréstimo não encontrado.", 404)

    if emprestimo.status == "devolvido":
        return erro("Este empréstimo já foi devolvido anteriormente.", 409)

    agora = datetime.now()
    emprestimo.data_devolucao = agora
    emprestimo.status = "devolvido"

    multa = 0.0
    if agora > emprestimo.data_prevista_devolucao:
        segundos_atraso = (agora - emprestimo.data_prevista_devolucao).total_seconds()
        dias_atraso = math.ceil(segundos_atraso / 86400)
        multa = dias_atraso * VALOR_MULTA_POR_DIA

    emprestimo.multa = multa

    usuario = storage.obter_usuario(emprestimo.usuario_id)
    if usuario is not None and multa > 0:
        usuario.multa_pendente += multa

    livro = storage.obter_livro(emprestimo.livro_id)
    if livro is not None:
        livro.disponivel = True

    return jsonify(emprestimo.to_dict()), 200
