"""Estruturas de dados em memória e geração de identificadores sequenciais."""
from typing import Dict

from app.models import Emprestimo, Livro, Usuario


class Storage:
    def __init__(self) -> None:
        self.livros: Dict[int, Livro] = {}
        self.usuarios: Dict[int, Usuario] = {}
        self.emprestimos: Dict[int, Emprestimo] = {}
        self._proximo_id_livro = 1
        self._proximo_id_usuario = 1
        self._proximo_id_emprestimo = 1

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


storage = Storage()
