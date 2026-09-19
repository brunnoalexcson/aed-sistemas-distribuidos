"""Modelos Pydantic de entrada e saída."""

from typing import Any, Optional

from pydantic import BaseModel


class LivroCreate(BaseModel):
    titulo: Optional[Any] = None
    autor: Optional[Any] = None
    isbn: Optional[Any] = None


class Livro(BaseModel):
    id: int
    titulo: str
    autor: str
    isbn: str
    status: str


class UsuarioCreate(BaseModel):
    nome: Optional[Any] = None
    email: Optional[Any] = None
    status: Optional[Any] = None


class Usuario(BaseModel):
    id: int
    nome: str
    email: str
    status: str
    multa_pendente: float


class EmprestimoCreate(BaseModel):
    usuario_id: Optional[Any] = None
    livro_id: Optional[Any] = None
    data_emprestimo: Optional[Any] = None


class DevolucaoCreate(BaseModel):
    emprestimo_id: Optional[Any] = None
    data_devolucao: Optional[Any] = None


class Emprestimo(BaseModel):
    id: int
    usuario_id: int
    livro_id: int
    data_emprestimo: str
    data_devolucao_prevista: str
    data_devolucao_real: Optional[str] = None
    multa: float
    status: str
