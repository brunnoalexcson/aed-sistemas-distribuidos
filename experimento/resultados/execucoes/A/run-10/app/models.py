"""
Modelos Pydantic de entrada e saída do Sistema de Gestão de Biblioteca.

Os modelos de entrada aceitam os campos com tipagem permissiva
(``Any``) propositalmente: a validação de formato, tamanho e regras de
negócio é feita manualmente nas rotas de app/main.py, para que as
mensagens de erro retornadas sigam exatamente o formato definido na
especificação (``{"erro": "<mensagem>"}``), em vez do formato padrão
de erro de validação do FastAPI/Pydantic.
"""

from typing import Any, Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Livro
# ---------------------------------------------------------------------------

class LivroCreate(BaseModel):
    titulo: Any = None
    autor: Any = None
    isbn: Any = None


class LivroOut(BaseModel):
    id: int
    titulo: str
    autor: str
    isbn: str
    status: str


# ---------------------------------------------------------------------------
# Usuario
# ---------------------------------------------------------------------------

class UsuarioCreate(BaseModel):
    nome: Any = None
    email: Any = None
    status: Any = None


class UsuarioOut(BaseModel):
    id: int
    nome: str
    email: str
    status: str
    multa_pendente: float


# ---------------------------------------------------------------------------
# Emprestimo
# ---------------------------------------------------------------------------

class EmprestimoCreate(BaseModel):
    usuario_id: Any = None
    livro_id: Any = None
    data_emprestimo: Any = None


class EmprestimoOut(BaseModel):
    id: int
    usuario_id: int
    livro_id: int
    data_emprestimo: str
    data_devolucao_prevista: str
    data_devolucao_real: Optional[str]
    multa: float
    status: str


# ---------------------------------------------------------------------------
# Devolucao
# ---------------------------------------------------------------------------

class DevolucaoCreate(BaseModel):
    emprestimo_id: Any = None
    data_devolucao: Any = None
