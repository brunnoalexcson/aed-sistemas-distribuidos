"""Modelos de dados da biblioteca: Livro, Usuario e Emprestimo.

São classes simples (dataclasses) mantidas inteiramente em memória, sem
qualquer dependência de banco de dados, conforme pedido na especificação.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional

STATUS_ABERTO = "aberto"
STATUS_DEVOLVIDO = "devolvido"


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
    livro_id: int
    usuario_id: int
    data_emprestimo: date
    data_prevista_devolucao: date
    data_devolucao: Optional[date] = None
    multa: float = 0.0
    status: str = STATUS_ABERTO

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "livro_id": self.livro_id,
            "usuario_id": self.usuario_id,
            "data_emprestimo": self.data_emprestimo.isoformat(),
            "data_prevista_devolucao": self.data_prevista_devolucao.isoformat(),
            "data_devolucao": (
                self.data_devolucao.isoformat() if self.data_devolucao else None
            ),
            "multa": round(self.multa, 2),
            "status": self.status,
        }
