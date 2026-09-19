"""Regras de negócio do sistema de biblioteca."""

import math
from datetime import datetime, timedelta

from app.errors import ConflitoRegraNegocio, NaoEncontrado, RequisicaoInvalida
from app.models import Emprestimo, Livro, Usuario
from app.storage import (
    repositorio_emprestimos,
    repositorio_livros,
    repositorio_usuarios,
)

PRAZO_EMPRESTIMO_DIAS = 14
LIMITE_LIVROS_POR_USUARIO = 3
VALOR_MULTA_POR_DIA_ATRASO = 1.50


# --------------------------------------------------------------------------
# Livros
# --------------------------------------------------------------------------

def criar_livro(dados: dict) -> Livro:
    titulo = (dados or {}).get("titulo")
    autor = (dados or {}).get("autor")
    isbn = (dados or {}).get("isbn")

    if not titulo or not str(titulo).strip():
        raise RequisicaoInvalida("O campo 'titulo' é obrigatório.")
    if not autor or not str(autor).strip():
        raise RequisicaoInvalida("O campo 'autor' é obrigatório.")
    if not isbn or not str(isbn).strip():
        raise RequisicaoInvalida("O campo 'isbn' é obrigatório.")

    return repositorio_livros.criar(titulo=str(titulo).strip(), autor=str(autor).strip(), isbn=str(isbn).strip())


def listar_livros() -> list:
    return repositorio_livros.listar()


def buscar_livro(livro_id: int) -> Livro:
    livro = repositorio_livros.buscar(livro_id)
    if livro is None:
        raise NaoEncontrado(f"Livro com id {livro_id} não encontrado.")
    return livro


def excluir_livro(livro_id: int) -> None:
    livro = buscar_livro(livro_id)
    if not livro.disponivel:
        raise ConflitoRegraNegocio("Não é possível excluir um livro que está emprestado no momento.")
    repositorio_livros.remover(livro_id)


# --------------------------------------------------------------------------
# Usuários
# --------------------------------------------------------------------------

def criar_usuario(dados: dict) -> Usuario:
    nome = (dados or {}).get("nome")
    email = (dados or {}).get("email")

    if not nome or not str(nome).strip():
        raise RequisicaoInvalida("O campo 'nome' é obrigatório.")
    if not email or not str(email).strip() or "@" not in str(email):
        raise RequisicaoInvalida("O campo 'email' é obrigatório e deve ser um e-mail válido.")

    return repositorio_usuarios.criar(nome=str(nome).strip(), email=str(email).strip())


def listar_usuarios() -> list:
    return repositorio_usuarios.listar()


def buscar_usuario(usuario_id: int) -> Usuario:
    usuario = repositorio_usuarios.buscar(usuario_id)
    if usuario is None:
        raise NaoEncontrado(f"Usuário com id {usuario_id} não encontrado.")
    return usuario


def atualizar_usuario(usuario_id: int, dados: dict) -> Usuario:
    usuario = buscar_usuario(usuario_id)
    dados = dados or {}

    if "nome" in dados:
        nome = dados.get("nome")
        if not nome or not str(nome).strip():
            raise RequisicaoInvalida("O campo 'nome' não pode ser vazio.")
        usuario.nome = str(nome).strip()

    if "email" in dados:
        email = dados.get("email")
        if not email or not str(email).strip() or "@" not in str(email):
            raise RequisicaoInvalida("O campo 'email' deve ser um e-mail válido.")
        usuario.email = str(email).strip()

    if "ativo" in dados:
        ativo = dados.get("ativo")
        if not isinstance(ativo, bool):
            raise RequisicaoInvalida("O campo 'ativo' deve ser um valor booleano (true ou false).")
        usuario.ativo = ativo

    return usuario


# --------------------------------------------------------------------------
# Empréstimos
# --------------------------------------------------------------------------

