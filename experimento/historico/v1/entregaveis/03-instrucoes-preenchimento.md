# Entregável 3 — Instruções de Preenchimento do Documento de Requisitos

**Refere-se a:** `entregaveis/02-modelo-requisitos.md` (template v1.0)
**Versão das instruções:** 1.0
**Data:** 2026-09-19

---

## Por que estas instruções existem

Um template sem instruções é preenchido de forma diferente por cada pessoa — e, quando isso acontece, a conformidade do código gerado vira sorte. Estas instruções padronizam **como** cada seção é escrita, de modo que dois analistas diferentes, especificando o mesmo sistema, produzam documentos equivalentes em precisão.

O documento é lido por uma LLM. Ela não pergunta, não infere contexto organizacional e não sinaliza dúvida: quando o texto admite duas leituras, ela escolhe uma — e pode escolher outra na execução seguinte. Cada regra abaixo existe para eliminar uma fonte concreta de variação.

---

# Parte I — Regras gerais de redação

Valem para o documento inteiro.

### R1. Forma verbal padronizada

Todo requisito começa com **"O sistema deve"** (obrigatório) ou **"O sistema pode"** (opcional).

| | |
|---|---|
| ❌ Errado | "Seria bom que o sistema validasse o e-mail." |
| ✅ Certo | "O sistema deve rejeitar cadastro cujo campo `email` não contenha `@`." |

**Motivo:** "seria bom", "idealmente" e "preferencialmente" não distinguem o obrigatório do acessório, e a LLM trata os dois igual — às vezes implementando, às vezes não.

### R2. Atomicidade — um requisito por identificador

Se a frase tem um "e" ligando duas ações, são dois requisitos.

| | |
|---|---|
| ❌ Errado | "RF-03: O sistema deve cadastrar o usuário e enviar e-mail de confirmação." |
| ✅ Certo | "RF-03: O sistema deve cadastrar o usuário." / "RF-04: O sistema deve enviar e-mail de confirmação." |

**Motivo:** com dois comportamentos sob um único ID, um critério de aceitação não consegue ser binário — o código pode atender metade do requisito, e a medição perde objetividade.

### R3. Palavras proibidas

Nenhuma destas pode aparecer no documento, porque **não são verificáveis**:

> rápido · lento · fácil · simples · amigável · intuitivo · adequado · apropriado · eficiente · robusto · escalável · otimizado · flexível · seguro (sem critério) · moderno · limpo · boa performance · alta disponibilidade (sem número) · se possível · quando necessário · etc. · entre outros

Substitua sempre por **número com unidade** ou por **comportamento observável**.

| | |
|---|---|
| ❌ Errado | "O sistema deve responder rapidamente." |
| ✅ Certo | "O sistema deve responder a `GET /livros` em até 500 ms para um acervo de até 1.000 registros." |

Atenção especial a **"etc."** e **"entre outros"**: são listas incompletas, e a LLM completa a lista sozinha.

### R4. Nomes técnicos entre crases e literais

Todo campo, rota, status, valor de enum e mensagem de erro é escrito entre crases, **exatamente** como deve aparecer no código.

| | |
|---|---|
| ❌ Errado | "Retornar erro informando que o livro não está disponível." |
| ✅ Certo | "Retornar status `409` com corpo `{"erro": "Livro indisponível"}`." |

**Motivo:** "informar que o livro não está disponível" tem dezenas de implementações válidas; um teste automatizado precisa de uma.

### R5. Todo requisito funcional tem sucesso e falha

Mínimo de um critério de aceitação de **caminho feliz** e um de **caminho de erro**.

**Motivo:** LLMs implementam o caminho feliz com facilidade; é no tratamento de erro que a conformidade se perde. Um documento que só especifica sucesso mede apenas a parte fácil.

### R6. Critérios no formato Dado / Quando / Então, com resultado observável

> **CA-04.2** Dado um usuário com 3 empréstimos ativos, quando `POST /emprestimos` for chamado, então a resposta deve ter status `422` e corpo `{"erro": "Limite de empréstimos atingido"}`.

