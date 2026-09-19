"""Modelos Pydantic de entrada e saida."""

from typing import Annotated, Literal, Optional

from pydantic import BaseModel, StringConstraints

TituloStr = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]
AutorStr = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]
NomeStr = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]


class LivroCreate(BaseModel):
    titulo: TituloStr
    autor: AutorStr
    isbn: str


class LivroOut(BaseModel):
    id: int
    titulo: str
    autor: str
    isbn: str
    status: str


class UsuarioCreate(BaseModel):
    nome: NomeStr
    email: str
    status: Optional[Literal["ativo", "inativo"]] = None


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


class DevolucaoCreate(BaseModel):
    emprestimo_id: int
    data_devolucao: Optional[str] = None


class EmprestimoOut(BaseModel):
    id: int
    usuario_id: int
    livro_id: int
    data_emprestimo: str
    data_devolucao_prevista: str
    data_devolucao_real: Optional[str] = None
    multa: float
    status: str
