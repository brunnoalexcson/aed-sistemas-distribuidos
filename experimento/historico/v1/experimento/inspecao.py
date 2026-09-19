#!/usr/bin/env python3
"""
Inspeção dos requisitos não funcionais estruturais — apoio à Etapa 7.

Alguns RNF não são observáveis pela interface HTTP e por isso não podem virar
teste de integração. Eles são verificados aqui, por inspeção automatizada de
critério BINÁRIO, com a regra de decisão fixada ANTES das execuções (exigência
da Etapa 5 do processo):

  RNF-01  Estrutura ...... o conjunto de arquivos é exatamente
                           {app/__init__.py, app/main.py, app/models.py,
                            app/storage.py}. Arquivo a mais ou a menos reprova.
  RNF-02  Ponto de entrada  app/main.py atribui a um nome `app` uma instância
                           de FastAPI, permitindo `uvicorn app.main:app`.
  RNF-03  Dependências .... nenhum módulo importado fora de {fastapi, pydantic,
                           uvicorn}, da biblioteca padrão e do próprio pacote.

Estes resultados são reportados SEPARADAMENTE da conformidade funcional; não
entram no cálculo da taxa de conformidade nem no teste de hipótese.

Uso:
    python experimento/inspecao.py --run <dir>
    python experimento/inspecao.py --todos
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RESULTADOS = RAIZ / "experimento" / "resultados"

ESTRUTURA_ESPERADA = {"app/__init__.py", "app/main.py", "app/models.py", "app/storage.py"}
TERCEIROS_PERMITIDOS = {"fastapi", "pydantic", "uvicorn", "starlette", "app"}
PADROES_IGNORADOS = ("__pycache__", ".pyc", ".resultado.json")


def arquivos_relevantes(dir_run: Path) -> set[str]:
    encontrados = set()
    for caminho in dir_run.rglob("*"):
        if not caminho.is_file():
            continue
        relativo = caminho.relative_to(dir_run).as_posix()
        if any(p in relativo for p in PADROES_IGNORADOS):
            continue
        encontrados.add(relativo)
    return encontrados


def modulos_importados(dir_run: Path) -> set[str]:
    """Raízes dos módulos importados por todos os .py da execução."""
    raizes: set[str] = set()
    for arquivo in dir_run.rglob("*.py"):
        if "__pycache__" in arquivo.as_posix():
            continue
        try:
            arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            raizes.add("<arquivo ilegível>")
            continue
        for no in ast.walk(arvore):
            if isinstance(no, ast.Import):
                for alias in no.names:
                    raizes.add(alias.name.split(".")[0])
            elif isinstance(no, ast.ImportFrom):
                if no.level == 0 and no.module:
                    raizes.add(no.module.split(".")[0])
    return raizes


def expoe_app_fastapi(dir_run: Path) -> bool:
    main = dir_run / "app" / "main.py"
    if not main.exists():
        return False
    try:
        arvore = ast.parse(main.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return False
    for no in ast.walk(arvore):
        if not isinstance(no, ast.Assign):
            continue
        nomes = [a.id for a in no.targets if isinstance(a, ast.Name)]
        if "app" not in nomes or not isinstance(no.value, ast.Call):
            continue
        chamada = no.value.func
        nome_chamada = (chamada.id if isinstance(chamada, ast.Name)
                        else chamada.attr if isinstance(chamada, ast.Attribute) else "")
        if nome_chamada == "FastAPI":
            return True
    return False


def inspecionar(dir_run: Path) -> dict:
    encontrados = arquivos_relevantes(dir_run)
    importados = modulos_importados(dir_run)
    externos = sorted(m for m in importados
                      if m not in TERCEIROS_PERMITIDOS and m not in sys.stdlib_module_names)

    return {
        "execucao": dir_run.name,
        "RNF-01": encontrados == ESTRUTURA_ESPERADA,
        "RNF-01_extras": sorted(encontrados - ESTRUTURA_ESPERADA),
        "RNF-01_faltantes": sorted(ESTRUTURA_ESPERADA - encontrados),
        "RNF-02": expoe_app_fastapi(dir_run),
        "RNF-03": not externos,
        "RNF-03_externos": externos,
    }


def imprimir(r: dict) -> None:
    print(f"\nexecução: {r['execucao']}")
    print(f"  RNF-01 estrutura ...... {'OK' if r['RNF-01'] else 'REPROVADO'}")
    if r["RNF-01_extras"]:
        print(f"           arquivos a mais: {', '.join(r['RNF-01_extras'])}")
    if r["RNF-01_faltantes"]:
        print(f"           arquivos ausentes: {', '.join(r['RNF-01_faltantes'])}")
    print(f"  RNF-02 ponto de entrada {'OK' if r['RNF-02'] else 'REPROVADO'}")
    print(f"  RNF-03 dependências ... {'OK' if r['RNF-03'] else 'REPROVADO'}")
    if r["RNF-03_externos"]:
        print(f"           fora da allowlist: {', '.join(r['RNF-03_externos'])}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Inspeciona os RNF estruturais.")
    ap.add_argument("--run", type=Path, help="diretório de uma execução")
    ap.add_argument("--todos", action="store_true", help="todas as execuções de todos os braços")
    args = ap.parse_args()

    if args.run:
        imprimir(inspecionar(args.run.resolve()))
        return 0

    if not args.todos:
        ap.error("informe --run ou --todos")

    linhas = []
    for dir_braco in sorted((RESULTADOS / "execucoes").iterdir()):
        if not dir_braco.is_dir():
            continue
        for dir_run in sorted(d for d in dir_braco.iterdir() if d.is_dir()):
            if not any(dir_run.rglob("*.py")):
                continue
            r = inspecionar(dir_run)
            r["braco"] = dir_braco.name
            linhas.append(r)
            print(f"{dir_braco.name}/{r['execucao']}: "
                  f"RNF-01 {'OK' if r['RNF-01'] else 'X'}  "
                  f"RNF-02 {'OK' if r['RNF-02'] else 'X'}  "
                  f"RNF-03 {'OK' if r['RNF-03'] else 'X'}")

    if linhas:
        destino = RESULTADOS / "inspecao.csv"
        with destino.open("w", newline="", encoding="utf-8") as f:
            campos = ["braco", "execucao", "RNF-01", "RNF-02", "RNF-03",
                      "RNF-01_extras", "RNF-01_faltantes", "RNF-03_externos"]
            escritor = csv.DictWriter(f, fieldnames=campos)
            escritor.writeheader()
            for linha in linhas:
                escritor.writerow({c: (json.dumps(linha[c], ensure_ascii=False)
                                       if isinstance(linha[c], list) else linha[c])
                                   for c in campos})
        print(f"\n{destino} gravado ({len(linhas)} execuções)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