O "então" precisa ser verificável por uma máquina: status, valor de campo, mensagem. "Então o sistema deve tratar o erro adequadamente" não é critério de aceitação.

### R7. Nada implícito

Se não está escrito, será inventado. Em caso de dúvida sobre incluir uma informação, **inclua**. O custo de uma linha a mais no documento é desprezível; o custo de uma lacuna é uma execução inteira fora de conformidade.

Itens tipicamente esquecidos: valor inicial de campos de estado; o que acontece com IDs inexistentes; formato de data; fuso horário; se a lista vazia retorna `200` com `[]` ou `404`; ordem de validação quando dois erros se aplicam.

### R8. Consistência de vocabulário

Um conceito, um nome, do começo ao fim. Se a entidade é `Emprestimo`, ela não é "locação" em outra seção. Registre o termo no Glossário (Seção 3) e use-o sempre.

---

# Parte II — Instruções por seção

Para cada seção: **propósito**, **obrigatoriedade**, **erros comuns** e um par **certo / errado**.

---

## Seção 0 — Metadados

**Propósito:** rastrear qual versão do documento gerou qual resultado experimental.
**Obrigatório:** todos os campos. O campo *Revisor* não pode conter o mesmo nome do campo *Autores* (Etapa 4 do processo exige independência).

**Erro comum:** deixar "Versão do documento" fixa em 1.0 durante todo o trabalho. Cada correção após uma rodada de testes gera nova versão — é o que permite comparar v1 e v2 no relatório.

---

## Seção 1 — Objetivo do sistema

**Propósito:** dar à LLM o enquadramento em uma frase, antes de qualquer detalhe.
**Obrigatório:** exatamente uma frase, no formato *"O sistema permite que [ator] [ação] para [benefício]"*.

| | |
|---|---|
| ❌ Errado | "Sistema de biblioteca moderno e completo para gestão de acervo." |
| ✅ Certo | "O sistema permite que bibliotecários registrem empréstimos e devoluções de livros para controlar a circulação do acervo." |

**Erro comum:** escrever um parágrafo de marketing. O objetivo não vende o sistema, delimita-o. Se não couber em uma frase, o escopo ainda não foi fechado (volte à Etapa 2 do processo).

---

## Seção 2 — Escopo

**Propósito:** 2.1 diz o que construir; **2.2 impede a LLM de construir o que ninguém pediu**.
**Obrigatório:** ambas as subseções. 2.2 vazia é reprovação automática na validação.

| | |
|---|---|
| ❌ Errado | (2.2 em branco, ou "nada a declarar") |
| ✅ Certo | "O sistema **não** implementa: autenticação ou autorização; interface web; persistência em disco; envio de e-mail; Docker; logging estruturado; paginação." |

**Erro comum:** achar que "não pedimos, logo não será feito". LLMs completam sistemas com o que consideram boas práticas — autenticação e paginação são as adições espontâneas mais frequentes, e ambas alteram as respostas dos endpoints, quebrando critérios de aceitação que nada tinham a ver com elas.

---

## Seção 3 — Glossário

**Propósito:** impedir que o mesmo conceito apareça com dois nomes.
**Obrigatório:** todo termo de domínio que não seja de conhecimento geral, e todo termo com significado específico neste sistema.

| | |
|---|---|
| ❌ Errado | "Multa: valor cobrado do usuário." |
| ✅ Certo | "Multa: valor em reais devido por devolução após a `data_devolucao_prevista`, calculado conforme RN-04. Não implica bloqueio automático do usuário." |

**Erro comum:** definir o termo repetindo o termo ("Empréstimo: quando há um empréstimo"). Uma definição útil diz quando o conceito se aplica e quando **não** se aplica.

---

## Seção 4 — Stack técnica e restrições

**Propósito:** eliminar a maior fonte isolada de não conformidade — a LLM escolher a tecnologia.
**Obrigatório:** todas as linhas da tabela, inclusive *Bibliotecas proibidas*.

