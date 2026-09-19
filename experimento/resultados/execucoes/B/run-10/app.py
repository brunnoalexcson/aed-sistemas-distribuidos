"""Ponto de entrada da API REST do Sistema de Biblioteca.

Execução local:
    pip install -r requirements.txt
    python app.py

A API sobe por padrão em http://127.0.0.1:5000/.
"""

from biblioteca import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
