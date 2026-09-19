"""Entidades de domínio da biblioteca: Livro, Usuario e Emprestimo."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


def novo_id() -> str:
    return str(uuid.uuid4())


@dataclass
class Livro:
    titulo: str
    autor: str
    isbn: str
    id: str = field(default_factory=novo_id)
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
    nome: str
    email: str
    id: str = field(default_factory=novo_id)
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
    livro_id: str
    usuario_id: str
    data_emprestimo: datetime
    data_prevista_devolucao: datetime
    id: str = field(default_factory=novo_id)
    data_devolucao: Optional[datetime] = None
    multa: float = 0.0
    devolvido: bool = False

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
            "devolvido": self.devolvido,
            "em_atraso": (
                not self.devolvido
                and datetime.utcnow() > self.data_prevista_devolucao
            ),
        }
