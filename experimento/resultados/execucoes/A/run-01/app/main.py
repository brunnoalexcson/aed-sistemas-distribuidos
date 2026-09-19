from datetime import date, datetime, timedelta
from typing import List, Literal, Optional

from fastapi import FastAPI, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.models import (
    DevolucaoCreate,
    EmprestimoCreate,
    EmprestimoOut,
    LivroCreate,
    LivroOut,
    UsuarioCreate,
    UsuarioOut,
)
from app.storage import storage

app = FastAPI()


def erro_response(status_code: int, mensagem: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"erro": mensagem})


@app.exception_handler(RequestValidationError)
async def tratar_erro_validacao(request: Request, exc: RequestValidationError) -> JSONResponse:
    mensagem = "Dados inválidos"
    for item in exc.errors():
        loc = item.get("loc", ())
        tipo = item.get("type", "")
        if tipo == "value_error" and "isbn" in loc:
            mensagem = "ISBN inválido"
            break
        if tipo == "value_error" and "email" in loc:
            mensagem = "E-mail inválido"
            break
    return erro_response(422, mensagem)


@app.exception_handler(StarletteHTTPException)
async def tratar_erro_http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    mensagem = exc.detail if isinstance(exc.detail, str) else "Erro"
    return erro_response(exc.status_code, mensagem)


@app.post("/livros", status_code=201, response_model=LivroOut)
async def criar_livro(livro: LivroCreate):
    isbn_existente = any(l["isbn"] == livro.isbn for l in storage.livros.values())
    if isbn_existente:
        return erro_response(409, "ISBN já cadastrado")

    novo_id = storage.proximo_id_livro()
    registro = {
        "id": novo_id,
        "titulo": livro.titulo,
        "autor": livro.autor,
        "isbn": livro.isbn,
        "status": "disponivel",
    }
    storage.livros[novo_id] = registro
    return registro


@app.get("/livros", response_model=List[LivroOut])
async def listar_livros(
    status: Optional[Literal["disponivel", "emprestado"]] = Query(default=None),
):
    livros = list(storage.livros.values())
    if status is not None:
        livros = [livro for livro in livros if livro["status"] == status]
    return livros


@app.get("/livros/{livro_id}", response_model=LivroOut)
async def consultar_livro(livro_id: int):
    livro = storage.livros.get(livro_id)
    if livro is None:
        return erro_response(404, "Livro não encontrado")
    return livro


@app.delete("/livros/{livro_id}", status_code=204)
async def excluir_livro(livro_id: int):
    livro = storage.livros.get(livro_id)
    if livro is None:
        return erro_response(404, "Livro não encontrado")

    possui_emprestimo_ativo = any(
        emprestimo["livro_id"] == livro_id and emprestimo["status"] == "ativo"
        for emprestimo in storage.emprestimos.values()
    )
    if possui_emprestimo_ativo:
        return erro_response(409, "Livro possui empréstimo ativo")

    del storage.livros[livro_id]
    return Response(status_code=204)


@app.post("/usuarios", status_code=201, response_model=UsuarioOut)
async def criar_usuario(usuario: UsuarioCreate):
    email_existente = any(u["email"] == usuario.email for u in storage.usuarios.values())
    if email_existente:
        return erro_response(409, "E-mail já cadastrado")

    novo_id = storage.proximo_id_usuario()
    status_usuario = usuario.status if usuario.status is not None else "ativo"
    registro = {
        "id": novo_id,
        "nome": usuario.nome,
        "email": usuario.email,
        "status": status_usuario,
        "multa_pendente": 0.0,
    }
    storage.usuarios[novo_id] = registro
    return registro


@app.get("/usuarios/{usuario_id}", response_model=UsuarioOut)
async def consultar_usuario(usuario_id: int):
    usuario = storage.usuarios.get(usuario_id)
    if usuario is None:
        return erro_response(404, "Usuário não encontrado")
    return usuario


