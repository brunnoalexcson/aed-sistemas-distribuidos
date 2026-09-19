"""Regras de negócio da biblioteca: cadastro, empréstimo, devolução e multa."""

import math
from datetime import datetime, timedelta

from .armazenamento import Armazenamento
from .erros import ConflitoDeRegraDeNegocio, NaoEncontrado, RequisicaoInvalida
from .modelos import Emprestimo, Livro, Usuario

PRAZO_EMPRESTIMO_DIAS = 14
LIMITE_LIVROS_POR_USUARIO = 3
VALOR_MULTA_POR_DIA_ATRASO = 1.50


def _texto_obrigatorio(valor, nome_campo: str) -> str:
    if valor is None or not str(valor).strip():
        raise RequisicaoInvalida(f"O campo '{nome_campo}' é obrigatório.")
    return str(valor).strip()


class ServicoDeBiblioteca:
    def __init__(self, armazenamento: Armazenamento):
        self.armazenamento = armazenamento

    # ------------------------------------------------------------------
    # Livros
    # ------------------------------------------------------------------
    def cadastrar_livro(self, titulo, autor, isbn) -> Livro:
        titulo = _texto_obrigatorio(titulo, "titulo")
        autor = _texto_obrigatorio(autor, "autor")
        isbn = _texto_obrigatorio(isbn, "isbn")
        livro = Livro(titulo=titulo, autor=autor, isbn=isbn)
        return self.armazenamento.livros.adicionar(livro)

    def listar_livros(self):
        return sorted(self.armazenamento.livros.listar(), key=lambda l: l.titulo.lower())

    def buscar_livro(self, livro_id: str) -> Livro:
        livro = self.armazenamento.livros.obter(livro_id)
        if livro is None:
            raise NaoEncontrado(f"Livro com id '{livro_id}' não foi encontrado.")
        return livro

    def excluir_livro(self, livro_id: str) -> None:
        livro = self.buscar_livro(livro_id)
        if not livro.disponivel:
            raise ConflitoDeRegraDeNegocio(
                "Não é possível excluir um livro que está emprestado no momento."
            )
        self.armazenamento.livros.remover(livro_id)

    # ------------------------------------------------------------------
    # Usuários
    # ------------------------------------------------------------------
    def cadastrar_usuario(self, nome, email) -> Usuario:
        nome = _texto_obrigatorio(nome, "nome")
        email = _texto_obrigatorio(email, "email")
        usuario = Usuario(nome=nome, email=email)
        return self.armazenamento.usuarios.adicionar(usuario)

    def listar_usuarios(self):
        return sorted(self.armazenamento.usuarios.listar(), key=lambda u: u.nome.lower())

    def buscar_usuario(self, usuario_id: str) -> Usuario:
        usuario = self.armazenamento.usuarios.obter(usuario_id)
        if usuario is None:
            raise NaoEncontrado(f"Usuário com id '{usuario_id}' não foi encontrado.")
        return usuario

    def registrar_pagamento_multa(self, usuario_id: str):
        usuario = self.buscar_usuario(usuario_id)
        if usuario.multa_pendente <= 0:
            raise ConflitoDeRegraDeNegocio("O usuário não possui multa pendente.")
        valor_pago = usuario.multa_pendente
        usuario.multa_pendente = 0.0
        return usuario, valor_pago

    # ------------------------------------------------------------------
    # Empréstimos
    # ------------------------------------------------------------------
    def _emprestimos_em_aberto_do_usuario(self, usuario_id: str):
        return [
            emprestimo
            for emprestimo in self.armazenamento.emprestimos.listar()
            if emprestimo.usuario_id == usuario_id and not emprestimo.devolvido
        ]

    def registrar_emprestimo(self, usuario_id: str, livro_id: str) -> Emprestimo:
        usuario_id = _texto_obrigatorio(usuario_id, "usuario_id")
        livro_id = _texto_obrigatorio(livro_id, "livro_id")

        usuario = self.buscar_usuario(usuario_id)
        livro = self.buscar_livro(livro_id)

        if not livro.disponivel:
            raise ConflitoDeRegraDeNegocio(
                "O livro solicitado não está disponível para empréstimo."
            )

        if not usuario.ativo:
            raise ConflitoDeRegraDeNegocio(
                "Usuário inativo não pode pegar livro emprestado."
            )

        if usuario.multa_pendente > 0:
            raise ConflitoDeRegraDeNegocio(
                "Usuário possui multa pendente e está impedido de pegar "
                "livros emprestados até quitá-la."
            )

        if len(self._emprestimos_em_aberto_do_usuario(usuario_id)) >= LIMITE_LIVROS_POR_USUARIO:
            raise ConflitoDeRegraDeNegocio(
                f"Usuário já atingiu o limite de {LIMITE_LIVROS_POR_USUARIO} "
                "livros emprestados simultaneamente."
            )

        agora = datetime.utcnow()
        emprestimo = Emprestimo(
            livro_id=livro.id,
            usuario_id=usuario.id,
            data_emprestimo=agora,
            data_prevista_devolucao=agora + timedelta(days=PRAZO_EMPRESTIMO_DIAS),
        )
        livro.disponivel = False
        self.armazenamento.emprestimos.adicionar(emprestimo)
        return emprestimo

    def buscar_emprestimo(self, emprestimo_id: str) -> Emprestimo:
        emprestimo = self.armazenamento.emprestimos.obter(emprestimo_id)
        if emprestimo is None:
            raise NaoEncontrado(
                f"Empréstimo com id '{emprestimo_id}' não foi encontrado."
            )
        return emprestimo

    def registrar_devolucao(self, emprestimo_id: str) -> Emprestimo:
        emprestimo = self.buscar_emprestimo(emprestimo_id)
        if emprestimo.devolvido:
            raise ConflitoDeRegraDeNegocio("Este empréstimo já foi devolvido.")

        agora = datetime.utcnow()
        emprestimo.data_devolucao = agora
        emprestimo.devolvido = True

        if agora > emprestimo.data_prevista_devolucao:
            segundos_atraso = (agora - emprestimo.data_prevista_devolucao).total_seconds()
            dias_atraso = max(1, math.ceil(segundos_atraso / 86400))
            multa = round(dias_atraso * VALOR_MULTA_POR_DIA_ATRASO, 2)
            emprestimo.multa = multa
            usuario = self.buscar_usuario(emprestimo.usuario_id)
            usuario.multa_pendente = round(usuario.multa_pendente + multa, 2)

        livro = self.buscar_livro(emprestimo.livro_id)
        livro.disponivel = True

        return emprestimo

    def listar_emprestimos_do_usuario(self, usuario_id: str, apenas_em_aberto: bool = False):
        self.buscar_usuario(usuario_id)
        emprestimos = [
            emprestimo
            for emprestimo in self.armazenamento.emprestimos.listar()
            if emprestimo.usuario_id == usuario_id
        ]
        if apenas_em_aberto:
            emprestimos = [e for e in emprestimos if not e.devolvido]
        emprestimos.sort(key=lambda e: e.data_emprestimo, reverse=True)
        return emprestimos
