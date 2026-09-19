# Sistema de Biblioteca — API REST

API REST em Python (Flask) para gerenciar o acervo de livros, o cadastro de
usuários e os empréstimos de uma biblioteca. Todos os dados são mantidos em
memória (não há banco de dados) e não há autenticação nem interface gráfica.

## Como executar

```bash
pip install -r requirements.txt
python app.py
```

A API sobe em `http://localhost:5000`.

## Regras de negócio

- Prazo de devolução: 14 dias a partir do empréstimo.
- Cada usuário pode ter no máximo 3 livros emprestados ao mesmo tempo.
- Usuário inativo não pode pegar livro emprestado.
- Usuário com multa pendente não pode pegar livro emprestado.
- Não é possível excluir um livro que está emprestado no momento.
- Multa por atraso: R$ 1,50 por dia de atraso, somada à pendência do usuário.

## Endpoints

### Livros

- `POST /books` — cadastra um livro. Body: `{"title", "author", "isbn"}`.
- `GET /books` — lista todos os livros.
- `GET /books/<id>` — busca um livro específico.
- `DELETE /books/<id>` — exclui um livro (409 se estiver emprestado).

### Usuários

- `POST /users` — cadastra um usuário. Body: `{"name", "email"}`.
- `GET /users` — lista todos os usuários.
- `GET /users/<id>` — busca um usuário específico.
- `PATCH /users/<id>` — atualiza dados do usuário, incluindo
  `{"active": true|false}` para ativar/inativar.
- `GET /users/<id>/loans` — lista os empréstimos do usuário. Aceita
  `?status=open` ou `?status=returned` para filtrar.
- `POST /users/<id>/pay_fine` — registra o pagamento da multa, zerando a
  pendência do usuário.

### Empréstimos

- `POST /loans` — registra um empréstimo. Body: `{"book_id", "user_id"}`.
- `GET /loans` — lista todos os empréstimos. Aceita `?status=open` ou
  `?status=returned`.
- `GET /loans/<id>` — busca um empréstimo específico.
- `POST /loans/<id>/return` — registra a devolução do livro e calcula a
  multa em caso de atraso.

## Códigos de erro

- `400` — dados de entrada ausentes ou inválidos.
- `404` — livro, usuário ou empréstimo não encontrado.
- `409` — violação de regra de negócio (livro indisponível, usuário
  inativo, multa pendente, limite de empréstimos atingido, exclusão de
  livro emprestado, devolução de empréstimo já devolvido).

Todas as respostas de erro têm o formato `{"error": "mensagem"}`.
