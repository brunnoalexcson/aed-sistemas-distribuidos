"""Ponto de entrada da API REST da biblioteca do bairro.

Execução:
    python run.py

O servidor sobe em modo de desenvolvimento na porta 5000, com todos os
dados mantidos em memória (não há persistência em banco de dados).
"""

from biblioteca import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
