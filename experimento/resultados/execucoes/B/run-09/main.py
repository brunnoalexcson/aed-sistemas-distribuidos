"""Ponto de entrada da API REST da biblioteca do bairro.

Execução:
    python main.py

A aplicação sobe em http://127.0.0.1:5000 por padrão, mantendo todos
os dados em memória (livros, usuários e empréstimos são perdidos ao
encerrar o processo).
"""

from app import criar_app

app = criar_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
