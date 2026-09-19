"""RF-07 — Consultar produtos em alerta de estoque mínimo. Critérios CA-07.1 a CA-07.3."""
import pytest
from conftest import criar_produto, produto_com_saldo


@pytest.mark.ca("CA-07.1")
def test_ca_07_1_produto_abaixo_do_minimo_aparece_no_alerta(client):
    produto = criar_produto(client, estoque_minimo=10)  # quantidade inicial 0
    r = client.get("/alertas")
    assert r.status_code == 200
    corpo = r.json()
    assert isinstance(corpo, list)
    assert any(item["id"] == produto["id"] for item in corpo)


@pytest.mark.ca("CA-07.2")
def test_ca_07_2_produto_acima_do_minimo_nao_aparece_no_alerta(client):
    produto = produto_com_saldo(client, 20, estoque_minimo=10)
    r = client.get("/alertas")
    assert r.status_code == 200
    assert not any(item["id"] == produto["id"] for item in r.json())


@pytest.mark.ca("CA-07.3")
def test_ca_07_3_produto_igual_ao_minimo_nao_aparece_no_alerta(client):
    produto = produto_com_saldo(client, 10, estoque_minimo=10)
    r = client.get("/alertas")
    assert r.status_code == 200
    assert not any(item["id"] == produto["id"] for item in r.json())
