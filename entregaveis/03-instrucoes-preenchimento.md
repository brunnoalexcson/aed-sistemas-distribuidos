# Entregável 3 — Instruções de preenchimento

**Versão:** 1.1 · **Modelo:** [02-modelo-requisitos.md](02-modelo-requisitos.md) · **Data:** 2026-09-19

Revisão posterior ao experimento. As [instruções 1.0](../experimento/historico/v1/entregaveis/03-instrucoes-preenchimento.md) foram preservadas; a conformidade medida refere-se aos documentos históricos.

## 1. Preparação e regras gerais

Copie o modelo para um documento do sistema e preencha todas as seções. Remova as instruções editoriais quando terminar. Não deixe marcadores como `[nome]` ou `TBD` em um documento aprovado. Uma seção não aplicável deve conter justificativa, em vez de informação inventada.

- Use **“O sistema deve”** para obrigações e **“O sistema pode”** para opções explicitamente fora da métrica obrigatória. Defina o denominador da avaliação antes da geração; não exclua requisitos depois de observar falhas.
- Escreva um comportamento por requisito. A conjunção “e” é um indício para revisão, não prova automática de falta de atomicidade: campos que compõem a mesma operação podem permanecer juntos.
- Substitua adjetivos vagos por propriedades verificáveis. “Rápido” precisa de carga e tempo; “arquivo `app/main.py` presente” é uma condição binária válida, sem número artificial.
- Use os mesmos nomes técnicos em todo o documento e destaque-os com crases. Mensagens comparadas literalmente devem ter grafia e pontuação exatas.
- Para cada RF, descreva sucesso e erro quando houver caminho de erro. Se não houver, justifique e inclua um caso limite, como lista vazia. Não invente erros apenas para cumprir o checklist.
- Escreva CAs no formato Dado/Quando/Então: estado inicial, ação e resultado observável. Um CA deve ser atendido somente se todas as suas condições forem verificadas.
- Resolva lacunas antes da geração. A especificação reduz decisões implícitas, mas não elimina a possibilidade de erros de implementação da LLM.

## 2. Como preencher cada seção

### 0 — Metadados

Identifique sistema, versão, autores, revisor, data e origem das necessidades. **Certo:** “Revisor: pendente; status: em revisão” quando não ocorreu revisão. **Errado:** “aprovado por revisor do grupo” sem responsável ou evidência. Atribuição genérica não comprova revisão independente.

### 1 — Objetivo e atores

Descreva o benefício e quem utiliza o sistema; prefira uma frase clara para o objetivo. **Certo:** “O sistema permite que bibliotecários registrem empréstimos para controlar a circulação do acervo.” **Errado:** “Sistema moderno e completo.” Liste atores com papéis distintos; uma descrição longa exige revisão, não divisão automática do produto.

### 2 — Escopo

Liste capacidades incluídas e exclusões que limitem expectativas. **Certo:** “Inclui empréstimos; exclui reservas e autenticação nesta versão.” **Errado:** “Fazer tudo de uma biblioteca.” A exclusão deve ser compatível com os requisitos e com a finalidade do sistema.

### 3 — Glossário

Defina termos com significado específico. **Certo:** “Empréstimo ativo: registro sem devolução concluída.” **Errado:** “Empréstimo: um empréstimo.” Evite sinônimos que aparentem entidades diferentes e verifique conceitos do domínio, como obra versus exemplar.

### 4 — Tecnologia e ambiente

Especifique bibliotecas e versões exatas ou faixas compatíveis justificadas. Congele as versões efetivamente instaladas no ambiente do experimento. **Certo:** “Pydantic v2; versões instaladas registradas no manifesto.” **Errado:** exigir uma versão indisponível ou escrever apenas “usar Python”. Declare persistência, bibliotecas permitidas e restrições a dependências transitivas. Uma faixa na especificação e versões exatas no ambiente cumprem papéis distintos.

### 5 — Dados

Para cada campo, informe tipo, obrigatoriedade, validações, valor inicial e exemplo. Identificadores precisam de regra de geração; estados precisam de enumeração e transições; datas e valores monetários precisam de convenções. **Certo:** “`status`: `disponivel` ou `emprestado`, inicialmente `disponivel`.” **Errado:** “O livro possui status.” Esclareça o comportamento quando um recurso relacionado for excluído.

### 6 — Regras de negócio

Escreva condição e consequência verificáveis e relacione os requisitos afetados. **Certo:** “RN-01: usuário com três empréstimos ativos não pode registrar outro.” **Errado:** “Usuários têm restrições.” Toda regra deve ter origem identificável e toda referência deve apontar para um ID existente.

### 7 — Requisitos funcionais e CAs

Preencha descrição, origem, ator, prioridade, entradas, processamento, saída e regras relacionadas. Use `RF-01`, `RF-02` e `CA-01.1`, `CA-01.2`, sem reutilizar IDs.

