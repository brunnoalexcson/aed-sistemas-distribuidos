"""Instancia da aplicacao FastAPI e todas as rotas."""

import re
from datetime import date, datetime, timedelta
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.models import DevolucaoCreate, EmprestimoCreate, LivroCreate, UsuarioCreate
from app.storage import storage

app = FastAPI()

ISBN_REGEX = re.compile(r"^[0-9]{13}$")
DATA_FORMATO = "%Y-%m-%d"


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"erro": "Dados inválidos"})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"erro": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"erro": "Erro interno do servidor"})


def _erro(status_code: int, mensagem: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail=mensagem)


def _validar_isbn(isbn: str) -> None:
    if not ISBN_REGEX.fullmatch(isbn):
        raise _erro(422, "ISBN inválido")


def _validar_email(email: str) -> None:
    partes = email.split("@")
    if len(partes) != 2 or len(partes[0]) < 1 or len(partes[1]) < 1:
        raise _erro(422, "E-mail inválido")


def _parse_data(valor: Optional[str]) -> str:
    if valor is None:
        return date.today().strftime(DATA_FORMATO)
    try:
        datetime.strptime(valor, DATA_FORMATO)
    except ValueError:
        raise _erro(422, "Dados inválidos")
    return valor


def _livro_para_saida(livro: dict) -> dict:
    return {
        "id": livro["id"],
        "titulo": livro["titulo"],
        "autor": livro["autor"],
        "isbn": livro["isbn"],
        "status": livro["status"],
    }


def _usuario_para_saida(usuario: dict) -> dict:
    return {
        "id": usuario["id"],
        "nome": usuario["nome"],
        "email": usuario["email"],
        "status": usuario["status"],
        "multa_pendente": usuario["multa_pendente"],
    }


def _emprestimo_para_saida(emprestimo: dict) -> dict:
    return {
        "id": emprestimo["id"],
        "usuario_id": emprestimo["usuario_id"],
        "livro_id": emprestimo["livro_id"],
        "data_emprestimo": emprestimo["data_emprestimo"],
        "data_devolucao_prevista": emprestimo["data_devolucao_prevista"],
        "data_devolucao_real": emprestimo["data_devolucao_real"],
        "multa": emprestimo["multa"],
        "status": emprestimo["status"],
    }


@app.post("/livros", status_code=201)
def criar_livro(dados: LivroCreate):
    _validar_isbn(dados.isbn)
    for livro in storage.livros.values():
        if livro["isbn"] == dados.isbn:
            raise _erro(409, "ISBN já cadastrado")

    novo_id = storage.proximo_id_livro()
    livro = {
        "id": novo_id,
        "titulo": dados.titulo,
        "autor": dados.autor,
        "isbn": dados.isbn,
        "status": "disponivel",
    }
    storage.livros[novo_id] = livro
    return _livro_para_saida(livro)


@app.get("/livros")
def listar_livros(
    status: Optional[Literal["disponivel", "emprestado"]] = Query(default=None),
):
    livros = list(storage.livros.values())
    if status is not None:
        livros = [livro for livro in livros if livro["status"] == status]
    return [_livro_para_saida(livro) for livro in livros]


@app.get("/livros/{livro_id}")
def consultar_livro(livro_id: int):
    livro = storage.livros.get(livro_id)
    if livro is None:
        raise _erro(404, "Livro não encontrado")
    return _livro_para_saida(livro)


@app.delete("/livros/{livro_id}", status_code=204)
def excluir_livro(livro_id: int):
    livro = storage.livros.get(livro_id)
    if livro is None:
        raise _erro(404, "Livro não encontrado")

    tem_emprestimo_ativo = any(
        emprestimo["livro_id"] == livro_id and emprestimo["status"] == "ativo"
        for emprestimo in storage.emprestimos.values()
    )
    if tem_emprestimo_ativo:
        raise _erro(409, "Livro possui empréstimo ativo")

    del storage.livros[livro_id]
    return None


@app.post("/usuarios", status_code=201)
def criar_usuario(dados: UsuarioCreate):
    _validar_email(dados.email)
    for usuario in storage.usuarios.values():
        if usuario["email"] == dados.email:
            raise _erro(409, "E-mail já cadastrado")

    novo_id = storage.proximo_id_usuario()
    usuario = {
        "id": novo_id,
        "nome": dados.nome,
        "email": dados.email,
        "status": dados.status if dados.status is not None else "ativo",
        "multa_pendente": 0.0,
    }
    storage.usuarios[novo_id] = usuario
    return _usuario_para_saida(usuario)