@app.post("/emprestimos", status_code=201, response_model=EmprestimoOut)
async def registrar_emprestimo(emprestimo: EmprestimoCreate):
    usuario = storage.usuarios.get(emprestimo.usuario_id)
    if usuario is None:
        return erro_response(404, "Usuário não encontrado")

    livro = storage.livros.get(emprestimo.livro_id)
    if livro is None:
        return erro_response(404, "Livro não encontrado")

    if usuario["status"] == "inativo":
        return erro_response(422, "Usuário inativo")

    if usuario["multa_pendente"] > 0:
        return erro_response(422, "Usuário possui multa pendente")

    emprestimos_ativos = sum(
        1
        for item in storage.emprestimos.values()
        if item["usuario_id"] == usuario["id"] and item["status"] == "ativo"
    )
    if emprestimos_ativos >= 3:
        return erro_response(422, "Limite de empréstimos atingido")

    if livro["status"] == "emprestado":
        return erro_response(409, "Livro indisponível")

    if emprestimo.data_emprestimo is not None:
        data_emprestimo_str = emprestimo.data_emprestimo
    else:
        data_emprestimo_str = date.today().strftime("%Y-%m-%d")

    data_emprestimo_obj = datetime.strptime(data_emprestimo_str, "%Y-%m-%d").date()
    data_prevista_obj = data_emprestimo_obj + timedelta(days=14)
    data_prevista_str = data_prevista_obj.strftime("%Y-%m-%d")

    novo_id = storage.proximo_id_emprestimo()
    registro = {
        "id": novo_id,
        "usuario_id": usuario["id"],
        "livro_id": livro["id"],
        "data_emprestimo": data_emprestimo_str,
        "data_devolucao_prevista": data_prevista_str,
        "data_devolucao_real": None,
        "multa": 0.0,
        "status": "ativo",
    }
    storage.emprestimos[novo_id] = registro
    livro["status"] = "emprestado"
    return registro


@app.post("/devolucoes", response_model=EmprestimoOut)
async def registrar_devolucao(devolucao: DevolucaoCreate):
    emprestimo = storage.emprestimos.get(devolucao.emprestimo_id)
    if emprestimo is None:
        return erro_response(404, "Empréstimo não encontrado")

    if emprestimo["status"] == "devolvido":
        return erro_response(409, "Empréstimo já devolvido")

    if devolucao.data_devolucao is not None:
        data_devolucao_str = devolucao.data_devolucao
    else:
        data_devolucao_str = date.today().strftime("%Y-%m-%d")

    data_devolucao_obj = datetime.strptime(data_devolucao_str, "%Y-%m-%d").date()
    data_prevista_obj = datetime.strptime(
        emprestimo["data_devolucao_prevista"], "%Y-%m-%d"
    ).date()

    dias_atraso = (data_devolucao_obj - data_prevista_obj).days
    if dias_atraso > 0:
        multa = round(1.50 * dias_atraso, 2)
    else:
        multa = 0.0

    usuario = storage.usuarios.get(emprestimo["usuario_id"])
    if usuario is not None:
        usuario["multa_pendente"] = round(usuario["multa_pendente"] + multa, 2)

    emprestimo["data_devolucao_real"] = data_devolucao_str
    emprestimo["multa"] = multa
    emprestimo["status"] = "devolvido"

    livro = storage.livros.get(emprestimo["livro_id"])
    if livro is not None:
        livro["status"] = "disponivel"

    return emprestimo


@app.get("/usuarios/{usuario_id}/emprestimos", response_model=List[EmprestimoOut])
async def listar_emprestimos_usuario(
    usuario_id: int,
    status: Optional[Literal["ativo", "devolvido"]] = Query(default=None),
):
    usuario = storage.usuarios.get(usuario_id)
    if usuario is None:
        return erro_response(404, "Usuário não encontrado")

    emprestimos = [
        emprestimo
        for emprestimo in storage.emprestimos.values()
        if emprestimo["usuario_id"] == usuario_id
    ]
    if status is not None:
        emprestimos = [emprestimo for emprestimo in emprestimos if emprestimo["status"] == status]
    return emprestimos


@app.post("/usuarios/{usuario_id}/pagamento-multa", response_model=UsuarioOut)
async def pagar_multa(usuario_id: int):
    usuario = storage.usuarios.get(usuario_id)
    if usuario is None:
        return erro_response(404, "Usuário não encontrado")

    if usuario["multa_pendente"] == 0:
        return erro_response(409, "Usuário não possui multa pendente")

    usuario["multa_pendente"] = 0.0
    return usuario
