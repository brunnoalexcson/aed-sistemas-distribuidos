"""Instância da aplicação FastAPI e todas as rotas do sistema de gestão
de biblioteca."""

from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import storage
from app.models import (
    DevolucaoCreate,
    Emprestimo,
    EmprestimoCreate,
    Livro,
    LivroCreate,
    Usuario,
    UsuarioCreate,
)

app = FastAPI()


class ApiError(Exception):
    """Erro de aplicação com status HTTP e mensagem no formato da Seção 10."""

    def __init__(self, status_code: int, mensagem: str):
        self.status_code = status_code
        self.mensagem = mensagem


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"erro": exc.mensagem})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    erros = exc.errors()
    for erro in erros:
        loc = erro.get("loc", ())
        campo = loc[-1] if loc else None
        if campo == "isbn" and erro.get("type") == "value_error":
            return JSONResponse(status_code=422, content={"erro": "ISBN inválido"})
        if campo == "email" and erro.get("type") == "value_error":
            return JSONResponse(status_code=422, content={"erro": "E-mail inválido"})
    return JSONResponse(status_code=422, content={"erro": "Dados inválidos"})


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    mensagem = exc.detail if isinstance(exc.detail, str) else "Erro"
    return JSONResponse(status_code=exc.status_code, content={"erro": mensagem})


@app.exception_handler(Exception)
async def erro_interno_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500, content={"erro": "Erro interno do servidor"}
    )


# ---------------------------------------------------------------------------
# Livros
# ---------------------------------------------------------------------------


@app.post("/livros", status_code=201, response_model=Livro)
async def criar_livro(payload: LivroCreate):
    isbn_existente = any(l["isbn"] == payload.isbn for l in storage.livros.values())
    if isbn_existente:
        raise ApiError(409, "ISBN já cadastrado")

    novo_id = storage.proximo_id_livro()
    livro = {
        "id": novo_id,
        "titulo": payload.titulo,
        "autor": payload.autor,
        "isbn": payload.isbn,
        "status": "disponivel",
    }
    storage.livros[novo_id] = livro
    return livro


@app.get("/livros", response_model=List[Livro])
async def listar_livros(status: Optional[str] = None):
    if status is not None and status not in ("disponivel", "emprestado"):
        raise ApiError(422, "Dados inválidos")

    resultado = list(storage.livros.values())
    if status is not None:
        resultado = [l for l in resultado if l["status"] == status]
    return resultado


@app.get("/livros/{id}", response_model=Livro)
async def consultar_livro(id: int):
    livro = storage.livros.get(id)
    if livro is None:
        raise ApiError(404, "Livro não encontrado")
    return livro


@app.delete("/livros/{id}", status_code=204)
async def excluir_livro(id: int):
    livro = storage.livros.get(id)
    if livro is None:
        raise ApiError(404, "Livro não encontrado")

    tem_emprestimo_ativo = any(
        e["livro_id"] == id and e["status"] == "ativo"
        for e in storage.emprestimos.values()
    )
    if tem_emprestimo_ativo:
        raise ApiError(409, "Livro possui empréstimo ativo")

    del storage.livros[id]
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Usuários
# ---------------------------------------------------------------------------


@app.post("/usuarios", status_code=201, response_model=Usuario)
async def criar_usuario(payload: UsuarioCreate):
    email_existente = any(
        u["email"] == payload.email for u in storage.usuarios.values()
    )
    if email_existente:
        raise ApiError(409, "E-mail já cadastrado")

    novo_id = storage.proximo_id_usuario()
    usuario = {
        "id": novo_id,
        "nome": payload.nome,
        "email": payload.email,
        "status": payload.status if payload.status is not None else "ativo",
        "multa_pendente": 0.0,
    }
    storage.usuarios[novo_id] = usuario
    return usuario


@app.get("/usuarios/{id}", response_model=Usuario)
async def consultar_usuario(id: int):
    usuario = storage.usuarios.get(id)
    if usuario is None:
        raise ApiError(404, "Usuário não encontrado")
    return usuario


# ---------------------------------------------------------------------------
# Empréstimos
# ---------------------------------------------------------------------------


