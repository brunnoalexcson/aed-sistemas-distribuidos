"""API REST do sistema de biblioteca do bairro.

Funcionalidades cobertas:
  - Cadastro de livros (título, autor, ISBN) e listagem/busca/exclusão.
    Um livro não pode ser excluído enquanto estiver emprestado.
  - Cadastro de usuários (nome, e-mail).
  - Registro de empréstimos, com as regras:
      * prazo de devolução de 14 dias (duas semanas);
      * um usuário pode ter no máximo 3 livros emprestados ao mesmo tempo;
      * usuário inativo não pode pegar livro emprestado;
      * usuário com multa pendente não pode pegar livro emprestado;
      * o livro fica indisponível enquanto estiver emprestado.
  - Registro de devolução, com cálculo de multa de R$ 1,50 por dia de
    atraso, que fica pendente na conta do usuário até ser paga.
  - Pagamento de multa, zerando a pendência do usuário.
  - Listagem dos empréstimos de um usuário, com filtro opcional para
    mostrar apenas os que estão em aberto.

Todo o estado é mantido em memória (sem banco de dados), e a aplicação
não possui autenticação nem interface gráfica: é apenas a API.
"""

from datetime import date, datetime, timedelta

from flask import Flask, jsonify, request

from errors import ApiError
from models import STATUS_ABERTO, STATUS_DEVOLVIDO, Emprestimo, Livro, Usuario
from storage import storage

PRAZO_DEVOLUCAO_DIAS = 14
VALOR_MULTA_POR_DIA = 1.50
LIMITE_EMPRESTIMOS_POR_USUARIO = 3


