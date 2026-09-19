"""Estruturas de dados em memória e geração de identificadores."""

from typing import Dict


class Storage:
    """Armazena os dados do sistema em memória, no processo."""

    def __init__(self) -> None:
        self.livros: Dict[int, dict] = {}
        self.usuarios: Dict[int, dict] = {}
        self.emprestimos: Dict[int, dict] = {}

        self._livro_seq: int = 0
        self._usuario_seq: int = 0
        self._emprestimo_seq: int = 0

    def next_livro_id(self) -> int:
        self._livro_seq += 1
        return self._livro_seq

    def next_usuario_id(self) -> int:
        self._usuario_seq += 1
        return self._usuario_seq

    def next_emprestimo_id(self) -> int:
        self._emprestimo_seq += 1
        return self._emprestimo_seq


storage = Storage()
