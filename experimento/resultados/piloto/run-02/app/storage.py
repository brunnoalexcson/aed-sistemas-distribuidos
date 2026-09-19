class Storage:
    """Estruturas de dados em memória e geração de identificadores sequenciais."""

    def __init__(self):
        self.livros = {}
        self.usuarios = {}
        self.emprestimos = {}
        self._proximo_livro_id = 1
        self._proximo_usuario_id = 1
        self._proximo_emprestimo_id = 1

    def gerar_livro_id(self):
        novo_id = self._proximo_livro_id
        self._proximo_livro_id += 1
        return novo_id

    def gerar_usuario_id(self):
        novo_id = self._proximo_usuario_id
        self._proximo_usuario_id += 1
        return novo_id

    def gerar_emprestimo_id(self):
        novo_id = self._proximo_emprestimo_id
        self._proximo_emprestimo_id += 1
        return novo_id


db = Storage()
