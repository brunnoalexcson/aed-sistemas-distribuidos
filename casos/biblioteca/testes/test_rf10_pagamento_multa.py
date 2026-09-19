"""RF-10 — Quitar multa do usuário. Critérios CA-10.1 a CA-10.3."""
import pytest
from conftest import corpo_erro, criar_usuario, usuario_com_multa


@pytest.mark.ca("CA-10.1")
def test_ca_10_1_pagamento_zera_multa_pendente(client):
    usuario = usuario_com_multa(client)
    r = client.post(f"/usuarios/{usuario['id']}/pagamento-multa")
    assert r.status_code == 200
    assert r.json()["multa_pendente"] == 0


@pytest.mark.ca("CA-10.2")
def test_ca_10_2_pagamento_sem_multa_retorna_409(client):
    usuario = criar_usuario(client)
    r = client.post(f"/usuarios/{usuario['id']}/pagamento-multa")
    assert r.status_code == 409
    assert corpo_erro(r) == {"erro": "Usuário não possui multa pendente"}


@pytest.mark.ca("CA-10.3")
def test_ca_10_3_usuario_inexistente_retorna_404(client):
    r = client.post("/usuarios/99999999/pagamento-multa")
    assert r.status_code == 404
    assert corpo_erro(r) == {"erro": "Usuário não encontrado"}
