# Prompt padrão do experimento

Este prompt é **variável controlada**: seu texto é idêntico em todas as execuções,
de todos os braços. As únicas partes que mudam entre execuções são os campos
`{DIRETORIO}` e `{ESPECIFICACAO}`, substituídos por `experimento/runner.py`.

Alterar qualquer palavra deste arquivo invalida a comparação entre execuções já
realizadas e as seguintes. Se for necessário alterá-lo, a mudança gera uma nova
versão do prompt e toda a rodada é reexecutada.

---

## Texto do prompt

```
Implemente o sistema de software descrito na especificação abaixo.

Condições da tarefa:
1. Escreva todos os arquivos do sistema dentro do diretório {DIRETORIO}. Não crie
   nem modifique nenhum arquivo fora desse diretório.
2. Não leia nenhum arquivo do repositório. A especificação abaixo é a única fonte
   de informação sobre o sistema.
3. Entregue arquivos completos e funcionais, sem trechos omitidos e sem
   marcadores de continuação.
4. Não escreva testes automatizados.
5. Não peça esclarecimentos e não faça perguntas: implemente a partir do que está
   escrito abaixo.
6. Ao terminar, responda apenas com a lista dos arquivos que você criou.

ESPECIFICAÇÃO:

{ESPECIFICACAO}
```

---

## Justificativa de cada condição

| Condição | Por que está no prompt |
|---|---|
| 1 | Isola a execução; sem isso, execuções concorrentes se sobrescrevem. |
| 2 | Impede que a LLM leia a suíte de testes ou outras execuções — é a principal ameaça à validade num ambiente de arquivos compartilhado. |
| 3 | Elimina entregas parciais, que impediriam a aplicação de subir por motivo alheio ao mérito da especificação. |
| 4 | Testes escritos pela própria LLM não são usados na medição; pedir que os escreva só consumiria a execução. |
| 5 | Garante execução em turno único, sem conversa adicional (Etapa 6 do processo). |
| 6 | Padroniza a saída e evita que a LLM gaste a resposta explicando o código. |

**Nota deliberada:** o prompt **não** contém nenhuma instrução sobre qualidade,
tecnologia, estrutura de arquivos ou tratamento de erros. Tudo isso é papel da
especificação. Se o prompt carregasse essas instruções, o experimento estaria
medindo o prompt, e não o documento de requisitos — que é a variável
independente sob teste.
