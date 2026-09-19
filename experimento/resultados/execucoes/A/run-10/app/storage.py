"""
Estruturas de dados em memória e geração de identificadores para o
Sistema de Gestão de Biblioteca.

Toda a persistência é feita apenas em memória, no processo, usando
estruturas de dados nativas do Python (dict e list). O estado é
perdido quando o processo é encerrado.
"""

from typing import Dict


class Storage:
    """Contém todo o estado em memória da aplicação."""

    def __init__(self) -> None:
        self.livros: Dict[int, dict] = {}
        self.usuarios: Dict[int, dict] = {}
        self.emprestimos: Dict[int, dict] = {}

        self._proximo_id_livro: int = 1
        self._proximo_id_usuario: int = 1
        self._proximo_id_emprestimo: int = 1

    def gerar_id_livro(self) -> int:
        novo_id = self._proximo_id_livro
        self._proximo_id_livro += 1
        return novo_id

    def gerar_id_usuario(self) -> int:
        novo_id = self._proximo_id_usuario
        self._proximo_id_usuario += 1
        return novo_id

    def gerar_id_emprestimo(self) -> int:
        novo_id = self._proximo_id_emprestimo
        self._proximo_id_emprestimo += 1
        return novo_id


# Instância única, compartilhada por toda a aplicação.
db = Storage()
