"""RF-02 — Listar livros. Critérios CA-02.1 a CA-02.3."""
import pytest
from conftest import corpo_erro, criar_livro


@pytest.mark.ca("CA-02.1")
def test_ca_02_1_listagem_retorna_200_e_contem_livro_cadastrado(client):
    livro = criar_livro(client)
    r = client.get("/livros")
    assert r.status_code == 200
    corpo = r.json()
    assert isinstance(corpo, list)
    assert any(item["id"] == livro["id"] for item in corpo)


@pytest.mark.ca("CA-02.2")
def test_ca_02_2_filtro_por_status_disponivel(client):
    criar_livro(client)
    r = client.get("/livros", params={"status": "disponivel"})
    assert r.status_code == 200
    corpo = r.json()
    assert isinstance(corpo, list)
    assert all(item["status"] == "disponivel" for item in corpo)


@pytest.mark.ca("CA-02.3")
def test_ca_02_3_filtro_com_valor_invalido_retorna_422(client):
    r = client.get("/livros", params={"status": "inexistente"})
    assert r.status_code == 422
    assert corpo_erro(r) == {"erro": "Dados inválidos"}
