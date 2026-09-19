"""Sistema de Gestão de Biblioteca — implementação de REFERÊNCIA (escrita à mão).

Usada apenas para o teste de sanidade do instrumento de medição.
"""
from datetime import date, timedelta

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app import storage
from app.models import DevolucaoEntrada, EmprestimoEntrada, LivroEntrada, UsuarioEntrada

app = FastAPI()

VALOR_MULTA_POR_DIA = 1.50
PRAZO_DIAS = 14


# --- Formato global de erro (Seção 10) -------------------------------------

@app.exception_handler(RequestValidationError)
async def erro_validacao(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"erro": "Dados inválidos"})


@app.exception_handler(HTTPException)
async def erro_http(request: Request, exc: HTTPException):
    if exc.status_code == 204:
        return Response(status_code=204)
    return JSONResponse(status_code=exc.status_code, content={"erro": exc.detail})


def falha(status: int, mensagem: str):
    raise HTTPException(status_code=status, detail=mensagem)


def data_valida(texto: str) -> date | None:
    try:
        return date.fromisoformat(texto)
    except ValueError:
        return None


# --- RF-01 / RF-02 / RF-03 / RF-04 — Livros --------------------------------

@app.post("/livros", status_code=201)
def cadastrar_livro(entrada: LivroEntrada):
    if len(entrada.isbn) != 13 or not entrada.isbn.isdigit():
        falha(422, "ISBN inválido")
    if not 1 <= len(entrada.titulo.strip()) <= 200:
        falha(422, "Dados inválidos")
    if not 1 <= len(entrada.autor.strip()) <= 100:
        falha(422, "Dados inválidos")
    if any(l["isbn"] == entrada.isbn for l in storage.livros.values()):
        falha(409, "ISBN já cadastrado")

    livro = {
        "id": storage.proximo_id_livro(),
        "titulo": entrada.titulo,
        "autor": entrada.autor,
        "isbn": entrada.isbn,
        "status": "disponivel",
    }
    storage.livros[livro["id"]] = livro
    return livro


@app.get("/livros")
def listar_livros(status: str | None = None):
    if status is not None and status not in ("disponivel", "emprestado"):
        falha(422, "Dados inválidos")
    itens = list(storage.livros.values())
    if status is not None:
        itens = [l for l in itens if l["status"] == status]
    return itens


@app.get("/livros/{livro_id}")
def consultar_livro(livro_id: int):
    livro = storage.livros.get(livro_id)
    if livro is None:
        falha(404, "Livro não encontrado")
    return livro


@app.delete("/livros/{livro_id}", status_code=204)
def excluir_livro(livro_id: int):
    livro = storage.livros.get(livro_id)
    if livro is None:
        falha(404, "Livro não encontrado")
    tem_ativo = any(
        e["livro_id"] == livro_id and e["status"] == "ativo"
        for e in storage.emprestimos.values()
    )
    if tem_ativo:
        falha(409, "Livro possui empréstimo ativo")
    del storage.livros[livro_id]
    return Response(status_code=204)


# --- RF-05 / RF-06 / RF-10 — Usuários --------------------------------------

def email_valido(email: str) -> bool:
    if email.count("@") != 1:
        return False
    antes, depois = email.split("@")
    return len(antes) >= 1 and len(depois) >= 1


@app.post("/usuarios", status_code=201)
def cadastrar_usuario(entrada: UsuarioEntrada):
    if not email_valido(entrada.email):
        falha(422, "E-mail inválido")
    if not 1 <= len(entrada.nome.strip()) <= 100:
        falha(422, "Dados inválidos")
    if entrada.status is not None and entrada.status not in ("ativo", "inativo"):
        falha(422, "Dados inválidos")
    if any(u["email"] == entrada.email for u in storage.usuarios.values()):
        falha(409, "E-mail já cadastrado")

    usuario = {
        "id": storage.proximo_id_usuario(),
        "nome": entrada.nome,
        "email": entrada.email,
        "status": entrada.status or "ativo",
        "multa_pendente": 0.0,
    }
    storage.usuarios[usuario["id"]] = usuario
    return usuario