| | |
|---|---|
| ❌ Errado | "Usar Python." |
| ✅ Certo | "Python 3.11 ou superior; FastAPI; Pydantic v2; Uvicorn; persistência em memória (dicionários no processo); bibliotecas permitidas: apenas as citadas; proibidas: SQLAlchemy, bancos de dados externos, ORMs, Docker, bibliotecas de autenticação." |

**Motivo:** sem isso, a LLM pode gerar em outra linguagem, ou com bibliotecas incompatíveis com a suíte de testes — e o código será avaliado como reprovado por um motivo que nada tem a ver com os requisitos de negócio.

**Erro comum:** especificar a versão do framework com precisão excessiva (`FastAPI 0.110.0`) quando o ambiente de teste tem outra. Prefira "3.11 ou superior" a um pin exato que o ambiente não honra — **mas** seja exato quanto à biblioteca em si.

---

## Seção 5 — Modelo de dados

**Propósito:** fixar os nomes de campo reais, que aparecerão literalmente no JSON.
**Obrigatório:** para cada atributo — tipo, obrigatoriedade, validação e exemplo. Para todo campo de estado — a enumeração completa dos valores e o valor inicial.

| | |
|---|---|
| ❌ Errado | "Livro tem título, autor e status." |
| ✅ Certo | Tabela com `id` (inteiro, gerado pelo sistema, sequencial a partir de `1`), `titulo` (string, obrigatório, 1–200 caracteres), `status` (string, valores `disponivel` \| `emprestado`, inicial `disponivel`). |

**Erros comuns:**
- Não dizer quem gera o `id` (cliente ou sistema) nem a partir de qual valor.
- Usar acento ou maiúscula no nome do campo em uma seção e não em outra (`título` vs `titulo`). Escolha um e repita.
- Omitir o valor inicial do campo de estado — a LLM inventa, e metade das execuções começa em um estado e metade em outro.

---

## Seção 6 — Regras de negócio

**Propósito:** isolar a lógica que vários requisitos compartilham, para escrevê-la uma vez só.
**Obrigatório:** ID, enunciado verificável e requisitos afetados.

| | |
|---|---|
| ❌ Errado | "RN-02: Usuários inadimplentes têm restrições." |
| ✅ Certo | "RN-02: Um usuário com `multa_pendente` maior que `0` não pode registrar novo empréstimo." |

**Erro comum:** escrever a regra como narrativa de processo em vez de condição verificável. Teste: a regra consegue ser avaliada como verdadeira ou falsa diante de um estado concreto do sistema? Se não, reescreva.

---

## Seção 7 — Requisitos funcionais

**Propósito:** o coração do documento.
**Obrigatório:** todos os campos do bloco; no mínimo um CA de sucesso e um de falha (R5).

**Numeração:** `RF-01`, `RF-02`, … e critérios `CA-01.1`, `CA-01.2` (o número antes do ponto é o do requisito). Essa convenção não é cosmética: a suíte de testes e a medição de conformidade dependem dela para mapear teste → critério.

**Exemplo de requisito preenchido no nível de precisão exigido:**

> ### RF-04 — Registrar empréstimo
>
> - **Descrição:** O sistema deve registrar o empréstimo de um livro disponível a um usuário ativo.
> - **Ator:** Bibliotecário
> - **Prioridade:** Must
> - **Entrada:** `usuario_id` (inteiro), `livro_id` (inteiro)
> - **Processamento:** verificar RN-01 e RN-02; marcar o livro como `emprestado`; definir `data_devolucao_prevista` = data atual + 14 dias.
> - **Saída:** objeto `Emprestimo` com status `201`.
> - **Regras relacionadas:** RN-01, RN-02
> - **Critérios de aceitação:**
>   - **CA-04.1** Dado um livro com status `disponivel` e um usuário com 0 empréstimos ativos, quando `POST /emprestimos` for chamado, então a resposta deve ter status `201` e o livro passar a ter status `emprestado`.
>   - **CA-04.2** Dado um usuário com 3 empréstimos ativos, quando `POST /emprestimos` for chamado, então a resposta deve ter status `422` e corpo `{"erro": "Limite de empréstimos atingido"}`.
>   - **CA-04.3** Dado um livro com status `emprestado`, quando `POST /emprestimos` for chamado, então a resposta deve ter status `409` e corpo `{"erro": "Livro indisponível"}`.

