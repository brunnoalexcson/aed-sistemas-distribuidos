"""RF-03 — Consultar produto por identificador. Critérios CA-03.1 e CA-03.2."""
import pytest
from conftest import corpo_erro, criar_produto


@pytest.mark.ca("CA-03.1")
def test_ca_03_1_consulta_por_id_retorna_200_com_o_produto(client):
    produto = criar_produto(client)
    r = client.get(f"/produtos/{produto['id']}")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["id"] == produto["id"]
    assert corpo["sku"] == produto["sku"]


@pytest.mark.ca("CA-03.2")
def test_ca_03_2_consulta_de_id_inexistente_retorna_404(client):
    r = client.get("/produtos/99999999")
    assert r.status_code == 404
    assert corpo_erro(r) == {"erro": "Produto não encontrado"}
