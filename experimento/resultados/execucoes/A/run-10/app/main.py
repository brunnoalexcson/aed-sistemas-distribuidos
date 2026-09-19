"""
Sistema de Gestão de Biblioteca.

Instância da aplicação FastAPI e todas as rotas do sistema.

A aplicação é inicializável pelo comando:

    uvicorn app.main:app

executado a partir da pasta que contém a pasta "app".
"""

import re
from datetime import date, timedelta
from typing import Optional

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response

from app.models import (
    DevolucaoCreate,
    EmprestimoCreate,
    EmprestimoOut,
    LivroCreate,
    LivroOut,
    UsuarioCreate,
    UsuarioOut,
)
from app.storage import db

app = FastAPI()

_DATA_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_ISBN_RE = re.compile(r"^[0-9]{13}$")


# ---------------------------------------------------------------------------
# Erros
# ---------------------------------------------------------------------------

class AppError(Exception):
    """Erro de aplicação, convertido em resposta {"erro": "<mensagem>"}."""

    def __init__(self, status_code: int, mensagem: str) -> None:
        self.status_code = status_code
        self.mensagem = mensagem


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"erro": exc.mensagem})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # Cobre corpo malformado (JSON inválido) e parâmetros de rota com
    # tipo incorreto, garantindo o formato de erro padrão do sistema.
    return JSONResponse(status_code=422, content={"erro": "Dados inválidos"})


# ---------------------------------------------------------------------------
# Auxiliares de validação
# ---------------------------------------------------------------------------

def _is_int(valor) -> bool:
    return isinstance(valor, int) and not isinstance(valor, bool)


def _parse_data(valor: str) -> date:
    """Converte uma string AAAA-MM-DD em date. Lança ValueError se inválida."""
    if not isinstance(valor, str) or not _DATA_RE.fullmatch(valor):
        raise ValueError("formato de data inválido")
    return date.fromisoformat(valor)


def _email_valido(valor: str) -> bool:
    if valor.count("@") != 1:
        return False
    parte_local, parte_dominio = valor.split("@")
    return len(parte_local) >= 1 and len(parte_dominio) >= 1


def _livro_to_out(livro: dict) -> LivroOut:
    return LivroOut(**livro)


def _usuario_to_out(usuario: dict) -> UsuarioOut:
    return UsuarioOut(**usuario)


def _emprestimo_to_out(emprestimo: dict) -> EmprestimoOut:
    return EmprestimoOut(**emprestimo)


# ---------------------------------------------------------------------------
# RF-01 / RF-02 / RF-03 / RF-04 — Livros
# ---------------------------------------------------------------------------

@app.post("/livros", response_model=LivroOut, status_code=201)
async def cadastrar_livro(body: LivroCreate) -> LivroOut:
    titulo = body.titulo
    autor = body.autor
    isbn = body.isbn

    # Mensagens de formato específicas têm precedência sobre a genérica.
    if isinstance(isbn, str) and not _ISBN_RE.fullmatch(isbn):
        raise AppError(422, "ISBN inválido")

    if not isinstance(titulo, str) or not isinstance(autor, str) or not isinstance(isbn, str):
        raise AppError(422, "Dados inválidos")

    titulo_limpo = titulo.strip()
    autor_limpo = autor.strip()

    if not (1 <= len(titulo_limpo) <= 200):
        raise AppError(422, "Dados inválidos")
    if not (1 <= len(autor_limpo) <= 100):
        raise AppError(422, "Dados inválidos")

    if any(l["isbn"] == isbn for l in db.livros.values()):
        raise AppError(409, "ISBN já cadastrado")

    novo_id = db.gerar_id_livro()
    livro = {
        "id": novo_id,
        "titulo": titulo_limpo,
        "autor": autor_limpo,
        "isbn": isbn,
        "status": "disponivel",
    }
    db.livros[novo_id] = livro
    return _livro_to_out(livro)


