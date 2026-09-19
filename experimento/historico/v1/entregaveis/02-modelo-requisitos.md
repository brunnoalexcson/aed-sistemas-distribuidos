# Documento de Especificação de Requisitos — [Nome do Sistema]

<!--
================================================================================
TEMPLATE — Entregável 2 (o artefato)
Versão do template: 1.0

COMO USAR
  1. Copie este arquivo para casos/<sistema>/requisitos-<sistema>.md
  2. Leia o Entregável 3 (instruções de preenchimento) antes de escrever.
  3. Substitua todo [texto entre colchetes]. Os comentários de orientação podem
     ser apagados ou mantidos: não aparecem no Markdown renderizado.
  4. Nenhuma seção marcada OBRIGATÓRIA pode ficar vazia.

REGRA QUE GOVERNA O DOCUMENTO INTEIRO
  Todo nome técnico (campo, rota, status, mensagem) é escrito entre crases e
  EXATAMENTE como deve aparecer no código. O que não estiver escrito aqui será
  inventado pela LLM.
================================================================================
-->

## 0. Metadados — OBRIGATÓRIA

| Campo | Valor |
|---|---|
| Nome do sistema | [ ] |
| Versão do documento | [ex.: 1.0] |
| Versão do template | 1.0 |
| Autores | [ ] |
| Revisor (não pode ser autor) | [ ] |
| Data | [AAAA-MM-DD] |
| Status | [Rascunho \| Em revisão \| Aprovado] |

---

## 1. Objetivo do sistema — OBRIGATÓRIA

<!-- Uma ÚNICA frase, no formato abaixo. Se precisar de duas frases, o escopo
     está grande demais ou ainda não foi entendido. -->

O sistema permite que [ator] [ação] para [benefício].

---

## 2. Escopo — OBRIGATÓRIA

### 2.1 Incluído

<!-- Lista do que o sistema faz, em alto nível. Cada item vira um ou mais
     requisitos funcionais na Seção 7. -->

- [ ]

### 2.2 Explicitamente excluído

<!-- ESTA SUBSEÇÃO É A MAIS IGNORADA E UMA DAS MAIS IMPORTANTES.
     Liste o que a LLM NÃO deve implementar. Sem isto, ela adiciona
     autenticação, front-end, Docker, logging, cache e afins por conta própria,
     e cada adição é uma oportunidade de desviar do contrato especificado. -->

O sistema **não** implementa:

- [ ]

---

## 3. Glossário — OBRIGATÓRIA

<!-- Todo termo de domínio usado no documento. Serve para que o mesmo conceito
     não apareça com dois nomes diferentes ao longo do texto. -->

| Termo | Definição |
|---|---|
| [ ] | [ ] |

---

## 4. Stack técnica e restrições de implementação — OBRIGATÓRIA

<!-- Versões EXATAS. "Usar Python" não é especificação: é convite à escolha
     alheia. Bibliotecas proibidas importam tanto quanto as permitidas. -->

| Item | Especificação obrigatória |
|---|---|
| Linguagem / versão | [ex.: Python 3.11 ou superior] |
| Framework | [ex.: FastAPI] |
| Validação de dados | [ex.: Pydantic v2] |
| Servidor de aplicação | [ex.: Uvicorn] |
| Persistência | [ex.: em memória, no processo] |
| Bibliotecas permitidas | [lista fechada] |
| Bibliotecas proibidas | [lista explícita] |

---

## 5. Modelo de dados — OBRIGATÓRIA

<!-- Repita o bloco 5.x para cada entidade. Os nomes dos atributos são os nomes
     REAIS dos campos no JSON e no código. -->

### 5.1 Entidade: [Nome]

| Atributo | Tipo | Obrigatório | Restrições / validação | Exemplo |
|---|---|---|---|---|
| `[ ]` | [ ] | [Sim \| Não] | [ ] | `[ ]` |

<!-- Se a entidade tiver um campo de estado, enumere TODOS os valores possíveis
     e o valor inicial. Estados não enumerados são inventados. -->

**Estados possíveis de `[campo]`:** `[valor1]`, `[valor2]` · **valor inicial:** `[valor1]`

---

## 6. Regras de negócio — OBRIGATÓRIA

<!-- Enunciados verificáveis, numerados, referenciados pelos requisitos. Uma
     regra por linha; se houver "e" ligando duas condições independentes,
     separe em duas regras. -->

| ID | Regra | Requisitos afetados |
|---|---|---|
| RN-01 | [ ] | [RF-xx] |

---

## 7. Requisitos funcionais — OBRIGATÓRIA

