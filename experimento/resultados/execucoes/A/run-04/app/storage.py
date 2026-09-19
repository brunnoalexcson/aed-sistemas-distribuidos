"""Estruturas de dados em memória e geração de identificadores.

Todo o estado do sistema é mantido no processo, usando apenas estruturas
nativas do Python (dict e list). O estado é perdido ao encerrar o processo.
"""

from typing import Dict


class Storage:
    """Mantém o estado do sistema em memória e gera identificadores sequenciais."""

    def __init__(self) -> None:
        self.livros: Dict[int, dict] = {}
        self.usuarios: Dict[int, dict] = {}
        self.emprestimos: Dict[int, dict] = {}

        self._proximo_livro_id: int = 1
        self._proximo_usuario_id: int = 1
        self._proximo_emprestimo_id: int = 1

    def next_livro_id(self) -> int:
        novo_id = self._proximo_livro_id
        self._proximo_livro_id += 1
        return novo_id

    def next_usuario_id(self) -> int:
        novo_id = self._proximo_usuario_id
        self._proximo_usuario_id += 1
        return novo_id

    def next_emprestimo_id(self) -> int:
        novo_id = self._proximo_emprestimo_id
        self._proximo_emprestimo_id += 1
        return novo_id


storage = Storage()
