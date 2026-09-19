"""RF-06 — Consultar usuário por identificador. Critérios CA-06.1 e CA-06.2."""
import pytest
from conftest import corpo_erro, criar_usuario


@pytest.mark.ca("CA-06.1")
def test_ca_06_1_consulta_por_id_retorna_200_com_o_usuario(client):
    usuario = criar_usuario(client)
    r = client.get(f"/usuarios/{usuario['id']}")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["id"] == usuario["id"]
    assert corpo["email"] == usuario["email"]


@pytest.mark.ca("CA-06.2")
def test_ca_06_2_consulta_de_id_inexistente_retorna_404(client):
    r = client.get("/usuarios/99999999")
    assert r.status_code == 404
    assert corpo_erro(r) == {"erro": "Usuário não encontrado"}
