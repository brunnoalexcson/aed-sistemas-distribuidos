"""Instância da aplicação FastAPI e todas as rotas."""

import re
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.models import DevolucaoCreate, EmprestimoCreate, LivroCreate, UsuarioCreate
from app.storage import storage

app = FastAPI()

DATA_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ---------------------------------------------------------------------------
# Tratamento de erros global
# ---------------------------------------------------------------------------


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request, exc):
    return JSONResponse(status_code=422, content={"erro": "Dados inválidos"})


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    detail = exc.detail
    if isinstance(detail, dict) and "erro" in detail:
        content = detail
    else:
        content = {"erro": str(detail)}
    return JSONResponse(status_code=exc.status_code, content=content)


def erro(status_code: int, mensagem: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"erro": mensagem})


# ---------------------------------------------------------------------------
# Funções auxiliares de validação
# ---------------------------------------------------------------------------


def isbn_valido(isbn: str) -> bool:
    return isinstance(isbn, str) and len(isbn) == 13 and isbn.isdigit()


def email_valido(email: str) -> bool:
    if not isinstance(email, str):
        return False
    if email.count("@") != 1:
        return False
    local, dominio = email.split("@")
    return len(local) >= 1 and len(dominio) >= 1


def texto_valido(valor: str, minimo: int, maximo: int) -> bool:
    if not isinstance(valor, str):
        return False
    tamanho = len(valor.strip())
    return minimo <= tamanho <= maximo


def parse_data(valor: str) -> Optional[date]:
    if not isinstance(valor, str) or not DATA_REGEX.match(valor):
        return None
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Funções auxiliares de busca
# ---------------------------------------------------------------------------


def buscar_livro_ou_404(livro_id: int) -> dict:
    livro = storage.livros.get(livro_id)
    if livro is None:
        raise erro(404, "Livro não encontrado")
    return livro


def buscar_usuario_ou_404(usuario_id: int) -> dict:
    usuario = storage.usuarios.get(usuario_id)
    if usuario is None:
        raise erro(404, "Usuário não encontrado")
    return usuario


def buscar_emprestimo_ou_404(emprestimo_id: int) -> dict:
    emprestimo = storage.emprestimos.get(emprestimo_id)
    if emprestimo is None:
        raise erro(404, "Empréstimo não encontrado")
    return emprestimo


# ---------------------------------------------------------------------------
# RF-01 / RF-02 / RF-03 / RF-04 — Livros
# ---------------------------------------------------------------------------


@app.post("/livros", status_code=201)
async def cadastrar_livro(dados: LivroCreate):
    if not isbn_valido(dados.isbn):
        raise erro(422, "ISBN inválido")

    if not texto_valido(dados.titulo, 1, 200):
        raise erro(422, "Dados inválidos")

    if not texto_valido(dados.autor, 1, 100):
        raise erro(422, "Dados inválidos")

    for livro in storage.livros.values():
        if livro["isbn"] == dados.isbn:
            raise erro(409, "ISBN já cadastrado")

    livro_id = storage.next_livro_id()
    livro = {
        "id": livro_id,
        "titulo": dados.titulo.strip(),
        "autor": dados.autor.strip(),
        "isbn": dados.isbn,
        "status": "disponivel",
    }
    storage.livros[livro_id] = livro
    return JSONResponse(status_code=201, content=livro)


@app.get("/livros")
async def listar_livros(status: Optional[str] = Query(None)):
    if status is not None and status not in ("disponivel", "emprestado"):
        raise erro(422, "Dados inválidos")

    livros = list(storage.livros.values())
    if status is not None:
        livros = [livro for livro in livros if livro["status"] == status]

    return JSONResponse(status_code=200, content=livros)


@app.get("/livros/{livro_id}")
async def consultar_livro(livro_id: int):
    livro = buscar_livro_ou_404(livro_id)
    return JSONResponse(status_code=200, content=livro)


@app.delete("/livros/{livro_id}", status_code=204)
async def excluir_livro(livro_id: int):
    livro = buscar_livro_ou_404(livro_id)

    tem_emprestimo_ativo = any(
        emprestimo["livro_id"] == livro_id and emprestimo["status"] == "ativo"
        for emprestimo in storage.emprestimos.values()
    )
    if tem_emprestimo_ativo:
        raise erro(409, "Livro possui empréstimo ativo")

    del storage.livros[livro_id]
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# RF-05 / RF-06 — Usuários
# ---------------------------------------------------------------------------


@app.post("/usuarios", status_code=201)
async def cadastrar_usuario(dados: UsuarioCreate):
    if not email_valido(dados.email):
        raise erro(422, "E-mail inválido")

    if not texto_valido(dados.nome, 1, 100):
        raise erro(422, "Dados inválidos")

    if dados.status is not None and dados.status not in ("ativo", "inativo"):
        raise erro(422, "Dados inválidos")

    for usuario in storage.usuarios.values():
        if usuario["email"] == dados.email:
            raise erro(409, "E-mail já cadastrado")

    usuario_id = storage.next_usuario_id()
    usuario = {
        "id": usuario_id,
        "nome": dados.nome.strip(),
        "email": dados.email,
        "status": dados.status if dados.status is not None else "ativo",
        "multa_pendente": 0.0,
    }
    storage.usuarios[usuario_id] = usuario
    return JSONResponse(status_code=201, content=usuario)