@app.get("/usuarios/{usuario_id}")
def consultar_usuario(usuario_id: int):
    usuario = storage.usuarios.get(usuario_id)
    if usuario is None:
        falha(404, "Usuário não encontrado")
    return usuario


@app.post("/usuarios/{usuario_id}/pagamento-multa")
def quitar_multa(usuario_id: int):
    usuario = storage.usuarios.get(usuario_id)
    if usuario is None:
        falha(404, "Usuário não encontrado")
    if usuario["multa_pendente"] == 0:
        falha(409, "Usuário não possui multa pendente")
    usuario["multa_pendente"] = 0.0
    return usuario


@app.get("/usuarios/{usuario_id}/emprestimos")
def listar_emprestimos_do_usuario(usuario_id: int, status: str | None = None):
    if usuario_id not in storage.usuarios:
        falha(404, "Usuário não encontrado")
    if status is not None and status not in ("ativo", "devolvido"):
        falha(422, "Dados inválidos")
    itens = [e for e in storage.emprestimos.values() if e["usuario_id"] == usuario_id]
    if status is not None:
        itens = [e for e in itens if e["status"] == status]
    return itens


# --- RF-07 / RF-08 — Empréstimos e devoluções ------------------------------

@app.post("/emprestimos", status_code=201)
def registrar_emprestimo(entrada: EmprestimoEntrada):
    if entrada.data_emprestimo is not None and data_valida(entrada.data_emprestimo) is None:
        falha(422, "Dados inválidos")

    usuario = storage.usuarios.get(entrada.usuario_id)
    if usuario is None:
        falha(404, "Usuário não encontrado")
    livro = storage.livros.get(entrada.livro_id)
    if livro is None:
        falha(404, "Livro não encontrado")

    if usuario["status"] == "inativo":
        falha(422, "Usuário inativo")
    if usuario["multa_pendente"] > 0:
        falha(422, "Usuário possui multa pendente")
    ativos = sum(
        1 for e in storage.emprestimos.values()
        if e["usuario_id"] == usuario["id"] and e["status"] == "ativo"
    )
    if ativos >= 3:
        falha(422, "Limite de empréstimos atingido")
    if livro["status"] == "emprestado":
        falha(409, "Livro indisponível")

    inicio = date.fromisoformat(entrada.data_emprestimo) if entrada.data_emprestimo else date.today()
    emprestimo = {
        "id": storage.proximo_id_emprestimo(),
        "usuario_id": usuario["id"],
        "livro_id": livro["id"],
        "data_emprestimo": inicio.isoformat(),
        "data_devolucao_prevista": (inicio + timedelta(days=PRAZO_DIAS)).isoformat(),
        "data_devolucao_real": None,
        "multa": 0.0,
        "status": "ativo",
    }
    storage.emprestimos[emprestimo["id"]] = emprestimo
    livro["status"] = "emprestado"
    return emprestimo


@app.post("/devolucoes")
def registrar_devolucao(entrada: DevolucaoEntrada):
    if entrada.data_devolucao is not None and data_valida(entrada.data_devolucao) is None:
        falha(422, "Dados inválidos")

    emprestimo = storage.emprestimos.get(entrada.emprestimo_id)
    if emprestimo is None:
        falha(404, "Empréstimo não encontrado")
    if emprestimo["status"] == "devolvido":
        falha(409, "Empréstimo já devolvido")

    devolucao = date.fromisoformat(entrada.data_devolucao) if entrada.data_devolucao else date.today()
    prevista = date.fromisoformat(emprestimo["data_devolucao_prevista"])
    dias_atraso = (devolucao - prevista).days
    multa = round(VALOR_MULTA_POR_DIA * dias_atraso, 2) if dias_atraso > 0 else 0.0

    emprestimo["data_devolucao_real"] = devolucao.isoformat()
    emprestimo["multa"] = multa
    emprestimo["status"] = "devolvido"

    usuario = storage.usuarios[emprestimo["usuario_id"]]
    usuario["multa_pendente"] = round(usuario["multa_pendente"] + multa, 2)

    livro = storage.livros.get(emprestimo["livro_id"])
    if livro is not None:
        livro["status"] = "disponivel"
    return emprestimo
