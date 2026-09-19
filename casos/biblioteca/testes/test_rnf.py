"""
Requisitos não funcionais verificáveis automaticamente (Seção 9).

Estes testes NÃO entram na conformidade funcional (os 40 critérios de
aceitação). São reportados como métrica separada pelo medidor.
"""
import time

import pytest
from conftest import criar_livro, isbn_unico


@pytest.mark.ca("RNF-04")
def test_rnf_04_formato_global_de_erro(client):
    """Toda resposta de erro tem `erro` como única chave (Seção 10)."""
    respostas = [
        client.get("/livros/99999999"),
        client.get("/usuarios/99999999"),
        client.post("/devolucoes", json={"emprestimo_id": 99999999}),
        client.post("/livros", json={"titulo": "X", "autor": "Y", "isbn": "123"}),
    ]
    for r in respostas:
        assert r.status_code >= 400, f"esperada resposta de erro, veio {r.status_code}"
        corpo = r.json()
        assert isinstance(corpo, dict), f"corpo de erro não é objeto JSON: {corpo!r}"
        assert list(corpo.keys()) == ["erro"], f"chaves inesperadas no erro: {list(corpo.keys())}"
        assert isinstance(corpo["erro"], str)


@pytest.mark.ca("RNF-05")
def test_rnf_05_listagem_responde_em_ate_500ms_com_200_livros(client):
    for _ in range(200):
        client.post("/livros", json={
            "titulo": "Livro de carga", "autor": "Autor", "isbn": isbn_unico(),
        })
    inicio = time.perf_counter()
    r = client.get("/livros")
    decorrido_ms = (time.perf_counter() - inicio) * 1000
    assert r.status_code == 200
    assert decorrido_ms <= 500, f"listagem levou {decorrido_ms:.1f} ms"
