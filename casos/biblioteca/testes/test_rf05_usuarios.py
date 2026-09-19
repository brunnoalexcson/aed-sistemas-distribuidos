"""RF-05 — Cadastrar usuário. Critérios CA-05.1 a CA-05.4."""
import pytest
from conftest import corpo_erro, criar_usuario, email_unico


@pytest.mark.ca("CA-05.1")
def test_ca_05_1_cadastro_valido_retorna_201_ativo_sem_multa(client):
    r = client.post("/usuarios", json={"nome": "Maria Silva", "email": email_unico()})
    assert r.status_code == 201
    corpo = r.json()
    assert isinstance(corpo["id"], int)
    assert corpo["status"] == "ativo"
    assert corpo["multa_pendente"] == 0


@pytest.mark.ca("CA-05.2")
def test_ca_05_2_email_sem_arroba_retorna_422(client):
    r = client.post("/usuarios", json={"nome": "Maria Silva", "email": "mariaexemplo.com"})
    assert r.status_code == 422
    assert corpo_erro(r) == {"erro": "E-mail inválido"}


@pytest.mark.ca("CA-05.3")
def test_ca_05_3_email_duplicado_retorna_409(client):
    usuario = criar_usuario(client)
    r = client.post("/usuarios", json={"nome": "Outro nome", "email": usuario["email"]})
    assert r.status_code == 409
    assert corpo_erro(r) == {"erro": "E-mail já cadastrado"}


@pytest.mark.ca("CA-05.4")
def test_ca_05_4_nome_vazio_retorna_422(client):
    r = client.post("/usuarios", json={"nome": "", "email": email_unico()})
    assert r.status_code == 422
    assert corpo_erro(r) == {"erro": "Dados inválidos"}
