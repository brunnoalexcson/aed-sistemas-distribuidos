"""RF-04 — Registrar entrada de estoque. Critérios CA-04.1 a CA-04.5."""
import pytest
from conftest import corpo_erro, criar_produto, movimentar


@pytest.mark.ca("CA-04.1")
def test_ca_04_1_entrada_retorna_201_com_saldo_apos(client):
    produto = criar_produto(client)
    r = client.post("/movimentacoes", json={
        "produto_id": produto["id"], "tipo": "entrada", "quantidade": 50,
    })
    assert r.status_code == 201
    assert r.json()["saldo_apos"] == 50


@pytest.mark.ca("CA-04.2")
def test_ca_04_2_entrada_atualiza_quantidade_do_produto(client):
    produto = criar_produto(client)
    movimentar(client, produto["id"], "entrada", 50)
    r = client.get(f"/produtos/{produto['id']}")
    assert r.status_code == 200
    assert r.json()["quantidade"] == 50


@pytest.mark.ca("CA-04.3")
def test_ca_04_3_produto_inexistente_retorna_404(client):
    r = client.post("/movimentacoes", json={
        "produto_id": 99999999, "tipo": "entrada", "quantidade": 10,
    })
    assert r.status_code == 404
    assert corpo_erro(r) == {"erro": "Produto não encontrado"}


@pytest.mark.ca("CA-04.4")
def test_ca_04_4_quantidade_zero_retorna_422(client):
    produto = criar_produto(client)
    r = client.post("/movimentacoes", json={
        "produto_id": produto["id"], "tipo": "entrada", "quantidade": 0,
    })
    assert r.status_code == 422
    assert corpo_erro(r) == {"erro": "Dados inválidos"}


@pytest.mark.ca("CA-04.5")
def test_ca_04_5_tipo_invalido_retorna_422(client):
    produto = criar_produto(client)
    r = client.post("/movimentacoes", json={
        "produto_id": produto["id"], "tipo": "transferencia", "quantidade": 10,
    })
    assert r.status_code == 422
    assert corpo_erro(r) == {"erro": "Dados inválidos"}