@app.get("/usuarios/{usuario_id}")
async def consultar_usuario(usuario_id: int):
    usuario = buscar_usuario_ou_404(usuario_id)
    return JSONResponse(status_code=200, content=usuario)


# ---------------------------------------------------------------------------
# RF-07 — Empréstimos
# ---------------------------------------------------------------------------


@app.post("/emprestimos", status_code=201)
async def registrar_emprestimo(dados: EmprestimoCreate):
    data_emprestimo_obj: date
    if dados.data_emprestimo is not None:
        parsed = parse_data(dados.data_emprestimo)
        if parsed is None:
            raise erro(422, "Dados inválidos")
        data_emprestimo_obj = parsed
    else:
        data_emprestimo_obj = date.today()

    usuario = storage.usuarios.get(dados.usuario_id)
    if usuario is None:
        raise erro(404, "Usuário não encontrado")

    livro = storage.livros.get(dados.livro_id)
    if livro is None:
        raise erro(404, "Livro não encontrado")

    if usuario["status"] == "inativo":
        raise erro(422, "Usuário inativo")

    if usuario["multa_pendente"] > 0:
        raise erro(422, "Usuário possui multa pendente")

    emprestimos_ativos = sum(
        1
        for emprestimo in storage.emprestimos.values()
        if emprestimo["usuario_id"] == usuario["id"] and emprestimo["status"] == "ativo"
    )
    if emprestimos_ativos >= 3:
        raise erro(422, "Limite de empréstimos atingido")

    if livro["status"] == "emprestado":
        raise erro(409, "Livro indisponível")

    data_devolucao_prevista_obj = data_emprestimo_obj + timedelta(days=14)

    emprestimo_id = storage.next_emprestimo_id()
    emprestimo = {
        "id": emprestimo_id,
        "usuario_id": usuario["id"],
        "livro_id": livro["id"],
        "data_emprestimo": data_emprestimo_obj.isoformat(),
        "data_devolucao_prevista": data_devolucao_prevista_obj.isoformat(),
        "data_devolucao_real": None,
        "multa": 0.0,
        "status": "ativo",
    }
    storage.emprestimos[emprestimo_id] = emprestimo
    livro["status"] = "emprestado"

    return JSONResponse(status_code=201, content=emprestimo)


# ---------------------------------------------------------------------------
# RF-08 — Devoluções
# ---------------------------------------------------------------------------


@app.post("/devolucoes", status_code=200)
async def registrar_devolucao(dados: DevolucaoCreate):
    if dados.data_devolucao is not None:
        parsed = parse_data(dados.data_devolucao)
        if parsed is None:
            raise erro(422, "Dados inválidos")
        data_devolucao_obj = parsed
    else:
        data_devolucao_obj = date.today()

    emprestimo = storage.emprestimos.get(dados.emprestimo_id)
    if emprestimo is None:
        raise erro(404, "Empréstimo não encontrado")

    if emprestimo["status"] == "devolvido":
        raise erro(409, "Empréstimo já devolvido")

    data_devolucao_prevista_obj = datetime.strptime(
        emprestimo["data_devolucao_prevista"], "%Y-%m-%d"
    ).date()

    dias_atraso = (data_devolucao_obj - data_devolucao_prevista_obj).days
    if dias_atraso > 0:
        multa = round(1.50 * dias_atraso, 2)
    else:
        multa = 0.0

    emprestimo["data_devolucao_real"] = data_devolucao_obj.isoformat()
    emprestimo["multa"] = multa
    emprestimo["status"] = "devolvido"

    usuario = storage.usuarios.get(emprestimo["usuario_id"])
    if usuario is not None:
        usuario["multa_pendente"] = round(usuario["multa_pendente"] + multa, 2)

    livro = storage.livros.get(emprestimo["livro_id"])
    if livro is not None:
        livro["status"] = "disponivel"

    return JSONResponse(status_code=200, content=emprestimo)


# ---------------------------------------------------------------------------
# RF-09 — Listar empréstimos de um usuário
# ---------------------------------------------------------------------------


@app.get("/usuarios/{usuario_id}/emprestimos")
async def listar_emprestimos_usuario(usuario_id: int, status: Optional[str] = Query(None)):
    if status is not None and status not in ("ativo", "devolvido"):
        raise erro(422, "Dados inválidos")

    buscar_usuario_ou_404(usuario_id)

    emprestimos = [
        emprestimo
        for emprestimo in storage.emprestimos.values()
        if emprestimo["usuario_id"] == usuario_id
    ]
    if status is not None:
        emprestimos = [emprestimo for emprestimo in emprestimos if emprestimo["status"] == status]

    return JSONResponse(status_code=200, content=emprestimos)


# ---------------------------------------------------------------------------
# RF-10 — Quitar multa do usuário
# ---------------------------------------------------------------------------


@app.post("/usuarios/{usuario_id}/pagamento-multa")
async def pagar_multa(usuario_id: int):
    usuario = buscar_usuario_ou_404(usuario_id)

    if usuario["multa_pendente"] == 0:
        raise erro(409, "Usuário não possui multa pendente")

    usuario["multa_pendente"] = 0.0
    return JSONResponse(status_code=200, content=usuario)
