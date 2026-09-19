"""Estruturas de dados em memória e geração de identificadores.

Este módulo mantém todo o estado do sistema usando apenas estruturas de
dados nativas do Python (dict e list). O estado é perdido ao encerrar o
processo, e isso é aceito conforme a especificação.
"""

from typing import Dict

# Acervo de livros: id -> dados do livro
livros: Dict[int, dict] = {}

# Usuários cadastrados: id -> dados do usuário
usuarios: Dict[int, dict] = {}

# Empréstimos registrados: id -> dados do empréstimo
emprestimos: Dict[int, dict] = {}

_livro_id_seq = 0
_usuario_id_seq = 0
_emprestimo_id_seq = 0


def proximo_id_livro() -> int:
    """Gera o próximo id sequencial para um livro, iniciando em 1."""
    global _livro_id_seq
    _livro_id_seq += 1
    return _livro_id_seq


def proximo_id_usuario() -> int:
    """Gera o próximo id sequencial para um usuário, iniciando em 1."""
    global _usuario_id_seq
    _usuario_id_seq += 1
    return _usuario_id_seq


def proximo_id_emprestimo() -> int:
    """Gera o próximo id sequencial para um empréstimo, iniciando em 1."""
    global _emprestimo_id_seq
    _emprestimo_id_seq += 1
    return _emprestimo_id_seq
