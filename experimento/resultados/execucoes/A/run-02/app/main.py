"""Instância da aplicação FastAPI e todas as rotas do sistema."""

import re
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from fastapi import Body, FastAPI, HTTPException, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.models import EmprestimoOut, LivroOut, UsuarioOut
from app.storage import storage

app = FastAPI()

FORMATO_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def erro_response(status_code: int, mensagem: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"erro": mensagem})


@app.exception_handler(RequestValidationError)
async def tratar_erro_validacao(request: Request, exc: RequestValidationError) -> JSONResponse:
    return erro_response(422, "Dados inválidos")


@app.exception_handler(StarletteHTTPException)
async def tratar_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    mensagem = exc.detail if isinstance(exc.detail, str) else "Erro"
    return erro_response(exc.status_code, mensagem)


def parse_data(valor: Any) -> date:
    if not isinstance(valor, str) or not FORMATO_DATA.match(valor):
        raise ValueError("formato de data inválido")
    ano, mes, dia = valor.split("-")
    return date(int(ano), int(mes), int(dia))


def validar_isbn_formato(isbn: str) -> bool:
    return isinstance(isbn, str) and len(isbn) == 13 and isbn.isdigit()


def validar_email_formato(email: str) -> bool:
    if not isinstance(email, str):
        return False
    if email.count("@") != 1:
        return False
    parte_local, parte_dominio = email.split("@")
    return len(parte_local) >= 1 and len(parte_dominio) >= 1


# ---------------------------------------------------------------------------
# Livros
# ---------------------------------------------------------------------------


