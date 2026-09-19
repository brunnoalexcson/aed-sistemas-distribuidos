from datetime import date, timedelta
from typing import List, Optional

from fastapi import Body, FastAPI, HTTPException, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.models import Emprestimo, Livro, Usuario
from app.storage import db

app = FastAPI()


@app.exception_handler(RequestValidationError)
async def tratar_erro_validacao(request, exc):
    return JSONResponse(status_code=422, content={"erro": "Dados inválidos"})


@app.exception_handler(HTTPException)
async def tratar_http_exception(request, exc):
    detalhe = exc.detail
    if isinstance(detalhe, dict) and "erro" in detalhe:
        conteudo = {"erro": detalhe["erro"]}
    else:
        conteudo = {"erro": str(detalhe)}
    return JSONResponse(status_code=exc.status_code, content=conteudo)


def erro(status_code: int, mensagem: str):
    raise HTTPException(status_code=status_code, detail={"erro": mensagem})


def _texto_valido(valor, tamanho_minimo, tamanho_maximo):
    if not isinstance(valor, str):
        return False
    tamanho = len(valor.strip())
    return tamanho_minimo <= tamanho <= tamanho_maximo


def _isbn_formato_valido(isbn):
    return len(isbn) == 13 and all(caractere in "0123456789" for caractere in isbn)


def _email_formato_valido(email):
    if email.count("@") != 1:
        return False
    local, _, dominio = email.partition("@")
    return len(local) >= 1 and len(dominio) >= 1


