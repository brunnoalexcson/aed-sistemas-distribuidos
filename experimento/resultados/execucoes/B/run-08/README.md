# Sistema de Biblioteca — API REST

API REST em Python (Flask) para gerenciar o acervo de livros, o cadastro de
usuários e o controle de empréstimos de uma biblioteca de bairro. Os dados
são mantidos inteiramente em memória (não há banco de dados) e a API não
possui autenticação nem interface gráfica.

## Requisitos

- Python 3.9 ou superior

## Instalação

```bash
pip install -r requirements.txt
```

## Execução

```bash
python app.py
```

O servidor sobe por padrão em `http://localhost:5000`.

## Regras de negócio implementadas

- Cada livro tem título, autor e ISBN, e fica disponível ou indisponível
  conforme está ou não emprestado.
- Cada usuário tem nome e e-mail, um status de ativo/inativo e um saldo de
  multa pendente.
- Um livro não pode ser excluído do acervo enquanto estiver emprestado.
- O prazo de devolução de um empréstimo é de 14 dias (duas semanas) a partir
  da data do empréstimo.
- Um usuário só pode ter no máximo 3 empréstimos em aberto simultaneamente.
- Usuário inativo não pode pegar livro emprestado.
- Usuário com multa pendente não pode pegar livro emprestado até quitá-la.
- Na devolução, se houver atraso, é calculada uma multa de R$ 1,50 por dia
  de atraso, somada ao saldo de multa pendente do usuário.
- O bibliotecário pode registrar o pagamento da multa, zerando a pendência
  do usuário.
- É possível consultar os empréstimos de um usuário, com filtro para listar
  apenas os que estão em aberto.

## Endpoints

### Livros

| Método | Rota                | Descrição                                         |
|--------|---------------------|----------------------------------------------------|
| POST   | `/livros`           | Cadastra um livro (`titulo`, `autor`, `isbn`).      |
| GET    | `/livros`           | Lista os livros (filtro opcional `?disponivel=true|false`). |
| GET    | `/livros/<id>`      | Busca um livro específico.                          |
| DELETE | `/livros/<id>`      | Exclui um livro (falha se estiver emprestado).      |

### Usuários

| Método | Rota                                   | Descrição                                             |
|--------|-----------------------------------------|--------------------------------------------------------|
| POST   | `/usuarios`                             | Cadastra um usuário (`nome`, `email`).                  |
| GET    | `/usuarios`                             | Lista os usuários cadastrados.                          |
| GET    | `/usuarios/<id>`                        | Busca um usuário específico.                            |
| GET    | `/usuarios/<id>/emprestimos`            | Lista os empréstimos do usuário (filtro `?em_aberto=true|false`). |
| POST   | `/usuarios/<id>/pagamento-multa`        | Registra o pagamento da multa pendente do usuário.      |

### Empréstimos

| Método | Rota                              | Descrição                                                    |
|--------|-------------------------------------|---------------------------------------------------------------|
| POST   | `/emprestimos`                      | Registra um empréstimo (`livro_id`, `usuario_id`).             |
| GET    | `/emprestimos`                      | Lista todos os empréstimos (filtro `?em_aberto=true|false`).   |
| GET    | `/emprestimos/<id>`                 | Busca um empréstimo específico.                                |
| POST   | `/emprestimos/<id>/devolucao`       | Registra a devolução de um empréstimo e calcula multa, se houver atraso. |

## Tratamento de erros

Todas as respostas de erro retornam um JSON no formato `{"erro": "mensagem"}`
com o código HTTP apropriado:

- `400` — dados de entrada inválidos ou ausentes.
- `404` — livro, usuário ou empréstimo não encontrado.
- `409` — violação de alguma regra de negócio (ex.: livro indisponível,
  limite de empréstimos atingido, usuário inativo, multa pendente, livro
  emprestado ao tentar excluir, empréstimo já devolvido).

## Estrutura do projeto

- `app.py` — aplicação Flask com as rotas e as regras de negócio.
- `models.py` — entidades `Book`, `User` e `Loan`.
- `storage.py` — armazenamento em memória e geração de identificadores.
- `errors.py` — exceções da API e tratamento centralizado de erros HTTP.
- `requirements.txt` — dependências do projeto.
