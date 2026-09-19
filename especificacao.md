Artefato: modelo (template) do documento de requisitos, em Markdown.

### Template (modelo-requisitos.md)
O documento em branco, com as seções, campos e marcações para preencher

### Instruções de preenchimento 
Manual que explica como preencher cada seção do template

### Documento preenchido (ex: requisitos-biblioteca.md)
O template preenchido para um sistema concreto

O artefato é o markdown, mas o markdown vazio e reutilizável, não o preenchido para um sistema específico. O preenchido é a prova de que o template funciona.

O que será avaliado é o processo e o template, que devem ser genéricos, aplicáveis a qualquer sistema. O software é apenas o objeto de teste do experimento.

Existem duas implicações práticas:
1. É necessário escolher um (ou mais) sistemas para testar. Os requisitos que serão analisados são os requisitos desse sistema escolhido. O critério de escolha deve ser a testabilidade. Exemplos:
- API REST de gestão de bibliotecas (livros, usuários, empréstimos, devoluções, multas)
- API de controle de estoque (produtos, entradas, saídas, alerta de estoque mínimo)
- Sistema de agendamento de consultas (horários, conflitos, cancelamento)

Uma API REST em Python com FastAPI é uma boa escolha porque dá para testar tudo automaticamente com ``pytest``, que torna a medição da conformidade objetiva. O tamanho ideal para o prazo é algo entre 8 a 12 requisitos funcionais, gerando 30 a 45 critérios de aceitação. 

2. Testar o template em dois sistemas diferentes fortalece muito o relatório, porque demonstra que o template é genérico e não foi ajustado para um único caso

## Entregável 1 - Processo
Definir as etapas que qualquer pessoa segue para sair de uma ideia de sistema até um documento pronto para a LLM, e depois até a verificação. Um processo bem descrito tem, para cada etapa: objetivo, entradas, atividades, saídas e critério de saída (o que precisa estar pronto para avançar). Proponho oito etapas.

Etapa 1 — Elicitação. Objetivo: entender o problema. Entrada: a ideia ou demanda do sistema. Atividades: identificar o objetivo do sistema, os usuários (atores), as funcionalidades desejadas e as restrições. Técnicas possíveis: entrevista simulada, brainstorming, análise de sistemas similares. Saída: lista bruta de necessidades em linguagem livre. Critério de saída: objetivo do sistema escrito em uma frase e todos os atores identificados.

Etapa 2 — Análise e modelagem. Objetivo: transformar necessidades soltas em estrutura. Atividades: identificar as entidades do domínio (ex.: Livro, Usuário, Empréstimo) e seus atributos, identificar as regras de negócio (ex.: "um usuário não pode ter mais de 3 empréstimos ativos"), separar o que é funcional do que é não funcional, definir o escopo (o que está dentro e o que está explicitamente fora). Saída: modelo de dados, lista de regras de negócio, escopo delimitado. Critério de saída: toda necessidade da Etapa 1 foi classificada ou descartada com justificativa.

Etapa 3 — Especificação. Objetivo: preencher o template. Atividades: escrever cada requisito funcional com identificador único, cada regra de negócio, cada requisito não funcional de forma mensurável, os contratos de interface (endpoints, formatos JSON exatos, códigos HTTP) e, o mais importante, os critérios de aceitação de cada requisito no formato Dado/Quando/Então. Saída: documento de requisitos preenchido.

Etapa 4 — Validação do documento. Objetivo: garantir a qualidade antes de gastar tempo com a LLM. Atividades: revisão por um membro que não escreveu o documento, usando um checklist baseado nas características de bons requisitos da norma ISO/IEC/IEEE 29148 (necessário, não ambíguo, completo, consistente, atômico, verificável, rastreável). Saída: documento revisado e checklist assinado. Critério de saída: 100% dos itens do checklist atendidos. Esta etapa é o que diferencia um processo de engenharia de "escrever qualquer coisa e ver no que dá".