@app.get("/livros", response_model=list)
async def listar_livros(status: Optional[str] = Query(default=None)):
    if status is not None and status not in ("disponivel", "emprestado"):
        raise AppError(422, "Dados inválidos")

    livros = list(db.livros.values())
    if status is not None:
        livros = [l for l in livros if l["status"] == status]

    return [_livro_to_out(l) for l in livros]


@app.get("/livros/{id}", response_model=LivroOut)
async def consultar_livro(id: int) -> LivroOut:
    livro = db.livros.get(id)
    if livro is None:
        raise AppError(404, "Livro não encontrado")
    return _livro_to_out(livro)


@app.delete("/livros/{id}", status_code=204)
async def excluir_livro(id: int) -> Response:
    livro = db.livros.get(id)
    if livro is None:
        raise AppError(404, "Livro não encontrado")

    tem_emprestimo_ativo = any(
        e["livro_id"] == id and e["status"] == "ativo" for e in db.emprestimos.values()
    )
    if tem_emprestimo_ativo:
        raise AppError(409, "Livro possui empréstimo ativo")

    del db.livros[id]
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# RF-05 / RF-06 — Usuários
# ---------------------------------------------------------------------------

@app.post("/usuarios", response_model=UsuarioOut, status_code=201)
async def cadastrar_usuario(body: UsuarioCreate) -> UsuarioOut:
    nome = body.nome
    email = body.email
    status_informado = body.status

    if isinstance(email, str) and not _email_valido(email):
        raise AppError(422, "E-mail inválido")

    if not isinstance(nome, str) or not isinstance(email, str):
        raise AppError(422, "Dados inválidos")

    nome_limpo = nome.strip()
    if not (1 <= len(nome_limpo) <= 100):
        raise AppError(422, "Dados inválidos")

    if status_informado is None:
        status_final = "ativo"
    else:
        if not isinstance(status_informado, str) or status_informado not in ("ativo", "inativo"):
            raise AppError(422, "Dados inválidos")
        status_final = status_informado

    if any(u["email"] == email for u in db.usuarios.values()):
        raise AppError(409, "E-mail já cadastrado")

    novo_id = db.gerar_id_usuario()
    usuario = {
        "id": novo_id,
        "nome": nome_limpo,
        "email": email,
        "status": status_final,
        "multa_pendente": 0.0,
    }
    db.usuarios[novo_id] = usuario
    return _usuario_to_out(usuario)


@app.get("/usuarios/{id}", response_model=UsuarioOut)
async def consultar_usuario(id: int) -> UsuarioOut:
    usuario = db.usuarios.get(id)
    if usuario is None:
        raise AppError(404, "Usuário não encontrado")
    return _usuario_to_out(usuario)


# ---------------------------------------------------------------------------
# RF-07 / RF-08 — Empréstimos e devoluções
# ---------------------------------------------------------------------------

@app.post("/emprestimos", response_model=EmprestimoOut, status_code=201)
async def registrar_emprestimo(body: EmprestimoCreate) -> EmprestimoOut:
    usuario_id = body.usuario_id
    livro_id = body.livro_id
    data_emprestimo_bruta = body.data_emprestimo

    if not _is_int(usuario_id) or not _is_int(livro_id):
        raise AppError(422, "Dados inválidos")

    data_emprestimo: date
    if data_emprestimo_bruta is None:
        data_emprestimo = date.today()
    else:
        try:
            data_emprestimo = _parse_data(data_emprestimo_bruta)
        except (ValueError, TypeError):
            raise AppError(422, "Dados inválidos")

    usuario = db.usuarios.get(usuario_id)
    if usuario is None:
        raise AppError(404, "Usuário não encontrado")

    livro = db.livros.get(livro_id)
    if livro is None:
        raise AppError(404, "Livro não encontrado")

    # RN-03
    if usuario["status"] == "inativo":
        raise AppError(422, "Usuário inativo")

    # RN-02
    if usuario["multa_pendente"] > 0:
        raise AppError(422, "Usuário possui multa pendente")

    # RN-01
    emprestimos_ativos = sum(
        1
        for e in db.emprestimos.values()
        if e["usuario_id"] == usuario_id and e["status"] == "ativo"
    )
    if emprestimos_ativos >= 3:
        raise AppError(422, "Limite de empréstimos atingido")

    # RN-05
    if livro["status"] == "emprestado":
        raise AppError(409, "Livro indisponível")

    data_devolucao_prevista = data_emprestimo + timedelta(days=14)

    novo_id = db.gerar_id_emprestimo()
    emprestimo = {
        "id": novo_id,
        "usuario_id": usuario_id,
        "livro_id": livro_id,
        "data_emprestimo": data_emprestimo.isoformat(),
        "data_devolucao_prevista": data_devolucao_prevista.isoformat(),
        "data_devolucao_real": None,
        "multa": 0.0,
        "status": "ativo",
    }
    db.emprestimos[novo_id] = emprestimo
    livro["status"] = "emprestado"

    return _emprestimo_to_out(emprestimo)


