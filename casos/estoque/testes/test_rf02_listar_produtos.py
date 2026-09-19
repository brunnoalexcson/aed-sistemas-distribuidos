"""RF-02 — Listar produtos. Critérios CA-02.1 e CA-02.2."""
import pytest
from conftest import criar_produto


@pytest.mark.ca("CA-02.1")
def test_ca_02_1_listagem_retorna_200_e_contem_produto(client):
    produto = criar_produto(client)
    r = client.get("/produtos")
    assert r.status_code == 200
    corpo = r.json()
    assert isinstance(corpo, list)
    assert any(item["id"] == produto["id"] for item in corpo)


@pytest.mark.ca("CA-02.2")
def test_ca_02_2_itens_da_listagem_tem_as_chaves_especificadas(client):
    produto = criar_produto(client)
    r = client.get("/produtos")
    assert r.status_code == 200
    item = next(i for i in r.json() if i["id"] == produto["id"])
    assert set(item) >= {"id", "nome", "sku", "estoque_minimo", "quantidade"}
