"""
Suíte de conformidade — Sistema de Controle de Estoque.

ETAPA 5 DO PROCESSO. Derivada exclusivamente dos critérios de aceitação de
casos/estoque/requisitos-estoque.md, antes de qualquer geração de código.

CONVENÇÃO DE NOMES (da qual a medição depende):
    test_ca_04_1_<descricao>  ->  critério CA-04.1
    test_rnf_04_<descricao>   ->  requisito não funcional RNF-04

ISOLAMENTO: a aplicação mantém estado em memória e roda uma vez por execução.
Todo teste provisiona os próprios dados e nenhum teste afirma contagens globais.
"""

import itertools
import os
import random
import string

import httpx
import pytest

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000")
TIMEOUT = float(os.environ.get("TIMEOUT", "15"))

_ALFABETO = string.ascii_uppercase + string.digits
_contador = itertools.count(random.randint(1, 9_000_000))


def pytest_configure(config):
    config.addinivalue_line("markers", "ca(id): critério de aceitação coberto pelo teste")


@pytest.fixture(scope="session")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as c:
        yield c


def sku_unico() -> str:
    """SKU válido pela Seção 5.1: 8 caracteres de [A-Z0-9]."""
    return "".join(random.choice(_ALFABETO) for _ in range(8))


def criar_produto(client, estoque_minimo: int = 10) -> dict:
    r = client.post("/produtos", json={
        "nome": "Parafuso M6", "sku": sku_unico(), "estoque_minimo": estoque_minimo,
    })
    assert r.status_code == 201, f"provisionamento de produto falhou: {r.status_code} {r.text}"
    return r.json()


def movimentar(client, produto_id: int, tipo: str, quantidade: int) -> dict:
    r = client.post("/movimentacoes", json={
        "produto_id": produto_id, "tipo": tipo, "quantidade": quantidade,
    })
    assert r.status_code == 201, f"provisionamento de movimentação falhou: {r.status_code} {r.text}"
    return r.json()


def produto_com_saldo(client, saldo: int, estoque_minimo: int = 10) -> dict:
    produto = criar_produto(client, estoque_minimo)
    movimentar(client, produto["id"], "entrada", saldo)
    return produto


def corpo_erro(resposta) -> dict:
    try:
        return resposta.json()
    except Exception:
        return {}
