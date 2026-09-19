"""
Requisitos não funcionais verificáveis automaticamente (Seção 9).

Não entram na conformidade funcional; são reportados como métrica separada.
"""
import time

import pytest
from conftest import criar_produto, sku_unico


@pytest.mark.ca("RNF-04")
def test_rnf_04_formato_global_de_erro(client):
    produto = criar_produto(client)
    respostas = [
        client.get("/produtos/99999999"),
        client.get("/produtos/99999999/movimentacoes"),
        client.post("/movimentacoes", json={
            "produto_id": produto["id"], "tipo": "entrada", "quantidade": 0}),
        client.post("/produtos", json={"nome": "X", "sku": "AB", "estoque_minimo": 1}),
    ]
    for r in respostas:
        assert r.status_code >= 400, f"esperada resposta de erro, veio {r.status_code}"
        corpo = r.json()
        assert isinstance(corpo, dict), f"corpo de erro não é objeto JSON: {corpo!r}"
        assert list(corpo.keys()) == ["erro"], f"chaves inesperadas no erro: {list(corpo.keys())}"
        assert isinstance(corpo["erro"], str)


@pytest.mark.ca("RNF-05")
def test_rnf_05_listagem_responde_em_ate_500ms_com_200_produtos(client):
    for _ in range(200):
        client.post("/produtos", json={
            "nome": "Produto de carga", "sku": sku_unico(), "estoque_minimo": 1,
        })
    inicio = time.perf_counter()
    r = client.get("/produtos")
    decorrido_ms = (time.perf_counter() - inicio) * 1000
    assert r.status_code == 200
    assert decorrido_ms <= 500, f"listagem levou {decorrido_ms:.1f} ms"
