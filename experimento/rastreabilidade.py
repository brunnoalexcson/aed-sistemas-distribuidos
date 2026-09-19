#!/usr/bin/env python3
"""
Verificador de rastreabilidade — apoio à Etapa 5 do processo.

Confere a bijeção entre os critérios de aceitação declarados no documento de
requisitos e os testes da suíte de conformidade:

  - todo critério do documento tem exatamente um teste;
  - todo teste corresponde a um critério existente no documento;
  - a matriz de rastreabilidade (Seção 12) cita todos os requisitos.

Sem essa conferência, a taxa de conformidade pode ser calculada sobre uma base
incompleta sem que ninguém perceba.

Uso:
    python experimento/rastreabilidade.py [--caso biblioteca]
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PADRAO_TESTE = re.compile(r"def (test_ca_(\d+)_(\d+)_\w+)\(")


def criterios_do_documento(caso: str) -> list[str]:
    doc = next((RAIZ / "casos" / caso).glob("requisitos-*.md"))
    return re.findall(r"\*\*(CA-\d+\.\d+)\*\*", doc.read_text(encoding="utf-8"))


def criterios_dos_testes(caso: str) -> dict[str, list[str]]:
    """Preserva todas as ocorrências, inclusive definições duplicadas."""
    encontrados: dict[str, list[str]] = {}
    for arquivo in sorted((RAIZ / "casos" / caso / "testes").glob("test_*.py")):
        arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
        for no in ast.walk(arvore):
            if not isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            m = PADRAO_TESTE.match(f"def {no.name}(")
            if m:
                nome, rf, seq = m.groups()
                encontrados.setdefault(f"CA-{int(rf):02d}.{int(seq)}", []).append(
                    f"{arquivo.name}:{no.lineno}::{nome}")
    return encontrados


def requisitos_fora_da_matriz(caso: str) -> list[str]:
    doc = next((RAIZ / "casos" / caso).glob("requisitos-*.md")).read_text(encoding="utf-8")
    declarados = set(re.findall(r"^### (RF-\d+)", doc, re.MULTILINE))
    matriz = doc[doc.index("## 12."):]
    return sorted(rf for rf in declarados if rf not in matriz)


def problemas_do_caso(caso: str) -> dict[str, list[str]]:
    documento = criterios_do_documento(caso)
    testes = criterios_dos_testes(caso)

    duplicados = sorted({ca for ca in documento if documento.count(ca) > 1})
    sem_teste = sorted(set(documento) - set(testes))
    sem_criterio = sorted(set(testes) - set(documento))
    fora_da_matriz = requisitos_fora_da_matriz(caso)

    return {
        "critérios duplicados no documento": duplicados,
        "critérios com múltiplos testes": [ca for ca, nomes in testes.items() if len(nomes) != 1],
        "critérios sem teste correspondente": sem_teste,
        "testes sem critério no documento": sem_criterio,
        "requisitos ausentes da matriz (Seção 12)": fora_da_matriz,
    }


def verificar(caso: str) -> bool:
    print(f"caso ................. {caso}")
    print(f"critérios no documento {len(criterios_do_documento(caso))}")
    print(f"testes na suíte ...... {sum(map(len, criterios_dos_testes(caso).values()))}")

    problemas = False
    for rotulo, itens in problemas_do_caso(caso).items():
        if itens:
            problemas = True
            print(f"\nPROBLEMA — {rotulo}:")
            for item in itens:
                print(f"  {item}")

    if not problemas:
        print("\nOK — bijeção critério <-> teste íntegra, matriz completa.")
    return not problemas


def main() -> int:
    ap = argparse.ArgumentParser(description="Verifica a rastreabilidade critério <-> teste.")
    ap.add_argument("--caso", help="caso específico; omitido, verifica todos")
    args = ap.parse_args()

    casos = [args.caso] if args.caso else sorted(
        d.name for d in (RAIZ / "casos").iterdir() if d.is_dir())

    tudo_ok = True
    for i, caso in enumerate(casos):
        if i:
            print()
        tudo_ok &= verificar(caso)
    return 0 if tudo_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
