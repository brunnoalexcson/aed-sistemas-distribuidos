# API da Biblioteca

API REST em Python (Flask) para gerenciar o acervo de livros, o cadastro de
usuários e os empréstimos de uma biblioteca de bairro. Todos os dados são
mantidos em memória (não há banco de dados) e a API não possui autenticação
nem interface gráfica.

## Como executar

```bash
pip install -r requirements.txt
python app.py
```

A API sobe em `http://localhost:5000`.

## Regras de negócio implementadas

- Prazo de devolução: 14 dias (duas semanas) a partir do empréstimo.
- Um usuário pode ter no máximo 3 livros emprestados ao mesmo tempo.
- Usuário inativo não pode pegar livro emprestado.
- Usuário com multa pendente não pode pegar livro emprestado até quitá-la.
- Um livro emprestado fica indisponível para novos empréstimos.
- Um livro não pode ser excluído enquanto estiver emprestado.
- Multa por atraso na devolução: R$ 1,50 por dia de atraso, somada à conta
  do usuário até que seja paga.

## Endpoints

### Livros

- `POST /livros` — cadastra um livro. Corpo: `{"titulo", "autor", "isbn"}`.
- `GET /livros` — lista todos os livros. Filtro opcional `?disponivel=true`.
- `GET /livros/<id>` — busca um livro específico.
- `DELETE /livros/<id>` — exclui um livro (falha com 409 se estiver emprestado).

### Usuários

- `POST /usuarios` — cadastra um usuário. Corpo: `{"nome", "email"}`
  (opcionalmente `"ativo": true|false`, padrão `true`).
- `GET /usuarios` — lista todos os usuários.
- `GET /usuarios/<id>` — busca um usuário específico.
- `GET /usuarios/<id>/emprestimos` — lista os empréstimos do usuário.
  Filtro opcional `?abertos=true` para retornar somente os em aberto.
- `POST /usuarios/<id>/pagamento-multa` — registra o pagamento da multa,
  zerando a pendência do usuário.

### Empréstimos

- `POST /emprestimos` — registra um empréstimo. Corpo:
  `{"usuario_id", "livro_id"}` (opcionalmente `"data_emprestimo": "AAAA-MM-DD"`
  para simular empréstimos com data retroativa).
- `GET /emprestimos` — lista todos os empréstimos. Filtro opcional
  `?abertos=true`.
- `GET /emprestimos/<id>` — busca um empréstimo específico.
- `POST /emprestimos/<id>/devolucao` — registra a devolução do livro,
  calculando a multa por atraso se houver (opcionalmente aceita
  `{"data_devolucao": "AAAA-MM-DD"}` para simular a data de devolução).

## Códigos de status HTTP

- `200` — operação concluída com sucesso (consulta ou atualização).
- `201` — recurso criado com sucesso.
- `204` — recurso excluído com sucesso (sem corpo de resposta).
- `400` — dados de entrada inválidos ou ausentes.
- `404` — recurso (livro, usuário ou empréstimo) não encontrado.
- `409` — violação de regra de negócio (ex.: livro indisponível, usuário
  inativo, limite de empréstimos atingido, multa pendente, livro emprestado
  no momento da exclusão).
