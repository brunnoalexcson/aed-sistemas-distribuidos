"""Instância da aplicação FastAPI e todas as rotas do sistema."""

import re
from datetime import date, datetime, timedelta
from typing import List, Literal, Optional

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response

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

_ISBN_RE = re.compile(r"^[0-9]{13}$")


class ErroAPI(Exception):
    """Exceção que carrega o status HTTP e a mensagem de erro exatos."""

    def __init__(self, status_code: int, mensagem: str) -> None:
        self.status_code = status_code
        self.mensagem = mensagem


@app.exception_handler(ErroAPI)
async def tratar_erro_api(request: Request, exc: ErroAPI) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"erro": exc.mensagem})


@app.exception_handler(RequestValidationError)
async def tratar_erro_validacao(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(status_code=422, content={"erro": "Dados inválidos"})


def _validar_isbn(isbn: str) -> None:
    if not isinstance(isbn, str) or _ISBN_RE.fullmatch(isbn) is None:
        raise ErroAPI(422, "ISBN inválido")


def _texto_valido(valor: str, minimo: int, maximo: int) -> bool:
    if not isinstance(valor, str):
        return False
    tamanho = len(valor.strip())
    return minimo <= tamanho <= maximo


def _email_valido(email: str) -> bool:
    if not isinstance(email, str):
        return False
    if email.count("@") != 1:
        return False
    parte_local, parte_dominio = email.split("@")
    return len(parte_local) >= 1 and len(parte_dominio) >= 1


def _formatar_data(valor: date) -> str:
    return valor.strftime("%Y-%m-%d")


def _parsear_data(valor: str) -> date:
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise ErroAPI(422, "Dados inválidos")


# --------------------------------------------------------------------------
# Livros
# --------------------------------------------------------------------------


@app.post("/livros", response_model=Livro, status_code=201)
def criar_livro(dados: LivroCreate) -> dict:
    _validar_isbn(dados.isbn)

    if not _texto_valido(dados.titulo, 1, 200) or not _texto_valido(dados.autor, 1, 100):
        raise ErroAPI(422, "Dados inválidos")

    if any(livro["isbn"] == dados.isbn for livro in storage.livros.values()):
        raise ErroAPI(409, "ISBN já cadastrado")

    novo_id = storage.gerar_id_livro()
    livro = {
        "id": novo_id,
        "titulo": dados.titulo,
        "autor": dados.autor,
        "isbn": dados.isbn,
        "status": "disponivel",
    }
    storage.livros[novo_id] = livro
    return livro


@app.get("/livros", response_model=List[Livro])
def listar_livros(
    status: Optional[Literal["disponivel", "emprestado"]] = Query(default=None)
) -> list:
    livros = list(storage.livros.values())
    if status is not None:
        livros = [livro for livro in livros if livro["status"] == status]
    return livros


@app.get("/livros/{livro_id}", response_model=Livro)
def consultar_livro(livro_id: int) -> dict:
    livro = storage.livros.get(livro_id)
    if livro is None:
        raise ErroAPI(404, "Livro não encontrado")
    return livro


@app.delete("/livros/{livro_id}", status_code=204)
def excluir_livro(livro_id: int) -> Response:
    livro = storage.livros.get(livro_id)
    if livro is None:
        raise ErroAPI(404, "Livro não encontrado")

    possui_emprestimo_ativo = any(
        emprestimo["livro_id"] == livro_id and emprestimo["status"] == "ativo"
        for emprestimo in storage.emprestimos.values()
    )
    if possui_emprestimo_ativo:
        raise ErroAPI(409, "Livro possui empréstimo ativo")

    del storage.livros[livro_id]
    return Response(status_code=204)


# --------------------------------------------------------------------------
# Usuários
# --------------------------------------------------------------------------


@app.post("/usuarios", response_model=Usuario, status_code=201)
def criar_usuario(dados: UsuarioCreate) -> dict:
    if not _email_valido(dados.email):
        raise ErroAPI(422, "E-mail inválido")

    status_informado = dados.status if dados.status is not None else "ativo"

    if not _texto_valido(dados.nome, 1, 100) or status_informado not in (
        "ativo",
        "inativo",
    ):
        raise ErroAPI(422, "Dados inválidos")

    if any(usuario["email"] == dados.email for usuario in storage.usuarios.values()):
        raise ErroAPI(409, "E-mail já cadastrado")

    novo_id = storage.gerar_id_usuario()
    usuario = {
        "id": novo_id,
        "nome": dados.nome,
        "email": dados.email,
        "status": status_informado,
        "multa_pendente": 0.0,
    }
    storage.usuarios[novo_id] = usuario
    return usuario


@app.get("/usuarios/{usuario_id}", response_model=Usuario)
def consultar_usuario(usuario_id: int) -> dict:
    usuario = storage.usuarios.get(usuario_id)
    if usuario is None:
        raise ErroAPI(404, "Usuário não encontrado")
    return usuario


# --------------------------------------------------------------------------
# Empréstimos
# --------------------------------------------------------------------------


@app.post("/emprestimos", response_model=Emprestimo, status_code=201)
def registrar_emprestimo(dados: EmprestimoCreate) -> dict:
    usuario = storage.usuarios.get(dados.usuario_id)
    if usuario is None:
        raise ErroAPI(404, "Usuário não encontrado")

    livro = storage.livros.get(dados.livro_id)
    if livro is None:
        raise ErroAPI(404, "Livro não encontrado")

    if usuario["status"] == "inativo":
        raise ErroAPI(422, "Usuário inativo")

    if usuario["multa_pendente"] > 0:
        raise ErroAPI(422, "Usuário possui multa pendente")

    emprestimos_ativos = sum(
        1
        for emprestimo in storage.emprestimos.values()
        if emprestimo["usuario_id"] == dados.usuario_id
        and emprestimo["status"] == "ativo"
    )
    if emprestimos_ativos >= 3:
        raise ErroAPI(422, "Limite de empréstimos atingido")

    if livro["status"] == "emprestado":
        raise ErroAPI(409, "Livro indisponível")

    if dados.data_emprestimo is not None:
        data_emprestimo = _parsear_data(dados.data_emprestimo)
    else:
        data_emprestimo = date.today()

    data_devolucao_prevista = data_emprestimo + timedelta(days=14)

    novo_id = storage.gerar_id_emprestimo()
    emprestimo = {
        "id": novo_id,
        "usuario_id": dados.usuario_id,
        "livro_id": dados.livro_id,
        "data_emprestimo": _formatar_data(data_emprestimo),
        "data_devolucao_prevista": _formatar_data(data_devolucao_prevista),
        "data_devolucao_real": None,
        "multa": 0.0,
        "status": "ativo",
    }
    storage.emprestimos[novo_id] = emprestimo
    livro["status"] = "emprestado"
    return emprestimo


@app.post("/devolucoes", response_model=Emprestimo)
def registrar_devolucao(dados: DevolucaoCreate) -> dict:
    emprestimo = storage.emprestimos.get(dados.emprestimo_id)
    if emprestimo is None:
        raise ErroAPI(404, "Empréstimo não encontrado")

    if emprestimo["status"] == "devolvido":
        raise ErroAPI(409, "Empréstimo já devolvido")

    if dados.data_devolucao is not None:
        data_devolucao = _parsear_data(dados.data_devolucao)
    else:
        data_devolucao = date.today()

    data_devolucao_prevista = _parsear_data(emprestimo["data_devolucao_prevista"])
    dias_atraso = (data_devolucao - data_devolucao_prevista).days
    multa = round(1.50 * dias_atraso, 2) if dias_atraso > 0 else 0.0

    emprestimo["data_devolucao_real"] = _formatar_data(data_devolucao)
    emprestimo["multa"] = multa
    emprestimo["status"] = "devolvido"

    usuario = storage.usuarios.get(emprestimo["usuario_id"])
    if usuario is not None:
        usuario["multa_pendente"] = round(usuario["multa_pendente"] + multa, 2)

    livro = storage.livros.get(emprestimo["livro_id"])
    if livro is not None:
        livro["status"] = "disponivel"

    return emprestimo


@app.get("/usuarios/{usuario_id}/emprestimos", response_model=List[Emprestimo])
def listar_emprestimos_usuario(
    usuario_id: int,
    status: Optional[Literal["ativo", "devolvido"]] = Query(default=None),
) -> list:
    usuario = storage.usuarios.get(usuario_id)
    if usuario is None:
        raise ErroAPI(404, "Usuário não encontrado")

    emprestimos = [
        emprestimo
        for emprestimo in storage.emprestimos.values()
        if emprestimo["usuario_id"] == usuario_id
    ]
    if status is not None:
        emprestimos = [
            emprestimo for emprestimo in emprestimos if emprestimo["status"] == status
        ]
    return emprestimos


@app.post("/usuarios/{usuario_id}/pagamento-multa", response_model=Usuario)
def pagar_multa(usuario_id: int) -> dict:
    usuario = storage.usuarios.get(usuario_id)
    if usuario is None:
        raise ErroAPI(404, "Usuário não encontrado")

    if usuario["multa_pendente"] == 0:
        raise ErroAPI(409, "Usuário não possui multa pendente")

    usuario["multa_pendente"] = 0.0
    return usuario