Etapa 5 — Derivação dos testes de conformidade. Objetivo: construir o instrumento de medição antes de gerar o código. Atividades: transformar cada critério de aceitação em um caso de teste automatizado (ou, se impossível, em um item de checklist de inspeção manual). Saída: suíte de testes e planilha de rastreabilidade (critério → teste). Ponto metodológico crucial: os testes precisam nascer do documento, e não do código gerado. Se vocês escreverem os testes depois de olhar o código, contaminam a medição e o experimento perde validade.

Etapa 6 — Geração do código. Atividades: enviar o documento à LLM com um prompt fixo e padronizado (o mesmo em todas as execuções), em sessão nova, sem correções manuais e sem conversa adicional. Saída: código gerado, salvo exatamente como veio, com registro de modelo, versão, data e hora.

Etapa 7 — Verificação da conformidade. Atividades: executar a suíte de testes sobre o código gerado, sem alterar nada no código (se ele não roda, os critérios dependentes contam como falha), registrar aprovados e reprovados. Saída: taxa de conformidade da execução.

Etapa 8 — Análise e melhoria. Atividades: classificar cada falha pela causa (ambiguidade no documento, informação ausente no template, erro da LLM apesar de o documento estar claro) e, quando a causa é o documento ou o template, corrigir o template ou as instruções (não apenas o documento daquele sistema) e reexecutar. Saída: nova versão do template (v1 → v2) e registro das mudanças. É aqui que aparece a exigência de "design iterativo com ciclos de teste, análise e melhoria".

## Entregável 2 - Artefato (template em Markdown)

O template precisa atacar as causas conhecidas de não conformidade em código gerado por LLM. As principais são: a LLM escolhe sozinha tudo que não foi especificado (tecnologia, nome de campo, formato de resposta, código de erro), preenche lacunas com suposições e ignora requisitos vagos. Cada seção do template existe para eliminar uma dessas fontes de erro. Uma estrutura adequada:

# Documento de Especificação de Requisitos — [Nome do Sistema]

## 0. Metadados
| Campo | Valor |
|---|---|
| Versão do documento | |
| Versão do template | 1.0 |
| Autores | |
| Data | |

## 1. Objetivo do sistema
<!-- Uma frase: o sistema permite que [ator] faça [ação] para [benefício]. -->

## 2. Escopo
### 2.1 Incluído
### 2.2 Explicitamente excluído
<!-- Liste o que a LLM NÃO deve implementar (autenticação, front-end etc.). -->

## 3. Glossário
| Termo | Definição |
|---|---|

## 4. Stack técnica e restrições de implementação
| Item | Especificação obrigatória |
|---|---|
| Linguagem / versão | |
| Framework | |
| Persistência | |
| Bibliotecas permitidas | |
| Bibliotecas proibidas | |

## 5. Modelo de dados
### 5.1 Entidade: [Nome]
| Atributo | Tipo | Obrigatório | Restrições/validação | Exemplo |
|---|---|---|---|---|

## 6. Regras de negócio
| ID | Regra | Requisitos afetados |
|---|---|---|
| RN-01 | | |

## 7. Requisitos funcionais
### RF-01 — [Título curto]
- **Descrição:** O sistema deve ...
- **Ator:**
- **Prioridade:** Must | Should | Could
- **Entrada:**
- **Processamento:**
- **Saída:**
- **Regras relacionadas:** RN-xx
- **Critérios de aceitação:**
  - **CA-01.1** Dado ..., quando ..., então ...
  - **CA-01.2** Dado ..., quando ..., então ...

## 8. Contratos de interface
### 8.1 [MÉTODO] /caminho
- **Requisito:** RF-xx
- **Corpo da requisição (JSON exato):**
- **Resposta de sucesso (status + JSON exato):**
- **Respostas de erro (status + mensagem exata):**

## 9. Requisitos não funcionais
| ID | Categoria | Requisito mensurável | Como verificar |
|---|---|---|---|
| RNF-01 | | | |

## 10. Tratamento de erros (padrão global)

