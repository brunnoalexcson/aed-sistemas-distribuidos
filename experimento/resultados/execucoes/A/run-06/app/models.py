"""Modelos Pydantic de entrada e saída do Sistema de Gestão de Biblioteca."""

from typing import Any, Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Modelos de entrada (corpos de requisição)
#
# Os campos são tipados como `Any` propositalmente: a validação de formato,
# tipo e regra de negócio é feita manualmente nas rotas, de modo a permitir
# o controle exato das mensagens de erro e da ordem de precedência definidos
# na Seção 10 da especificação.
# ---------------------------------------------------------------------------


class LivroCreate(BaseModel):
    titulo: Any = None
    autor: Any = None
    isbn: Any = None


class UsuarioCreate(BaseModel):
    nome: Any = None
    email: Any = None
    status: Any = None


class EmprestimoCreate(BaseModel):
    usuario_id: Any = None
    livro_id: Any = None
    data_emprestimo: Any = None


class DevolucaoCreate(BaseModel):
    emprestimo_id: Any = None
    data_devolucao: Any = None


# ---------------------------------------------------------------------------
# Modelos de saída (entidades completas)
# ---------------------------------------------------------------------------


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
    data_devolucao_real: Optional[str]
    multa: float
    status: str
