"""RF-09 — Listar empréstimos de um usuário. Critérios CA-09.1 a CA-09.3."""
import pytest
from conftest import corpo_erro, criar_emprestimo, criar_livro, criar_usuario


@pytest.mark.ca("CA-09.1")
def test_ca_09_1_listagem_retorna_200_e_contem_o_emprestimo(client):
    usuario = criar_usuario(client)
    livro = criar_livro(client)
    emprestimo = criar_emprestimo(client, usuario["id"], livro["id"])
    r = client.get(f"/usuarios/{usuario['id']}/emprestimos")
    assert r.status_code == 200
    corpo = r.json()
    assert isinstance(corpo, list)
    assert any(item["id"] == emprestimo["id"] for item in corpo)


@pytest.mark.ca("CA-09.2")
def test_ca_09_2_filtro_por_status_ativo(client):
    usuario = criar_usuario(client)
    ativo = criar_emprestimo(client, usuario["id"], criar_livro(client)["id"])
    devolvido = criar_emprestimo(client, usuario["id"], criar_livro(client)["id"])
    assert client.post("/devolucoes", json={"emprestimo_id": devolvido["id"]}).status_code == 200

    r = client.get(f"/usuarios/{usuario['id']}/emprestimos", params={"status": "ativo"})
    assert r.status_code == 200
    corpo = r.json()
    assert isinstance(corpo, list)
    assert all(item["status"] == "ativo" for item in corpo)
    assert any(item["id"] == ativo["id"] for item in corpo)


@pytest.mark.ca("CA-09.3")
def test_ca_09_3_usuario_inexistente_retorna_404(client):
    r = client.get("/usuarios/99999999/emprestimos")
    assert r.status_code == 404
    assert corpo_erro(r) == {"erro": "Usuário não encontrado"}