**Certo:** “Dado um usuário com três empréstimos ativos, quando registrar outro empréstimo, então retornar `422` com `{"erro": "Limite de empréstimos atingido"}`.” **Errado:** “Então tratar o erro corretamente.” Especifique também o estado final quando ele integrar o comportamento exigido. Os testes devem observar as condições declaradas, não apenas o status HTTP.

### 8 — Contratos de interface

Para APIs, detalhe método, rota, parâmetros, corpo, códigos HTTP e respostas literais. Para outros sistemas, use comandos, ações ou mensagens com entradas e saídas equivalentes. **Certo:** `GET /livros/999` retorna `404` e `{"erro": "Livro não encontrado"}` quando o ID não existe. **Errado:** “Consultar livro retorna um objeto.” Use JSON válido com valores reais; descreva separadamente os tipos. Operações sem corpo devem dizer “sem corpo”.

### 9 — Requisitos não funcionais

Informe a condição de aprovação e o instrumento. **Certo:** “Consultar a lista com 200 livros deve levar no máximo 500 ms, medidos no cliente HTTP local.” **Errado:** “A consulta deve ser eficiente.” Registre condições de carga, repetições e ambiente. Inspeções de arquivos e dependências são binárias. Não confunda bom resultado funcional com atendimento automático dos RNFs.

### 10 — Erros globais

Defina formato, casos de validação, precedência e efeitos sobre o estado. **Certo:** “Validar corpo antes de consultar o recurso; uma rejeição não altera o saldo.” **Errado:** “Tratar erros conforme boas práticas.” Verifique consistência com as tabelas específicas das operações.

### 11 — Geração e inicialização

Defina árvore obrigatória ou ilustrativa, arquivos adicionais permitidos, comando, diretório e objeto de entrada. **Certo:** “Executar `uvicorn app.main:app` na raiz do projeto.” **Errado:** “Gerar API funcional.” Em comparação experimental, um contrato de execução comum deve ser fornecido aos grupos quando a intenção for isolar o efeito da organização textual. Alterar o prompt ou o contrato cria uma nova rodada.

### 12 — Rastreabilidade

Relacione necessidades, requisitos, CAs, regras, interfaces e instrumentos. Complete os nomes dos testes na etapa 5. **Certo:** “CA-01.1 → `test_ca_01_1_cadastro_valido`.” **Errado:** “Testado pelo pytest.” Execute o verificador e revise as asserções: IDs correspondentes não garantem que o teste cubra todo o enunciado. Inclua RNFs por teste ou inspeção.

### 13 — Versões

Registre mudanças, autoria, data e situação da revisão. **Certo:** “1.1: esclarecida precedência; avaliação em nova rodada pendente.” **Errado:** manter “1.0” depois de mudar o documento já utilizado. Preserve cada versão avaliada e seus prompts; resultados anteriores não validam automaticamente a versão nova.

## 3. Checklist para a revisão

Marque cada item como aprovado, reprovado ou não aplicável com justificativa. A aprovação final exige evidência de revisão por pessoa distinta do autor e ausência de pendências nos itens aplicáveis.

| Item | Verificação | Resultado e evidência |
|---|---|---|
| C01 | Metadados e origens preenchidos; revisão identificada sem atribuições fictícias | [preencher] |
| C02 | Seções completas ou não aplicáveis justificadas; sem placeholders | [preencher] |
| C03 | Escopo incluído/excluído consistente com necessidades e requisitos | [preencher] |
| C04 | Vocabulário consistente e propriedades verificáveis | [preencher] |
| C05 | Requisitos com IDs únicos e comportamentos delimitados | [preencher] |
| C06 | Sucesso, falha aplicável e limites representados em CAs | [preencher] |
| C07 | CAs com Dado/Quando/Então e resultados observáveis | [preencher] |
| C08 | Dados, estados, datas e validações definidos | [preencher] |
| C09 | Contratos com respostas e exemplos válidos, incluindo recursos inexistentes quando aplicável | [preencher] |
| C10 | Erros globais e precedência consistentes | [preencher] |
| C11 | Ambiente compatível, dependências e inicialização definidos | [preencher] |
| C12 | RNFs com instrumentos e limites de aprovação | [preencher] |
| C13 | Rastreabilidade completa, sem testes duplicados ou critérios órfãos | [preencher] |
| C14 | Asserções cobrem as condições dos CAs; revisão sem consultar saídas da geração | [preencher] |
| C15 | Versões preservadas; alterações posteriores não atribuídas à rodada anterior | [preencher] |

**Parecer:** [aprovado/reprovado/pendente] · **Revisor:** [nome] · **Data:** [data] · **Evidências:** [referências].

## 4. Separação entre prescrição e evidência

Estas instruções descrevem como conduzir novas aplicações do processo. Não comprovam que todas as etapas foram realizadas no experimento histórico. Registre ausência de logs de geração, revisão independente ou metadados como limitação. Nunca substitua um resultado observado por um valor esperado para atingir a meta da atividade.
