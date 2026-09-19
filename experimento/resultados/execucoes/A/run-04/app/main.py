"""Instância da aplicação FastAPI e todas as rotas do sistema."""

import re
from datetime import date, timedelta
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response

from app.models import (
    Emprestimo,
    EmprestimoCreate,
    DevolucaoCreate,
    Livro,
    LivroCreate,
    Usuario,
    UsuarioCreate,
)
from app.storage import storage

app = FastAPI()

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ---------------------------------------------------------------------------
# Tratamento global de erros (Seção 10)
# ---------------------------------------------------------------------------


@app.exception_handler(RequestValidationError)
async def _validation_exception_handler(request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"erro": "Dados inválidos"})


@app.exception_handler(HTTPException)
async def _http_exception_handler(request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict) and "erro" in detail:
        conteudo = {"erro": detail["erro"]}
    elif isinstance(detail, str):
        conteudo = {"erro": detail}
    else:
        conteudo = {"erro": "Erro"}
    return JSONResponse(status_code=exc.status_code, content=conteudo)


# ---------------------------------------------------------------------------
# Funções auxiliares de validação
# ---------------------------------------------------------------------------


def _valid_str(valor, min_len: int, max_len: int) -> bool:
    return isinstance(valor, str) and min_len <= len(valor.strip()) <= max_len


def _valid_int(valor) -> bool:
    return isinstance(valor, int) and not isinstance(valor, bool)


def _valid_date_str(valor) -> bool:
    if not isinstance(valor, str) or not _DATE_RE.match(valor):
        return False
    try:
        date.fromisoformat(valor)
        return True
    except ValueError:
        return False


def _isbn_valido(isbn: str) -> bool:
    return len(isbn) == 13 and all(c in "0123456789" for c in isbn)


def _email_valido(email: str) -> bool:
    if email.count("@") != 1:
        return False
    antes, depois = email.split("@")
    return len(antes) >= 1 and len(depois) >= 1


# ---------------------------------------------------------------------------
# RF-01, RF-02, RF-03, RF-04 — Livros
# ---------------------------------------------------------------------------


@app.post("/livros", response_model=Livro, status_code=201)
def criar_livro(payload: LivroCreate) -> dict:
    body = payload.model_dump()
    isbn = body.get("isbn")
    titulo = body.get("titulo")
    autor = body.get("autor")

    if isinstance(isbn, str) and not _isbn_valido(isbn):
        raise HTTPException(422, detail={"erro": "ISBN inválido"})

    if not _valid_str(titulo, 1, 200):
        raise HTTPException(422, detail={"erro": "Dados inválidos"})
    if not _valid_str(autor, 1, 100):
        raise HTTPException(422, detail={"erro": "Dados inválidos"})
    if not (isinstance(isbn, str) and _isbn_valido(isbn)):
        raise HTTPException(422, detail={"erro": "Dados inválidos"})

    if any(l["isbn"] == isbn for l in storage.livros.values()):
        raise HTTPException(409, detail={"erro": "ISBN já cadastrado"})

    novo_id = storage.next_livro_id()
    livro = {
        "id": novo_id,
        "titulo": titulo,
        "autor": autor,
        "isbn": isbn,
        "status": "disponivel",
    }
    storage.livros[novo_id] = livro
    return livro


@app.get("/livros", response_model=List[Livro])
def listar_livros(status: Optional[str] = None) -> list:
    if status is not None and status not in ("disponivel", "emprestado"):
        raise HTTPException(422, detail={"erro": "Dados inválidos"})

    livros = list(storage.livros.values())
    if status is not None:
        livros = [l for l in livros if l["status"] == status]
    return livros


@app.get("/livros/{id}", response_model=Livro)
def consultar_livro(id: int) -> dict:
    livro = storage.livros.get(id)
    if livro is None:
        raise HTTPException(404, detail={"erro": "Livro não encontrado"})
    return livro


@app.delete("/livros/{id}", status_code=204)
def excluir_livro(id: int) -> Response:
    livro = storage.livros.get(id)
    if livro is None:
        raise HTTPException(404, detail={"erro": "Livro não encontrado"})

    tem_emprestimo_ativo = any(
        e["livro_id"] == id and e["status"] == "ativo" for e in storage.emprestimos.values()
    )
    if tem_emprestimo_ativo:
        raise HTTPException(409, detail={"erro": "Livro possui empréstimo ativo"})

    del storage.livros[id]
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# RF-05, RF-06 — Usuários
# ---------------------------------------------------------------------------


@app.post("/usuarios", response_model=Usuario, status_code=201)
def criar_usuario(payload: UsuarioCreate) -> dict:
    body = payload.model_dump()
    nome = body.get("nome")
    email = body.get("email")
    status_informado = body.get("status")

    if isinstance(email, str) and not _email_valido(email):
        raise HTTPException(422, detail={"erro": "E-mail inválido"})

    if not _valid_str(nome, 1, 100):
        raise HTTPException(422, detail={"erro": "Dados inválidos"})
    if not (isinstance(email, str) and _email_valido(email)):
        raise HTTPException(422, detail={"erro": "Dados inválidos"})
    if status_informado is not None and status_informado not in ("ativo", "inativo"):
        raise HTTPException(422, detail={"erro": "Dados inválidos"})

    if any(u["email"] == email for u in storage.usuarios.values()):
        raise HTTPException(409, detail={"erro": "E-mail já cadastrado"})

    novo_id = storage.next_usuario_id()
    usuario = {
        "id": novo_id,
        "nome": nome,
        "email": email,
        "status": status_informado if status_informado is not None else "ativo",
        "multa_pendente": 0.0,
    }
    storage.usuarios[novo_id] = usuario
    return usuario


