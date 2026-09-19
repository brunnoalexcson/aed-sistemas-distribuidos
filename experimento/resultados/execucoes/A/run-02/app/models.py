"""Modelos Pydantic de entrada e saída do sistema."""

from typing import Optional

from pydantic import BaseModel


class LivroCreate(BaseModel):
    titulo: str
    autor: str
    isbn: str


class LivroOut(BaseModel):
    id: int
    titulo: str
    autor: str
    isbn: str
    status: str


class UsuarioCreate(BaseModel):
    nome: str
    email: str
    status: Optional[str] = None


class UsuarioOut(BaseModel):
    id: int
    nome: str
    email: str
    status: str
    multa_pendente: float


class EmprestimoCreate(BaseModel):
    usuario_id: int
    livro_id: int
    data_emprestimo: Optional[str] = None


class EmprestimoOut(BaseModel):
    id: int
    usuario_id: int
    livro_id: int
    data_emprestimo: str
    data_devolucao_prevista: str
    data_devolucao_real: Optional[str] = None
    multa: float
    status: str


class DevolucaoCreate(BaseModel):
    emprestimo_id: int
    data_devolucao: Optional[str] = None
