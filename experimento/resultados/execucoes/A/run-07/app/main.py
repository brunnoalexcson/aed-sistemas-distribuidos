"""Instância da aplicação FastAPI e definição de todas as rotas."""
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.models import (
    DevolucaoCreate,
    Emprestimo,
    EmprestimoCreate,
    Livro,
    LivroCreate,
    Usuario,
    UsuarioCreate,
)
from app.storage import storage

app = FastAPI()


def erro(status_code: int, mensagem: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"erro": mensagem})


@app.exception_handler(RequestValidationError)
async def tratar_erro_validacao(request: Request, exc: RequestValidationError) -> JSONResponse:
    return erro(422, "Dados inválidos")


@app.exception_handler(StarletteHTTPException)
async def tratar_erro_http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and set(exc.detail.keys()) == {"erro"}:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return erro(exc.status_code, "Dados inválidos")


async def _corpo_json(request: Request) -> Optional[dict]:
    try:
        dados = await request.json()
    except Exception:
        return None
    if not isinstance(dados, dict):
        return None
    return dados


def _data_hoje() -> str:
    return date.today().isoformat()


def _parse_data(valor: str) -> date:
    return datetime.strptime(valor, "%Y-%m-%d").date()


def _mensagem_erro_validacao(exc: ValidationError, mensagens_especificas: list) -> str:
    textos = [item.get("msg", "") for item in exc.errors()]
    for mensagem in mensagens_especificas:
        if any(mensagem in texto for texto in textos):
            return mensagem
    return "Dados inválidos"


# ---------------------------------------------------------------------------
# Livros
# ---------------------------------------------------------------------------


@app.post("/livros")
async def criar_livro(request: Request):
    dados = await _corpo_json(request)
    if dados is None:
        return erro(422, "Dados inválidos")

    try:
        entrada = LivroCreate(**dados)
    except ValidationError as exc:
        mensagem = _mensagem_erro_validacao(exc, ["ISBN inválido"])
        return erro(422, mensagem)

    if any(livro.isbn == entrada.isbn for livro in storage.livros.values()):
        return erro(409, "ISBN já cadastrado")

    novo_id = storage.gerar_id_livro()
    livro = Livro(
        id=novo_id,
        titulo=entrada.titulo,
        autor=entrada.autor,
        isbn=entrada.isbn,
        status="disponivel",
    )
    storage.livros[novo_id] = livro
    return JSONResponse(status_code=201, content=livro.model_dump())


@app.get("/livros")
async def listar_livros(status: Optional[str] = None):
    if status is not None and status not in ("disponivel", "emprestado"):
        return erro(422, "Dados inválidos")

    livros = list(storage.livros.values())
    if status is not None:
        livros = [livro for livro in livros if livro.status == status]

    return JSONResponse(status_code=200, content=[livro.model_dump() for livro in livros])


@app.get("/livros/{id}")
async def consultar_livro(id: int):
    livro = storage.livros.get(id)
    if livro is None:
        return erro(404, "Livro não encontrado")
    return JSONResponse(status_code=200, content=livro.model_dump())


@app.delete("/livros/{id}")
async def excluir_livro(id: int):
    livro = storage.livros.get(id)
    if livro is None:
        return erro(404, "Livro não encontrado")

    tem_emprestimo_ativo = any(
        emprestimo.livro_id == id and emprestimo.status == "ativo"
        for emprestimo in storage.emprestimos.values()
    )
    if tem_emprestimo_ativo:
        return erro(409, "Livro possui empréstimo ativo")

    del storage.livros[id]
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Usuários
# ---------------------------------------------------------------------------


@app.post("/usuarios")
async def criar_usuario(request: Request):
    dados = await _corpo_json(request)
    if dados is None:
        return erro(422, "Dados inválidos")

    try:
        entrada = UsuarioCreate(**dados)
    except ValidationError as exc:
        mensagem = _mensagem_erro_validacao(exc, ["E-mail inválido"])
        return erro(422, mensagem)

    if any(usuario.email == entrada.email for usuario in storage.usuarios.values()):
        return erro(409, "E-mail já cadastrado")

    novo_id = storage.gerar_id_usuario()
    usuario = Usuario(
        id=novo_id,
        nome=entrada.nome,
        email=entrada.email,
        status=entrada.status or "ativo",
        multa_pendente=0.0,
    )
    storage.usuarios[novo_id] = usuario
    return JSONResponse(status_code=201, content=usuario.model_dump())


@app.get("/usuarios/{id}")
async def consultar_usuario(id: int):
    usuario = storage.usuarios.get(id)
    if usuario is None:
        return erro(404, "Usuário não encontrado")
    return JSONResponse(status_code=200, content=usuario.model_dump())


