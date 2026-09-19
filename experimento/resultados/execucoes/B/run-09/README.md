# Sistema de Biblioteca — API REST

API REST em Python (Flask) para gerenciar o acervo de livros, o cadastro
de usuários e os empréstimos da biblioteca do bairro. Não há autenticação
nem interface gráfica — apenas a API. Todos os dados são mantidos em
memória (não há banco de dados); ao reiniciar o processo, os dados são
perdidos.

## Instalação

```bash
pip install -r requirements.txt
```

## Execução

```bash
python main.py
```

A API sobe em `http://127.0.0.1:5000`.

## Regras de negócio

- Prazo de devolução: 14 dias (duas semanas) a partir do empréstimo.
- Um usuário pode ter no máximo 3 livros emprestados (ainda não
  devolvidos) ao mesmo tempo.
- Usuário inativo (`ativo = false`) não pode pegar livro emprestado.
- Usuário com multa pendente não pode pegar livro emprestado até quitá-la.
- Não é possível excluir um livro que está emprestado no momento.
- Multa por atraso na devolução: R$ 1,50 por dia de atraso, somada à
  multa pendente do usuário.

## Endpoints

### Livros

| Método | Rota                | Descrição                                             |
|--------|---------------------|--------------------------------------------------------|
| POST   | `/livros`           | Cadastra um livro (`titulo`, `autor`, `isbn`).          |
| GET    | `/livros`           | Lista todos os livros do acervo.                        |
| GET    | `/livros/<id>`      | Busca um livro específico.                              |
| DELETE | `/livros/<id>`      | Exclui um livro (falha se ele estiver emprestado).      |

### Usuários

| Método | Rota                                  | Descrição                                                         |
|--------|---------------------------------------|--------------------------------------------------------------------|
| POST   | `/usuarios`                           | Cadastra um usuário (`nome`, `email`).                              |
| GET    | `/usuarios`                           | Lista todos os usuários.                                            |
| GET    | `/usuarios/<id>`                      | Busca um usuário específico.                                        |
| PATCH  | `/usuarios/<id>`                      | Atualiza `nome`, `email` e/ou `ativo` de um usuário.                |
| GET    | `/usuarios/<id>/emprestimos`          | Lista os empréstimos do usuário (use `?em_aberto=true` para filtrar apenas os em aberto). |
| POST   | `/usuarios/<id>/multas/pagamento`     | Registra o pagamento da multa pendente do usuário, zerando-a.      |

### Empréstimos

| Método | Rota                                | Descrição                                                       |
|--------|-------------------------------------|-------------------------------------------------------------------|
| POST   | `/emprestimos`                      | Registra um empréstimo (`livro_id`, `usuario_id`).                  |
| GET    | `/emprestimos`                      | Lista todos os empréstimos registrados.                            |
| GET    | `/emprestimos/<id>`                 | Busca um empréstimo específico.                                    |
| POST   | `/emprestimos/<id>/devolucao`       | Registra a devolução do livro, calculando multa se houver atraso.  |

## Códigos de erro

- `400` — dados de entrada ausentes ou inválidos.
- `404` — livro, usuário ou empréstimo não encontrado.
- `409` — violação de regra de negócio (livro indisponível, usuário
  inativo, multa pendente, limite de empréstimos atingido, exclusão de
  livro emprestado, devolução de empréstimo já devolvido, etc.).

Todas as respostas de erro seguem o formato `{"erro": "mensagem"}`.
