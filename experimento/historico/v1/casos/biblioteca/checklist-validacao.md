# Checklist de Validação — Sistema de Gestão de Biblioteca

**Etapa 4 do processo** (Entregável 1) · **Documento avaliado:** `requisitos-biblioteca.md` v1.0
**Revisor:** Revisor designado do grupo (não participou da redação — exigência de independência do processo)
**Data da revisão:** 2026-09-19

> Critério de saída da Etapa 4: **100% dos itens atendidos**. Um único item reprovado
> devolve o documento à Etapa 3. Este checklist é o mesmo definido na Parte III do
> Entregável 3 (instruções de preenchimento).

## Completude

- [x] Nenhuma seção obrigatória está vazia ou contém placeholder (`[ ]`, "a definir", "TBD").
- [x] A Seção 2.2 (escopo excluído) lista ao menos um item.
- [x] Todo campo de estado do modelo de dados tem enumeração completa e valor inicial.
- [x] Todo endpoint da Seção 8 tem corpo de requisição, resposta de sucesso e todas as respostas de erro.
- [x] Existe resposta `404` especificada para toda operação que recebe um identificador.
- [x] A Seção 10 define formato de erro único e regra de precedência.
- [x] A Seção 11 define a árvore de arquivos e o ponto de entrada exato.

## Qualidade dos requisitos (ISO/IEC/IEEE 29148)

- [x] **Necessário:** todo requisito rastreia a uma necessidade da Etapa 1 ou a uma regra de negócio.
- [x] **Não ambíguo:** nenhuma palavra da lista proibida aparece no documento (verificado por busca textual — ver evidência abaixo).
- [x] **Atômico:** nenhum requisito tem "e" ligando duas ações distintas.
- [x] **Verificável:** todo critério de aceitação tem resultado observável (status, valor ou mensagem).
- [x] **Consistente:** nenhum requisito contradiz outro; nomes de campo idênticos em todas as seções.
- [x] **Rastreável:** todo requisito tem ID único e aparece na matriz da Seção 12.

## Critérios de aceitação

- [x] Todo RF tem no mínimo um CA de sucesso e um de falha.
- [x] Todo CA segue o formato Dado / Quando / Então.
- [x] Todo CA tem estado inicial concreto (o "dado" não é genérico).
- [x] A numeração dos CAs segue `CA-<nº do RF>.<sequencial>`.
- [x] Nenhum CA descreve implementação interna em vez de comportamento observável.

## Precisão técnica

- [x] Todo nome técnico está entre crases e escrito como aparecerá no código.
- [x] Toda mensagem de erro está escrita literalmente, entre crases.
- [x] Todo JSON de exemplo é JSON válido, com valores reais (não tipos).
- [x] A Seção 4 declara linguagem, framework, persistência e bibliotecas proibidas.

## Rastreabilidade

- [x] A matriz da Seção 12 contém todos os RF do documento.
- [x] Toda regra RN-xx citada em algum requisito existe na Seção 6.
- [x] Todo RF citado na Seção 6 existe na Seção 7.

---

## Evidências da revisão

| Verificação | Instrumento | Resultado |
|---|---|---|
| Ausência de palavras proibidas | busca textual no documento | 0 ocorrências |
| Bijeção critério ↔ teste | `experimento/rastreabilidade.py --caso biblioteca` | OK — 40 critérios, 40 testes |
| Requisitos na matriz da Seção 12 | `experimento/rastreabilidade.py --caso biblioteca` | OK — 10 requisitos, nenhum ausente |
| Documento implementável sem contradição | implementação de referência medida pela suíte | 40/40 critérios atendidos |

> A última linha merece nota: antes de gastar execuções de LLM, uma implementação de
> referência escrita à mão foi submetida à suíte de conformidade. Atingir 40/40
> demonstra que o documento é **internamente consistente** — nenhum par de critérios
> se contradiz e nenhum critério é impossível de satisfazer. Se essa implementação
> não chegasse a 100%, o defeito estaria no documento ou na suíte, não na LLM.

**Resultado da validação:** ☑ Aprovado ☐ Reprovado

**Revisor:** Revisor designado do grupo — **Data:** 2026-09-19
