# AED — Processo e artefato de requisitos para geração por LLM

A atividade está organizada em quatro entregáveis Markdown. A reavaliação das dez implementações de biblioteca associadas ao documento estruturado confirmou **100% de conformidade funcional (40/40 critérios em cada execução)**, acima da meta de 85%.

| Entregável | Documento |
|---|---|
| 1 — Processo | [Processo de análise e especificação](entregaveis/01-processo.md) |
| 2 — Artefato reutilizável | [Modelo de documento de requisitos](entregaveis/02-modelo-requisitos.md) |
| 3 — Manual | [Instruções de preenchimento](entregaveis/03-instrucoes-preenchimento.md) |
| 4 — Experimento | [Relatório técnico completo](entregaveis/04-relatorio-tecnico.md) |

O [enunciado](descricao-aed.md) é a fonte da atividade. `especificacao.md` é o planejamento histórico, não o relatório final.

## O que foi realizado

Foram reavaliados 20 artefatos existentes, identificados historicamente com o alias `sonnet`: dez no grupo A, com documento estruturado, e dez no grupo B, com texto livre. Não houve novas gerações de LLM.

| Grupo | Implementações | Resultado |
|---|---:|---|
| A — Biblioteca, documento estruturado | 10 | Todas com 40/40 CAs; média 100% |
| B — Biblioteca, texto livre | 10 | Todas com 0/40 pelo protocolo; `app/main.py` ausente |
| C — Estoque | 0 | Preparado, não realizado |
| D — Biblioteca, segundo modelo | 0 | Planejado, não realizado |

B não recebeu o mesmo contrato técnico de A e utiliza Flask. Seu zero é incompatibilidade com o protocolo fixo, não demonstração de que todas as funcionalidades estejam incorretas. A comparação é descritiva. O teste t sobre a média populacional ficou inconclusivo por variância zero; a análise binomial adicional é exploratória e tem hipótese própria. Consulte as limitações no relatório.

Os documentos entregues foram revisados para **1.1**. O experimento avalia a especificação baseada no modelo **1.0**, preservado no histórico. As melhorias 1.1 não receberam nova rodada de geração.

## Evidências

- [Dados originais](experimento/resultados/bruto.csv) e [códigos preservados](experimento/resultados/execucoes/).
- [Reavaliação completa](experimento/reavaliacoes/validacao-2026-09-19/), incluindo [CSV](experimento/reavaliacoes/validacao-2026-09-19/bruto.csv), [estatísticas](experimento/reavaliacoes/validacao-2026-09-19/estatisticas.json), [gráficos](experimento/reavaliacoes/validacao-2026-09-19/graficos/) e [logs](experimento/reavaliacoes/validacao-2026-09-19/logs/).
- [Ambiente e hashes](experimento/reavaliacoes/validacao-2026-09-19/ambiente.json) e [auditoria](experimento/reavaliacoes/validacao-2026-09-19/auditoria.json): 219 arquivos protegidos, 11 arquivados, 20 resultados comparados, zero divergências.
- [Versões anteriores dos documentos e instrumentos](experimento/historico/v1/) e [manifesto inicial](experimento/historico/v1/manifesto.json).

Os hashes comprovam preservação desde o início desta revisão. Não comprovam versão exata da LLM, independência das sessões ou revisão humana anterior; essas evidências não constam dos registros disponíveis.

## Como reproduzir

Execute na raiz deste projeto. O ambiente utilizado foi Python 3.14.4 com as versões de [requirements.txt](requirements.txt). Se `.venv` já existe, use-o; para preparar outro ambiente equivalente:

```bash
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Verifique o instrumento e a rastreabilidade:

```bash
.venv/bin/python -B -m pytest experimento/testes -q -p no:cacheprovider
.venv/bin/python -B experimento/rastreabilidade.py
.venv/bin/python -B experimento/runner.py status
```

Reavalie os códigos em uma **pasta nova**. O comando abaixo não gera código; grupos sem implementações são informados e ignorados. A medição requer permissão para abrir portas HTTP em `127.0.0.1`.

```bash
.venv/bin/python -B experimento/runner.py medir --todos --saida experimento/reavaliacoes/minha-reproducao
.venv/bin/python -B experimento/estatistica.py --entrada experimento/reavaliacoes/minha-reproducao/bruto.csv
.venv/bin/python -B experimento/auditar.py --reavaliacao experimento/reavaliacoes/minha-reproducao
```

O runner recusa pasta de saída existente e grava fora dos resultados históricos. Para outra reprodução, escolha outro nome. Sem `--saida`, cria uma pasta com data/hora UTC. Um bloqueio de infraestrutura produz medição inválida e código de saída 2; resolva o ambiente e execute novamente em pasta nova, sem transformar o bloqueio em nota zero.

Para apenas conferir a entrega existente:

```bash
.venv/bin/python -B experimento/auditar.py --reavaliacao experimento/reavaliacoes/validacao-2026-09-19
```

A análise estatística lê os JSON associados ao CSV, valida suas contagens e gera `estatisticas.json`, `estatisticas.md` e dois gráficos PNG. Para executar somente os cálculos, acrescente `--sem-graficos`.

Os comandos antigos de preparação e os prompts C/D permanecem como registro do desenho inicial; não são necessários para reproduzir esta entrega. Não há implantação ou publicação externa nesta atividade.
