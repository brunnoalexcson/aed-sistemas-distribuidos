"""Exceções da aplicação, mapeadas para códigos de status HTTP."""

from typing import Optional


class ErroDeAplicacao(Exception):
    """Erro base da aplicação. Convertido em resposta JSON pelo Flask."""

    status_code = 400

    def __init__(self, mensagem: str, status_code: Optional[int] = None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        if status_code is not None:
            self.status_code = status_code

    def to_dict(self) -> dict:
        return {"erro": self.mensagem}


class RequisicaoInvalida(ErroDeAplicacao):
    """Dados de entrada ausentes ou inválidos (HTTP 400)."""

    status_code = 400


class NaoEncontrado(ErroDeAplicacao):
    """Entidade referenciada não existe (HTTP 404)."""

    status_code = 404


class ConflitoDeRegraDeNegocio(ErroDeAplicacao):
    """Ação viola uma regra de negócio do domínio (HTTP 409)."""

    status_code = 409
