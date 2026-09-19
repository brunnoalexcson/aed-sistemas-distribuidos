"""Estruturas de dados em memoria e geracao de identificadores."""


class Storage:
    def __init__(self):
        self.livros = {}
        self.usuarios = {}
        self.emprestimos = {}
        self._livro_seq = 0
        self._usuario_seq = 0
        self._emprestimo_seq = 0

    def proximo_id_livro(self):
        self._livro_seq += 1
        return self._livro_seq

    def proximo_id_usuario(self):
        self._usuario_seq += 1
        return self._usuario_seq

    def proximo_id_emprestimo(self):
        self._emprestimo_seq += 1
        return self._emprestimo_seq


storage = Storage()
