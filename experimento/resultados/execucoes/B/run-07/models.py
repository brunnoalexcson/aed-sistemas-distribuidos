"""Modelos de dados do sistema de biblioteca.

Todos os dados são mantidos em memória (não há persistência em banco de
dados). Cada entidade possui um método `to_dict` usado para serialização
das respostas da API.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


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
    data_emprestimo: datetime
    data_prevista_devolucao: datetime
    data_devolucao: Optional[datetime] = None
    multa: float = 0.0
    status: str = "aberto"  # "aberto" ou "devolvido"

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
