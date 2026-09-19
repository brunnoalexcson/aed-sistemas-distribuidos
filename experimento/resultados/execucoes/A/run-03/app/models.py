"""Modelos Pydantic de entrada e saída."""

from typing import Optional

from pydantic import BaseModel


class Livro(BaseModel):
    id: int
    titulo: str
    autor: str
    isbn: str
    status: str


class Usuario(BaseModel):
    id: int
    nome: str
    email: str
    status: str
    multa_pendente: float


class Emprestimo(BaseModel):
    id: int
    usuario_id: int
    livro_id: int
    data_emprestimo: str
    data_devolucao_prevista: str
    data_devolucao_real: Optional[str] = None
    multa: float
    status: str
