# Sistema de Biblioteca — API REST

API REST em Python (Flask) para gerenciar o acervo de livros, o cadastro de
usuários e os empréstimos de uma biblioteca de bairro. Todos os dados são
mantidos em memória (não há banco de dados) e o serviço não possui
autenticação nem interface gráfica.

## Como executar

```bash
pip install -r requirements.txt
python app.py
```

O servidor sobe em `http://localhost:5000/`.

## Regras de negócio implementadas

- Cada livro tem título, autor e ISBN.
- Cada usuário tem nome e e-mail, e pode estar ativo ou inativo.
- Um livro só pode ser excluído do acervo se não estiver emprestado no momento.
- Ao emprestar um livro:
  - o livro precisa estar disponível;
  - o usuário precisa estar ativo;
  - o usuário não pode ter multa pendente;
  - o usuário não pode ter mais de 3 empréstimos em aberto simultaneamente.
- O prazo de devolução é de 14 dias a partir da data do empréstimo.
- Na devolução, o livro volta a ficar disponível; se houver atraso, é
  calculada uma multa de R$ 1,50 por dia de atraso, somada à pendência do
  usuário.
- O bibliotecário pode registrar o pagamento da multa, zerando a pendência.
- É possível listar os empréstimos de um usuário e filtrar apenas os que
  estão em aberto.

## Endpoints

### Livros

| Método | Rota                | Descrição                                   |
|--------|---------------------|----------------------------------------------|
| POST   | `/books`             | Cadastra um livro (`title`, `author`, `isbn`) |
| GET    | `/books`             | Lista todos os livros                         |
| GET    | `/books/<id>`        | Busca um livro específico                     |
| DELETE | `/books/<id>`        | Remove um livro (falha se estiver emprestado) |

### Usuários

| Método | Rota                        | Descrição                                            |
|--------|-----------------------------|-------------------------------------------------------|
| POST   | `/users`                     | Cadastra um usuário (`name`, `email`)                  |
| GET    | `/users`                     | Lista todos os usuários                                |
| GET    | `/users/<id>`                | Busca um usuário específico                            |
| PATCH  | `/users/<id>`                | Atualiza `name`, `email` e/ou `active`                 |
| POST   | `/users/<id>/pay-fine`       | Registra o pagamento da multa pendente do usuário      |
| GET    | `/users/<id>/loans`          | Lista os empréstimos do usuário                        |
| GET    | `/users/<id>/loans?status=open` | Lista apenas os empréstimos em aberto do usuário   |

### Empréstimos

| Método | Rota                    | Descrição                                          |
|--------|-------------------------|-----------------------------------------------------|
| POST   | `/loans`                 | Registra um empréstimo (`book_id`, `user_id`)        |
| GET    | `/loans`                 | Lista todos os empréstimos                           |
| GET    | `/loans/<id>`            | Busca um empréstimo específico                       |
| POST   | `/loans/<id>/return`     | Registra a devolução do empréstimo                   |

## Códigos de resposta

- `200 OK` / `201 Created` — operação bem-sucedida.
- `204 No Content` — exclusão de livro bem-sucedida.
- `400 Bad Request` — dados de entrada inválidos ou ausentes.
- `404 Not Found` — livro, usuário ou empréstimo inexistente.
- `409 Conflict` — violação de regra de negócio (ex.: livro indisponível,
  usuário inativo, multa pendente, limite de empréstimos atingido, exclusão
  de livro emprestado, devolução de empréstimo já finalizado).
