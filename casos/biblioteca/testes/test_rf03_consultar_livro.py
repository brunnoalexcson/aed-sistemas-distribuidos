"""RF-03 — Consultar livro por identificador. Critérios CA-03.1 e CA-03.2."""
import pytest
from conftest import corpo_erro, criar_livro


@pytest.mark.ca("CA-03.1")
def test_ca_03_1_consulta_por_id_retorna_200_com_o_livro(client):
    livro = criar_livro(client)
    r = client.get(f"/livros/{livro['id']}")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["id"] == livro["id"]
    assert corpo["titulo"] == livro["titulo"]


@pytest.mark.ca("CA-03.2")
def test_ca_03_2_consulta_de_id_inexistente_retorna_404(client):
    r = client.get("/livros/99999999")
    assert r.status_code == 404
    assert corpo_erro(r) == {"erro": "Livro não encontrado"}
