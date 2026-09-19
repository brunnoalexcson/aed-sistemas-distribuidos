"""RF-04 — Excluir livro. Critérios CA-04.1 a CA-04.3."""
import pytest
from conftest import corpo_erro, criar_emprestimo, criar_livro, criar_usuario


@pytest.mark.ca("CA-04.1")
def test_ca_04_1_exclusao_de_livro_disponivel_retorna_204(client):
    livro = criar_livro(client)
    r = client.delete(f"/livros/{livro['id']}")
    assert r.status_code == 204
    assert client.get(f"/livros/{livro['id']}").status_code == 404


@pytest.mark.ca("CA-04.2")
def test_ca_04_2_exclusao_de_id_inexistente_retorna_404(client):
    r = client.delete("/livros/99999999")
    assert r.status_code == 404
    assert corpo_erro(r) == {"erro": "Livro não encontrado"}


@pytest.mark.ca("CA-04.3")
def test_ca_04_3_exclusao_de_livro_com_emprestimo_ativo_retorna_409(client):
    usuario = criar_usuario(client)
    livro = criar_livro(client)
    criar_emprestimo(client, usuario["id"], livro["id"])
    r = client.delete(f"/livros/{livro['id']}")
    assert r.status_code == 409
    assert corpo_erro(r) == {"erro": "Livro possui empréstimo ativo"}