@app.get("/usuarios/{usuario_id}")
def consultar_usuario(usuario_id: int):
    usuario = storage.usuarios.get(usuario_id)
    if usuario is None:
        raise _erro(404, "Usuário não encontrado")
    return _usuario_para_saida(usuario)


@app.post("/emprestimos", status_code=201)
def registrar_emprestimo(dados: EmprestimoCreate):
    data_emprestimo = _parse_data(dados.data_emprestimo)

    usuario = storage.usuarios.get(dados.usuario_id)
    if usuario is None:
        raise _erro(404, "Usuário não encontrado")

    livro = storage.livros.get(dados.livro_id)
    if livro is None:
        raise _erro(404, "Livro não encontrado")

    if usuario["status"] == "inativo":
        raise _erro(422, "Usuário inativo")

    if usuario["multa_pendente"] > 0:
        raise _erro(422, "Usuário possui multa pendente")

    emprestimos_ativos = sum(
        1
        for emprestimo in storage.emprestimos.values()
        if emprestimo["usuario_id"] == usuario["id"] and emprestimo["status"] == "ativo"
    )
    if emprestimos_ativos >= 3:
        raise _erro(422, "Limite de empréstimos atingido")

    if livro["status"] == "emprestado":
        raise _erro(409, "Livro indisponível")

    data_emprestimo_dt = datetime.strptime(data_emprestimo, DATA_FORMATO).date()
    data_devolucao_prevista = (data_emprestimo_dt + timedelta(days=14)).strftime(
        DATA_FORMATO
    )

    novo_id = storage.proximo_id_emprestimo()
    emprestimo = {
        "id": novo_id,
        "usuario_id": usuario["id"],
        "livro_id": livro["id"],
        "data_emprestimo": data_emprestimo,
        "data_devolucao_prevista": data_devolucao_prevista,
        "data_devolucao_real": None,
        "multa": 0.0,
        "status": "ativo",
    }
    storage.emprestimos[novo_id] = emprestimo
    livro["status"] = "emprestado"
    return _emprestimo_para_saida(emprestimo)


@app.post("/devolucoes", status_code=200)
def registrar_devolucao(dados: DevolucaoCreate):
    data_devolucao = _parse_data(dados.data_devolucao)

    emprestimo = storage.emprestimos.get(dados.emprestimo_id)
    if emprestimo is None:
        raise _erro(404, "Empréstimo não encontrado")

    if emprestimo["status"] == "devolvido":
        raise _erro(409, "Empréstimo já devolvido")

    data_prevista_dt = datetime.strptime(
        emprestimo["data_devolucao_prevista"], DATA_FORMATO
    ).date()
    data_devolucao_dt = datetime.strptime(data_devolucao, DATA_FORMATO).date()

    dias_atraso = (data_devolucao_dt - data_prevista_dt).days
    if dias_atraso > 0:
        multa = round(1.50 * dias_atraso, 2)
    else:
        multa = 0.0

    usuario = storage.usuarios.get(emprestimo["usuario_id"])
    if usuario is not None:
        usuario["multa_pendente"] = round(usuario["multa_pendente"] + multa, 2)

    emprestimo["data_devolucao_real"] = data_devolucao
    emprestimo["multa"] = multa
    emprestimo["status"] = "devolvido"

    livro = storage.livros.get(emprestimo["livro_id"])
    if livro is not None:
        livro["status"] = "disponivel"

    return _emprestimo_para_saida(emprestimo)


@app.get("/usuarios/{usuario_id}/emprestimos")
def listar_emprestimos_usuario(
    usuario_id: int,
    status: Optional[Literal["ativo", "devolvido"]] = Query(default=None),
):
    usuario = storage.usuarios.get(usuario_id)
    if usuario is None:
        raise _erro(404, "Usuário não encontrado")

    emprestimos = [
        emprestimo
        for emprestimo in storage.emprestimos.values()
        if emprestimo["usuario_id"] == usuario_id
    ]
    if status is not None:
        emprestimos = [
            emprestimo for emprestimo in emprestimos if emprestimo["status"] == status
        ]

    return [_emprestimo_para_saida(emprestimo) for emprestimo in emprestimos]


@app.post("/usuarios/{usuario_id}/pagamento-multa", status_code=200)
def pagar_multa(usuario_id: int):
    usuario = storage.usuarios.get(usuario_id)
    if usuario is None:
        raise _erro(404, "Usuário não encontrado")

    if usuario["multa_pendente"] == 0:
        raise _erro(409, "Usuário não possui multa pendente")

    usuario["multa_pendente"] = 0.0
    return _usuario_para_saida(usuario)
