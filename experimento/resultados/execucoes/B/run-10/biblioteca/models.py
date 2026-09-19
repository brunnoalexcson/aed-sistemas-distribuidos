"""Modelos de domínio do sistema de biblioteca.

Todos os modelos são simples containers de dados (dataclasses) com um
método `to_dict` para facilitar a serialização em JSON pelas rotas Flask.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

# Prazo padrão de devolução de um empréstimo.
PRAZO_EMPRESTIMO_DIAS = 14

# Valor da multa por dia de atraso na devolução.
VALOR_MULTA_POR_DIA = 1.50


def _iso(dt: Optional[datetime]) -> Optional[str]:
    """Converte um datetime para string ISO 8601, preservando None."""
    return dt.isoformat() if dt is not None else None


@dataclass
class Livro:
    id: int
    titulo: str
    autor: str
    isbn: str
    disponivel: bool = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "titulo": self.titulo,
            "autor": self.autor,
            "isbn": self.isbn,
            "disponivel": self.disponivel,
        }


@dataclass
class Usuario:
    id: int
    nome: str
    email: str
    ativo: bool = True
    multa_pendente: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "ativo": self.ativo,
            "multa_pendente": round(self.multa_pendente, 2),
        }


@dataclass
class Emprestimo:
    id: int
    usuario_id: int
    livro_id: int
    data_emprestimo: datetime
    data_prevista_devolucao: datetime
    data_devolucao: Optional[datetime] = None
    multa_aplicada: float = 0.0
    status: str = "aberto"  # "aberto" ou "devolvido"

    @staticmethod
    def calcular_data_prevista(data_emprestimo: datetime) -> datetime:
        return data_emprestimo + timedelta(days=PRAZO_EMPRESTIMO_DIAS)

    @property
    def em_aberto(self) -> bool:
        return self.status == "aberto"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "livro_id": self.livro_id,
            "data_emprestimo": _iso(self.data_emprestimo),
            "data_prevista_devolucao": _iso(self.data_prevista_devolucao),
            "data_devolucao": _iso(self.data_devolucao),
            "multa_aplicada": round(self.multa_aplicada, 2),
            "status": self.status,
        }
