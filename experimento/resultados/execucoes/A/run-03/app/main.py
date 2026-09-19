"""Instância da aplicação FastAPI e todas as rotas do sistema."""

import re
from datetime import date, timedelta
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.models import Emprestimo, Livro, Usuario
from app.storage import db

app = FastAPI()

VALOR_MULTA_DIARIA = 1.50
PRAZO_EMPRESTIMO_DIAS = 14
LIMITE_EMPRESTIMOS_ATIVOS = 3

_ISBN_REGEX = re.compile(r"^[0-9]{13}$")
_DATA_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ---------------------------------------------------------------------------
# Tratamento de erros (padrão global — Seção 10)
# ---------------------------------------------------------------------------


class ApiError(StarletteHTTPException):
    def __init__(self, status_code: int, mensagem: str):
        super().__init__(status_code=status_code, detail={"erro": mensagem})


@app.exception_handler(ApiError)
async def tratar_api_error(request: Request, exc: ApiError):
    return JSONResponse(status_code=exc.status_code, content=exc.detail)


@app.exception_handler(RequestValidationError)
async def tratar_validation_error(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"erro": "Dados inválidos"})


@app.exception_handler(StarletteHTTPException)
async def tratar_http_exception(request: Request, exc: StarletteHTTPException):
    if isinstance(exc.detail, dict) and "erro" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"erro": "Dados inválidos"})


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------


async def _ler_corpo_json(request: Request) -> dict:
    try:
        corpo = await request.json()
    except Exception:
        raise ApiError(422, "Dados inválidos")
    if not isinstance(corpo, dict):
        raise ApiError(422, "Dados inválidos")
    return corpo


def _eh_inteiro(valor) -> bool:
    return isinstance(valor, int) and not isinstance(valor, bool)


def _string_valida(valor, minimo: int, maximo: int) -> bool:
    if not isinstance(valor, str):
        return False
    tamanho = len(valor.strip())
    return minimo <= tamanho <= maximo


def _isbn_valido(valor) -> bool:
    return isinstance(valor, str) and bool(_ISBN_REGEX.fullmatch(valor))


def _email_valido(valor) -> bool:
    if not isinstance(valor, str):
        return False
    if valor.count("@") != 1:
        return False
    parte_local, parte_dominio = valor.split("@")
    return len(parte_local) >= 1 and len(parte_dominio) >= 1


def _data_valida(valor) -> bool:
    if not isinstance(valor, str) or not _DATA_REGEX.fullmatch(valor):
        return False
    try:
        date.fromisoformat(valor)
    except ValueError:
        return False
    return True


def _livro_para_dict(livro: dict) -> dict:
    return Livro(**livro).model_dump()


def _usuario_para_dict(usuario: dict) -> dict:
    return Usuario(**usuario).model_dump()


def _emprestimo_para_dict(emprestimo: dict) -> dict:
    return Emprestimo(**emprestimo).model_dump()


def _contar_emprestimos_ativos(usuario_id: int) -> int:
    return sum(
        1
        for emprestimo in db.emprestimos.values()
        if emprestimo["usuario_id"] == usuario_id and emprestimo["status"] == "ativo"
    )


def _livro_possui_emprestimo_ativo(livro_id: int) -> bool:
    return any(
        emprestimo["livro_id"] == livro_id and emprestimo["status"] == "ativo"
        for emprestimo in db.emprestimos.values()
    )


# ---------------------------------------------------------------------------
# Livros
# ---------------------------------------------------------------------------


@app.post("/livros", status_code=201)
async def cadastrar_livro(request: Request):
    corpo = await _ler_corpo_json(request)

    isbn = corpo.get("isbn")
    if isinstance(isbn, str) and not _isbn_valido(isbn):
        raise ApiError(422, "ISBN inválido")

    titulo = corpo.get("titulo")
    autor = corpo.get("autor")

    if (
        not _string_valida(titulo, 1, 200)
        or not _string_valida(autor, 1, 100)
        or not _isbn_valido(isbn)
    ):
        raise ApiError(422, "Dados inválidos")

    if any(livro["isbn"] == isbn for livro in db.livros.values()):
        raise ApiError(409, "ISBN já cadastrado")

    novo_id = db.gerar_id_livro()
    livro = {
        "id": novo_id,
        "titulo": titulo.strip(),
        "autor": autor.strip(),
        "isbn": isbn,
        "status": "disponivel",
    }
    db.livros[novo_id] = livro
    return _livro_para_dict(livro)


@app.get("/livros")
async def listar_livros(status: Optional[str] = None):
    if status is not None and status not in ("disponivel", "emprestado"):
        raise ApiError(422, "Dados inválidos")

    livros = list(db.livros.values())
    if status is not None:
        livros = [livro for livro in livros if livro["status"] == status]

    return [_livro_para_dict(livro) for livro in livros]


@app.get("/livros/{id}")
async def consultar_livro(id: int):
    livro = db.livros.get(id)
    if livro is None:
        raise ApiError(404, "Livro não encontrado")
    return _livro_para_dict(livro)


@app.delete("/livros/{id}", status_code=204)
async def excluir_livro(id: int):
    livro = db.livros.get(id)
    if livro is None:
        raise ApiError(404, "Livro não encontrado")
    if _livro_possui_emprestimo_ativo(id):
        raise ApiError(409, "Livro possui empréstimo ativo")
    del db.livros[id]
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Usuários
# ---------------------------------------------------------------------------


