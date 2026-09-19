"""Regras de negócio do sistema de biblioteca.

Esta camada implementa as regras descritas pelo cliente:

- cadastro de livros e usuários;
- listagem e busca de livros;
- exclusão de livros (proibida quando o livro está emprestado);
- empréstimo de livros, com prazo de devolução de 2 semanas e as regras de
  limite de 3 livros por usuário, usuário inativo e usuário com multa
  pendente;
- devolução de livros, com cálculo de multa de R$ 1,50 por dia de atraso;
- pagamento de multas;
- consulta dos empréstimos de um usuário, com filtro para os que estão em
  aberto.
"""

from datetime import datetime, timedelta
from typing import Optional

from errors import ConflitoDeRegra, NaoEncontrado, RequisicaoInvalida
from models import Emprestimo, Livro, Usuario
from storage import Repositorio

PRAZO_EMPRESTIMO_DIAS = 14
LIMITE_LIVROS_POR_USUARIO = 3
VALOR_MULTA_POR_DIA = 1.50


class ServicoBiblioteca:
    def __init__(self, repositorio: Repositorio) -> None:
        self.repositorio = repositorio

    # ------------------------------------------------------------------
    # Livros
    # ------------------------------------------------------------------
    def cadastrar_livro(self, titulo: str, autor: str, isbn: str) -> Livro:
        titulo = (titulo or "").strip()
        autor = (autor or "").strip()
        isbn = (isbn or "").strip()

        if not titulo:
            raise RequisicaoInvalida("O campo 'titulo' é obrigatório.")
        if not autor:
            raise RequisicaoInvalida("O campo 'autor' é obrigatório.")
        if not isbn:
            raise RequisicaoInvalida("O campo 'isbn' é obrigatório.")

        if self.repositorio.buscar_livro_por_isbn(isbn) is not None:
            raise ConflitoDeRegra(f"Já existe um livro cadastrado com o ISBN '{isbn}'.")

        livro = Livro(
            id=self.repositorio.proximo_id_livro(),
            titulo=titulo,
            autor=autor,
            isbn=isbn,
        )
        return self.repositorio.adicionar_livro(livro)

    def listar_livros(self):
        return self.repositorio.listar_livros()

    def buscar_livro(self, livro_id: int) -> Livro:
        livro = self.repositorio.obter_livro(livro_id)
        if livro is None:
            raise NaoEncontrado(f"Livro com id {livro_id} não encontrado.")
        return livro

    def excluir_livro(self, livro_id: int) -> None:
        livro = self.buscar_livro(livro_id)
        if not livro.disponivel:
            raise ConflitoDeRegra(
                "Não é possível excluir um livro que está emprestado no momento."
            )
        self.repositorio.remover_livro(livro_id)

    # ------------------------------------------------------------------
    # Usuários
    # ------------------------------------------------------------------
    def cadastrar_usuario(self, nome: str, email: str) -> Usuario:
        nome = (nome or "").strip()
        email = (email or "").strip()

        if not nome:
            raise RequisicaoInvalida("O campo 'nome' é obrigatório.")
        if not email:
            raise RequisicaoInvalida("O campo 'email' é obrigatório.")

        if self.repositorio.buscar_usuario_por_email(email) is not None:
            raise ConflitoDeRegra(f"Já existe um usuário cadastrado com o e-mail '{email}'.")

        usuario = Usuario(
            id=self.repositorio.proximo_id_usuario(),
            nome=nome,
            email=email,
        )
        return self.repositorio.adicionar_usuario(usuario)

    def listar_usuarios(self):
        return self.repositorio.listar_usuarios()

    def buscar_usuario(self, usuario_id: int) -> Usuario:
        usuario = self.repositorio.obter_usuario(usuario_id)
        if usuario is None:
            raise NaoEncontrado(f"Usuário com id {usuario_id} não encontrado.")
        return usuario

    def atualizar_status_usuario(self, usuario_id: int, ativo: bool) -> Usuario:
        usuario = self.buscar_usuario(usuario_id)
        usuario.ativo = bool(ativo)
        return usuario

    # ------------------------------------------------------------------
    # Empréstimos
    # ------------------------------------------------------------------
    def registrar_emprestimo(self, usuario_id: int, livro_id: int) -> Emprestimo:
        usuario = self.buscar_usuario(usuario_id)
        livro = self.buscar_livro(livro_id)

        if not usuario.ativo:
            raise ConflitoDeRegra("Usuário inativo não pode pegar livro emprestado.")

        if usuario.multa_pendente > 0:
            raise ConflitoDeRegra(
                "Usuário possui multa pendente e está impedido de pegar livros "
                "emprestados até quitá-la."
            )

        if not livro.disponivel:
            raise ConflitoDeRegra("O livro não está disponível para empréstimo.")

        emprestimos_abertos = self.repositorio.contar_emprestimos_abertos_do_usuario(
            usuario_id
        )
        if emprestimos_abertos >= LIMITE_LIVROS_POR_USUARIO:
            raise ConflitoDeRegra(
                f"Usuário já possui o limite máximo de {LIMITE_LIVROS_POR_USUARIO} "
                "livros emprestados simultaneamente."
            )

        agora = datetime.now()
        emprestimo = Emprestimo(
            id=self.repositorio.proximo_id_emprestimo(),
            livro_id=livro.id,
            usuario_id=usuario.id,
            data_emprestimo=agora,
            data_prevista_devolucao=agora + timedelta(days=PRAZO_EMPRESTIMO_DIAS),
        )
        livro.disponivel = False
        return self.repositorio.adicionar_emprestimo(emprestimo)

    def devolver_livro(self, emprestimo_id: int) -> Emprestimo:
        emprestimo = self.repositorio.obter_emprestimo(emprestimo_id)
        if emprestimo is None:
            raise NaoEncontrado(f"Empréstimo com id {emprestimo_id} não encontrado.")

        if emprestimo.status != "aberto":
            raise ConflitoDeRegra("Este empréstimo já foi devolvido anteriormente.")

        agora = datetime.now()
        emprestimo.data_devolucao = agora
        emprestimo.status = "devolvido"

        dias_atraso = (agora.date() - emprestimo.data_prevista_devolucao.date()).days
        if dias_atraso > 0:
            multa = dias_atraso * VALOR_MULTA_POR_DIA
            emprestimo.multa = multa
            usuario = self.repositorio.obter_usuario(emprestimo.usuario_id)
            if usuario is not None:
                usuario.multa_pendente += multa

        livro = self.repositorio.obter_livro(emprestimo.livro_id)
        if livro is not None:
            livro.disponivel = True

        return emprestimo

    def listar_emprestimos_do_usuario(
        self, usuario_id: int, apenas_em_aberto: bool = False
    ):
        self.buscar_usuario(usuario_id)  # garante que o usuário existe
        emprestimos = self.repositorio.listar_emprestimos_por_usuario(usuario_id)
        if apenas_em_aberto:
            emprestimos = [e for e in emprestimos if e.status == "aberto"]
        return emprestimos

    def listar_emprestimos(self):
        return self.repositorio.listar_emprestimos()

    # ------------------------------------------------------------------
    # Multas
    # ------------------------------------------------------------------
    def pagar_multa(self, usuario_id: int) -> Usuario:
        usuario = self.buscar_usuario(usuario_id)
        if usuario.multa_pendente <= 0:
            raise ConflitoDeRegra("Usuário não possui multa pendente para pagar.")
        usuario.multa_pendente = 0.0
        return usuario
