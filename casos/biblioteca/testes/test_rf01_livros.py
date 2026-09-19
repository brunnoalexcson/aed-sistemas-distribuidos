"""RF-01 — Cadastrar livro. Critérios CA-01.1 a CA-01.4."""
import pytest
from conftest import corpo_erro, criar_livro, isbn_unico


@pytest.mark.ca("CA-01.1")
def test_ca_01_1_cadastro_valido_retorna_201_e_status_disponivel(client):
    isbn = isbn_unico()
    r = client.post("/livros", json={
        "titulo": "Dom Casmurro", "autor": "Machado de Assis", "isbn": isbn,
    })
    assert r.status_code == 201
    corpo = r.json()
    assert isinstance(corpo["id"], int)
    assert corpo["titulo"] == "Dom Casmurro"
    assert corpo["autor"] == "Machado de Assis"
    assert corpo["status"] == "disponivel"


@pytest.mark.ca("CA-01.2")
def test_ca_01_2_isbn_com_10_caracteres_retorna_422(client):
    r = client.post("/livros", json={
        "titulo": "Dom Casmurro", "autor": "Machado de Assis", "isbn": "1234567890",
    })
    assert r.status_code == 422
    assert corpo_erro(r) == {"erro": "ISBN inválido"}


@pytest.mark.ca("CA-01.3")
def test_ca_01_3_isbn_duplicado_retorna_409(client):
    livro = criar_livro(client)
    r = client.post("/livros", json={
        "titulo": "Outro título", "autor": "Outro autor", "isbn": livro["isbn"],
    })
    assert r.status_code == 409
    assert corpo_erro(r) == {"erro": "ISBN já cadastrado"}


@pytest.mark.ca("CA-01.4")
def test_ca_01_4_titulo_vazio_retorna_422(client):
    r = client.post("/livros", json={
        "titulo": "", "autor": "Machado de Assis", "isbn": isbn_unico(),
    })
    assert r.status_code == 422
    assert corpo_erro(r) == {"erro": "Dados inválidos"}
