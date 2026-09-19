"""Armazenamento em memória (repositórios) do sistema de biblioteca.

Não há persistência em banco de dados: todos os dados vivem apenas
enquanto o processo da aplicação estiver em execução.
"""

from typing import Dict, Optional

from app.models import Emprestimo, Livro, Usuario


class RepositorioLivros:
    def __init__(self):
        self._dados: Dict[int, Livro] = {}
        self._proximo_id = 1

    def criar(self, titulo: str, autor: str, isbn: str) -> Livro:
        livro = Livro(id=self._proximo_id, titulo=titulo, autor=autor, isbn=isbn)
        self._dados[livro.id] = livro
        self._proximo_id += 1
        return livro

    def listar(self) -> list:
        return list(self._dados.values())

    def buscar(self, livro_id: int) -> Optional[Livro]:
        return self._dados.get(livro_id)

    def remover(self, livro_id: int) -> None:
        self._dados.pop(livro_id, None)


class RepositorioUsuarios:
    def __init__(self):
        self._dados: Dict[int, Usuario] = {}
        self._proximo_id = 1

    def criar(self, nome: str, email: str) -> Usuario:
        usuario = Usuario(id=self._proximo_id, nome=nome, email=email)
        self._dados[usuario.id] = usuario
        self._proximo_id += 1
        return usuario

    def listar(self) -> list:
        return list(self._dados.values())

    def buscar(self, usuario_id: int) -> Optional[Usuario]:
        return self._dados.get(usuario_id)


class RepositorioEmprestimos:
    def __init__(self):
        self._dados: Dict[int, Emprestimo] = {}
        self._proximo_id = 1

    def criar(self, livro_id: int, usuario_id: int, data_emprestimo, data_prevista_devolucao) -> Emprestimo:
        emprestimo = Emprestimo(
            id=self._proximo_id,
            livro_id=livro_id,
            usuario_id=usuario_id,
            data_emprestimo=data_emprestimo,
            data_prevista_devolucao=data_prevista_devolucao,
        )
        self._dados[emprestimo.id] = emprestimo
        self._proximo_id += 1
        return emprestimo

    def listar(self) -> list:
        return list(self._dados.values())

    def buscar(self, emprestimo_id: int) -> Optional[Emprestimo]:
        return self._dados.get(emprestimo_id)

    def listar_por_usuario(self, usuario_id: int) -> list:
        return [e for e in self._dados.values() if e.usuario_id == usuario_id]

    def emprestimos_abertos_por_usuario(self, usuario_id: int) -> list:
        return [e for e in self._dados.values() if e.usuario_id == usuario_id and not e.devolvido]

    def emprestimo_aberto_por_livro(self, livro_id: int) -> Optional[Emprestimo]:
        for emprestimo in self._dados.values():
            if emprestimo.livro_id == livro_id and not emprestimo.devolvido:
                return emprestimo
        return None


# Instâncias únicas (singletons) usadas por toda a aplicação, já que
# tudo é mantido em memória em um único processo.
repositorio_livros = RepositorioLivros()
repositorio_usuarios = RepositorioUsuarios()
repositorio_emprestimos = RepositorioEmprestimos()
