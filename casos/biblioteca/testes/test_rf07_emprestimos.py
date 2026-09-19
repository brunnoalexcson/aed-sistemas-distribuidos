"""RF-07 — Registrar empréstimo. Critérios CA-07.1 a CA-07.9."""
import pytest
from conftest import (corpo_erro, criar_emprestimo, criar_livro, criar_usuario,
                      usuario_com_multa)


@pytest.mark.ca("CA-07.1")
def test_ca_07_1_emprestimo_valido_retorna_201_ativo(client):
    usuario = criar_usuario(client)
    livro = criar_livro(client)
    r = client.post("/emprestimos", json={"usuario_id": usuario["id"], "livro_id": livro["id"]})
    assert r.status_code == 201
    corpo = r.json()
    assert isinstance(corpo["id"], int)
    assert corpo["status"] == "ativo"
    assert corpo["data_devolucao_real"] is None
    assert corpo["multa"] == 0


@pytest.mark.ca("CA-07.2")
def test_ca_07_2_livro_passa_a_emprestado(client):
    usuario = criar_usuario(client)
    livro = criar_livro(client)
    criar_emprestimo(client, usuario["id"], livro["id"])
    r = client.get(f"/livros/{livro['id']}")
    assert r.status_code == 200
    assert r.json()["status"] == "emprestado"


@pytest.mark.ca("CA-07.3")
def test_ca_07_3_data_devolucao_prevista_e_data_emprestimo_mais_14_dias(client):
    usuario = criar_usuario(client)
    livro = criar_livro(client)
    r = client.post("/emprestimos", json={
        "usuario_id": usuario["id"], "livro_id": livro["id"], "data_emprestimo": "2026-01-01",
    })
    assert r.status_code == 201
    assert r.json()["data_devolucao_prevista"] == "2026-01-15"


@pytest.mark.ca("CA-07.4")
def test_ca_07_4_usuario_inexistente_retorna_404(client):
    livro = criar_livro(client)
    r = client.post("/emprestimos", json={"usuario_id": 99999999, "livro_id": livro["id"]})
    assert r.status_code == 404
    assert corpo_erro(r) == {"erro": "Usuário não encontrado"}


@pytest.mark.ca("CA-07.5")
def test_ca_07_5_livro_inexistente_retorna_404(client):
    usuario = criar_usuario(client)
    r = client.post("/emprestimos", json={"usuario_id": usuario["id"], "livro_id": 99999999})
    assert r.status_code == 404
    assert corpo_erro(r) == {"erro": "Livro não encontrado"}


@pytest.mark.ca("CA-07.6")
def test_ca_07_6_livro_ja_emprestado_retorna_409(client):
    primeiro = criar_usuario(client)
    segundo = criar_usuario(client)
    livro = criar_livro(client)
    criar_emprestimo(client, primeiro["id"], livro["id"])
    r = client.post("/emprestimos", json={"usuario_id": segundo["id"], "livro_id": livro["id"]})
    assert r.status_code == 409
    assert corpo_erro(r) == {"erro": "Livro indisponível"}


@pytest.mark.ca("CA-07.7")
def test_ca_07_7_limite_de_tres_emprestimos_ativos_retorna_422(client):
    usuario = criar_usuario(client)
    for _ in range(3):
        criar_emprestimo(client, usuario["id"], criar_livro(client)["id"])
    quarto = criar_livro(client)
    r = client.post("/emprestimos", json={"usuario_id": usuario["id"], "livro_id": quarto["id"]})
    assert r.status_code == 422
    assert corpo_erro(r) == {"erro": "Limite de empréstimos atingido"}


@pytest.mark.ca("CA-07.8")
def test_ca_07_8_usuario_com_multa_pendente_retorna_422(client):
    usuario = usuario_com_multa(client)
    livro = criar_livro(client)
    r = client.post("/emprestimos", json={"usuario_id": usuario["id"], "livro_id": livro["id"]})
    assert r.status_code == 422
    assert corpo_erro(r) == {"erro": "Usuário possui multa pendente"}


@pytest.mark.ca("CA-07.9")
def test_ca_07_9_usuario_inativo_retorna_422(client):
    usuario = criar_usuario(client, status="inativo")
    livro = criar_livro(client)
    r = client.post("/emprestimos", json={"usuario_id": usuario["id"], "livro_id": livro["id"]})
    assert r.status_code == 422
    assert corpo_erro(r) == {"erro": "Usuário inativo"}