@app.post("/usuarios", status_code=201)
async def cadastrar_usuario(request: Request):
    corpo = await _ler_corpo_json(request)

    email = corpo.get("email")
    if isinstance(email, str) and not _email_valido(email):
        raise ApiError(422, "E-mail inválido")

    nome = corpo.get("nome")
    status_informado = corpo.get("status", "ativo")
    if status_informado is None:
        status_informado = "ativo"

    if (
        not _string_valida(nome, 1, 100)
        or not _email_valido(email)
        or status_informado not in ("ativo", "inativo")
    ):
        raise ApiError(422, "Dados inválidos")

    if any(usuario["email"] == email for usuario in db.usuarios.values()):
        raise ApiError(409, "E-mail já cadastrado")

    novo_id = db.gerar_id_usuario()
    usuario = {
        "id": novo_id,
        "nome": nome.strip(),
        "email": email,
        "status": status_informado,
        "multa_pendente": 0.0,
    }
    db.usuarios[novo_id] = usuario
    return _usuario_para_dict(usuario)


@app.get("/usuarios/{id}")
async def consultar_usuario(id: int):
    usuario = db.usuarios.get(id)
    if usuario is None:
        raise ApiError(404, "Usuário não encontrado")
    return _usuario_para_dict(usuario)


@app.get("/usuarios/{id}/emprestimos")
async def listar_emprestimos_usuario(id: int, status: Optional[str] = None):
    if status is not None and status not in ("ativo", "devolvido"):
        raise ApiError(422, "Dados inválidos")

    usuario = db.usuarios.get(id)
    if usuario is None:
        raise ApiError(404, "Usuário não encontrado")

    emprestimos = [
        emprestimo for emprestimo in db.emprestimos.values() if emprestimo["usuario_id"] == id
    ]
    if status is not None:
        emprestimos = [emprestimo for emprestimo in emprestimos if emprestimo["status"] == status]

    return [_emprestimo_para_dict(emprestimo) for emprestimo in emprestimos]


@app.post("/usuarios/{id}/pagamento-multa")
async def pagar_multa(id: int):
    usuario = db.usuarios.get(id)
    if usuario is None:
        raise ApiError(404, "Usuário não encontrado")
    if usuario["multa_pendente"] == 0:
        raise ApiError(409, "Usuário não possui multa pendente")
    usuario["multa_pendente"] = 0.0
    return _usuario_para_dict(usuario)


# ---------------------------------------------------------------------------
# Empréstimos e devoluções
# ---------------------------------------------------------------------------


@app.post("/emprestimos", status_code=201)
async def registrar_emprestimo(request: Request):
    corpo = await _ler_corpo_json(request)

    usuario_id = corpo.get("usuario_id")
    livro_id = corpo.get("livro_id")
    data_emprestimo_informada = corpo.get("data_emprestimo")

    if not _eh_inteiro(usuario_id) or not _eh_inteiro(livro_id):
        raise ApiError(422, "Dados inválidos")

    if data_emprestimo_informada is not None and not _data_valida(data_emprestimo_informada):
        raise ApiError(422, "Dados inválidos")

    usuario = db.usuarios.get(usuario_id)
    livro = db.livros.get(livro_id)

    if usuario is None:
        raise ApiError(404, "Usuário não encontrado")
    if livro is None:
        raise ApiError(404, "Livro não encontrado")

    if usuario["status"] == "inativo":
        raise ApiError(422, "Usuário inativo")
    if usuario["multa_pendente"] > 0:
        raise ApiError(422, "Usuário possui multa pendente")
    if _contar_emprestimos_ativos(usuario_id) >= LIMITE_EMPRESTIMOS_ATIVOS:
        raise ApiError(422, "Limite de empréstimos atingido")
    if livro["status"] == "emprestado":
        raise ApiError(409, "Livro indisponível")

    if data_emprestimo_informada is not None:
        data_emprestimo = date.fromisoformat(data_emprestimo_informada)
    else:
        data_emprestimo = date.today()

    data_devolucao_prevista = data_emprestimo + timedelta(days=PRAZO_EMPRESTIMO_DIAS)

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

    return _emprestimo_para_dict(emprestimo)


@app.post("/devolucoes")
async def registrar_devolucao(request: Request):
    corpo = await _ler_corpo_json(request)

    emprestimo_id = corpo.get("emprestimo_id")
    data_devolucao_informada = corpo.get("data_devolucao")

    if not _eh_inteiro(emprestimo_id):
        raise ApiError(422, "Dados inválidos")

    if data_devolucao_informada is not None and not _data_valida(data_devolucao_informada):
        raise ApiError(422, "Dados inválidos")

    emprestimo = db.emprestimos.get(emprestimo_id)
    if emprestimo is None:
        raise ApiError(404, "Empréstimo não encontrado")

    if emprestimo["status"] == "devolvido":
        raise ApiError(409, "Empréstimo já devolvido")

    if data_devolucao_informada is not None:
        data_devolucao = date.fromisoformat(data_devolucao_informada)
    else:
        data_devolucao = date.today()

    data_devolucao_prevista = date.fromisoformat(emprestimo["data_devolucao_prevista"])
    dias_atraso = (data_devolucao - data_devolucao_prevista).days
    multa = round(VALOR_MULTA_DIARIA * dias_atraso, 2) if dias_atraso > 0 else 0.0

    usuario = db.usuarios[emprestimo["usuario_id"]]
    usuario["multa_pendente"] = round(usuario["multa_pendente"] + multa, 2)

    emprestimo["data_devolucao_real"] = data_devolucao.isoformat()
    emprestimo["multa"] = multa
    emprestimo["status"] = "devolvido"

    livro = db.livros.get(emprestimo["livro_id"])
    if livro is not None:
        livro["status"] = "disponivel"

    return _emprestimo_para_dict(emprestimo)
