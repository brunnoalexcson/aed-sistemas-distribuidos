"""RF-06 — Listar movimentações de um produto. Critérios CA-06.1 a CA-06.3."""
import pytest
from conftest import corpo_erro, criar_produto, movimentar, produto_com_saldo


@pytest.mark.ca("CA-06.1")
def test_ca_06_1_listagem_retorna_200_e_contem_a_movimentacao(client):
    produto = criar_produto(client)
    movimentacao = movimentar(client, produto["id"], "entrada", 50)
    r = client.get(f"/produtos/{produto['id']}/movimentacoes")
    assert r.status_code == 200
    corpo = r.json()
    assert isinstance(corpo, list)
    assert any(item["id"] == movimentacao["id"] for item in corpo)


@pytest.mark.ca("CA-06.2")
def test_ca_06_2_filtro_por_tipo_saida(client):
    produto = produto_com_saldo(client, 50)
    saida = movimentar(client, produto["id"], "saida", 10)
    r = client.get(f"/produtos/{produto['id']}/movimentacoes", params={"tipo": "saida"})
    assert r.status_code == 200
    corpo = r.json()
    assert isinstance(corpo, list)
    assert all(item["tipo"] == "saida" for item in corpo)
    assert any(item["id"] == saida["id"] for item in corpo)


@pytest.mark.ca("CA-06.3")
def test_ca_06_3_produto_inexistente_retorna_404(client):
    r = client.get("/produtos/99999999/movimentacoes")
    assert r.status_code == 404
    assert corpo_erro(r) == {"erro": "Produto não encontrado"}
