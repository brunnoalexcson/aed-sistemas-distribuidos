# Sistema de biblioteca — API REST

API REST em Python (Flask) para gerenciar o acervo de livros, o cadastro de
usuários e os empréstimos de uma biblioteca. Não há autenticação, não há
interface gráfica e todos os dados são armazenados em memória (não há banco
de dados); os dados são perdidos ao reiniciar o processo.

## Como executar

```bash
pip install -r requirements.txt
python app.py
```

O servidor sobe em `http://localhost:5000`.

## Regras de negócio

- Prazo de devolução de um empréstimo: 14 dias a partir da data do empréstimo.
- Um usuário pode ter no máximo 3 empréstimos em aberto simultaneamente.
- Usuário inativo não pode pegar livro emprestado.
- Usuário com multa pendente não pode pegar livro emprestado até quitá-la.
- Um livro emprestado não pode ser excluído do acervo.
- Multa por atraso na devolução: R$ 1,50 por dia de atraso, somada à
  pendência do usuário.

## Endpoints

### Livros

- `POST /livros` — cadastra um livro. Corpo: `{"titulo", "autor", "isbn"}`.
- `GET /livros` — lista todos os livros.
- `GET /livros/<id>` — busca um livro pelo id.
- `DELETE /livros/<id>` — exclui um livro (erro 409 se estiver emprestado).

### Usuários

- `POST /usuarios` — cadastra um usuário. Corpo: `{"nome", "email"}`.
- `GET /usuarios` — lista todos os usuários.
- `GET /usuarios/<id>` — busca um usuário pelo id.
- `GET /usuarios/<id>/emprestimos` — lista os empréstimos de um usuário.
  Aceita o parâmetro de consulta opcional `?status=aberto` ou
  `?status=devolvido` para filtrar.
- `POST /usuarios/<id>/pagamentos-multa` — registra o pagamento da multa
  pendente do usuário, zerando a pendência.

### Empréstimos

- `POST /emprestimos` — registra um novo empréstimo. Corpo:
  `{"livro_id", "usuario_id"}`.
- `GET /emprestimos` — lista todos os empréstimos.
- `GET /emprestimos/<id>` — busca um empréstimo pelo id.
- `POST /emprestimos/<id>/devolucao` — registra a devolução de um
  empréstimo, calculando a multa em caso de atraso.

## Códigos de erro

Erros são retornados como JSON no formato `{"erro": "mensagem"}`, com os
seguintes códigos HTTP:

- `400` — dados de entrada ausentes ou inválidos.
- `404` — recurso (livro, usuário ou empréstimo) não encontrado.
- `409` — violação de regra de negócio (ex.: livro indisponível, usuário
  inativo, multa pendente, limite de empréstimos atingido, exclusão de
  livro emprestado, devolução de empréstimo já devolvido).
