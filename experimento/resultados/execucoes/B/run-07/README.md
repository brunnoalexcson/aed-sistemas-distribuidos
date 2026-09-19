# Sistema de Biblioteca — API REST

API REST em Python (Flask) para gerenciar o acervo de livros, o cadastro de
usuários e os empréstimos de uma biblioteca. Não possui login nem interface
gráfica, e todos os dados são armazenados em memória (sem banco de dados) —
os dados são perdidos ao reiniciar a aplicação.

## Instalação e execução

```bash
pip install -r requirements.txt
python app.py
```

A API sobe em `http://127.0.0.1:5000/`.

## Regras de negócio implementadas

- Cada usuário pode ter no máximo 3 livros emprestados simultaneamente.
- Usuário inativo não pode pegar livro emprestado.
- Usuário com multa pendente fica impedido de pegar livros emprestados até
  quitá-la.
- Um livro emprestado fica indisponível para outros usuários.
- O prazo de devolução é de 14 dias (2 semanas) a partir do empréstimo.
- Ao devolver com atraso, é calculada uma multa de R$ 1,50 por dia de
  atraso, que fica pendente na conta do usuário.
- Não é possível excluir um livro que está emprestado no momento.

## Endpoints

### Livros

| Método | Rota                | Descrição                                             |
|--------|---------------------|--------------------------------------------------------|
| POST   | `/livros`           | Cadastra um livro (`titulo`, `autor`, `isbn`).          |
| GET    | `/livros`           | Lista os livros. Filtro opcional `?disponivel=true/false`. |
| GET    | `/livros/<id>`      | Busca um livro específico.                              |
| DELETE | `/livros/<id>`      | Exclui um livro (falha se estiver emprestado).          |

### Usuários

| Método | Rota                                | Descrição                                                       |
|--------|-------------------------------------|-------------------------------------------------------------------|
| POST   | `/usuarios`                         | Cadastra um usuário (`nome`, `email`).                            |
| GET    | `/usuarios`                         | Lista os usuários.                                                 |
| GET    | `/usuarios/<id>`                    | Busca um usuário específico.                                       |
| PATCH  | `/usuarios/<id>`                    | Atualiza o status do usuário (`ativo`: true/false).                |
| GET    | `/usuarios/<id>/emprestimos`        | Lista os empréstimos do usuário. Filtro opcional `?em_aberto=true`. |
| POST   | `/usuarios/<id>/multa/pagamento`    | Registra o pagamento da multa pendente do usuário.                 |

### Empréstimos

| Método | Rota                              | Descrição                                            |
|--------|------------------------------------|-------------------------------------------------------|
| POST   | `/emprestimos`                     | Registra um empréstimo (`usuario_id`, `livro_id`).     |
| GET    | `/emprestimos`                     | Lista todos os empréstimos.                            |
| GET    | `/emprestimos/<id>`                | Busca um empréstimo específico.                        |
| POST   | `/emprestimos/<id>/devolucao`      | Registra a devolução do livro do empréstimo.           |

## Códigos de erro

- `400 Bad Request`: dados obrigatórios ausentes ou inválidos.
- `404 Not Found`: livro, usuário ou empréstimo inexistente.
- `409 Conflict`: violação de regra de negócio (livro emprestado, limite de
  empréstimos atingido, usuário inativo, multa pendente, ISBN/e-mail
  duplicado, etc.).
