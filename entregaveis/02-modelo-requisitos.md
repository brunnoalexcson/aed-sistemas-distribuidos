# Documento de especificação de requisitos — [Nome do sistema]

<!-- MODELO REUTILIZÁVEL — Entregável 2, versão 1.1.
Revisão posterior ao experimento; a versão 1.0 avaliada está em
experimento/historico/v1/entregaveis/02-modelo-requisitos.md.
Copie este documento e preencha os campos. Leia as instruções antes.
Para seções não aplicáveis, escreva “Não aplicável” e justifique.
Os exemplos HTTP devem ser substituídos pelo contrato da interface real.
-->

## 0. Metadados

| Campo | Valor |
|---|---|
| Sistema | [nome] |
| Versão da especificação | [versão] |
| Versão do modelo | 1.1 |
| Autores | [nomes] |
| Revisor independente | [nome ou pendente] |
| Data | [AAAA-MM-DD] |
| Situação | [Rascunho / Em revisão / Aprovado] |
| Necessidades de origem | [referência ao levantamento] |

## 1. Objetivo e atores

O sistema permite que [ator] [ação] para [benefício].

| Ator | Responsabilidade ou necessidade |
|---|---|
| [ator] | [necessidade] |

## 2. Escopo

### 2.1 Incluído

- [capacidade incluída]

### 2.2 Excluído

- [capacidade excluída e motivo]

## 3. Glossário

| Termo | Definição no domínio |
|---|---|
| [termo] | [significado] |

## 4. Tecnologia e ambiente

<!-- Especifique versões exatas OU faixas compatíveis justificadas.
Registre as versões efetivamente instaladas no manifesto do experimento.
A especificação e o ambiente de teste precisam ser compatíveis. -->

| Item | Restrição |
|---|---|
| Linguagem e versão compatível | [linguagem, versão/faixa] |
| Framework e versão compatível | [framework, versão/faixa] |
| Bibliotecas permitidas | [lista fechada; explicitar dependências transitivas quando relevantes] |
| Bibliotecas ou recursos proibidos | [lista ou não aplicável justificado] |
| Persistência e duração dos dados | [mecanismo; quando o estado é descartado] |
| Ambiente e inicialização | [referência ao ambiente reproduzível] |

## 5. Modelo de dados

### 5.1 Entidade: [nome]

| Campo | Tipo | Obrigatório | Restrições | Valor inicial ou exemplo |
|---|---|---|---|---|
| `[campo]` | [tipo] | [sim/não] | [limites, unicidade, geração] | [valor] |

- **Identificador:** [quem gera, tipo, regra de unicidade].
- **Estados e transições:** [valores permitidos, estado inicial e transições válidas].
- **Datas e valores numéricos:** [formato, fuso horário, unidade e arredondamento quando aplicáveis].
- **Relacionamentos:** [referências e comportamento na exclusão].

<!-- Repita 5.x para cada entidade. -->

## 6. Regras de negócio

| ID | Regra verificável | Origem | Requisitos afetados |
|---|---|---|---|
| RN-01 | [condição e consequência] | [necessidade] | RF-01 |

## 7. Requisitos funcionais

### RF-01 — [Título]

- **Descrição:** O sistema deve [comportamento].
- **Origem:** [necessidade].
- **Ator:** [ator].
- **Prioridade:** [Must / Should / Could].
- **Entrada:** [campos, tipos e pré-condições].
- **Processamento:** [regra observável, referenciando RN-xx].
- **Saída:** [resultado e estado final].
- **Regras relacionadas:** [IDs ou não aplicável].
- **Critérios de aceitação:**
  - **CA-01.1** Dado [estado concreto], quando [ação], então [resultado verificável].
  - **CA-01.2** Dado [estado de erro ou limite], quando [ação], então [resultado verificável].

<!-- Repita para cada RF. Deve haver caminho de sucesso e de falha quando
aplicável. Se não houver falha definida, registre a justificativa e um caso
limite, sem inventar comportamento para preencher o modelo. -->

## 8. Contratos de interface

### 8.1 [Operação]

- **Requisito:** [RF-xx].
- **Interface:** [método e rota HTTP / comando e argumentos / ação de tela / mensagem].
- **Entrada exata:** [exemplo completo e válido, ou “sem entrada”].
- **Resposta de sucesso:** [status ou código de saída, estrutura e exemplo literal].

| Condição de erro | Código/status | Resposta literal |
|---|---|---|
| [condição] | [código] | [mensagem ou objeto completo] |

- **Ausência de dados:** [retorno de consulta vazia ou recurso inexistente].
- **Ordenação, filtros e repetição:** [comportamento quando aplicável].

<!-- Não inclua marcadores de tipo em blocos declarados como JSON.
Exemplos com valores reais devem acompanhar a descrição dos campos. -->

## 9. Requisitos não funcionais

| ID | Categoria | Requisito verificável | Instrumento e condição de aprovação |
|---|---|---|---|
| RNF-01 | [categoria] | O sistema deve [propriedade com medida ou condição binária] | [teste/inspeção, dados e limite] |

<!-- Desempenho precisa de carga, unidade e limite. Estrutura e dependências
podem ser verificadas por inspeção binária, sem inventar uma medida numérica. -->

## 10. Tratamento global de erros

- **Formato:** [estrutura e exemplo literal].
- **Validação:** [campos ausentes, tipos inválidos, valores fora dos limites].
- **Precedência:** [ordem quando mais de um erro ocorre].
- **Efeito sobre o estado:** [garantias em caso de rejeição].

## 11. Instruções de geração

### 11.1 Arquivos esperados

```text
[árvore de pastas e arquivos]
```

Indique se a árvore é obrigatória ou ilustrativa e quais arquivos adicionais são permitidos: [regra].

### 11.2 Inicialização

- **Comando exato:** `[comando]`.
- **Pasta de trabalho:** `[pasta]`.
- **Objeto/ponto de entrada:** `[nome e caminho]`.
- **Configuração necessária:** [variáveis e valores de teste, ou nenhuma].

### 11.3 Restrições de geração

1. Entregar arquivos completos, sem trechos omitidos.
2. Implementar os comportamentos incluídos e respeitar o escopo excluído.
3. Preservar nomes, contratos e mensagens especificados.
4. Respeitar as dependências e versões compatíveis da seção 4.
5. Produzir somente os arquivos autorizados pela seção 11.1.
6. Aplicar a política de dúvidas definida antes da geração: [neste experimento, turno único, sem esclarecimentos; ambiguidades descobertas devem ser registradas como limitação e corrigidas em nova versão].

## 12. Rastreabilidade

| Necessidade | Requisito | Critérios | Regras | Interface | Teste ou inspeção |
|---|---|---|---|---|---|
| [origem] | RF-01 | CA-01.1, CA-01.2 | RN-01 | [operação] | [IDs dos testes] |
| [origem] | RNF-01 | [condição de aprovação] | [regra ou N/A] | [interface ou N/A] | [instrumento] |

## 13. Histórico de versões e revisão

| Versão | Data | Autor | Alteração | Situação da revisão |
|---|---|---|---|---|
| [versão] | [data] | [nome] | [mudança] | [parecer e evidência] |

<!-- Registro do modelo: 1.1 acrescenta origem dos requisitos, explicita
compatibilidade de versões, admite seções não aplicáveis justificadas e
separa revisão comprovada de revisão pendente. Não foi objeto de nova
rodada de geração nesta entrega. -->