def registrar_emprestimo(dados: dict) -> Emprestimo:
    dados = dados or {}
    livro_id = dados.get("livro_id")
    usuario_id = dados.get("usuario_id")

    if livro_id is None:
        raise RequisicaoInvalida("O campo 'livro_id' é obrigatório.")
    if usuario_id is None:
        raise RequisicaoInvalida("O campo 'usuario_id' é obrigatório.")

    livro = buscar_livro(livro_id)
    usuario = buscar_usuario(usuario_id)

    if not livro.disponivel:
        raise ConflitoRegraNegocio("Este livro já está emprestado no momento.")

    if not usuario.ativo:
        raise ConflitoRegraNegocio("Usuário inativo não pode pegar livro emprestado.")

    if usuario.multa_pendente > 0:
        raise ConflitoRegraNegocio("Usuário com multa pendente não pode pegar livro emprestado até quitá-la.")

    emprestimos_abertos = repositorio_emprestimos.emprestimos_abertos_por_usuario(usuario_id)
    if len(emprestimos_abertos) >= LIMITE_LIVROS_POR_USUARIO:
        raise ConflitoRegraNegocio(
            f"Usuário já possui o máximo de {LIMITE_LIVROS_POR_USUARIO} livros emprestados ao mesmo tempo."
        )

    agora = datetime.now()
    data_prevista = agora + timedelta(days=PRAZO_EMPRESTIMO_DIAS)

    emprestimo = repositorio_emprestimos.criar(
        livro_id=livro_id,
        usuario_id=usuario_id,
        data_emprestimo=agora,
        data_prevista_devolucao=data_prevista,
    )
    livro.disponivel = False
    return emprestimo


def buscar_emprestimo(emprestimo_id: int) -> Emprestimo:
    emprestimo = repositorio_emprestimos.buscar(emprestimo_id)
    if emprestimo is None:
        raise NaoEncontrado(f"Empréstimo com id {emprestimo_id} não encontrado.")
    return emprestimo


def listar_emprestimos() -> list:
    return repositorio_emprestimos.listar()


def registrar_devolucao(emprestimo_id: int) -> Emprestimo:
    emprestimo = buscar_emprestimo(emprestimo_id)

    if emprestimo.devolvido:
        raise ConflitoRegraNegocio("Este empréstimo já foi devolvido anteriormente.")

    agora = datetime.now()
    emprestimo.data_devolucao = agora
    emprestimo.devolvido = True

    livro = repositorio_livros.buscar(emprestimo.livro_id)
    if livro is not None:
        livro.disponivel = True

    if agora > emprestimo.data_prevista_devolucao:
        atraso = agora - emprestimo.data_prevista_devolucao
        dias_atraso = max(1, math.ceil(atraso.total_seconds() / 86400))
        multa = round(dias_atraso * VALOR_MULTA_POR_DIA_ATRASO, 2)
        emprestimo.multa = multa

        usuario = repositorio_usuarios.buscar(emprestimo.usuario_id)
        if usuario is not None:
            usuario.multa_pendente = round(usuario.multa_pendente + multa, 2)

    return emprestimo


def listar_emprestimos_do_usuario(usuario_id: int, apenas_em_aberto: bool = False) -> list:
    buscar_usuario(usuario_id)  # garante que o usuário existe (404 caso não exista)
    if apenas_em_aberto:
        return repositorio_emprestimos.emprestimos_abertos_por_usuario(usuario_id)
    return repositorio_emprestimos.listar_por_usuario(usuario_id)


def pagar_multa(usuario_id: int) -> dict:
    usuario = buscar_usuario(usuario_id)

    if usuario.multa_pendente <= 0:
        raise RequisicaoInvalida("O usuário não possui multa pendente para pagar.")

    valor_pago = usuario.multa_pendente
    usuario.multa_pendente = 0.0

    return {
        "usuario_id": usuario.id,
        "valor_pago": round(valor_pago, 2),
        "multa_pendente": round(usuario.multa_pendente, 2),
    }