def _eh_inteiro(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


def _parsear_data_opcional(valor):
    if valor is None:
        return date.today()
    if not isinstance(valor, str):
        erro(422, "Dados inválidos")
    try:
        return date.fromisoformat(valor)
    except ValueError:
        erro(422, "Dados inválidos")


@app.post("/livros", response_model=Livro, status_code=201)
def criar_livro(body: dict = Body(...)):
    isbn = body.get("isbn")
    if isinstance(isbn, str) and not _isbn_formato_valido(isbn):
        erro(422, "ISBN inválido")

    titulo = body.get("titulo")
    autor = body.get("autor")

    if not _texto_valido(titulo, 1, 200):
        erro(422, "Dados inválidos")
    if not _texto_valido(autor, 1, 100):
        erro(422, "Dados inválidos")
    if not isinstance(isbn, str):
        erro(422, "Dados inválidos")

    for livro_existente in db.livros.values():
        if livro_existente["isbn"] == isbn:
            erro(409, "ISBN já cadastrado")

    novo_id = db.gerar_livro_id()
    livro = {
        "id": novo_id,
        "titulo": titulo,
        "autor": autor,
        "isbn": isbn,
        "status": "disponivel",
    }
    db.livros[novo_id] = livro
    return livro


@app.get("/livros", response_model=List[Livro])
def listar_livros(status: Optional[str] = None):
    if status is not None and status not in ("disponivel", "emprestado"):
        erro(422, "Dados inválidos")
    livros = list(db.livros.values())
    if status is not None:
        livros = [livro for livro in livros if livro["status"] == status]
    return livros


@app.get("/livros/{livro_id}", response_model=Livro)
def consultar_livro(livro_id: int):
    livro = db.livros.get(livro_id)
    if livro is None:
        erro(404, "Livro não encontrado")
    return livro


@app.delete("/livros/{livro_id}", status_code=204)
def excluir_livro(livro_id: int):
    livro = db.livros.get(livro_id)
    if livro is None:
        erro(404, "Livro não encontrado")

    possui_emprestimo_ativo = any(
        emprestimo["livro_id"] == livro_id and emprestimo["status"] == "ativo"
        for emprestimo in db.emprestimos.values()
    )
    if possui_emprestimo_ativo:
        erro(409, "Livro possui empréstimo ativo")

    del db.livros[livro_id]
    return Response(status_code=204)


@app.post("/usuarios", response_model=Usuario, status_code=201)
def criar_usuario(body: dict = Body(...)):
    email = body.get("email")
    if isinstance(email, str) and not _email_formato_valido(email):
        erro(422, "E-mail inválido")

    nome = body.get("nome")
    status_informado = body.get("status")

    if not _texto_valido(nome, 1, 100):
        erro(422, "Dados inválidos")
    if not isinstance(email, str):
        erro(422, "Dados inválidos")
    if status_informado is not None and status_informado not in ("ativo", "inativo"):
        erro(422, "Dados inválidos")

    for usuario_existente in db.usuarios.values():
        if usuario_existente["email"] == email:
            erro(409, "E-mail já cadastrado")

    novo_id = db.gerar_usuario_id()
    usuario = {
        "id": novo_id,
        "nome": nome,
        "email": email,
        "status": status_informado if status_informado is not None else "ativo",
        "multa_pendente": 0.0,
    }
    db.usuarios[novo_id] = usuario
    return usuario


@app.get("/usuarios/{usuario_id}", response_model=Usuario)
def consultar_usuario(usuario_id: int):
    usuario = db.usuarios.get(usuario_id)
    if usuario is None:
        erro(404, "Usuário não encontrado")
    return usuario


@app.post("/emprestimos", response_model=Emprestimo, status_code=201)
def criar_emprestimo(body: dict = Body(...)):
    usuario_id = body.get("usuario_id")
    livro_id = body.get("livro_id")
    data_emprestimo_valor = body.get("data_emprestimo")

    if not _eh_inteiro(usuario_id):
        erro(422, "Dados inválidos")
    if not _eh_inteiro(livro_id):
        erro(422, "Dados inválidos")

    data_emprestimo = _parsear_data_opcional(data_emprestimo_valor)

    usuario = db.usuarios.get(usuario_id)
    if usuario is None:
        erro(404, "Usuário não encontrado")

    livro = db.livros.get(livro_id)
    if livro is None:
        erro(404, "Livro não encontrado")

    if usuario["status"] == "inativo":
        erro(422, "Usuário inativo")

    if usuario["multa_pendente"] > 0:
        erro(422, "Usuário possui multa pendente")

    emprestimos_ativos = sum(
        1
        for emprestimo in db.emprestimos.values()
        if emprestimo["usuario_id"] == usuario_id and emprestimo["status"] == "ativo"
    )
    if emprestimos_ativos >= 3:
        erro(422, "Limite de empréstimos atingido")

    if livro["status"] == "emprestado":
        erro(409, "Livro indisponível")

    data_devolucao_prevista = data_emprestimo + timedelta(days=14)

    novo_id = db.gerar_emprestimo_id()
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
    return emprestimo


@app.post("/devolucoes", response_model=Emprestimo)
def registrar_devolucao(body: dict = Body(...)):
    emprestimo_id = body.get("emprestimo_id")
    data_devolucao_valor = body.get("data_devolucao")

    if not _eh_inteiro(emprestimo_id):
        erro(422, "Dados inválidos")

    data_devolucao = _parsear_data_opcional(data_devolucao_valor)

    emprestimo = db.emprestimos.get(emprestimo_id)
    if emprestimo is None:
        erro(404, "Empréstimo não encontrado")

    if emprestimo["status"] == "devolvido":
        erro(409, "Empréstimo já devolvido")

    data_devolucao_prevista = date.fromisoformat(emprestimo["data_devolucao_prevista"])
    dias_atraso = (data_devolucao - data_devolucao_prevista).days
    if dias_atraso > 0:
        multa = round(1.50 * dias_atraso, 2)
    else:
        multa = 0.0

    usuario = db.usuarios[emprestimo["usuario_id"]]
    usuario["multa_pendente"] = round(usuario["multa_pendente"] + multa, 2)

    emprestimo["data_devolucao_real"] = data_devolucao.isoformat()
    emprestimo["multa"] = multa
    emprestimo["status"] = "devolvido"

    livro = db.livros.get(emprestimo["livro_id"])
    if livro is not None:
        livro["status"] = "disponivel"

    return emprestimo


@app.get("/usuarios/{usuario_id}/emprestimos", response_model=List[Emprestimo])
def listar_emprestimos_usuario(usuario_id: int, status: Optional[str] = None):
    if status is not None and status not in ("ativo", "devolvido"):
        erro(422, "Dados inválidos")

    usuario = db.usuarios.get(usuario_id)
    if usuario is None:
        erro(404, "Usuário não encontrado")

    emprestimos = [
        emprestimo
        for emprestimo in db.emprestimos.values()
        if emprestimo["usuario_id"] == usuario_id
    ]
    if status is not None:
        emprestimos = [emprestimo for emprestimo in emprestimos if emprestimo["status"] == status]
    return emprestimos


@app.post("/usuarios/{usuario_id}/pagamento-multa", response_model=Usuario)
def pagar_multa(usuario_id: int):
    usuario = db.usuarios.get(usuario_id)
    if usuario is None:
        erro(404, "Usuário não encontrado")

    if usuario["multa_pendente"] == 0:
        erro(409, "Usuário não possui multa pendente")

    usuario["multa_pendente"] = 0.0
    return usuario
