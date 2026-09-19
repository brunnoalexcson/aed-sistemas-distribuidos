"""API REST do sistema de biblioteca do bairro.

Permite cadastrar livros e usuários, controlar empréstimos e devoluções,
calcular multas por atraso e registrar o pagamento delas. Não há autenticação
nem interface gráfica: apenas endpoints HTTP. Todo o estado é mantido em
memória (sem banco de dados).
"""

from flask import Flask, jsonify, request

from store import ApiError, Biblioteca

app = Flask(__name__)
biblioteca = Biblioteca()


# ---------------------------------------------------------------
# Tratamento de erros
# ---------------------------------------------------------------

@app.errorhandler(ApiError)
def tratar_erro_api(erro: ApiError):
    resposta = jsonify({"erro": erro.message})
    resposta.status_code = erro.status_code
    return resposta


@app.errorhandler(404)
def tratar_rota_nao_encontrada(_erro):
    return jsonify({"erro": "Recurso não encontrado."}), 404


@app.errorhandler(405)
def tratar_metodo_nao_permitido(_erro):
    return jsonify({"erro": "Método não permitido para este recurso."}), 405


@app.errorhandler(500)
def tratar_erro_interno(_erro):
    return jsonify({"erro": "Erro interno do servidor."}), 500


def corpo_json() -> dict:
    dados = request.get_json(silent=True)
    if dados is None or not isinstance(dados, dict):
        raise ApiError("Corpo da requisição deve ser um JSON válido.", 400)
    return dados


def _texto_para_bool(valor) -> bool:
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, str):
        return valor.strip().lower() in ("1", "true", "sim", "yes")
    return False


# ---------------------------------------------------------------
# Livros
# ---------------------------------------------------------------

@app.route("/livros", methods=["POST"])
def criar_livro():
    dados = corpo_json()
    livro = biblioteca.criar_livro(
        titulo=dados.get("titulo"),
        autor=dados.get("autor"),
        isbn=dados.get("isbn"),
    )
    return jsonify(livro.to_dict()), 201


@app.route("/livros", methods=["GET"])
def listar_livros():
    livros = biblioteca.listar_livros()
    return jsonify([livro.to_dict() for livro in livros]), 200


@app.route("/livros/<int:livro_id>", methods=["GET"])
def buscar_livro(livro_id):
    livro = biblioteca.buscar_livro(livro_id)
    return jsonify(livro.to_dict()), 200


@app.route("/livros/<int:livro_id>", methods=["DELETE"])
def excluir_livro(livro_id):
    biblioteca.excluir_livro(livro_id)
    return "", 204


# ---------------------------------------------------------------
# Usuários
# ---------------------------------------------------------------

@app.route("/usuarios", methods=["POST"])
def criar_usuario():
    dados = corpo_json()
    usuario = biblioteca.criar_usuario(
        nome=dados.get("nome"),
        email=dados.get("email"),
    )
    return jsonify(usuario.to_dict()), 201


@app.route("/usuarios", methods=["GET"])
def listar_usuarios():
    usuarios = biblioteca.listar_usuarios()
    return jsonify([usuario.to_dict() for usuario in usuarios]), 200


@app.route("/usuarios/<int:usuario_id>", methods=["GET"])
def buscar_usuario(usuario_id):
    usuario = biblioteca.buscar_usuario(usuario_id)
    return jsonify(usuario.to_dict()), 200


@app.route("/usuarios/<int:usuario_id>", methods=["PATCH"])
def atualizar_usuario(usuario_id):
    dados = corpo_json()
    usuario = biblioteca.atualizar_usuario(
        usuario_id,
        nome=dados.get("nome"),
        email=dados.get("email"),
        ativo=dados.get("ativo"),
    )
    return jsonify(usuario.to_dict()), 200


@app.route("/usuarios/<int:usuario_id>/emprestimos", methods=["GET"])
def listar_emprestimos_usuario(usuario_id):
    apenas_abertos = _texto_para_bool(request.args.get("abertos", ""))
    emprestimos = biblioteca.listar_emprestimos_usuario(
        usuario_id, apenas_abertos=apenas_abertos
    )
    return jsonify([emprestimo.to_dict() for emprestimo in emprestimos]), 200


@app.route("/usuarios/<int:usuario_id>/multas/pagamentos", methods=["POST"])
def pagar_multa(usuario_id):
    usuario, valor_pago = biblioteca.pagar_multa(usuario_id)
    return (
        jsonify({"usuario": usuario.to_dict(), "valor_pago": round(valor_pago, 2)}),
        200,
    )


# ---------------------------------------------------------------
# Empréstimos
# ---------------------------------------------------------------

@app.route("/emprestimos", methods=["POST"])
def criar_emprestimo():
    dados = corpo_json()
    usuario_id = dados.get("usuario_id")
    livro_id = dados.get("livro_id")
    if not isinstance(usuario_id, int) or not isinstance(livro_id, int):
        raise ApiError(
            "Os campos 'usuario_id' e 'livro_id' são obrigatórios e devem ser "
            "números inteiros.",
            400,
        )
    emprestimo = biblioteca.criar_emprestimo(usuario_id, livro_id)
    return jsonify(emprestimo.to_dict()), 201


@app.route("/emprestimos", methods=["GET"])
def listar_emprestimos():
    emprestimos = biblioteca.listar_emprestimos()
    return jsonify([emprestimo.to_dict() for emprestimo in emprestimos]), 200


@app.route("/emprestimos/<int:emprestimo_id>", methods=["GET"])
def buscar_emprestimo(emprestimo_id):
    emprestimo = biblioteca.buscar_emprestimo(emprestimo_id)
    return jsonify(emprestimo.to_dict()), 200


@app.route("/emprestimos/<int:emprestimo_id>/devolucao", methods=["POST"])
def devolver_emprestimo(emprestimo_id):
    emprestimo = biblioteca.registrar_devolucao(emprestimo_id)
    return jsonify(emprestimo.to_dict()), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