def create_app() -> Flask:
    app = Flask(__name__)

    # Garante que caracteres acentuados sejam retornados como UTF-8 legível
    # (e não escapados em \uXXXX) nas respostas JSON, em qualquer versão do Flask.
    try:
        app.json.ensure_ascii = False  # Flask >= 2.3
    except AttributeError:
        app.config["JSON_AS_ASCII"] = False  # Flask < 2.3

    # ------------------------------------------------------------------
    # Tratamento de erros
    # ------------------------------------------------------------------
    @app.errorhandler(ApiError)
    def handle_api_error(err: ApiError):
        response = jsonify(err.to_dict())
        response.status_code = err.status_code
        return response

    @app.errorhandler(404)
    def handle_404(_err):
        return jsonify({"erro": "recurso não encontrado"}), 404

    @app.errorhandler(405)
    def handle_405(_err):
        return jsonify({"erro": "método não permitido para este recurso"}), 405

    @app.errorhandler(500)
    def handle_500(_err):
        return jsonify({"erro": "erro interno do servidor"}), 500

    # ------------------------------------------------------------------
    # Funções auxiliares
    # ------------------------------------------------------------------
    def get_json_body() -> dict:
        data = request.get_json(silent=True)
        if data is None or not isinstance(data, dict):
            raise ApiError("corpo da requisição deve ser um JSON válido", 400)
        return data

    def campo_texto(data: dict, campo: str, obrigatorio: bool = True) -> str:
        valor = data.get(campo)
        if valor is None:
            valor = ""
        valor = str(valor).strip()
        if obrigatorio and not valor:
            raise ApiError(f"campo '{campo}' é obrigatório", 400)
        return valor

    def parse_data_iso(valor, campo: str) -> date:
        try:
            return datetime.strptime(valor, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            raise ApiError(
                f"campo '{campo}' deve estar no formato AAAA-MM-DD", 400
            )

    def parse_inteiro(valor, campo: str) -> int:
        try:
            if isinstance(valor, bool):
                raise ValueError
            return int(valor)
        except (TypeError, ValueError):
            raise ApiError(f"campo '{campo}' deve ser um número inteiro", 400)

    def obter_livro_ou_404(livro_id: int) -> Livro:
        livro = storage.livros.get(livro_id)
        if livro is None:
            raise ApiError("livro não encontrado", 404)
        return livro

    def obter_usuario_ou_404(usuario_id: int) -> Usuario:
        usuario = storage.usuarios.get(usuario_id)
        if usuario is None:
            raise ApiError("usuário não encontrado", 404)
        return usuario

    def obter_emprestimo_ou_404(emprestimo_id: int) -> Emprestimo:
        emprestimo = storage.emprestimos.get(emprestimo_id)
        if emprestimo is None:
            raise ApiError("empréstimo não encontrado", 404)
        return emprestimo

    def parse_bool_query_param(nome: str) -> bool:
        valor = request.args.get(nome, "")
        return valor.strip().lower() in ("1", "true", "sim", "yes")

    # ------------------------------------------------------------------
    # Raiz / health check
    # ------------------------------------------------------------------
    @app.route("/", methods=["GET"])
    def raiz():
        return jsonify(
            {
                "servico": "API da biblioteca",
                "status": "ok",
            }
        ), 200

    # ------------------------------------------------------------------
    # Livros
    # ------------------------------------------------------------------
    @app.route("/livros", methods=["POST"])
    def criar_livro():
        data = get_json_body()
        titulo = campo_texto(data, "titulo")
        autor = campo_texto(data, "autor")
        isbn = campo_texto(data, "isbn")

        livro_id = storage.next_livro_id()
        livro = Livro(id=livro_id, titulo=titulo, autor=autor, isbn=isbn)
        storage.livros[livro_id] = livro
        return jsonify(livro.to_dict()), 201

    @app.route("/livros", methods=["GET"])
    def listar_livros():
        apenas_disponiveis = parse_bool_query_param("disponivel")
        livros = [
            livro.to_dict()
            for livro in storage.livros.values()
            if not apenas_disponiveis or livro.disponivel
        ]
        return jsonify(livros), 200

    @app.route("/livros/<int:livro_id>", methods=["GET"])
    def buscar_livro(livro_id):
        livro = obter_livro_ou_404(livro_id)
        return jsonify(livro.to_dict()), 200

    @app.route("/livros/<int:livro_id>", methods=["DELETE"])
    def excluir_livro(livro_id):
        obter_livro_ou_404(livro_id)

        emprestado = any(
            emprestimo.livro_id == livro_id and emprestimo.status == STATUS_ABERTO
            for emprestimo in storage.emprestimos.values()
        )
        if emprestado:
            raise ApiError(
                "não é possível excluir um livro que está emprestado no momento", 409
            )

        del storage.livros[livro_id]
        return "", 204

    # ------------------------------------------------------------------
    # Usuários
    # ------------------------------------------------------------------
    @app.route("/usuarios", methods=["POST"])
    def criar_usuario():
        data = get_json_body()
        nome = campo_texto(data, "nome")
        email = campo_texto(data, "email")

        ativo = data.get("ativo", True)
        if not isinstance(ativo, bool):
            raise ApiError("campo 'ativo' deve ser um valor booleano", 400)

        usuario_id = storage.next_usuario_id()
        usuario = Usuario(id=usuario_id, nome=nome, email=email, ativo=ativo)
        storage.usuarios[usuario_id] = usuario
        return jsonify(usuario.to_dict()), 201

    @app.route("/usuarios", methods=["GET"])
    def listar_usuarios():
        usuarios = [usuario.to_dict() for usuario in storage.usuarios.values()]
        return jsonify(usuarios), 200

    @app.route("/usuarios/<int:usuario_id>", methods=["GET"])
    def buscar_usuario(usuario_id):
        usuario = obter_usuario_ou_404(usuario_id)
        return jsonify(usuario.to_dict()), 200

    @app.route("/usuarios/<int:usuario_id>/emprestimos", methods=["GET"])
    def listar_emprestimos_usuario(usuario_id):
        obter_usuario_ou_404(usuario_id)
        apenas_abertos = parse_bool_query_param("abertos")

        emprestimos = [
            emprestimo.to_dict()
            for emprestimo in storage.emprestimos.values()
            if emprestimo.usuario_id == usuario_id
            and (not apenas_abertos or emprestimo.status == STATUS_ABERTO)
        ]
        return jsonify(emprestimos), 200

    @app.route("/usuarios/<int:usuario_id>/pagamento-multa", methods=["POST"])
    def pagar_multa(usuario_id):
        usuario = obter_usuario_ou_404(usuario_id)
        usuario.multa_pendente = 0.0
        return jsonify(usuario.to_dict()), 200

    # ------------------------------------------------------------------
    # Empréstimos
    # ------------------------------------------------------------------
    @app.route("/emprestimos", methods=["POST"])
    def criar_emprestimo():
        data = get_json_body()

        if "usuario_id" not in data or data.get("usuario_id") is None:
            raise ApiError("campo 'usuario_id' é obrigatório", 400)
        if "livro_id" not in data or data.get("livro_id") is None:
            raise ApiError("campo 'livro_id' é obrigatório", 400)

        usuario_id = parse_inteiro(data.get("usuario_id"), "usuario_id")
        livro_id = parse_inteiro(data.get("livro_id"), "livro_id")

        usuario = obter_usuario_ou_404(usuario_id)
        livro = obter_livro_ou_404(livro_id)

        if not usuario.ativo:
            raise ApiError("usuário inativo não pode pegar livro emprestado", 409)

        if usuario.multa_pendente > 0:
            raise ApiError(
                "usuário possui multa pendente e está impedido de pegar "
                "livros emprestados até quitá-la",
                409,
            )

        emprestimos_abertos = sum(
            1
            for emprestimo in storage.emprestimos.values()
            if emprestimo.usuario_id == usuario_id and emprestimo.status == STATUS_ABERTO
        )
        if emprestimos_abertos >= LIMITE_EMPRESTIMOS_POR_USUARIO:
            raise ApiError(
                f"usuário já atingiu o limite de {LIMITE_EMPRESTIMOS_POR_USUARIO} "
                "livros emprestados simultaneamente",
                409,
            )

        if not livro.disponivel:
            raise ApiError("livro indisponível para empréstimo", 409)

        # Permite informar explicitamente a data do empréstimo (útil, por
        # exemplo, para simular empréstimos antigos e testar o cálculo de
        # multa por atraso). Quando ausente, usa a data atual.
        if data.get("data_emprestimo"):
            data_emprestimo = parse_data_iso(data.get("data_emprestimo"), "data_emprestimo")
        else:
            data_emprestimo = date.today()

        data_prevista_devolucao = data_emprestimo + timedelta(days=PRAZO_DEVOLUCAO_DIAS)

        emprestimo_id = storage.next_emprestimo_id()
        emprestimo = Emprestimo(
            id=emprestimo_id,
            livro_id=livro_id,
            usuario_id=usuario_id,
            data_emprestimo=data_emprestimo,
            data_prevista_devolucao=data_prevista_devolucao,
        )
        storage.emprestimos[emprestimo_id] = emprestimo
        livro.disponivel = False

        return jsonify(emprestimo.to_dict()), 201

    @app.route("/emprestimos", methods=["GET"])
    def listar_emprestimos():
        apenas_abertos = parse_bool_query_param("abertos")
        emprestimos = [
            emprestimo.to_dict()
            for emprestimo in storage.emprestimos.values()
            if not apenas_abertos or emprestimo.status == STATUS_ABERTO
        ]
        return jsonify(emprestimos), 200

    @app.route("/emprestimos/<int:emprestimo_id>", methods=["GET"])
    def buscar_emprestimo(emprestimo_id):
        emprestimo = obter_emprestimo_ou_404(emprestimo_id)
        return jsonify(emprestimo.to_dict()), 200

    @app.route("/emprestimos/<int:emprestimo_id>/devolucao", methods=["POST"])
    def devolver_emprestimo(emprestimo_id):
        emprestimo = obter_emprestimo_ou_404(emprestimo_id)

        if emprestimo.status == STATUS_DEVOLVIDO:
            raise ApiError("empréstimo já foi devolvido anteriormente", 409)

        livro = obter_livro_ou_404(emprestimo.livro_id)
        usuario = obter_usuario_ou_404(emprestimo.usuario_id)

        data = request.get_json(silent=True) or {}
        if data.get("data_devolucao"):
            data_devolucao = parse_data_iso(data.get("data_devolucao"), "data_devolucao")
        else:
            data_devolucao = date.today()

        dias_atraso = max(0, (data_devolucao - emprestimo.data_prevista_devolucao).days)
        multa = round(dias_atraso * VALOR_MULTA_POR_DIA, 2)

        emprestimo.data_devolucao = data_devolucao
        emprestimo.status = STATUS_DEVOLVIDO
        emprestimo.multa = multa

        livro.disponivel = True
        usuario.multa_pendente = round(usuario.multa_pendente + multa, 2)

        return jsonify(emprestimo.to_dict()), 200

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
