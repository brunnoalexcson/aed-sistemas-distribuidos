"""Armazenamento em memória para a API da biblioteca.

Toda a persistência do sistema é feita em estruturas de dados em memória
(process-local), sem uso de banco de dados. Um lock simples garante geração
segura de identificadores em caso de requisições concorrentes.
"""

import threading
from typing import Dict

from models import Emprestimo, Livro, Usuario


class Storage:
    def __init__(self):
        self._lock = threading.Lock()
        self.livros: Dict[int, Livro] = {}
        self.usuarios: Dict[int, Usuario] = {}
        self.emprestimos: Dict[int, Emprestimo] = {}
        self._livro_seq = 0
        self._usuario_seq = 0
        self._emprestimo_seq = 0

    def next_livro_id(self) -> int:
        with self._lock:
            self._livro_seq += 1
            return self._livro_seq

    def next_usuario_id(self) -> int:
        with self._lock:
            self._usuario_seq += 1
            return self._usuario_seq

    def next_emprestimo_id(self) -> int:
        with self._lock:
            self._emprestimo_seq += 1
            return self._emprestimo_seq

    def reset(self) -> None:
        """Limpa todos os dados (útil para reiniciar o estado da API)."""
        with self._lock:
            self.livros.clear()
            self.usuarios.clear()
            self.emprestimos.clear()
            self._livro_seq = 0
            self._usuario_seq = 0
            self._emprestimo_seq = 0


# Instância única compartilhada por toda a aplicação.
storage = Storage()