## 11. Instruções de geração para a LLM
- Estrutura de pastas e arquivos esperada
- Formato da entrega (arquivos completos, sem trechos omitidos)
- Proibição de funcionalidades não especificadas
- Proibição de alterar nomes de campos, rotas e mensagens

## 12. Matriz de rastreabilidade
| Requisito | Critérios de aceitação | Regras | Endpoint | Caso de teste |
|---|---|---|---|---|

Para dar uma ideia do nível de precisão que o template exige, veja um requisito preenchido corretamente para a biblioteca:
### RF-04 — Registrar empréstimo
- **Descrição:** O sistema deve registrar o empréstimo de um livro disponível a um usuário ativo.
- **Entrada:** `usuario_id` (inteiro), `livro_id` (inteiro)
- **Processamento:** verificar RN-01 e RN-02; marcar o livro como `emprestado`; definir `data_devolucao_prevista` = data atual + 14 dias.
- **Saída:** objeto Emprestimo com status HTTP 201.
- **Regras relacionadas:** RN-01, RN-02
- **Critérios de aceitação:**
  - **CA-04.1** Dado um livro com status `disponivel` e um usuário com 0 empréstimos ativos, quando `POST /emprestimos` for chamado, então a resposta deve ter status 201 e o livro passar a ter status `emprestado`.
  - **CA-04.2** Dado um usuário com 3 empréstimos ativos, quando `POST /emprestimos` for chamado, então a resposta deve ter status 422 e corpo `{"erro": "Limite de empréstimos atingido"}`.
  - **CA-04.3** Dado um livro com status `emprestado`, quando `POST /emprestimos` for chamado, então a resposta deve ter status 409 e corpo `{"erro": "Livro indisponível"}`.

  ## Entregável 03 - Instrução de preenchimento

  É o manual do template. Um template sem instruções é preenchido de forma diferente por cada pessoa, e aí a conformidade vira sorte. As instruções devem ter duas partes.

Regras gerais de redação, válidas para o documento inteiro:

Todo requisito começa com "O sistema deve" (obrigatório) ou "O sistema pode" (opcional); nunca "seria bom", "idealmente".
Um requisito por identificador (atomicidade): se a frase tem "e" ligando duas ações, divida.
Palavras proibidas por serem não verificáveis: rápido, fácil, amigável, intuitivo, adequado, eficiente, robusto, etc., entre outros. Substitua por números com unidade ("responder em até 500 ms").
Todo nome técnico (campo, rota, status, mensagem) vai entre crases e é escrito exatamente como deve aparecer no código.
Todo requisito funcional tem no mínimo um critério de aceitação de sucesso e um de falha.
Todo critério de aceitação segue Dado/Quando/Então e tem resultado observável (status, valor, mensagem).
Nada é deixado implícito: se não está escrito, a LLM vai inventar.

Instruções por seção, explicando o propósito de cada uma, o que é obrigatório, erros comuns e um exemplo certo e um errado. Por exemplo, para a Seção 4: "Especifique a versão exata da linguagem e do framework. Errado: 'usar Python'. Certo: 'Python 3.11, FastAPI 0.110, SQLite via SQLAlchemy 2.0'. Motivo: sem isso, a LLM pode gerar em outra linguagem ou com bibliotecas incompatíveis com a suíte de testes." Cada seção do template recebe um bloco assim.

Vale incluir no final o checklist de validação usado na Etapa 4 do processo (ex.: "todo RF possui CA de falha?", "existe alguma palavra da lista proibida?", "todos os endpoints têm todas as respostas de erro definidas?").

## Entregável 04 - Relatório técnico com testes de hipótese

Esta é a parte que mais pesa, e onde "método científico" precisa ser levado ao pé da letra.

6.1 Métrica de conformidade

Defina a unidade de medida como o critério de aceitação, não o requisito, porque é mais granular e objetivo. A fórmula básica:

Conformidade (%) = (critérios de aceitação atendidos ÷ total de critérios de aceitação) × 100

