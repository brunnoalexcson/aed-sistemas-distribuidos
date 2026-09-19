"""Estruturas de dados em memória e geração de identificadores."""


class Storage:
    """Armazena o estado do sistema em memória, no processo.

    O estado é perdido ao encerrar o processo, e isso é aceito conforme a
    especificação (Seção 4).
    """

    def __init__(self):
        self.livros = {}
        self.usuarios = {}
        self.emprestimos = {}
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


db = Storage()
