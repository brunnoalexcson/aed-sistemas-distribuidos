"""Armazenamento em memória (sem banco de dados) para as entidades."""

import threading
from typing import Dict, List, Optional


class Repositorio:
    """Repositório genérico em memória, indexado por id, thread-safe."""

    def __init__(self):
        self._dados: Dict[str, object] = {}
        self._lock = threading.Lock()

    def adicionar(self, entidade):
        with self._lock:
            self._dados[entidade.id] = entidade
        return entidade

    def obter(self, id_: str) -> Optional[object]:
        return self._dados.get(id_)

    def listar(self) -> List[object]:
        return list(self._dados.values())

    def remover(self, id_: str) -> None:
        with self._lock:
            self._dados.pop(id_, None)


class Armazenamento:
    """Agrupa os repositórios de todas as entidades da aplicação."""

    def __init__(self):
        self.livros = Repositorio()
        self.usuarios = Repositorio()
        self.emprestimos = Repositorio()