Cada critério é binário: passou ou falhou. Se quiserem sofisticar, podem usar pesos por prioridade (Must = 3, Should = 2, Could = 1), mas justifiquem no relatório. Requisitos não funcionais que não dão para testar automaticamente (ex.: "o código deve seguir a estrutura de pastas X") entram por checklist de inspeção, com critério binário definido antes.

Regras de medição que precisam estar escritas: o código é avaliado exatamente como a LLM entregou; se não compila ou não sobe, todos os critérios dependentes falham; nenhum membro corrige nada.

6.2 Hipóteses
H₀ (nula): a conformidade média do código gerado a partir do template é menor ou igual a 85% (μ ≤ 85).
H₁ (alternativa): a conformidade média é superior a 85% (μ > 85).

É um teste unilateral. Vocês querem rejeitar H₀, e o nível de significância usual é α = 0,05.

6.3 Desenho do experimento

Variável independente: o documento de requisitos no formato do template. Variável dependente: a taxa de conformidade. Variáveis controladas: prompt (idêntico em todas as execuções), modelo e versão da LLM, idioma, sessão nova a cada execução, documento idêntico.

LLMs não são determinísticas, então uma única execução não prova nada. Façam no mínimo 10 execuções independentes por LLM, idealmente com duas ou três LLMs diferentes (ex.: ChatGPT, Claude, Gemini), o que mostra que o resultado não depende de um fornecedor.

Um reforço opcional, mas muito valorizado: um grupo de controle, em que o mesmo sistema é descrito em texto livre (um parágrafo informal) e também passa por 10 gerações. Aí vocês mostram não só que o template passa de 85%, mas que ele é responsável pela melhora.

6.4 Análise estatística

Com as 10 taxas de cada LLM, calculem média, desvio-padrão, mínimo, máximo e intervalo de confiança de 95%. Apliquem o teste t para uma amostra contra o valor 85. Se os dados não parecerem normais (teste de Shapiro-Wilk com p < 0,05), usem o teste de Wilcoxon para uma amostra no lugar. Um exemplo ilustrativo de como o resultado aparece no relatório: média 91,2%, desvio 4,1, n = 10, resulta em t = (91,2 − 85) ÷ (4,1 ÷ √10) ≈ 4,78, com 9 graus de liberdade e p < 0,001, portanto H₀ é rejeitada. Esses números são só um exemplo de formato; os de vocês virão das execuções reais, e tudo isso se calcula em Python com scipy.stats.ttest_1samp ou até em planilha.

6.5 Estrutura do relatório

Uma estrutura adequada: Introdução (problema e objetivo); Fundamentação teórica (engenharia de requisitos, ISO/IEC/IEEE 29148, LLMs em geração de código, BDD); Hipótese; Método (objeto de estudo, LLMs usadas, procedimento, variáveis, instrumentos, métrica, análise estatística); Resultados (tabela com cada execução, estatísticas, teste, gráfico); Discussão (análise das falhas por categoria, qual requisito mais falhou e por quê); Ameaças à validade; Melhorias propostas no processo e no template; Conclusão; Referências; Apêndices (documento preenchido, prompt usado, códigos gerados, suíte de testes).

As ameaças à validade mostram maturidade e costumam ser o que separa nota boa de nota máxima. Exemplos: o sistema testado é pequeno e pode não representar sistemas reais (validade externa); o grupo que escreveu o documento também escreveu os testes (mitigação: testes derivados só dos critérios e escritos antes da geração); versões das LLMs mudam com o tempo (mitigação: registrar data e versão); amostra pequena.

Se a primeira rodada ficar abaixo de 85%, não é fracasso: é exatamente o ciclo iterativo pedido. Registrem a v1, analisem as falhas, melhorem o template, rodem a v2 e reportem as duas. Um relatório que mostra "v1 teve 78%, identificamos que faltava a seção de mensagens de erro, a v2 teve 93%" é mais forte cientificamente do que um que simplesmente acertou de primeira.