# ---------------------------------------------------------------------------
# Empréstimos e devoluções
# ---------------------------------------------------------------------------


@app.post("/emprestimos")
async def registrar_emprestimo(request: Request):
    dados = await _corpo_json(request)
    if dados is None:
        return erro(422, "Dados inválidos")

    try:
        entrada = EmprestimoCreate(**dados)
    except ValidationError:
        return erro(422, "Dados inválidos")

    usuario = storage.usuarios.get(entrada.usuario_id)
    if usuario is None:
        return erro(404, "Usuário não encontrado")

    livro = storage.livros.get(entrada.livro_id)
    if livro is None:
        return erro(404, "Livro não encontrado")

    if usuario.status == "inativo":
        return erro(422, "Usuário inativo")

    if usuario.multa_pendente > 0:
        return erro(422, "Usuário possui multa pendente")

    emprestimos_ativos = sum(
        1
        for emprestimo in storage.emprestimos.values()
        if emprestimo.usuario_id == usuario.id and emprestimo.status == "ativo"
    )
    if emprestimos_ativos >= 3:
        return erro(422, "Limite de empréstimos atingido")

    if livro.status == "emprestado":
        return erro(409, "Livro indisponível")

    data_emprestimo_str = entrada.data_emprestimo or _data_hoje()
    data_emprestimo_date = _parse_data(data_emprestimo_str)
    data_devolucao_prevista = (data_emprestimo_date + timedelta(days=14)).isoformat()

    novo_id = storage.gerar_id_emprestimo()
    emprestimo = Emprestimo(
        id=novo_id,
        usuario_id=usuario.id,
        livro_id=livro.id,
        data_emprestimo=data_emprestimo_str,
        data_devolucao_prevista=data_devolucao_prevista,
        data_devolucao_real=None,
        multa=0.0,
        status="ativo",
    )
    storage.emprestimos[novo_id] = emprestimo
    livro.status = "emprestado"

    return JSONResponse(status_code=201, content=emprestimo.model_dump())


@app.post("/devolucoes")
async def registrar_devolucao(request: Request):
    dados = await _corpo_json(request)
    if dados is None:
        return erro(422, "Dados inválidos")

    try:
        entrada = DevolucaoCreate(**dados)
    except ValidationError:
        return erro(422, "Dados inválidos")

    emprestimo = storage.emprestimos.get(entrada.emprestimo_id)
    if emprestimo is None:
        return erro(404, "Empréstimo não encontrado")

    if emprestimo.status == "devolvido":
        return erro(409, "Empréstimo já devolvido")

    data_devolucao_str = entrada.data_devolucao or _data_hoje()
    data_devolucao_date = _parse_data(data_devolucao_str)
    data_prevista_date = _parse_data(emprestimo.data_devolucao_prevista)

    dias_atraso = (data_devolucao_date - data_prevista_date).days
    multa = round(1.50 * dias_atraso, 2) if dias_atraso > 0 else 0.0

    emprestimo.data_devolucao_real = data_devolucao_str
    emprestimo.multa = multa
    emprestimo.status = "devolvido"

    livro = storage.livros.get(emprestimo.livro_id)
    if livro is not None:
        livro.status = "disponivel"

    usuario = storage.usuarios.get(emprestimo.usuario_id)
    if usuario is not None:
        usuario.multa_pendente = round(usuario.multa_pendente + multa, 2)

    return JSONResponse(status_code=200, content=emprestimo.model_dump())


@app.get("/usuarios/{id}/emprestimos")
async def listar_emprestimos_usuario(id: int, status: Optional[str] = None):
    if status is not None and status not in ("ativo", "devolvido"):
        return erro(422, "Dados inválidos")

    usuario = storage.usuarios.get(id)
    if usuario is None:
        return erro(404, "Usuário não encontrado")

    emprestimos = [
        emprestimo for emprestimo in storage.emprestimos.values() if emprestimo.usuario_id == id
    ]
    if status is not None:
        emprestimos = [emprestimo for emprestimo in emprestimos if emprestimo.status == status]

    return JSONResponse(
        status_code=200, content=[emprestimo.model_dump() for emprestimo in emprestimos]
    )


@app.post("/usuarios/{id}/pagamento-multa")
async def pagar_multa(id: int):
    usuario = storage.usuarios.get(id)
    if usuario is None:
        return erro(404, "Usuário não encontrado")

    if usuario.multa_pendente == 0:
        return erro(409, "Usuário não possui multa pendente")

    usuario.multa_pendente = 0.0
    return JSONResponse(status_code=200, content=usuario.model_dump())
