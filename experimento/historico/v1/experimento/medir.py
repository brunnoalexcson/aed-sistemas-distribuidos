#!/usr/bin/env python3
"""
Medidor de conformidade — Etapa 7 do processo.

Sobe a aplicação gerada por uma execução da LLM, roda a suíte de conformidade
do caso correspondente contra ela via HTTP e produz o resultado por critério
de aceitação.

REGRAS DE MEDIÇÃO IMPLEMENTADAS (definidas antes de qualquer execução):
  1. O código é avaliado exatamente como a LLM entregou. Este script nunca
     escreve dentro do diretório da execução.
  2. Se a aplicação não sobe, TODOS os critérios contam como não atendidos.
  3. Cada critério é binário: atendido (teste passou) ou não atendido.
  4. Erro de execução do teste (exception, timeout) conta como não atendido.

Uso:
    python experimento/medir.py --run <dir_da_execucao> [--caso biblioteca]
    python experimento/medir.py --run <dir> --json         # só o JSON
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PYTHON = RAIZ / ".venv" / "bin" / "python"
TEMPO_LIMITE_SUBIDA = 30.0
TEMPO_LIMITE_TESTES = 600

# test_ca_07_2_descricao -> CA-07.2 ; test_rnf_04_descricao -> RNF-04
PADRAO_CA = re.compile(r"^test_ca_(\d+)_(\d+)_")
PADRAO_RNF = re.compile(r"^test_rnf_(\d+)_")


def criterios_do_documento(caso: str) -> list[str]:
    """Lê os IDs de critério direto do documento de requisitos (fonte da verdade)."""
    doc = next((RAIZ / "casos" / caso).glob("requisitos-*.md"))
    return re.findall(r"\*\*(CA-\d+\.\d+)\*\*", doc.read_text(encoding="utf-8"))


def porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def pasta_da_aplicacao(dir_run: Path) -> Path | None:
    """
    Localiza a pasta a partir da qual `uvicorn app.main:app` funciona, isto é,
    a que contém `app/main.py`. Tolera a LLM ter aninhado o projeto em uma
    subpasta; NÃO tolera ponto de entrada com outro nome — isso é violação do
    RNF-02 e faz a aplicação não subir, por decisão de medição.
    """
    if (dir_run / "app" / "main.py").exists():
        return dir_run
    for caminho in sorted(dir_run.rglob("app/main.py")):
        return caminho.parent.parent
    return None


def esperar_subida(porta: int, processo: subprocess.Popen) -> bool:
    limite = time.time() + TEMPO_LIMITE_SUBIDA
    while time.time() < limite:
        if processo.poll() is not None:
            return False
        try:
            with socket.create_connection(("127.0.0.1", porta), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def rodar_testes(caso: str, porta: int, arquivo_junit: Path) -> subprocess.CompletedProcess:
    ambiente = dict(os.environ)
    ambiente["BASE_URL"] = f"http://127.0.0.1:{porta}"
    ambiente["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [str(PYTHON), "-m", "pytest", str(RAIZ / "casos" / caso / "testes"),
         "-q", "--no-header", "-p", "no:cacheprovider",
         f"--junitxml={arquivo_junit}"],
        capture_output=True, text=True, timeout=TEMPO_LIMITE_TESTES, env=ambiente,
    )


def ler_junit(arquivo: Path) -> dict[str, bool]:
    """Mapeia nome do teste -> aprovado, a partir do JUnit XML."""
    resultados: dict[str, bool] = {}
    if not arquivo.exists():
        return resultados
    for caso_teste in ET.parse(arquivo).getroot().iter("testcase"):
        nome = caso_teste.get("name", "")
        falhou = any(c.tag in ("failure", "error") for c in caso_teste)
        pulado = any(c.tag == "skipped" for c in caso_teste)
        resultados[nome] = not (falhou or pulado)
    return resultados


def medir(dir_run: Path, caso: str) -> dict:
    esperados = criterios_do_documento(caso)
    resultado = {
        "execucao": dir_run.name,
        "caso": caso,
        "app_subiu": False,
        "motivo_falha_subida": None,
        "criterios": {ca: False for ca in esperados},
        "rnf": {},
        "total_criterios": len(esperados),
        "criterios_atendidos": 0,
        "conformidade": 0.0,
    }

    base = pasta_da_aplicacao(dir_run)
    if base is None:
        resultado["motivo_falha_subida"] = "app/main.py não encontrado"
        return resultado

    porta = porta_livre()
    junit = Path(os.environ.get("TMPDIR", "/tmp")) / f"junit-{dir_run.name}-{porta}.xml"
    processo = subprocess.Popen(
        [str(PYTHON), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(porta)],
        cwd=base, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    try:
        if not esperar_subida(porta, processo):
            saida = ""
            if processo.poll() is not None:
                saida = (processo.stdout.read() or "")[-1500:]
            resultado["motivo_falha_subida"] = saida or "tempo limite de subida excedido"
            return resultado

        resultado["app_subiu"] = True
        try:
            rodar_testes(caso, porta, junit)
        except subprocess.TimeoutExpired:
            resultado["motivo_falha_subida"] = "tempo limite da suíte excedido"
            return resultado

        por_nome = ler_junit(junit)
        for nome, aprovado in por_nome.items():
            m = PADRAO_CA.match(nome)
            if m:
                ca = f"CA-{int(m.group(1)):02d}.{int(m.group(2))}"
                if ca in resultado["criterios"]:
                    resultado["criterios"][ca] = aprovado
                continue
            m = PADRAO_RNF.match(nome)
            if m:
                resultado["rnf"][f"RNF-{int(m.group(1)):02d}"] = aprovado
    finally:
        processo.terminate()
        try:
            processo.wait(timeout=10)
        except subprocess.TimeoutExpired:
            processo.kill()
        junit.unlink(missing_ok=True)

    atendidos = sum(resultado["criterios"].values())
    resultado["criterios_atendidos"] = atendidos
    resultado["conformidade"] = round(100.0 * atendidos / len(esperados), 2) if esperados else 0.0
    return resultado


def main() -> int:
    ap = argparse.ArgumentParser(description="Mede a conformidade de uma execução.")
    ap.add_argument("--run", required=True, type=Path, help="diretório da execução")
    ap.add_argument("--caso", default="biblioteca", help="caso de teste (pasta em casos/)")
    ap.add_argument("--json", action="store_true", help="imprime apenas JSON")
    args = ap.parse_args()

    if not args.run.is_dir():
        print(f"erro: diretório não encontrado: {args.run}", file=sys.stderr)
        return 2

    r = medir(args.run.resolve(), args.caso)
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0

    print(f"Execução ....... {r['execucao']}  (caso: {r['caso']})")
    if not r["app_subiu"]:
        print(f"Aplicação ...... NÃO SUBIU — {r['motivo_falha_subida']}")
        print("                 todos os critérios contam como não atendidos (regra de medição 2)")
    else:
        print("Aplicação ...... subiu")
    print()
    for ca, ok in sorted(r["criterios"].items()):
        print(f"  {'PASSOU ' if ok else 'FALHOU '} {ca}")
    if r["rnf"]:
        print()
        for rnf, ok in sorted(r["rnf"].items()):
            print(f"  {'PASSOU ' if ok else 'FALHOU '} {rnf}  (métrica separada)")
    print()
    print(f"Conformidade ... {r['criterios_atendidos']}/{r['total_criterios']} = {r['conformidade']:.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
