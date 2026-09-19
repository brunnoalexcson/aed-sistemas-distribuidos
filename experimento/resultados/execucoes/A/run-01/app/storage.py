from typing import Dict


class Storage:
    """Estruturas de dados em memória e geração de identificadores sequenciais."""

    def __init__(self) -> None:
        self.livros: Dict[int, dict] = {}
        self.usuarios: Dict[int, dict] = {}
        self.emprestimos: Dict[int, dict] = {}
        self._proximo_id_livro: int = 1
        self._proximo_id_usuario: int = 1
        self._proximo_id_emprestimo: int = 1

    def proximo_id_livro(self) -> int:
        novo_id = self._proximo_id_livro
        self._proximo_id_livro += 1
        return novo_id

    def proximo_id_usuario(self) -> int:
        novo_id = self._proximo_id_usuario
        self._proximo_id_usuario += 1
        return novo_id

    def proximo_id_emprestimo(self) -> int:
        novo_id = self._proximo_id_emprestimo
        self._proximo_id_emprestimo += 1
        return novo_id


storage = Storage()