Repare no que o exemplo faz: o processamento referencia regras em vez de repeti-las; a saída tem status; cada critério tem estado inicial concreto, ação exata e resultado literal.

**Erros comuns:**
- Critério sem estado inicial ("quando chamar o endpoint, então retorna 201") — sem o "dado", o teste não sabe o que montar.
- Critério que descreve implementação ("então o sistema deve salvar no dicionário") em vez de comportamento observável pela interface.
- Requisito de listagem sem dizer o que acontece com lista vazia.

---

## Seção 8 — Contratos de interface

**Propósito:** transformar cada requisito em um contrato HTTP literal.
**Obrigatório:** para cada endpoint — método, caminho, corpo da requisição em JSON literal, resposta de sucesso com status e JSON literal, e **todas** as respostas de erro.

| | |
|---|---|
| ❌ Errado | "POST /emprestimos — recebe os dados do empréstimo e retorna o empréstimo criado, ou erro." |
| ✅ Certo | JSON literal de requisição, JSON literal de resposta com status `201`, e tabela com `404` / `409` / `422`, cada um com a mensagem exata. |

**Erros comuns:**
- Escrever `{ "usuario_id": int }` em vez de um exemplo válido `{ "usuario_id": 1, "livro_id": 1 }`. O JSON tem que ser JSON, não pseudocódigo.
- Esquecer o `404` de recurso inexistente. É o erro mais esquecido e um dos mais testados.
- Não especificar se a resposta de criação devolve o objeto completo ou apenas o `id`.

---

## Seção 9 — Requisitos não funcionais

**Propósito:** exigências de qualidade, escritas de modo mensurável.
**Obrigatório:** ID, categoria, requisito com número e unidade, e método de verificação.

| | |
|---|---|
| ❌ Errado | "RNF-01: O sistema deve ser rápido e organizado." |
| ✅ Certo | "RNF-01 (Desempenho): O sistema deve responder a `GET /livros` em até 500 ms com 1.000 registros — verificação: teste automatizado." / "RNF-02 (Estrutura): O código deve seguir a árvore de arquivos da Seção 11.1 — verificação: inspeção binária." |

**Erro comum:** escrever RNF que ninguém sabe medir. Regra prática: se você não consegue escrever, ali mesmo, como verificaria, o requisito ainda não está pronto.

---

## Seção 10 — Tratamento de erros (padrão global)

**Propósito:** um formato de erro para o sistema inteiro, e uma ordem de precedência quando vários erros se aplicam.
**Obrigatório:** formato único, tabela de status e regra de precedência.

| | |
|---|---|
| ❌ Errado | (seção ausente; cada endpoint define seu formato) |
| ✅ Certo | "Formato único: `{"erro": "<mensagem>"}`. Precedência: 1º corpo malformado (`422`), 2º recurso inexistente (`404`), 3º violação de regra de negócio (`409`/`422`)." |

**Erro comum:** ignorar a precedência. Quando uma requisição viola duas condições ao mesmo tempo — por exemplo, usuário inexistente **e** livro indisponível —, sem regra de precedência metade das execuções retorna `404` e metade `409`. Esse único detalhe costuma responder por vários pontos percentuais de conformidade.

---

## Seção 11 — Instruções de geração para a LLM

**Propósito:** restringir a liberdade da LLM. É a seção que mais reduz a variância entre execuções.
**Obrigatório:** árvore de arquivos, ponto de entrada exato e as regras de geração.

| | |
|---|---|
| ❌ Errado | "Gere o código em Python seguindo boas práticas." |
| ✅ Certo | Árvore literal (`app/main.py`, `app/models.py`, …), comando de inicialização `uvicorn app.main:app`, e as proibições: sem funcionalidades extras, sem renomear campos, sem bibliotecas fora da lista, sem omitir trechos. |

