"""Armazenamento em memória do sistema de biblioteca.

Não há uso de banco de dados: todos os dados vivem em dicionários em
memória, válidos enquanto o processo da aplicação estiver em execução.
"""

from itertools import count
from typing import Dict, Optional

from models import Emprestimo, Livro, Usuario


class Repositorio:
    def __init__(self) -> None:
        self.livros: Dict[int, Livro] = {}
        self.usuarios: Dict[int, Usuario] = {}
        self.emprestimos: Dict[int, Emprestimo] = {}

        self._livro_id_seq = count(1)
        self._usuario_id_seq = count(1)
        self._emprestimo_id_seq = count(1)

    # ------------------------------------------------------------------
    # Livros
    # ------------------------------------------------------------------
    def proximo_id_livro(self) -> int:
        return next(self._livro_id_seq)

    def adicionar_livro(self, livro: Livro) -> Livro:
        self.livros[livro.id] = livro
        return livro

    def obter_livro(self, livro_id: int) -> Optional[Livro]:
        return self.livros.get(livro_id)

    def listar_livros(self):
        return list(self.livros.values())

    def remover_livro(self, livro_id: int) -> None:
        self.livros.pop(livro_id, None)

    def buscar_livro_por_isbn(self, isbn: str) -> Optional[Livro]:
        for livro in self.livros.values():
            if livro.isbn == isbn:
                return livro
        return None

    # ------------------------------------------------------------------
    # Usuários
    # ------------------------------------------------------------------
    def proximo_id_usuario(self) -> int:
        return next(self._usuario_id_seq)

    def adicionar_usuario(self, usuario: Usuario) -> Usuario:
        self.usuarios[usuario.id] = usuario
        return usuario

    def obter_usuario(self, usuario_id: int) -> Optional[Usuario]:
        return self.usuarios.get(usuario_id)

    def listar_usuarios(self):
        return list(self.usuarios.values())

    def buscar_usuario_por_email(self, email: str) -> Optional[Usuario]:
        for usuario in self.usuarios.values():
            if usuario.email.lower() == email.lower():
                return usuario
        return None

    # ------------------------------------------------------------------
    # Empréstimos
    # ------------------------------------------------------------------
    def proximo_id_emprestimo(self) -> int:
        return next(self._emprestimo_id_seq)

    def adicionar_emprestimo(self, emprestimo: Emprestimo) -> Emprestimo:
        self.emprestimos[emprestimo.id] = emprestimo
        return emprestimo

    def obter_emprestimo(self, emprestimo_id: int) -> Optional[Emprestimo]:
        return self.emprestimos.get(emprestimo_id)

    def listar_emprestimos(self):
        return list(self.emprestimos.values())

    def listar_emprestimos_por_usuario(self, usuario_id: int):
        return [
            emprestimo
            for emprestimo in self.emprestimos.values()
            if emprestimo.usuario_id == usuario_id
        ]

    def contar_emprestimos_abertos_do_usuario(self, usuario_id: int) -> int:
        return sum(
            1
            for emprestimo in self.emprestimos.values()
            if emprestimo.usuario_id == usuario_id and emprestimo.status == "aberto"
        )


# Instância única, compartilhada por toda a aplicação (armazenamento em
# memória do processo).
repositorio = Repositorio()
