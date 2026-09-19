"""Estado em memória (Seção 4) — implementação de REFERÊNCIA, escrita à mão.

Não faz parte do experimento: serve para validar que a suíte de conformidade
mede o que diz medir (teste de sanidade do instrumento).
"""
from itertools import count

livros: dict[int, dict] = {}
usuarios: dict[int, dict] = {}
emprestimos: dict[int, dict] = {}

_id_livro = count(1)
_id_usuario = count(1)
_id_emprestimo = count(1)


def proximo_id_livro() -> int:
    return next(_id_livro)


def proximo_id_usuario() -> int:
    return next(_id_usuario)


def proximo_id_emprestimo() -> int:
    return next(_id_emprestimo)
