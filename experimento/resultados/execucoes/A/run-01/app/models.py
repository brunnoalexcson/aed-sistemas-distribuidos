from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, field_validator


def _formato_data_valido(valor: str) -> bool:
    try:
        datetime.strptime(valor, "%Y-%m-%d")
    except (ValueError, TypeError):
        return False
    return True


class LivroCreate(BaseModel):
    titulo: str
    autor: str
    isbn: str

    @field_validator("titulo")
    @classmethod
    def validar_titulo(cls, valor: str) -> str:
        texto = valor.strip()
        if len(texto) < 1 or len(texto) > 200:
            raise ValueError("titulo fora dos limites de tamanho")
        return valor

    @field_validator("autor")
    @classmethod
    def validar_autor(cls, valor: str) -> str:
        texto = valor.strip()
        if len(texto) < 1 or len(texto) > 100:
            raise ValueError("autor fora dos limites de tamanho")
        return valor

    @field_validator("isbn")
    @classmethod
    def validar_isbn(cls, valor: str) -> str:
        if len(valor) != 13 or not valor.isdigit():
            raise ValueError("isbn invalido")
        return valor


class LivroOut(BaseModel):
    id: int
    titulo: str
    autor: str
    isbn: str
    status: str


class UsuarioCreate(BaseModel):
    nome: str
    email: str
    status: Optional[Literal["ativo", "inativo"]] = None

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, valor: str) -> str:
        texto = valor.strip()
        if len(texto) < 1 or len(texto) > 100:
            raise ValueError("nome fora dos limites de tamanho")
        return valor

    @field_validator("email")
    @classmethod
    def validar_email(cls, valor: str) -> str:
        if valor.count("@") != 1:
            raise ValueError("email invalido")
        parte_local, parte_dominio = valor.split("@")
        if len(parte_local) < 1 or len(parte_dominio) < 1:
            raise ValueError("email invalido")
        return valor


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

    @field_validator("data_emprestimo")
    @classmethod
    def validar_data_emprestimo(cls, valor: Optional[str]) -> Optional[str]:
        if valor is None:
            return valor
        if not _formato_data_valido(valor):
            raise ValueError("data_emprestimo invalida")
        return valor


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

    @field_validator("data_devolucao")
    @classmethod
    def validar_data_devolucao(cls, valor: Optional[str]) -> Optional[str]:
        if valor is None:
            return valor
        if not _formato_data_valido(valor):
            raise ValueError("data_devolucao invalida")
        return valor
