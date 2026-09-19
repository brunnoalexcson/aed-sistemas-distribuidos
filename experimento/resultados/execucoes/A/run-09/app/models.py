"""Modelos Pydantic de entrada e saída do sistema de gestão de biblioteca."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, field_validator


class LivroCreate(BaseModel):
    titulo: str
    autor: str
    isbn: str

    @field_validator("titulo")
    @classmethod
    def validar_titulo(cls, v: str) -> str:
        tamanho = len(v.strip())
        if tamanho < 1 or tamanho > 200:
            raise ValueError("titulo_invalido")
        return v

    @field_validator("autor")
    @classmethod
    def validar_autor(cls, v: str) -> str:
        tamanho = len(v.strip())
        if tamanho < 1 or tamanho > 100:
            raise ValueError("autor_invalido")
        return v

    @field_validator("isbn")
    @classmethod
    def validar_isbn(cls, v: str) -> str:
        if len(v) != 13 or not v.isdigit():
            raise ValueError("isbn_invalido")
        return v


class Livro(BaseModel):
    id: int
    titulo: str
    autor: str
    isbn: str
    status: Literal["disponivel", "emprestado"]


class UsuarioCreate(BaseModel):
    nome: str
    email: str
    status: Optional[Literal["ativo", "inativo"]] = None

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, v: str) -> str:
        tamanho = len(v.strip())
        if tamanho < 1 or tamanho > 100:
            raise ValueError("nome_invalido")
        return v

    @field_validator("email")
    @classmethod
    def validar_email(cls, v: str) -> str:
        if v.count("@") != 1:
            raise ValueError("email_invalido")
        antes, depois = v.split("@")
        if len(antes) < 1 or len(depois) < 1:
            raise ValueError("email_invalido")
        return v


class Usuario(BaseModel):
    id: int
    nome: str
    email: str
    status: Literal["ativo", "inativo"]
    multa_pendente: float


class EmprestimoCreate(BaseModel):
    usuario_id: int
    livro_id: int
    data_emprestimo: Optional[str] = None

    @field_validator("data_emprestimo")
    @classmethod
    def validar_data_emprestimo(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("data_invalida")
        return v


class DevolucaoCreate(BaseModel):
    emprestimo_id: int
    data_devolucao: Optional[str] = None

    @field_validator("data_devolucao")
    @classmethod
    def validar_data_devolucao(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("data_invalida")
        return v


class Emprestimo(BaseModel):
    id: int
    usuario_id: int
    livro_id: int
    data_emprestimo: str
    data_devolucao_prevista: str
    data_devolucao_real: Optional[str] = None
    multa: float
    status: Literal["ativo", "devolvido"]
