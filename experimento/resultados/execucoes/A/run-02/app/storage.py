"""Estruturas de dados em memória e geração de identificadores.

Toda a persistência do sistema é feita em estruturas nativas do Python
(``dict`` e ``list``), mantidas apenas durante a execução do processo.
"""

from typing import Dict, List, Optional


class Storage:
    """Armazena os dados do sistema em memória, no processo."""

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

    def isbn_existe(self, isbn: str, ignorar_id: Optional[int] = None) -> bool:
        for livro in self.livros.values():
            if livro["isbn"] == isbn and livro["id"] != ignorar_id:
                return True
        return False

    def email_existe(self, email: str, ignorar_id: Optional[int] = None) -> bool:
        for usuario in self.usuarios.values():
            if usuario["email"] == email and usuario["id"] != ignorar_id:
                return True
        return False

    def emprestimos_ativos_do_usuario(self, usuario_id: int) -> List[dict]:
        return [
            emprestimo
            for emprestimo in self.emprestimos.values()
            if emprestimo["usuario_id"] == usuario_id and emprestimo["status"] == "ativo"
        ]

    def livro_possui_emprestimo_ativo(self, livro_id: int) -> bool:
        return any(
            emprestimo["livro_id"] == livro_id and emprestimo["status"] == "ativo"
            for emprestimo in self.emprestimos.values()
        )

    def emprestimos_do_usuario(self, usuario_id: int) -> List[dict]:
        return [
            emprestimo
            for emprestimo in self.emprestimos.values()
            if emprestimo["usuario_id"] == usuario_id
        ]


storage = Storage()
