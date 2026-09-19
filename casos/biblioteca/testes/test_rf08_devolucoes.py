"""RF-08 — Registrar devolução. Critérios CA-08.1 a CA-08.7."""
import pytest
from conftest import corpo_erro, criar_emprestimo, criar_livro, criar_usuario


@pytest.mark.ca("CA-08.1")
def test_ca_08_1_devolucao_retorna_200_e_status_devolvido(client):
    usuario = criar_usuario(client)
    livro = criar_livro(client)
    emprestimo = criar_emprestimo(client, usuario["id"], livro["id"])
    r = client.post("/devolucoes", json={"emprestimo_id": emprestimo["id"]})
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["status"] == "devolvido"
    assert corpo["data_devolucao_real"] is not None


@pytest.mark.ca("CA-08.2")
def test_ca_08_2_livro_volta_a_disponivel(client):
    usuario = criar_usuario(client)
    livro = criar_livro(client)
    emprestimo = criar_emprestimo(client, usuario["id"], livro["id"])
    assert client.post("/devolucoes", json={"emprestimo_id": emprestimo["id"]}).status_code == 200
    r = client.get(f"/livros/{livro['id']}")
    assert r.status_code == 200
    assert r.json()["status"] == "disponivel"


@pytest.mark.ca("CA-08.3")
def test_ca_08_3_multa_de_seis_dias_de_atraso_e_9_reais(client):
    usuario = criar_usuario(client)
    livro = criar_livro(client)
    emprestimo = criar_emprestimo(client, usuario["id"], livro["id"], "2026-01-01")
    r = client.post("/devolucoes", json={
        "emprestimo_id": emprestimo["id"], "data_devolucao": "2026-01-21",
    })
    assert r.status_code == 200
    assert r.json()["multa"] == 9.0


@pytest.mark.ca("CA-08.4")
def test_ca_08_4_multa_e_somada_ao_multa_pendente_do_usuario(client):
    usuario = criar_usuario(client)
    livro = criar_livro(client)
    emprestimo = criar_emprestimo(client, usuario["id"], livro["id"], "2026-01-01")
    assert client.post("/devolucoes", json={
        "emprestimo_id": emprestimo["id"], "data_devolucao": "2026-01-21",
    }).status_code == 200
    r = client.get(f"/usuarios/{usuario['id']}")
    assert r.status_code == 200
    assert r.json()["multa_pendente"] == 9.0


@pytest.mark.ca("CA-08.5")
def test_ca_08_5_devolucao_antes_do_prazo_nao_gera_multa(client):
    usuario = criar_usuario(client)
    livro = criar_livro(client)
    emprestimo = criar_emprestimo(client, usuario["id"], livro["id"], "2026-01-01")
    r = client.post("/devolucoes", json={
        "emprestimo_id": emprestimo["id"], "data_devolucao": "2026-01-10",
    })
    assert r.status_code == 200
    assert r.json()["multa"] == 0


@pytest.mark.ca("CA-08.6")
def test_ca_08_6_emprestimo_inexistente_retorna_404(client):
    r = client.post("/devolucoes", json={"emprestimo_id": 99999999})
    assert r.status_code == 404
    assert corpo_erro(r) == {"erro": "Empréstimo não encontrado"}


@pytest.mark.ca("CA-08.7")
def test_ca_08_7_devolucao_de_emprestimo_ja_devolvido_retorna_409(client):
    usuario = criar_usuario(client)
    livro = criar_livro(client)
    emprestimo = criar_emprestimo(client, usuario["id"], livro["id"])
    assert client.post("/devolucoes", json={"emprestimo_id": emprestimo["id"]}).status_code == 200
    r = client.post("/devolucoes", json={"emprestimo_id": emprestimo["id"]})
    assert r.status_code == 409
    assert corpo_erro(r) == {"erro": "Empréstimo já devolvido"}
