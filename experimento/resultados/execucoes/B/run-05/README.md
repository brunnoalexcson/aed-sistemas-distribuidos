# Sistema de Biblioteca (API REST)

API REST em Python (Flask) para gerenciar o acervo de livros, o cadastro de
usuários e os empréstimos de uma biblioteca de bairro. Não há autenticação
nem interface gráfica, e todos os dados são mantidos em memória (não há
banco de dados) — os dados são perdidos ao reiniciar o processo.

## Como executar

```bash
pip install -r requirements.txt
python app.py
```

A API sobe em `http://localhost:5000`.

## Regras de negócio

- Cada usuário pode ter no máximo 3 livros emprestados ao mesmo tempo.
- Usuário inativo não pode pegar livro emprestado.
- Usuário com multa pendente não pode pegar livro emprestado até quitá-la.
- Um livro não pode ser excluído do acervo enquanto estiver emprestado.
- O prazo de devolução de um empréstimo é de 14 dias (duas semanas).
- Ao devolver um livro em atraso, é calculada uma multa de R$ 1,50 por dia
  de atraso, que fica pendente na conta do usuário até ser paga.

## Endpoints

### Livros

| Método | Rota | Descrição |
| --- | --- | --- |
| POST | `/livros` | Cadastra um livro. Corpo: `{"titulo", "autor", "isbn"}`. |
| GET | `/livros` | Lista todos os livros do acervo. |
| GET | `/livros/<id>` | Busca um livro específico. |
| DELETE | `/livros/<id>` | Exclui um livro (falha se estiver emprestado). |

### Usuários

| Método | Rota | Descrição |
| --- | --- | --- |
| POST | `/usuarios` | Cadastra um usuário. Corpo: `{"nome", "email"}`. |
| GET | `/usuarios` | Lista todos os usuários. |
| GET | `/usuarios/<id>` | Busca um usuário específico. |
| PATCH | `/usuarios/<id>` | Atualiza `nome`, `email` e/ou `ativo` do usuário. |
| GET | `/usuarios/<id>/emprestimos` | Lista os empréstimos do usuário. Use `?abertos=true` para ver só os em aberto. |
| POST | `/usuarios/<id>/multas/pagamentos` | Registra o pagamento da multa pendente, zerando-a. |

### Empréstimos

| Método | Rota | Descrição |
| --- | --- | --- |
| POST | `/emprestimos` | Registra um empréstimo. Corpo: `{"usuario_id", "livro_id"}`. |
| GET | `/emprestimos` | Lista todos os empréstimos. |
| GET | `/emprestimos/<id>` | Busca um empréstimo específico. |
| POST | `/emprestimos/<id>/devolucao` | Registra a devolução do empréstimo. |

## Códigos de erro

- `400` — dados de entrada ausentes ou inválidos.
- `404` — livro, usuário ou empréstimo não encontrado.
- `409` — violação de regra de negócio (livro emprestado, usuário inativo,
  multa pendente, limite de empréstimos atingido, empréstimo já devolvido).

Todas as respostas de erro têm o formato `{"erro": "mensagem descritiva"}`.