@app.post("/devolucoes", response_model=EmprestimoOut, status_code=200)
async def registrar_devolucao(body: DevolucaoCreate) -> EmprestimoOut:
    emprestimo_id = body.emprestimo_id
    data_devolucao_bruta = body.data_devolucao

    if not _is_int(emprestimo_id):
        raise AppError(422, "Dados inválidos")

    data_devolucao: date
    if data_devolucao_bruta is None:
        data_devolucao = date.today()
    else:
        try:
            data_devolucao = _parse_data(data_devolucao_bruta)
        except (ValueError, TypeError):
            raise AppError(422, "Dados inválidos")

    emprestimo = db.emprestimos.get(emprestimo_id)
    if emprestimo is None:
        raise AppError(404, "Empréstimo não encontrado")

    if emprestimo["status"] == "devolvido":
        raise AppError(409, "Empréstimo já devolvido")

    data_devolucao_prevista = date.fromisoformat(emprestimo["data_devolucao_prevista"])
    dias_atraso = (data_devolucao - data_devolucao_prevista).days

    if dias_atraso > 0:
        multa = round(1.50 * dias_atraso, 2)
    else:
        multa = 0.0

    emprestimo["data_devolucao_real"] = data_devolucao.isoformat()
    emprestimo["status"] = "devolvido"
    emprestimo["multa"] = multa

    usuario = db.usuarios[emprestimo["usuario_id"]]
    usuario["multa_pendente"] = round(usuario["multa_pendente"] + multa, 2)

    livro = db.livros[emprestimo["livro_id"]]
    livro["status"] = "disponivel"

    return _emprestimo_to_out(emprestimo)


# ---------------------------------------------------------------------------
# RF-09 — Listar empréstimos de um usuário
# ---------------------------------------------------------------------------

@app.get("/usuarios/{id}/emprestimos", response_model=list)
async def listar_emprestimos_usuario(id: int, status: Optional[str] = Query(default=None)):
    usuario = db.usuarios.get(id)
    if usuario is None:
        raise AppError(404, "Usuário não encontrado")

    if status is not None and status not in ("ativo", "devolvido"):
        raise AppError(422, "Dados inválidos")

    emprestimos = [e for e in db.emprestimos.values() if e["usuario_id"] == id]
    if status is not None:
        emprestimos = [e for e in emprestimos if e["status"] == status]

    return [_emprestimo_to_out(e) for e in emprestimos]


# ---------------------------------------------------------------------------
# RF-10 — Quitar multa do usuário
# ---------------------------------------------------------------------------

@app.post("/usuarios/{id}/pagamento-multa", response_model=UsuarioOut, status_code=200)
async def pagar_multa(id: int) -> UsuarioOut:
    usuario = db.usuarios.get(id)
    if usuario is None:
        raise AppError(404, "Usuário não encontrado")

    if usuario["multa_pendente"] == 0:
        raise AppError(409, "Usuário não possui multa pendente")

    usuario["multa_pendente"] = 0.0
    return _usuario_to_out(usuario)