@app.post("/emprestimos", status_code=201, response_model=Emprestimo)
async def registrar_emprestimo(payload: EmprestimoCreate):
    usuario = storage.usuarios.get(payload.usuario_id)
    if usuario is None:
        raise ApiError(404, "Usuário não encontrado")

    livro = storage.livros.get(payload.livro_id)
    if livro is None:
        raise ApiError(404, "Livro não encontrado")

    if usuario["status"] == "inativo":
        raise ApiError(422, "Usuário inativo")

    if usuario["multa_pendente"] > 0:
        raise ApiError(422, "Usuário possui multa pendente")

    emprestimos_ativos = sum(
        1
        for e in storage.emprestimos.values()
        if e["usuario_id"] == usuario["id"] and e["status"] == "ativo"
    )
    if emprestimos_ativos >= 3:
        raise ApiError(422, "Limite de empréstimos atingido")

    if livro["status"] == "emprestado":
        raise ApiError(409, "Livro indisponível")

    if payload.data_emprestimo is not None:
        data_emprestimo_str = payload.data_emprestimo
    else:
        data_emprestimo_str = date.today().isoformat()

    data_emprestimo_obj = datetime.strptime(data_emprestimo_str, "%Y-%m-%d").date()
    data_prevista_obj = data_emprestimo_obj + timedelta(days=14)
    data_devolucao_prevista_str = data_prevista_obj.isoformat()

    novo_id = storage.proximo_id_emprestimo()
    emprestimo = {
        "id": novo_id,
        "usuario_id": usuario["id"],
        "livro_id": livro["id"],
        "data_emprestimo": data_emprestimo_str,
        "data_devolucao_prevista": data_devolucao_prevista_str,
        "data_devolucao_real": None,
        "multa": 0.0,
        "status": "ativo",
    }
    storage.emprestimos[novo_id] = emprestimo
    livro["status"] = "emprestado"
    return emprestimo


@app.post("/devolucoes", response_model=Emprestimo)
async def registrar_devolucao(payload: DevolucaoCreate):
    emprestimo = storage.emprestimos.get(payload.emprestimo_id)
    if emprestimo is None:
        raise ApiError(404, "Empréstimo não encontrado")

    if emprestimo["status"] == "devolvido":
        raise ApiError(409, "Empréstimo já devolvido")

    if payload.data_devolucao is not None:
        data_devolucao_str = payload.data_devolucao
    else:
        data_devolucao_str = date.today().isoformat()

    data_prevista_obj = datetime.strptime(
        emprestimo["data_devolucao_prevista"], "%Y-%m-%d"
    ).date()
    data_devolucao_obj = datetime.strptime(data_devolucao_str, "%Y-%m-%d").date()

    dias_atraso = (data_devolucao_obj - data_prevista_obj).days
    if dias_atraso > 0:
        multa = round(1.50 * dias_atraso, 2)
    else:
        multa = 0.0

    emprestimo["data_devolucao_real"] = data_devolucao_str
    emprestimo["multa"] = multa
    emprestimo["status"] = "devolvido"

    usuario = storage.usuarios.get(emprestimo["usuario_id"])
    if usuario is not None:
        usuario["multa_pendente"] = round(usuario["multa_pendente"] + multa, 2)

    livro = storage.livros.get(emprestimo["livro_id"])
    if livro is not None:
        livro["status"] = "disponivel"

    return emprestimo


@app.get("/usuarios/{id}/emprestimos", response_model=List[Emprestimo])
async def listar_emprestimos_usuario(id: int, status: Optional[str] = None):
    if status is not None and status not in ("ativo", "devolvido"):
        raise ApiError(422, "Dados inválidos")

    usuario = storage.usuarios.get(id)
    if usuario is None:
        raise ApiError(404, "Usuário não encontrado")

    resultado = [e for e in storage.emprestimos.values() if e["usuario_id"] == id]
    if status is not None:
        resultado = [e for e in resultado if e["status"] == status]
    return resultado


@app.post("/usuarios/{id}/pagamento-multa", response_model=Usuario)
async def pagar_multa(id: int):
    usuario = storage.usuarios.get(id)
    if usuario is None:
        raise ApiError(404, "Usuário não encontrado")

    if usuario["multa_pendente"] == 0:
        raise ApiError(409, "Usuário não possui multa pendente")

    usuario["multa_pendente"] = 0.0
    return usuario
