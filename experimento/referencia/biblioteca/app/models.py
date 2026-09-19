"""Modelos de entrada (Seção 5).

Os campos são declarados com tipos permissivos de propósito: as validações de
tamanho e formato são aplicadas nas rotas, para respeitar a precedência de
mensagens definida na Seção 10.
"""
from pydantic import BaseModel


class LivroEntrada(BaseModel):
    titulo: str
    autor: str
    isbn: str


class UsuarioEntrada(BaseModel):
    nome: str
    email: str
    status: str | None = None


class EmprestimoEntrada(BaseModel):
    usuario_id: int
    livro_id: int
    data_emprestimo: str | None = None


class DevolucaoEntrada(BaseModel):
    emprestimo_id: int
    data_devolucao: str | None = None
