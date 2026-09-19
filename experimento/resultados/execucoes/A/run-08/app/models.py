"""Modelos Pydantic de entrada e saída."""

from typing import Optional

from pydantic import BaseModel


class LivroCreate(BaseModel):
    titulo: str
    autor: str
    isbn: str


class UsuarioCreate(BaseModel):
    nome: str
    email: str
    status: Optional[str] = None


class EmprestimoCreate(BaseModel):
    usuario_id: int
    livro_id: int
    data_emprestimo: Optional[str] = None


class DevolucaoCreate(BaseModel):
    emprestimo_id: int
    data_devolucao: Optional[str] = None