@app.get("/usuarios/{id}", response_model=Usuario)
def consultar_usuario(id: int) -> dict:
    usuario = storage.usuarios.get(id)
    if usuario is None:
        raise HTTPException(404, detail={"erro": "Usuário não encontrado"})
    return usuario


# ---------------------------------------------------------------------------
# RF-07 — Registrar empréstimo
# ---------------------------------------------------------------------------


@app.post("/emprestimos", response_model=Emprestimo, status_code=201)
def registrar_emprestimo(payload: EmprestimoCreate) -> dict:
    body = payload.model_dump()
    usuario_id = body.get("usuario_id")
    livro_id = body.get("livro_id")
    data_emprestimo_raw = body.get("data_emprestimo")

    if not _valid_int(usuario_id) or not _valid_int(livro_id):
        raise HTTPException(422, detail={"erro": "Dados inválidos"})
    if data_emprestimo_raw is not None and not _valid_date_str(data_emprestimo_raw):
        raise HTTPException(422, detail={"erro": "Dados inválidos"})

    usuario = storage.usuarios.get(usuario_id)
    if usuario is None:
        raise HTTPException(404, detail={"erro": "Usuário não encontrado"})

    livro = storage.livros.get(livro_id)
    if livro is None:
        raise HTTPException(404, detail={"erro": "Livro não encontrado"})

    if usuario["status"] == "inativo":
        raise HTTPException(422, detail={"erro": "Usuário inativo"})
    if usuario["multa_pendente"] > 0:
        raise HTTPException(422, detail={"erro": "Usuário possui multa pendente"})

    emprestimos_ativos = [
        e for e in storage.emprestimos.values()
        if e["usuario_id"] == usuario_id and e["status"] == "ativo"
    ]
    if len(emprestimos_ativos) >= 3:
        raise HTTPException(422, detail={"erro": "Limite de empréstimos atingido"})

    if livro["status"] == "emprestado":
        raise HTTPException(409, detail={"erro": "Livro indisponível"})

    data_emprestimo = data_emprestimo_raw if data_emprestimo_raw is not None else date.today().isoformat()
    data_prevista = (date.fromisoformat(data_emprestimo) + timedelta(days=14)).isoformat()

    novo_id = storage.next_emprestimo_id()
    emprestimo = {
        "id": novo_id,
        "usuario_id": usuario_id,
        "livro_id": livro_id,
        "data_emprestimo": data_emprestimo,
        "data_devolucao_prevista": data_prevista,
        "data_devolucao_real": None,
        "multa": 0.0,
        "status": "ativo",
    }
    storage.emprestimos[novo_id] = emprestimo
    livro["status"] = "emprestado"
    return emprestimo


# ---------------------------------------------------------------------------
# RF-08 — Registrar devolução
# ---------------------------------------------------------------------------


@app.post("/devolucoes", response_model=Emprestimo)
def registrar_devolucao(payload: DevolucaoCreate) -> dict:
    body = payload.model_dump()
    emprestimo_id = body.get("emprestimo_id")
    data_devolucao_raw = body.get("data_devolucao")

    if not _valid_int(emprestimo_id):
        raise HTTPException(422, detail={"erro": "Dados inválidos"})
    if data_devolucao_raw is not None and not _valid_date_str(data_devolucao_raw):
        raise HTTPException(422, detail={"erro": "Dados inválidos"})

    emprestimo = storage.emprestimos.get(emprestimo_id)
    if emprestimo is None:
        raise HTTPException(404, detail={"erro": "Empréstimo não encontrado"})

    if emprestimo["status"] == "devolvido":
        raise HTTPException(409, detail={"erro": "Empréstimo já devolvido"})

    data_devolucao = data_devolucao_raw if data_devolucao_raw is not None else date.today().isoformat()

    data_prevista = date.fromisoformat(emprestimo["data_devolucao_prevista"])
    data_real = date.fromisoformat(data_devolucao)
    dias_atraso = (data_real - data_prevista).days

    multa = round(1.50 * dias_atraso, 2) if dias_atraso > 0 else 0.0

    emprestimo["data_devolucao_real"] = data_devolucao
    emprestimo["multa"] = multa
    emprestimo["status"] = "devolvido"

    usuario = storage.usuarios[emprestimo["usuario_id"]]
    usuario["multa_pendente"] = round(usuario["multa_pendente"] + multa, 2)

    livro = storage.livros[emprestimo["livro_id"]]
    livro["status"] = "disponivel"

    return emprestimo


# ---------------------------------------------------------------------------
# RF-09 — Listar empréstimos de um usuário
# ---------------------------------------------------------------------------


@app.get("/usuarios/{id}/emprestimos", response_model=List[Emprestimo])
def listar_emprestimos_usuario(id: int, status: Optional[str] = None) -> list:
    if status is not None and status not in ("ativo", "devolvido"):
        raise HTTPException(422, detail={"erro": "Dados inválidos"})

    usuario = storage.usuarios.get(id)
    if usuario is None:
        raise HTTPException(404, detail={"erro": "Usuário não encontrado"})

    emprestimos = [e for e in storage.emprestimos.values() if e["usuario_id"] == id]
    if status is not None:
        emprestimos = [e for e in emprestimos if e["status"] == status]
    return emprestimos


# ---------------------------------------------------------------------------
# RF-10 — Quitar multa do usuário
# ---------------------------------------------------------------------------


@app.post("/usuarios/{id}/pagamento-multa", response_model=Usuario)
def pagar_multa(id: int) -> dict:
    usuario = storage.usuarios.get(id)
    if usuario is None:
        raise HTTPException(404, detail={"erro": "Usuário não encontrado"})

    if usuario["multa_pendente"] == 0:
        raise HTTPException(409, detail={"erro": "Usuário não possui multa pendente"})

    usuario["multa_pendente"] = 0.0
    return usuario