**Erro comum:** não fixar o ponto de entrada. Se o arquivo principal for `main.py` em uma execução e `src/api.py` em outra, a suíte de testes não sobe a aplicação — e todos os critérios falham por uma razão que não tem relação com o mérito do código.

**Sobre a regra da leitura literal:** a instrução *"em caso de ambiguidade, implemente a leitura mais literal; não adicione comportamento razoável não especificado"* existe porque o comportamento "razoável" de uma LLM é estatisticamente plausível, não determinístico — e portanto varia entre execuções.

---

## Seção 12 — Matriz de rastreabilidade

**Propósito:** provar cobertura — todo requisito chega a um teste, todo teste vem de um requisito.
**Obrigatório:** uma linha por requisito. A coluna *Caso de teste* é preenchida na Etapa 5 do processo.

**Erro comum:** preencher a matriz no fim, de memória. Ela deve ser preenchida enquanto se escreve a Seção 7; assim as lacunas aparecem enquanto ainda são baratas de corrigir.

---

# Parte III — Checklist de validação (Etapa 4 do processo)

Aplicado pelo **revisor**, que não pode ser autor do documento. **Todos** os itens precisam ser marcados para o documento avançar à Etapa 5. Um item reprovado devolve o documento à Etapa 3.

### Completude

- [ ] Nenhuma seção obrigatória está vazia ou contém placeholder (`[ ]`, "a definir", "TBD").
- [ ] A Seção 2.2 (escopo excluído) lista ao menos um item.
- [ ] Todo campo de estado do modelo de dados tem enumeração completa e valor inicial.
- [ ] Todo endpoint da Seção 8 tem corpo de requisição, resposta de sucesso e **todas** as respostas de erro.
- [ ] Existe resposta `404` especificada para toda operação que recebe um identificador.
- [ ] A Seção 10 define formato de erro único e regra de precedência.
- [ ] A Seção 11 define a árvore de arquivos e o ponto de entrada exato.

### Qualidade dos requisitos (ISO/IEC/IEEE 29148)

- [ ] **Necessário:** todo requisito rastreia a uma necessidade da Etapa 1 ou a uma regra de negócio.
- [ ] **Não ambíguo:** nenhuma palavra da lista proibida aparece no documento (verificado por busca textual).
- [ ] **Atômico:** nenhum requisito tem "e" ligando duas ações distintas.
- [ ] **Verificável:** todo critério de aceitação tem resultado observável (status, valor ou mensagem).
- [ ] **Consistente:** nenhum requisito contradiz outro; nomes de campo idênticos em todas as seções.
- [ ] **Rastreável:** todo requisito tem ID único e aparece na matriz da Seção 12.

### Critérios de aceitação

- [ ] Todo RF tem no mínimo um CA de sucesso **e** um de falha.
- [ ] Todo CA segue o formato Dado / Quando / Então.
- [ ] Todo CA tem estado inicial concreto (o "dado" não é genérico).
- [ ] A numeração dos CAs segue `CA-<nº do RF>.<sequencial>`.
- [ ] Nenhum CA descreve implementação interna em vez de comportamento observável.

### Precisão técnica

- [ ] Todo nome técnico está entre crases e escrito como aparecerá no código.
- [ ] Toda mensagem de erro está escrita literalmente, entre crases.
- [ ] Todo JSON de exemplo é JSON válido, com valores reais (não tipos).
- [ ] A Seção 4 declara linguagem, framework, persistência e bibliotecas proibidas.

### Rastreabilidade

- [ ] A matriz da Seção 12 contém todos os RF do documento.
- [ ] Toda regra RN-xx citada em algum requisito existe na Seção 6.
- [ ] Todo RF citado na Seção 6 existe na Seção 7.

**Resultado da validação:** ☐ Aprovado ☐ Reprovado — **Revisor:** ______________ — **Data:** ________
