"""RF-01 — Cadastrar produto. Critérios CA-01.1 a CA-01.4."""
import pytest
from conftest import corpo_erro, criar_produto, sku_unico


@pytest.mark.ca("CA-01.1")
def test_ca_01_1_cadastro_valido_retorna_201_com_quantidade_zero(client):
    r = client.post("/produtos", json={
        "nome": "Parafuso M6", "sku": sku_unico(), "estoque_minimo": 10,
    })
    assert r.status_code == 201
    corpo = r.json()
    assert isinstance(corpo["id"], int)
    assert corpo["nome"] == "Parafuso M6"
    assert corpo["quantidade"] == 0


@pytest.mark.ca("CA-01.2")
def test_ca_01_2_sku_com_5_caracteres_retorna_422(client):
    r = client.post("/produtos", json={
        "nome": "Parafuso M6", "sku": "ABC12", "estoque_minimo": 10,
    })
    assert r.status_code == 422
    assert corpo_erro(r) == {"erro": "SKU inválido"}


@pytest.mark.ca("CA-01.3")
def test_ca_01_3_sku_duplicado_retorna_409(client):
    produto = criar_produto(client)
    r = client.post("/produtos", json={
        "nome": "Outro produto", "sku": produto["sku"], "estoque_minimo": 5,
    })
    assert r.status_code == 409
    assert corpo_erro(r) == {"erro": "SKU já cadastrado"}


@pytest.mark.ca("CA-01.4")
def test_ca_01_4_estoque_minimo_negativo_retorna_422(client):
    r = client.post("/produtos", json={
        "nome": "Parafuso M6", "sku": sku_unico(), "estoque_minimo": -1,
    })
    assert r.status_code == 422
    assert corpo_erro(r) == {"erro": "Dados inválidos"}
