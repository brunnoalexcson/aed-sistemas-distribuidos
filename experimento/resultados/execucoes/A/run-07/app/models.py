"""Modelos Pydantic de entrada e saída do sistema."""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class LivroCreate(BaseModel):
    model_config = ConfigDict(strict=True)

    titulo: str
    autor: str
    isbn: str

    @field_validator("isbn")
    @classmethod
    def validar_isbn(cls, v: str) -> str:
        if len(v) != 13 or not v.isdigit():
            raise ValueError("ISBN inválido")
        return v

    @field_validator("titulo")
    @classmethod
    def validar_titulo(cls, v: str) -> str:
        if not (1 <= len(v.strip()) <= 200):
            raise ValueError("Dados inválidos")
        return v

    @field_validator("autor")
    @classmethod
    def validar_autor(cls, v: str) -> str:
        if not (1 <= len(v.strip()) <= 100):
            raise ValueError("Dados inválidos")
        return v


class Livro(BaseModel):
    id: int
    titulo: str
    autor: str
    isbn: str
    status: Literal["disponivel", "emprestado"]


class UsuarioCreate(BaseModel):
    model_config = ConfigDict(strict=True)

    nome: str
    email: str
    status: Optional[str] = None

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, v: str) -> str:
        if not (1 <= len(v.strip()) <= 100):
            raise ValueError("Dados inválidos")
        return v

    @field_validator("email")
    @classmethod
    def validar_email(cls, v: str) -> str:
        if v.count("@") != 1:
            raise ValueError("E-mail inválido")
        parte_local, parte_dominio = v.split("@")
        if len(parte_local) < 1 or len(parte_dominio) < 1:
            raise ValueError("E-mail inválido")
        return v

    @field_validator("status")
    @classmethod
    def validar_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("ativo", "inativo"):
            raise ValueError("Dados inválidos")
        return v


class Usuario(BaseModel):
    id: int
    nome: str
    email: str
    status: Literal["ativo", "inativo"]
    multa_pendente: float


class EmprestimoCreate(BaseModel):
    model_config = ConfigDict(strict=True)

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
            raise ValueError("Dados inválidos")
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


class DevolucaoCreate(BaseModel):
    model_config = ConfigDict(strict=True)

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
            raise ValueError("Dados inválidos")
        return v
