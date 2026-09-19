"""Armazenamento em memória do sistema de biblioteca.

Não há banco de dados: livros, usuários e empréstimos são mantidos em
dicionários em memória, válidos enquanto o processo da aplicação estiver
em execução.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .models import Livro, Usuario, Emprestimo


class Storage:
    def __init__(self):
        self._livros: Dict[int, Livro] = {}
        self._usuarios: Dict[int, Usuario] = {}
        self._emprestimos: Dict[int, Emprestimo] = {}

        self._proximo_id_livro = 1
        self._proximo_id_usuario = 1
        self._proximo_id_emprestimo = 1

    # ------------------------------------------------------------------
    # Livros
    # ------------------------------------------------------------------
    def novo_id_livro(self) -> int:
        novo_id = self._proximo_id_livro
        self._proximo_id_livro += 1
        return novo_id

    def salvar_livro(self, livro: Livro) -> Livro:
        self._livros[livro.id] = livro
        return livro

    def obter_livro(self, livro_id: int) -> Optional[Livro]:
        return self._livros.get(livro_id)

    def listar_livros(self) -> List[Livro]:
        return list(self._livros.values())

    def remover_livro(self, livro_id: int) -> None:
        self._livros.pop(livro_id, None)

    def existe_isbn(self, isbn: str) -> bool:
        return any(livro.isbn == isbn for livro in self._livros.values())

    # ------------------------------------------------------------------
    # Usuários
    # ------------------------------------------------------------------
    def novo_id_usuario(self) -> int:
        novo_id = self._proximo_id_usuario
        self._proximo_id_usuario += 1
        return novo_id

    def salvar_usuario(self, usuario: Usuario) -> Usuario:
        self._usuarios[usuario.id] = usuario
        return usuario

    def obter_usuario(self, usuario_id: int) -> Optional[Usuario]:
        return self._usuarios.get(usuario_id)

    def listar_usuarios(self) -> List[Usuario]:
        return list(self._usuarios.values())

    def existe_email(self, email: str) -> bool:
        return any(usuario.email.lower() == email.lower() for usuario in self._usuarios.values())

    # ------------------------------------------------------------------
    # Empréstimos
    # ------------------------------------------------------------------
    def novo_id_emprestimo(self) -> int:
        novo_id = self._proximo_id_emprestimo
        self._proximo_id_emprestimo += 1
        return novo_id

    def salvar_emprestimo(self, emprestimo: Emprestimo) -> Emprestimo:
        self._emprestimos[emprestimo.id] = emprestimo
        return emprestimo

    def obter_emprestimo(self, emprestimo_id: int) -> Optional[Emprestimo]:
        return self._emprestimos.get(emprestimo_id)

    def listar_emprestimos(self) -> List[Emprestimo]:
        return list(self._emprestimos.values())

    def listar_emprestimos_por_usuario(self, usuario_id: int) -> List[Emprestimo]:
        return [e for e in self._emprestimos.values() if e.usuario_id == usuario_id]

    def contar_emprestimos_abertos_do_usuario(self, usuario_id: int) -> int:
        return sum(
            1
            for e in self._emprestimos.values()
            if e.usuario_id == usuario_id and e.em_aberto
        )
