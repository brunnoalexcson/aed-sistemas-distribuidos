"""Camada de armazenamento em memória e regras de negócio do sistema de biblioteca.

Não há banco de dados: todo o estado (livros, usuários e empréstimos) vive em
estruturas Python mantidas em memória enquanto o processo da aplicação estiver
em execução.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Lock
from typing import Dict, List, Optional

# Regras de negócio do sistema
PRAZO_EMPRESTIMO_DIAS = 14
VALOR_MULTA_POR_DIA = 1.50
MAX_EMPRESTIMOS_ATIVOS_POR_USUARIO = 3


class ApiError(Exception):
    """Erro genérico da API, convertido em resposta HTTP com código apropriado."""

    status_code = 400

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class ValidationError(ApiError):
    """Dados de entrada inválidos ou ausentes."""

    status_code = 400


class NotFoundError(ApiError):
    """Recurso solicitado não existe."""

    status_code = 404


class ConflictError(ApiError):
    """Ação viola alguma regra de negócio do sistema."""

    status_code = 409


def _texto_obrigatorio(valor, nome_campo: str) -> str:
    if not isinstance(valor, str) or not valor.strip():
        raise ValidationError(
            f"O campo '{nome_campo}' é obrigatório e deve ser um texto não vazio."
        )
    return valor.strip()


@dataclass
class Livro:
    id: int
    titulo: str
    autor: str
    isbn: str
    disponivel: bool = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "titulo": self.titulo,
            "autor": self.autor,
            "isbn": self.isbn,
            "disponivel": self.disponivel,
        }


@dataclass
class Usuario:
    id: int
    nome: str
    email: str
    ativo: bool = True
    multa_pendente: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "ativo": self.ativo,
            "multa_pendente": round(self.multa_pendente, 2),
        }


@dataclass
class Emprestimo:
    id: int
    usuario_id: int
    livro_id: int
    data_emprestimo: datetime
    data_prevista_devolucao: datetime
    data_devolucao: Optional[datetime] = None
    multa: float = 0.0
    devolvido: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "livro_id": self.livro_id,
            "data_emprestimo": self.data_emprestimo.isoformat(),
            "data_prevista_devolucao": self.data_prevista_devolucao.isoformat(),
            "data_devolucao": (
                self.data_devolucao.isoformat() if self.data_devolucao else None
            ),
            "multa": round(self.multa, 2),
            "devolvido": self.devolvido,
        }


class Biblioteca:
    """Concentra o estado em memória e as regras de negócio do sistema."""

    def __init__(self):
        self._lock = Lock()
        self._livros: Dict[int, Livro] = {}
        self._usuarios: Dict[int, Usuario] = {}
        self._emprestimos: Dict[int, Emprestimo] = {}
        self._proximo_id_livro = 1
        self._proximo_id_usuario = 1
        self._proximo_id_emprestimo = 1

    # ---------------------------------------------------------------
    # Livros
    # ---------------------------------------------------------------

    def criar_livro(self, titulo, autor, isbn) -> Livro:
        titulo = _texto_obrigatorio(titulo, "titulo")
        autor = _texto_obrigatorio(autor, "autor")
        isbn = _texto_obrigatorio(isbn, "isbn")
        with self._lock:
            livro = Livro(
                id=self._proximo_id_livro, titulo=titulo, autor=autor, isbn=isbn
            )
            self._livros[livro.id] = livro
            self._proximo_id_livro += 1
            return livro

    def listar_livros(self) -> List[Livro]:
        return list(self._livros.values())

    def buscar_livro(self, livro_id: int) -> Livro:
        livro = self._livros.get(livro_id)
        if livro is None:
            raise NotFoundError(f"Livro {livro_id} não encontrado.")
        return livro

    def excluir_livro(self, livro_id: int) -> None:
        livro = self.buscar_livro(livro_id)
        if not livro.disponivel:
            raise ConflictError(
                "Não é possível excluir um livro que está emprestado no momento."
            )
        with self._lock:
            del self._livros[livro_id]

    # ---------------------------------------------------------------
    # Usuários
    # ---------------------------------------------------------------

    def criar_usuario(self, nome, email) -> Usuario:
        nome = _texto_obrigatorio(nome, "nome")
        email = _texto_obrigatorio(email, "email")
        with self._lock:
            usuario = Usuario(
                id=self._proximo_id_usuario, nome=nome, email=email
            )
            self._usuarios[usuario.id] = usuario
            self._proximo_id_usuario += 1
            return usuario

    def listar_usuarios(self) -> List[Usuario]:
        return list(self._usuarios.values())

    def buscar_usuario(self, usuario_id: int) -> Usuario:
        usuario = self._usuarios.get(usuario_id)
        if usuario is None:
            raise NotFoundError(f"Usuário {usuario_id} não encontrado.")
        return usuario

    def atualizar_usuario(
        self, usuario_id: int, nome=None, email=None, ativo=None
    ) -> Usuario:
        usuario = self.buscar_usuario(usuario_id)
        if nome is not None:
            usuario.nome = _texto_obrigatorio(nome, "nome")
        if email is not None:
            usuario.email = _texto_obrigatorio(email, "email")
        if ativo is not None:
            if not isinstance(ativo, bool):
                raise ValidationError("O campo 'ativo' deve ser um valor booleano.")
            usuario.ativo = ativo
        return usuario

    # ---------------------------------------------------------------
    # Empréstimos
    # ---------------------------------------------------------------

    def criar_emprestimo(self, usuario_id: int, livro_id: int) -> Emprestimo:
        usuario = self.buscar_usuario(usuario_id)
        livro = self.buscar_livro(livro_id)

        if not usuario.ativo:
            raise ConflictError(
                "Usuário inativo não pode pegar livro emprestado."
            )

        if usuario.multa_pendente > 0:
            raise ConflictError(
                "Usuário possui multa pendente e não pode pegar livro emprestado "
                "até quitá-la."
            )

        if not livro.disponivel:
            raise ConflictError("Livro não está disponível para empréstimo.")

        emprestimos_abertos = [
            e
            for e in self._emprestimos.values()
            if e.usuario_id == usuario_id and not e.devolvido
        ]
        if len(emprestimos_abertos) >= MAX_EMPRESTIMOS_ATIVOS_POR_USUARIO:
            raise ConflictError(
                "Usuário já atingiu o limite de "
                f"{MAX_EMPRESTIMOS_ATIVOS_POR_USUARIO} livros emprestados "
                "simultaneamente."
            )

        with self._lock:
            agora = datetime.now()
            emprestimo = Emprestimo(
                id=self._proximo_id_emprestimo,
                usuario_id=usuario_id,
                livro_id=livro_id,
                data_emprestimo=agora,
                data_prevista_devolucao=agora + timedelta(days=PRAZO_EMPRESTIMO_DIAS),
            )
            self._emprestimos[emprestimo.id] = emprestimo
            self._proximo_id_emprestimo += 1
            livro.disponivel = False
            return emprestimo

    def listar_emprestimos(self) -> List[Emprestimo]:
        return list(self._emprestimos.values())

    def buscar_emprestimo(self, emprestimo_id: int) -> Emprestimo:
        emprestimo = self._emprestimos.get(emprestimo_id)
        if emprestimo is None:
            raise NotFoundError(f"Empréstimo {emprestimo_id} não encontrado.")
        return emprestimo

    def registrar_devolucao(self, emprestimo_id: int) -> Emprestimo:
        emprestimo = self.buscar_emprestimo(emprestimo_id)
        if emprestimo.devolvido:
            raise ConflictError("Este empréstimo já foi devolvido anteriormente.")

        with self._lock:
            agora = datetime.now()
            emprestimo.data_devolucao = agora
            emprestimo.devolvido = True

            livro = self._livros.get(emprestimo.livro_id)
            if livro is not None:
                livro.disponivel = True

            if agora > emprestimo.data_prevista_devolucao:
                atraso = agora - emprestimo.data_prevista_devolucao
                dias_atraso = atraso.days
                if atraso.seconds > 0 or atraso.microseconds > 0:
                    dias_atraso += 1
                dias_atraso = max(dias_atraso, 1)

                multa = round(dias_atraso * VALOR_MULTA_POR_DIA, 2)
                emprestimo.multa = multa

                usuario = self._usuarios.get(emprestimo.usuario_id)
                if usuario is not None:
                    usuario.multa_pendente = round(
                        usuario.multa_pendente + multa, 2
                    )

            return emprestimo

    def listar_emprestimos_usuario(
        self, usuario_id: int, apenas_abertos: bool = False
    ) -> List[Emprestimo]:
        self.buscar_usuario(usuario_id)  # garante existência (gera 404 se não houver)
        emprestimos = [
            e for e in self._emprestimos.values() if e.usuario_id == usuario_id
        ]
        if apenas_abertos:
            emprestimos = [e for e in emprestimos if not e.devolvido]
        return emprestimos

    def pagar_multa(self, usuario_id: int):
        usuario = self.buscar_usuario(usuario_id)
        valor_pago = usuario.multa_pendente
        usuario.multa_pendente = 0.0
        return usuario, valor_pago
