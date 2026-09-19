"""API REST do sistema de biblioteca do bairro.

Aplicação Flask que expõe endpoints para:

- cadastro, listagem, busca e exclusão de livros;
- cadastro, listagem e busca de usuários;
- registro de empréstimos e devoluções;
- consulta dos empréstimos de um usuário (com filtro para os em aberto);
- pagamento de multas por atraso na devolução.

Não há autenticação/login nem interface gráfica: é apenas a API. Todos os
dados são mantidos em memória, sem uso de banco de dados.

Para executar localmente:

    pip install -r requirements.txt
    python app.py

A API sobe por padrão em http://127.0.0.1:5000/
"""

from flask import Flask, jsonify, request

from errors import ErroApi
from services import ServicoBiblioteca
from storage import repositorio

app = Flask(__name__)
servico = ServicoBiblioteca(repositorio)


# ----------------------------------------------------------------------
# Tratamento de erros
# ----------------------------------------------------------------------
@app.errorhandler(ErroApi)
def tratar_erro_api(erro: ErroApi):
    resposta = jsonify(erro.to_dict())
    resposta.status_code = erro.status_code
    return resposta


@app.errorhandler(404)
def tratar_404(_erro):
    resposta = jsonify({"erro": "Recurso não encontrado."})
    resposta.status_code = 404
    return resposta


@app.errorhandler(405)
def tratar_405(_erro):
    resposta = jsonify({"erro": "Método não permitido para este recurso."})
    resposta.status_code = 405
    return resposta


@app.errorhandler(500)
def tratar_500(_erro):
    resposta = jsonify({"erro": "Erro interno do servidor."})
    resposta.status_code = 500
    return resposta


def corpo_json() -> dict:
    """Obtém o corpo JSON da requisição, tratando corpos ausentes/ inválidos."""
    dados = request.get_json(silent=True)
    if dados is None:
        return {}
    if not isinstance(dados, dict):
        return {}
    return dados


def parametro_booleano(valor, padrao: bool = False) -> bool:
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, str):
        return valor.strip().lower() in ("1", "true", "sim", "yes")
    return padrao


# ----------------------------------------------------------------------
# Livros
# ----------------------------------------------------------------------
@app.route("/livros", methods=["POST"])
def criar_livro():
    dados = corpo_json()
    livro = servico.cadastrar_livro(
        titulo=dados.get("titulo"),
        autor=dados.get("autor"),
        isbn=dados.get("isbn"),
    )
    return jsonify(livro.to_dict()), 201


@app.route("/livros", methods=["GET"])
def listar_livros():
    disponivel_param = request.args.get("disponivel")
    livros = servico.listar_livros()
    if disponivel_param is not None:
        disponivel = parametro_booleano(disponivel_param)
        livros = [l for l in livros if l.disponivel == disponivel]
    return jsonify([livro.to_dict() for livro in livros]), 200


@app.route("/livros/<int:livro_id>", methods=["GET"])
def buscar_livro(livro_id: int):
    livro = servico.buscar_livro(livro_id)
    return jsonify(livro.to_dict()), 200


@app.route("/livros/<int:livro_id>", methods=["DELETE"])
def excluir_livro(livro_id: int):
    servico.excluir_livro(livro_id)
    return "", 204


# ----------------------------------------------------------------------
# Usuários
# ----------------------------------------------------------------------
@app.route("/usuarios", methods=["POST"])
def criar_usuario():
    dados = corpo_json()
    usuario = servico.cadastrar_usuario(
        nome=dados.get("nome"),
        email=dados.get("email"),
    )
    return jsonify(usuario.to_dict()), 201


@app.route("/usuarios", methods=["GET"])
def listar_usuarios():
    usuarios = servico.listar_usuarios()
    return jsonify([usuario.to_dict() for usuario in usuarios]), 200


@app.route("/usuarios/<int:usuario_id>", methods=["GET"])
def buscar_usuario(usuario_id: int):
    usuario = servico.buscar_usuario(usuario_id)
    return jsonify(usuario.to_dict()), 200


@app.route("/usuarios/<int:usuario_id>", methods=["PATCH"])
def atualizar_usuario(usuario_id: int):
    dados = corpo_json()
    if "ativo" not in dados:
        raise ErroApi("O campo 'ativo' é obrigatório para atualizar o usuário.", 400)
    usuario = servico.atualizar_status_usuario(usuario_id, parametro_booleano(dados.get("ativo")))
    return jsonify(usuario.to_dict()), 200


@app.route("/usuarios/<int:usuario_id>/emprestimos", methods=["GET"])
def listar_emprestimos_do_usuario(usuario_id: int):
    apenas_em_aberto = parametro_booleano(request.args.get("em_aberto"), padrao=False)
    emprestimos = servico.listar_emprestimos_do_usuario(usuario_id, apenas_em_aberto)
    return jsonify([e.to_dict() for e in emprestimos]), 200


@app.route("/usuarios/<int:usuario_id>/multa/pagamento", methods=["POST"])
def pagar_multa(usuario_id: int):
    usuario = servico.pagar_multa(usuario_id)
    return jsonify(usuario.to_dict()), 200


# ----------------------------------------------------------------------
# Empréstimos
# ----------------------------------------------------------------------
@app.route("/emprestimos", methods=["POST"])
def criar_emprestimo():
    dados = corpo_json()
    usuario_id = dados.get("usuario_id")
    livro_id = dados.get("livro_id")

    if usuario_id is None:
        raise ErroApi("O campo 'usuario_id' é obrigatório.", 400)
    if livro_id is None:
        raise ErroApi("O campo 'livro_id' é obrigatório.", 400)

    try:
        usuario_id = int(usuario_id)
        livro_id = int(livro_id)
    except (TypeError, ValueError):
        raise ErroApi("Os campos 'usuario_id' e 'livro_id' devem ser numéricos.", 400)

    emprestimo = servico.registrar_emprestimo(usuario_id=usuario_id, livro_id=livro_id)
    return jsonify(emprestimo.to_dict()), 201


@app.route("/emprestimos", methods=["GET"])
def listar_emprestimos():
    emprestimos = servico.listar_emprestimos()
    return jsonify([e.to_dict() for e in emprestimos]), 200


@app.route("/emprestimos/<int:emprestimo_id>", methods=["GET"])
def buscar_emprestimo(emprestimo_id: int):
    emprestimo = repositorio.obter_emprestimo(emprestimo_id)
    if emprestimo is None:
        raise ErroApi(f"Empréstimo com id {emprestimo_id} não encontrado.", 404)
    return jsonify(emprestimo.to_dict()), 200


@app.route("/emprestimos/<int:emprestimo_id>/devolucao", methods=["POST"])
def devolver_emprestimo(emprestimo_id: int):
    emprestimo = servico.devolver_livro(emprestimo_id)
    return jsonify(emprestimo.to_dict()), 200


if __name__ == "__main__":
    app.run(debug=True)
