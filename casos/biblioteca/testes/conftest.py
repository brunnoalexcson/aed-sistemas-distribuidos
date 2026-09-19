"""
Suíte de conformidade — Sistema de Gestão de Biblioteca.

ETAPA 5 DO PROCESSO. Esta suíte foi derivada EXCLUSIVAMENTE dos critérios de
aceitação de casos/biblioteca/requisitos-biblioteca.md, ANTES de qualquer
geração de código. Nenhum teste aqui foi escrito ou ajustado olhando para o
código produzido pelas LLMs.

CONVENÇÃO DE NOMES (da qual a medição depende):
    test_ca_07_2_<descricao>  ->  critério CA-07.2
    test_rnf_04_<descricao>   ->  requisito não funcional RNF-04

Cada função de teste corresponde a exatamente um critério de aceitação.

ISOLAMENTO: a aplicação sob teste mantém estado em memória e é executada uma
única vez por run. Por isso todo teste provisiona os próprios dados e NENHUM
teste faz afirmação sobre contagens globais (ex.: "a lista tem 1 item").
"""

import itertools
import os
import random

import httpx
import pytest

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000")
TIMEOUT = float(os.environ.get("TIMEOUT", "15"))

_contador = itertools.count(random.randint(1, 9_000_000))


def pytest_configure(config):
    config.addinivalue_line("markers", "ca(id): critério de aceitação coberto pelo teste")


@pytest.fixture(scope="session")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as c:
        yield c


# --------------------------------------------------------------------------
# Geradores de dados únicos — garantem independência entre testes mesmo com
# estado acumulado no processo da aplicação.
# --------------------------------------------------------------------------

def isbn_unico() -> str:
    """ISBN válido pela Seção 5.1: exatamente 13 dígitos."""
    return f"{next(_contador) % 10_000_000_000_000:013d}"


def email_unico() -> str:
    return f"usuario{next(_contador)}@exemplo.com"


# --------------------------------------------------------------------------
# Helpers de provisionamento.
#
# Usam apenas endpoints especificados no documento. Quando o provisionamento
# falha, o teste falha — é o comportamento desejado: segundo as regras de
# medição (Etapa 7), critérios dependentes de código quebrado contam como
# não atendidos.
# --------------------------------------------------------------------------

def criar_livro(client) -> dict:
    r = client.post("/livros", json={
        "titulo": "Dom Casmurro",
        "autor": "Machado de Assis",
        "isbn": isbn_unico(),
    })
    assert r.status_code == 201, f"provisionamento de livro falhou: {r.status_code} {r.text}"
    return r.json()


def criar_usuario(client, status: str | None = None) -> dict:
    corpo = {"nome": "Maria Silva", "email": email_unico()}
    if status is not None:
        corpo["status"] = status
    r = client.post("/usuarios", json=corpo)
    assert r.status_code == 201, f"provisionamento de usuário falhou: {r.status_code} {r.text}"
    return r.json()


def criar_emprestimo(client, usuario_id: int, livro_id: int, data_emprestimo: str | None = None) -> dict:
    corpo = {"usuario_id": usuario_id, "livro_id": livro_id}
    if data_emprestimo is not None:
        corpo["data_emprestimo"] = data_emprestimo
    r = client.post("/emprestimos", json=corpo)
    assert r.status_code == 201, f"provisionamento de empréstimo falhou: {r.status_code} {r.text}"
    return r.json()


def usuario_com_multa(client) -> dict:
    """
    Produz um usuário com `multa_pendente` maior que 0, usando o caminho
    especificado: empréstimo retroativo (RF-07) devolvido com atraso (RF-08).
    Atraso de 6 dias -> multa de 9.00 conforme RN-04.
    """
    usuario = criar_usuario(client)
    livro = criar_livro(client)
    emprestimo = criar_emprestimo(client, usuario["id"], livro["id"], "2026-01-01")
    r = client.post("/devolucoes", json={
        "emprestimo_id": emprestimo["id"],
        "data_devolucao": "2026-01-21",
    })
    assert r.status_code == 200, f"provisionamento de multa falhou: {r.status_code} {r.text}"
    return usuario


def corpo_erro(resposta) -> dict:
    """
    Corpo de erro no formato da Seção 10. Retorna {} quando a resposta não é
    JSON, para que a asserção do teste falhe com mensagem legível em vez de
    erro de parsing.
    """
    try:
        return resposta.json()
    except Exception:
        return {}
