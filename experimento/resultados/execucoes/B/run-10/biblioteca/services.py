"""Regras de negócio do sistema de biblioteca.

Esta camada concentra toda a lógica de domínio (cadastro de livros e
usuários, controle de empréstimos, cálculo de multas etc.), mantendo as
rotas Flask enxutas e focadas apenas em request/response HTTP.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import List, Optional

from .errors import ConflitoDeRegra, ErroDeValidacao, RecursoNaoEncontrado
from .models import Emprestimo, Livro, Usuario, VALOR_MULTA_POR_DIA
from .storage import Storage

MAX_EMPRESTIMOS_POR_USUARIO = 3


def _texto_valido(valor, campo: str) -> str:
    if not isinstance(valor, str) or not valor.strip():
        raise ErroDeValidacao(f"O campo '{campo}' é obrigatório e deve ser um texto não vazio.")
    return valor.strip()


class LibraryService:
    def __init__(self, storage: Storage):
        self.storage = storage

    # ------------------------------------------------------------------
    # Livros
    # ------------------------------------------------------------------
    def cadastrar_livro(self, dados: dict) -> Livro:
        titulo = _texto_valido(dados.get("titulo"), "titulo")
        autor = _texto_valido(dados.get("autor"), "autor")
        isbn = _texto_valido(dados.get("isbn"), "isbn")

        if self.storage.existe_isbn(isbn):
            raise ConflitoDeRegra(f"Já existe um livro cadastrado com o ISBN '{isbn}'.")

        livro = Livro(id=self.storage.novo_id_livro(), titulo=titulo, autor=autor, isbn=isbn)
        return self.storage.salvar_livro(livro)

    def listar_livros(self, disponivel: Optional[bool] = None) -> List[Livro]:
        livros = self.storage.listar_livros()
        if disponivel is not None:
            livros = [l for l in livros if l.disponivel == disponivel]
        return livros

    def buscar_livro(self, livro_id: int) -> Livro:
        livro = self.storage.obter_livro(livro_id)
        if livro is None:
            raise RecursoNaoEncontrado(f"Livro com id {livro_id} não encontrado.")
        return livro

    def excluir_livro(self, livro_id: int) -> None:
        livro = self.buscar_livro(livro_id)
        if not livro.disponivel:
            raise ConflitoDeRegra(
                "Não é possível excluir um livro que está emprestado no momento."
            )
        self.storage.remover_livro(livro_id)

    # ------------------------------------------------------------------
    # Usuários
    # ------------------------------------------------------------------
    def cadastrar_usuario(self, dados: dict) -> Usuario:
        nome = _texto_valido(dados.get("nome"), "nome")
        email = _texto_valido(dados.get("email"), "email")

        if "@" not in email or "." not in email.split("@")[-1]:
            raise ErroDeValidacao("O campo 'email' deve conter um e-mail válido.")

        if self.storage.existe_email(email):
            raise ConflitoDeRegra(f"Já existe um usuário cadastrado com o e-mail '{email}'.")

        usuario = Usuario(id=self.storage.novo_id_usuario(), nome=nome, email=email)
        return self.storage.salvar_usuario(usuario)

    def listar_usuarios(self) -> List[Usuario]:
        return self.storage.listar_usuarios()

    def buscar_usuario(self, usuario_id: int) -> Usuario:
        usuario = self.storage.obter_usuario(usuario_id)
        if usuario is None:
            raise RecursoNaoEncontrado(f"Usuário com id {usuario_id} não encontrado.")
        return usuario

    def atualizar_usuario(self, usuario_id: int, dados: dict) -> Usuario:
        usuario = self.buscar_usuario(usuario_id)

        if "nome" in dados:
            usuario.nome = _texto_valido(dados.get("nome"), "nome")

        if "email" in dados:
            novo_email = _texto_valido(dados.get("email"), "email")
            if "@" not in novo_email or "." not in novo_email.split("@")[-1]:
                raise ErroDeValidacao("O campo 'email' deve conter um e-mail válido.")
            if novo_email.lower() != usuario.email.lower() and self.storage.existe_email(novo_email):
                raise ConflitoDeRegra(f"Já existe um usuário cadastrado com o e-mail '{novo_email}'.")
            usuario.email = novo_email

        if "ativo" in dados:
            if not isinstance(dados.get("ativo"), bool):
                raise ErroDeValidacao("O campo 'ativo' deve ser um valor booleano (true ou false).")
            usuario.ativo = dados["ativo"]

        return self.storage.salvar_usuario(usuario)

    def registrar_pagamento_multa(self, usuario_id: int) -> Usuario:
        usuario = self.buscar_usuario(usuario_id)
        if usuario.multa_pendente <= 0:
            raise ErroDeValidacao("O usuário não possui multa pendente para pagamento.")
        usuario.multa_pendente = 0.0
        return self.storage.salvar_usuario(usuario)

    # ------------------------------------------------------------------
    # Empréstimos
    # ------------------------------------------------------------------
    def registrar_emprestimo(self, dados: dict) -> Emprestimo:
        usuario_id = dados.get("usuario_id")
        livro_id = dados.get("livro_id")

        if not isinstance(usuario_id, int) or not isinstance(livro_id, int):
            raise ErroDeValidacao(
                "Os campos 'usuario_id' e 'livro_id' são obrigatórios e devem ser inteiros."
            )

        usuario = self.buscar_usuario(usuario_id)
        livro = self.buscar_livro(livro_id)

        if not usuario.ativo:
            raise ConflitoDeRegra("Usuário inativo não pode pegar livro emprestado.")

        if usuario.multa_pendente > 0:
            raise ConflitoDeRegra(
                "Usuário está com multa pendente e não pode pegar livro emprestado até quitá-la."
            )

        if not livro.disponivel:
            raise ConflitoDeRegra("O livro solicitado não está disponível para empréstimo.")

        emprestimos_abertos = self.storage.contar_emprestimos_abertos_do_usuario(usuario_id)
        if emprestimos_abertos >= MAX_EMPRESTIMOS_POR_USUARIO:
            raise ConflitoDeRegra(
                f"Usuário já possui o máximo de {MAX_EMPRESTIMOS_POR_USUARIO} livros emprestados."
            )

        agora = datetime.now()
        emprestimo = Emprestimo(
            id=self.storage.novo_id_emprestimo(),
            usuario_id=usuario_id,
            livro_id=livro_id,
            data_emprestimo=agora,
            data_prevista_devolucao=Emprestimo.calcular_data_prevista(agora),
        )

        livro.disponivel = False
        self.storage.salvar_livro(livro)
        return self.storage.salvar_emprestimo(emprestimo)

    def listar_emprestimos(self, em_aberto: Optional[bool] = None) -> List[Emprestimo]:
        emprestimos = self.storage.listar_emprestimos()
        if em_aberto is not None:
            emprestimos = [e for e in emprestimos if e.em_aberto == em_aberto]
        return emprestimos

    def buscar_emprestimo(self, emprestimo_id: int) -> Emprestimo:
        emprestimo = self.storage.obter_emprestimo(emprestimo_id)
        if emprestimo is None:
            raise RecursoNaoEncontrado(f"Empréstimo com id {emprestimo_id} não encontrado.")
        return emprestimo

    def listar_emprestimos_do_usuario(
        self, usuario_id: int, em_aberto: Optional[bool] = None
    ) -> List[Emprestimo]:
        self.buscar_usuario(usuario_id)  # garante que o usuário existe (404 caso contrário)
        emprestimos = self.storage.listar_emprestimos_por_usuario(usuario_id)
        if em_aberto is not None:
            emprestimos = [e for e in emprestimos if e.em_aberto == em_aberto]
        return emprestimos

    def registrar_devolucao(self, emprestimo_id: int) -> Emprestimo:
        emprestimo = self.buscar_emprestimo(emprestimo_id)

        if not emprestimo.em_aberto:
            raise ConflitoDeRegra("Este empréstimo já foi devolvido anteriormente.")

        agora = datetime.now()
        dias_atraso = 0
        if agora > emprestimo.data_prevista_devolucao:
            diferenca = agora - emprestimo.data_prevista_devolucao
            dias_atraso = math.ceil(diferenca.total_seconds() / 86400)

        multa = round(dias_atraso * VALOR_MULTA_POR_DIA, 2) if dias_atraso > 0 else 0.0

        emprestimo.data_devolucao = agora
        emprestimo.status = "devolvido"
        emprestimo.multa_aplicada = multa
        self.storage.salvar_emprestimo(emprestimo)

        livro = self.storage.obter_livro(emprestimo.livro_id)
        if livro is not None:
            livro.disponivel = True
            self.storage.salvar_livro(livro)

        if multa > 0:
            usuario = self.storage.obter_usuario(emprestimo.usuario_id)
            if usuario is not None:
                usuario.multa_pendente = round(usuario.multa_pendente + multa, 2)
                self.storage.salvar_usuario(usuario)

        return emprestimo
