"""Instância da aplicação FastAPI e todas as rotas do sistema."""

from datetime import date, datetime, timedelta
from typing import Any, Optional

from fastapi import FastAPI, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.models import (
    DevolucaoCreate,
    Emprestimo,
    EmprestimoCreate,
    Livro,
    LivroCreate,
    Usuario,
    UsuarioCreate,
)
from app.storage import db


class AppError(Exception):
    """Erro de aplicação com status HTTP e mensagem exata a ser retornada."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message


app = FastAPI()


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"erro": exc.message})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(status_code=422, content={"erro": "Dados inválidos"})


# ---------------------------------------------------------------------------
# Funções auxiliares de validação
# ---------------------------------------------------------------------------


def _is_non_bool_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _valid_date_string(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def _valid_isbn_format(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return value.isascii() and value.isdigit() and len(value) == 13


def _valid_email_format(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    if value.count("@") != 1:
        return False
    local, dominio = value.split("@")
    return len(local) >= 1 and len(dominio) >= 1


# ---------------------------------------------------------------------------
# RF-01 / RF-02 / RF-03 / RF-04 — Livros
# ---------------------------------------------------------------------------


@app.post("/livros", status_code=201)
async def criar_livro(body: LivroCreate) -> JSONResponse:
    isbn = body.isbn

    if isinstance(isbn, str) and not _valid_isbn_format(isbn):
        raise AppError(422, "ISBN inválido")

    titulo_valido = isinstance(body.titulo, str) and 1 <= len(body.titulo.strip()) <= 200
    autor_valido = isinstance(body.autor, str) and 1 <= len(body.autor.strip()) <= 100
    isbn_valido = _valid_isbn_format(isbn)

    if not (titulo_valido and autor_valido and isbn_valido):
        raise AppError(422, "Dados inválidos")

    titulo = body.titulo.strip()
    autor = body.autor.strip()

    if any(livro["isbn"] == isbn for livro in db.livros.values()):
        raise AppError(409, "ISBN já cadastrado")

    livro_id = db.next_livro_id()
    livro = Livro(id=livro_id, titulo=titulo, autor=autor, isbn=isbn, status="disponivel")
    db.livros[livro_id] = livro.model_dump()

    return JSONResponse(status_code=201, content=db.livros[livro_id])


@app.get("/livros")
async def listar_livros(status: Optional[str] = Query(default=None)) -> JSONResponse:
    if status is not None and status not in ("disponivel", "emprestado"):
        raise AppError(422, "Dados inválidos")

    livros = list(db.livros.values())
    if status is not None:
        livros = [livro for livro in livros if livro["status"] == status]

    return JSONResponse(status_code=200, content=livros)


@app.get("/livros/{livro_id}")
async def consultar_livro(livro_id: int) -> JSONResponse:
    livro = db.livros.get(livro_id)
    if livro is None:
        raise AppError(404, "Livro não encontrado")

    return JSONResponse(status_code=200, content=livro)


@app.delete("/livros/{livro_id}", status_code=204)
async def excluir_livro(livro_id: int) -> Response:
    livro = db.livros.get(livro_id)
    if livro is None:
        raise AppError(404, "Livro não encontrado")

    possui_emprestimo_ativo = any(
        emprestimo["livro_id"] == livro_id and emprestimo["status"] == "ativo"
        for emprestimo in db.emprestimos.values()
    )
    if possui_emprestimo_ativo:
        raise AppError(409, "Livro possui empréstimo ativo")

    del db.livros[livro_id]

    return Response(status_code=204)


# ---------------------------------------------------------------------------
# RF-05 / RF-06 — Usuários
# ---------------------------------------------------------------------------


@app.post("/usuarios", status_code=201)
async def criar_usuario(body: UsuarioCreate) -> JSONResponse:
    email = body.email

    if isinstance(email, str) and not _valid_email_format(email):
        raise AppError(422, "E-mail inválido")

    nome_valido = isinstance(body.nome, str) and 1 <= len(body.nome.strip()) <= 100
    email_valido = _valid_email_format(email)
    status_bruto = body.status
    status_valido = status_bruto is None or status_bruto in ("ativo", "inativo")

    if not (nome_valido and email_valido and status_valido):
        raise AppError(422, "Dados inválidos")

    nome = body.nome.strip()
    status_final = status_bruto if status_bruto is not None else "ativo"

    if any(usuario["email"] == email for usuario in db.usuarios.values()):
        raise AppError(409, "E-mail já cadastrado")

    usuario_id = db.next_usuario_id()
    usuario = Usuario(
        id=usuario_id,
        nome=nome,
        email=email,
        status=status_final,
        multa_pendente=0.0,
    )
    db.usuarios[usuario_id] = usuario.model_dump()

    return JSONResponse(status_code=201, content=db.usuarios[usuario_id])


@app.get("/usuarios/{usuario_id}")
async def consultar_usuario(usuario_id: int) -> JSONResponse:
    usuario = db.usuarios.get(usuario_id)
    if usuario is None:
        raise AppError(404, "Usuário não encontrado")

    return JSONResponse(status_code=200, content=usuario)


# ---------------------------------------------------------------------------
# RF-07 — Registrar empréstimo
# ---------------------------------------------------------------------------


@app.post("/emprestimos", status_code=201)
async def registrar_emprestimo(body: EmprestimoCreate) -> JSONResponse:
    usuario_id = body.usuario_id
    livro_id = body.livro_id
    data_emprestimo_bruta = body.data_emprestimo

    usuario_id_valido = _is_non_bool_int(usuario_id)
    livro_id_valido = _is_non_bool_int(livro_id)
    data_valida = data_emprestimo_bruta is None or _valid_date_string(data_emprestimo_bruta)

    if not (usuario_id_valido and livro_id_valido and data_valida):
        raise AppError(422, "Dados inválidos")

    usuario = db.usuarios.get(usuario_id)
    if usuario is None:
        raise AppError(404, "Usuário não encontrado")

    livro = db.livros.get(livro_id)
    if livro is None:
        raise AppError(404, "Livro não encontrado")

    if usuario["status"] == "inativo":
        raise AppError(422, "Usuário inativo")

    if usuario["multa_pendente"] > 0:
        raise AppError(422, "Usuário possui multa pendente")

    emprestimos_ativos = sum(
        1
        for emprestimo in db.emprestimos.values()
        if emprestimo["usuario_id"] == usuario_id and emprestimo["status"] == "ativo"
    )
    if emprestimos_ativos >= 3:
        raise AppError(422, "Limite de empréstimos atingido")

    if livro["status"] == "emprestado":
        raise AppError(409, "Livro indisponível")

    data_emprestimo = (
        data_emprestimo_bruta if data_emprestimo_bruta is not None else date.today().isoformat()
    )
    data_emprestimo_data = datetime.strptime(data_emprestimo, "%Y-%m-%d").date()
    data_devolucao_prevista = (data_emprestimo_data + timedelta(days=14)).isoformat()

    emprestimo_id = db.next_emprestimo_id()
    emprestimo = Emprestimo(
        id=emprestimo_id,
        usuario_id=usuario_id,
        livro_id=livro_id,
        data_emprestimo=data_emprestimo,
        data_devolucao_prevista=data_devolucao_prevista,
        data_devolucao_real=None,
        multa=0.0,
        status="ativo",
    )
    db.emprestimos[emprestimo_id] = emprestimo.model_dump()

    livro["status"] = "emprestado"

    return JSONResponse(status_code=201, content=db.emprestimos[emprestimo_id])


# ---------------------------------------------------------------------------
# RF-08 — Registrar devolução
# ---------------------------------------------------------------------------


@app.post("/devolucoes", status_code=200)
async def registrar_devolucao(body: DevolucaoCreate) -> JSONResponse:
    emprestimo_id = body.emprestimo_id
    data_devolucao_bruta = body.data_devolucao

    emprestimo_id_valido = _is_non_bool_int(emprestimo_id)
    data_valida = data_devolucao_bruta is None or _valid_date_string(data_devolucao_bruta)

    if not (emprestimo_id_valido and data_valida):
        raise AppError(422, "Dados inválidos")

    emprestimo = db.emprestimos.get(emprestimo_id)
    if emprestimo is None:
        raise AppError(404, "Empréstimo não encontrado")

    if emprestimo["status"] == "devolvido":
        raise AppError(409, "Empréstimo já devolvido")

    data_devolucao = (
        data_devolucao_bruta if data_devolucao_bruta is not None else date.today().isoformat()
    )
    data_devolucao_data = datetime.strptime(data_devolucao, "%Y-%m-%d").date()
    data_prevista_data = datetime.strptime(
        emprestimo["data_devolucao_prevista"], "%Y-%m-%d"
    ).date()

    atraso = (data_devolucao_data - data_prevista_data).days
    if atraso > 0:
        multa = round(1.50 * atraso, 2)
    else:
        multa = 0.0

    usuario = db.usuarios[emprestimo["usuario_id"]]
    usuario["multa_pendente"] = round(usuario["multa_pendente"] + multa, 2)

    emprestimo["data_devolucao_real"] = data_devolucao
    emprestimo["multa"] = multa
    emprestimo["status"] = "devolvido"

    livro = db.livros[emprestimo["livro_id"]]
    livro["status"] = "disponivel"

    return JSONResponse(status_code=200, content=emprestimo)


# ---------------------------------------------------------------------------
# RF-09 — Listar empréstimos de um usuário
# ---------------------------------------------------------------------------


@app.get("/usuarios/{usuario_id}/emprestimos")
async def listar_emprestimos_usuario(
    usuario_id: int, status: Optional[str] = Query(default=None)
) -> JSONResponse:
    if status is not None and status not in ("ativo", "devolvido"):
        raise AppError(422, "Dados inválidos")

    usuario = db.usuarios.get(usuario_id)
    if usuario is None:
        raise AppError(404, "Usuário não encontrado")

    emprestimos = [
        emprestimo
        for emprestimo in db.emprestimos.values()
        if emprestimo["usuario_id"] == usuario_id
    ]
    if status is not None:
        emprestimos = [emprestimo for emprestimo in emprestimos if emprestimo["status"] == status]

    return JSONResponse(status_code=200, content=emprestimos)


# ---------------------------------------------------------------------------
# RF-10 — Quitar multa do usuário
# ---------------------------------------------------------------------------


@app.post("/usuarios/{usuario_id}/pagamento-multa")
async def pagar_multa(usuario_id: int) -> JSONResponse:
    usuario = db.usuarios.get(usuario_id)
    if usuario is None:
        raise AppError(404, "Usuário não encontrado")

    if usuario["multa_pendente"] == 0:
        raise AppError(409, "Usuário não possui multa pendente")

    usuario["multa_pendente"] = 0.0

    return JSONResponse(status_code=200, content=usuario)
