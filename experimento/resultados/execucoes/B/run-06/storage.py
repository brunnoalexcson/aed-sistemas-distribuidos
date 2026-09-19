"""Camada de armazenamento em memória do sistema de biblioteca.

Não há uso de banco de dados: todos os dados vivem em estruturas Python
em memória, protegidas por um lock para permitir uso em contexto de
múltiplas threads (como o servidor de desenvolvimento do Flask).
"""
import threading
from datetime import datetime
from typing import Dict, List, Optional

from models import Emprestimo, Livro, Usuario


class Storage:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._livros: Dict[int, Livro] = {}
        self._usuarios: Dict[int, Usuario] = {}
        self._emprestimos: Dict[int, Emprestimo] = {}
        self._proximo_id_livro = 1
        self._proximo_id_usuario = 1
        self._proximo_id_emprestimo = 1

    # ---------- Livros ----------

    def criar_livro(self, titulo: str, autor: str, isbn: str) -> Livro:
        with self._lock:
            livro = Livro(
                id=self._proximo_id_livro,
                titulo=titulo,
                autor=autor,
                isbn=isbn,
            )
            self._livros[livro.id] = livro
            self._proximo_id_livro += 1
            return livro

    def listar_livros(self) -> List[Livro]:
        return list(self._livros.values())

    def obter_livro(self, livro_id: int) -> Optional[Livro]:
        return self._livros.get(livro_id)

    def remover_livro(self, livro_id: int) -> None:
        with self._lock:
            self._livros.pop(livro_id, None)

    # ---------- Usuários ----------

    def criar_usuario(self, nome: str, email: str) -> Usuario:
        with self._lock:
            usuario = Usuario(
                id=self._proximo_id_usuario,
                nome=nome,
                email=email,
            )
            self._usuarios[usuario.id] = usuario
            self._proximo_id_usuario += 1
            return usuario

    def listar_usuarios(self) -> List[Usuario]:
        return list(self._usuarios.values())

    def obter_usuario(self, usuario_id: int) -> Optional[Usuario]:
        return self._usuarios.get(usuario_id)

    # ---------- Empréstimos ----------

    def criar_emprestimo(
        self,
        livro_id: int,
        usuario_id: int,
        data_emprestimo: datetime,
        data_prevista_devolucao: datetime,
    ) -> Emprestimo:
        with self._lock:
            emprestimo = Emprestimo(
                id=self._proximo_id_emprestimo,
                livro_id=livro_id,
                usuario_id=usuario_id,
                data_emprestimo=data_emprestimo,
                data_prevista_devolucao=data_prevista_devolucao,
            )
            self._emprestimos[emprestimo.id] = emprestimo
            self._proximo_id_emprestimo += 1
            return emprestimo

    def listar_emprestimos(self) -> List[Emprestimo]:
        return list(self._emprestimos.values())

    def obter_emprestimo(self, emprestimo_id: int) -> Optional[Emprestimo]:
        return self._emprestimos.get(emprestimo_id)

    def emprestimos_do_usuario(self, usuario_id: int) -> List[Emprestimo]:
        return [e for e in self._emprestimos.values() if e.usuario_id == usuario_id]

    def emprestimos_abertos_do_usuario(self, usuario_id: int) -> List[Emprestimo]:
        return [
            e for e in self.emprestimos_do_usuario(usuario_id) if e.status == "aberto"
        ]


# Instância única, compartilhada por toda a aplicação.
storage = Storage()
