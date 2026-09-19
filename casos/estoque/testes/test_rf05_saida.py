"""RF-05 — Registrar saída de estoque. Critérios CA-05.1 a CA-05.4."""
import pytest
from conftest import corpo_erro, movimentar, produto_com_saldo


@pytest.mark.ca("CA-05.1")
def test_ca_05_1_saida_retorna_201_com_saldo_apos(client):
    produto = produto_com_saldo(client, 50)
    r = client.post("/movimentacoes", json={
        "produto_id": produto["id"], "tipo": "saida", "quantidade": 20,
    })
    assert r.status_code == 201
    assert r.json()["saldo_apos"] == 30


@pytest.mark.ca("CA-05.2")
def test_ca_05_2_saida_atualiza_quantidade_do_produto(client):
    produto = produto_com_saldo(client, 50)
    movimentar(client, produto["id"], "saida", 20)
    r = client.get(f"/produtos/{produto['id']}")
    assert r.status_code == 200
    assert r.json()["quantidade"] == 30


@pytest.mark.ca("CA-05.3")
def test_ca_05_3_saida_acima_do_saldo_retorna_409(client):
    produto = produto_com_saldo(client, 50)
    r = client.post("/movimentacoes", json={
        "produto_id": produto["id"], "tipo": "saida", "quantidade": 51,
    })
    assert r.status_code == 409
    assert corpo_erro(r) == {"erro": "Quantidade insuficiente em estoque"}


@pytest.mark.ca("CA-05.4")
def test_ca_05_4_saida_igual_ao_saldo_zera_o_estoque(client):
    produto = produto_com_saldo(client, 50)
    r = client.post("/movimentacoes", json={
        "produto_id": produto["id"], "tipo": "saida", "quantidade": 50,
    })
    assert r.status_code == 201
    assert r.json()["saldo_apos"] == 0