@app.post("/livros", response_model=LivroOut, status_code=201)
async def criar_livro(body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    titulo = body.get("titulo")
    autor = body.get("autor")
    isbn = body.get("isbn")

    titulo_invalido = not isinstance(titulo, str) or not (1 <= len(titulo.strip()) <= 200)
    autor_invalido = not isinstance(autor, str) or not (1 <= len(autor.strip()) <= 100)
    isbn_ausente_ou_tipo_incorreto = not isinstance(isbn, str)
    isbn_formato_invalido = isinstance(isbn, str) and not validar_isbn_formato(isbn)

    if isbn_formato_invalido:
        raise HTTPException(status_code=422, detail="ISBN inválido")
    if titulo_invalido or autor_invalido or isbn_ausente_ou_tipo_incorreto:
        raise HTTPException(status_code=422, detail="Dados inválidos")

    if storage.isbn_existe(isbn):
        raise HTTPException(status_code=409, detail="ISBN já cadastrado")

    novo_id = storage.gerar_id_livro()
    livro = {
        "id": novo_id,
        "titulo": titulo,
        "autor": autor,
        "isbn": isbn,
        "status": "disponivel",
    }
    storage.livros[novo_id] = livro
    return livro


@app.get("/livros", response_model=List[LivroOut])
async def listar_livros(status: Optional[str] = Query(default=None)) -> List[Dict[str, Any]]:
    if status is not None and status not in ("disponivel", "emprestado"):
        raise HTTPException(status_code=422, detail="Dados inválidos")

    livros = list(storage.livros.values())
    if status is not None:
        livros = [livro for livro in livros if livro["status"] == status]
    return livros


@app.get("/livros/{id}", response_model=LivroOut)
async def consultar_livro(id: int) -> Dict[str, Any]:
    livro = storage.livros.get(id)
    if livro is None:
        raise HTTPException(status_code=404, detail="Livro não encontrado")
    return livro


@app.delete("/livros/{id}", status_code=204)
async def excluir_livro(id: int) -> Response:
    livro = storage.livros.get(id)
    if livro is None:
        raise HTTPException(status_code=404, detail="Livro não encontrado")
    if storage.livro_possui_emprestimo_ativo(id):
        raise HTTPException(status_code=409, detail="Livro possui empréstimo ativo")
    del storage.livros[id]
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Usuarios
# ---------------------------------------------------------------------------


@app.post("/usuarios", response_model=UsuarioOut, status_code=201)
async def criar_usuario(body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    nome = body.get("nome")
    email = body.get("email")
    status_valor = body.get("status", None)

    nome_invalido = not isinstance(nome, str) or not (1 <= len(nome.strip()) <= 100)
    email_ausente_ou_tipo_incorreto = not isinstance(email, str)
    email_formato_invalido = isinstance(email, str) and not validar_email_formato(email)
    status_invalido = status_valor is not None and (
        not isinstance(status_valor, str) or status_valor not in ("ativo", "inativo")
    )

    if email_formato_invalido:
        raise HTTPException(status_code=422, detail="E-mail inválido")
    if nome_invalido or email_ausente_ou_tipo_incorreto or status_invalido:
        raise HTTPException(status_code=422, detail="Dados inválidos")

    if storage.email_existe(email):
        raise HTTPException(status_code=409, detail="E-mail já cadastrado")

    novo_id = storage.gerar_id_usuario()
    usuario = {
        "id": novo_id,
        "nome": nome,
        "email": email,
        "status": status_valor if status_valor is not None else "ativo",
        "multa_pendente": 0.0,
    }
    storage.usuarios[novo_id] = usuario
    return usuario


@app.get("/usuarios/{id}", response_model=UsuarioOut)
async def consultar_usuario(id: int) -> Dict[str, Any]:
    usuario = storage.usuarios.get(id)
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario


# ---------------------------------------------------------------------------
# Emprestimos e devolucoes
# ---------------------------------------------------------------------------


@app.post("/emprestimos", response_model=EmprestimoOut, status_code=201)
async def registrar_emprestimo(body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    usuario_id = body.get("usuario_id")
    livro_id = body.get("livro_id")
    data_emprestimo_valor = body.get("data_emprestimo", None)

    usuario_id_invalido = not isinstance(usuario_id, int) or isinstance(usuario_id, bool)
    livro_id_invalido = not isinstance(livro_id, int) or isinstance(livro_id, bool)

    data_emprestimo_invalida = False
    data_emprestimo_obj: Optional[date] = None
    if data_emprestimo_valor is not None:
        try:
            data_emprestimo_obj = parse_data(data_emprestimo_valor)
        except (ValueError, TypeError):
            data_emprestimo_invalida = True

    if usuario_id_invalido or livro_id_invalido or data_emprestimo_invalida:
        raise HTTPException(status_code=422, detail="Dados inválidos")

    usuario = storage.usuarios.get(usuario_id)
    livro = storage.livros.get(livro_id)

    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if livro is None:
        raise HTTPException(status_code=404, detail="Livro não encontrado")

    if usuario["status"] == "inativo":
        raise HTTPException(status_code=422, detail="Usuário inativo")
    if usuario["multa_pendente"] > 0:
        raise HTTPException(status_code=422, detail="Usuário possui multa pendente")
    if len(storage.emprestimos_ativos_do_usuario(usuario_id)) >= 3:
        raise HTTPException(status_code=422, detail="Limite de empréstimos atingido")

    if livro["status"] == "emprestado":
        raise HTTPException(status_code=409, detail="Livro indisponível")

    if data_emprestimo_obj is None:
        data_emprestimo_obj = date.today()
    data_devolucao_prevista_obj = data_emprestimo_obj + timedelta(days=14)

    novo_id = storage.gerar_id_emprestimo()
    emprestimo = {
        "id": novo_id,
        "usuario_id": usuario_id,
        "livro_id": livro_id,
        "data_emprestimo": data_emprestimo_obj.isoformat(),
        "data_devolucao_prevista": data_devolucao_prevista_obj.isoformat(),
        "data_devolucao_real": None,
        "multa": 0.0,
        "status": "ativo",
    }
    storage.emprestimos[novo_id] = emprestimo
    livro["status"] = "emprestado"
    return emprestimo


@app.post("/devolucoes", response_model=EmprestimoOut)
async def registrar_devolucao(body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    emprestimo_id = body.get("emprestimo_id")
    data_devolucao_valor = body.get("data_devolucao", None)

    emprestimo_id_invalido = not isinstance(emprestimo_id, int) or isinstance(emprestimo_id, bool)

    data_devolucao_invalida = False
    data_devolucao_obj: Optional[date] = None
    if data_devolucao_valor is not None:
        try:
            data_devolucao_obj = parse_data(data_devolucao_valor)
        except (ValueError, TypeError):
            data_devolucao_invalida = True

    if emprestimo_id_invalido or data_devolucao_invalida:
        raise HTTPException(status_code=422, detail="Dados inválidos")

    emprestimo = storage.emprestimos.get(emprestimo_id)
    if emprestimo is None:
        raise HTTPException(status_code=404, detail="Empréstimo não encontrado")

    if emprestimo["status"] == "devolvido":
        raise HTTPException(status_code=409, detail="Empréstimo já devolvido")

    if data_devolucao_obj is None:
        data_devolucao_obj = date.today()

    data_devolucao_prevista_obj = parse_data(emprestimo["data_devolucao_prevista"])
    dias_atraso = (data_devolucao_obj - data_devolucao_prevista_obj).days
    if dias_atraso > 0:
        multa = round(1.50 * dias_atraso, 2)
    else:
        multa = 0.0

    usuario = storage.usuarios.get(emprestimo["usuario_id"])
    if usuario is not None:
        usuario["multa_pendente"] = round(usuario["multa_pendente"] + multa, 2)

    emprestimo["data_devolucao_real"] = data_devolucao_obj.isoformat()
    emprestimo["multa"] = multa
    emprestimo["status"] = "devolvido"

    livro = storage.livros.get(emprestimo["livro_id"])
    if livro is not None:
        livro["status"] = "disponivel"

    return emprestimo


@app.get("/usuarios/{id}/emprestimos", response_model=List[EmprestimoOut])
async def listar_emprestimos_usuario(
    id: int, status: Optional[str] = Query(default=None)
) -> List[Dict[str, Any]]:
    if status is not None and status not in ("ativo", "devolvido"):
        raise HTTPException(status_code=422, detail="Dados inválidos")

    usuario = storage.usuarios.get(id)
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    emprestimos = storage.emprestimos_do_usuario(id)
    if status is not None:
        emprestimos = [emprestimo for emprestimo in emprestimos if emprestimo["status"] == status]
    return emprestimos


@app.post("/usuarios/{id}/pagamento-multa", response_model=UsuarioOut)
async def pagar_multa(id: int) -> Dict[str, Any]:
    usuario = storage.usuarios.get(id)
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if usuario["multa_pendente"] == 0:
        raise HTTPException(status_code=409, detail="Usuário não possui multa pendente")
    usuario["multa_pendente"] = 0.0
    return usuario