<!-- Repita o bloco abaixo para cada requisito. Um requisito por identificador.
     Todo requisito precisa de, no mínimo, um critério de aceitação de SUCESSO
     e um de FALHA. -->

### RF-01 — [Título curto]

- **Descrição:** O sistema deve [ ].
- **Ator:** [ ]
- **Prioridade:** [Must \| Should \| Could]
- **Entrada:** [campos e tipos, com crases]
- **Processamento:** [passos, referenciando as regras RN-xx aplicáveis]
- **Saída:** [objeto retornado e status HTTP]
- **Regras relacionadas:** [RN-xx]
- **Critérios de aceitação:**
  - **CA-01.1** Dado [estado inicial], quando [ação], então [resultado observável: status, valor, mensagem].
  - **CA-01.2** Dado [estado inicial], quando [ação], então [resultado observável].

---

## 8. Contratos de interface — OBRIGATÓRIA (para sistemas com API)

<!-- O JSON precisa ser literal, não uma descrição do JSON. TODAS as respostas
     de erro precisam estar aqui, com status e mensagem exatos. Toda resposta de
     erro não especificada será inventada, e inventada diferente a cada execução. -->

### 8.1 `[MÉTODO] /[caminho]`

- **Requisito:** [RF-xx]
- **Corpo da requisição (JSON exato):**

```json
{ }
```

- **Resposta de sucesso — status `[ ]`:**

```json
{ }
```

- **Respostas de erro:**

| Status | Condição | Corpo exato |
|---|---|---|
| `[ ]` | [ ] | `{"erro": "[mensagem exata]"}` |

---

## 9. Requisitos não funcionais — OBRIGATÓRIA

<!-- Mensuráveis, com número e unidade, e com o método de verificação ao lado.
     Um RNF que não diz como é verificado não é um requisito: é uma intenção. -->

| ID | Categoria | Requisito mensurável | Como verificar |
|---|---|---|---|
| RNF-01 | [ ] | O sistema deve [ ] | [teste automatizado \| inspeção] |

---

## 10. Tratamento de erros (padrão global) — OBRIGATÓRIA

<!-- Define o formato ÚNICO de erro do sistema inteiro, para que não haja um
     formato por endpoint. -->

- **Formato único de resposta de erro:**

```json
{ }
```

- **Tabela de status HTTP e seu significado neste sistema:**

| Status | Uso neste sistema |
|---|---|
| `[ ]` | [ ] |

- **Precedência de validação:** <!-- Quando mais de um erro se aplica à mesma
  requisição, qual é retornado. Sem isto, a ordem varia por execução. -->

  [ex.: 1º corpo malformado → 2º recurso inexistente → 3º regra de negócio]

---

## 11. Instruções de geração para a LLM — OBRIGATÓRIA

<!-- Esta seção não descreve o sistema: ela restringe a LIBERDADE da LLM.
     É a seção que mais reduz variância entre execuções. -->

### 11.1 Estrutura de arquivos esperada

```
[árvore exata de pastas e arquivos]
```

### 11.2 Ponto de entrada

A aplicação deve ser inicializável por `[comando exato]`, com o objeto `[nome]`
exposto em `[caminho/arquivo.py]`.

### 11.3 Regras de geração

1. Entregue **arquivos completos**, sem trechos omitidos, sem `...`, sem "restante igual ao anterior".
2. **Não** implemente nada que não esteja neste documento, inclusive o que estiver listado na Seção 2.2.
3. **Não** altere nomes de campos, rotas, status HTTP ou mensagens de erro: use exatamente os desta especificação.
4. **Não** use bibliotecas fora da lista de permitidas da Seção 4.
5. Em caso de ambiguidade, implemente a leitura **mais literal** do texto; não adicione comportamento "razoável" não especificado.
6. Não escreva testes, README, Dockerfile ou documentação, salvo se a Seção 11.1 os incluir.

---

## 12. Matriz de rastreabilidade — OBRIGATÓRIA

<!-- Fecha o ciclo: requisito → critério → regra → endpoint → teste.
     Preenchida na Etapa 3 e completada na Etapa 5 (coluna de teste). -->

| Requisito | Critérios de aceitação | Regras | Endpoint | Caso de teste |
|---|---|---|---|---|
| RF-01 | CA-01.1, CA-01.2 | RN-01 | `[MÉTODO] /[caminho]` | `[test_...]` |

---

## 13. Controle de versões do documento

| Versão | Data | Autor | Mudança |
|---|---|---|---|
| 1.0 | [AAAA-MM-DD] | [ ] | Versão inicial |
