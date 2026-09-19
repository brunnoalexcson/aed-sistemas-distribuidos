#!/usr/bin/env python3
"""Medidor v1.1: protocolo funcional v1, com diagnóstico e logs da reavaliação.

Não modifica código, testes ou especificações históricos. Ausência do ponto de
entrada ou falha da aplicação vale zero pelo protocolo original. Falha do
ambiente/instrumento invalida a medição e NÃO é nota zero do produto.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import rastreabilidade

RAIZ = Path(__file__).resolve().parent.parent
PYTHON = RAIZ / ".venv" / "bin" / "python"
TEMPO_LIMITE_SUBIDA = 30.0
TEMPO_LIMITE_TESTES = 600
PADRAO_CA = re.compile(r"^test_ca_(\d+)_(\d+)_")
PADRAO_RNF = re.compile(r"^test_rnf_(\d+)_")


def criterios_do_documento(caso: str) -> list[str]:
    return rastreabilidade.criterios_do_documento(caso)


def porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def pasta_da_aplicacao(dir_run: Path) -> Path | None:
    # Mantém inclusive a tolerância histórica a uma pasta intermediária.
    if (dir_run / "app" / "main.py").exists():
        return dir_run
    for caminho in sorted(dir_run.rglob("app/main.py")):
        return caminho.parent.parent
    return None


def esperar_subida(porta: int, processo: subprocess.Popen) -> bool:
    limite = time.monotonic() + TEMPO_LIMITE_SUBIDA
    while time.monotonic() < limite:
        if processo.poll() is not None:
            return False
        try:
            with socket.create_connection(("127.0.0.1", porta), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def ambiente_execucao() -> dict[str, str]:
    return {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}


def verificar_ambiente() -> None:
    r = subprocess.run(
        [str(PYTHON), "-B", "-c", "import uvicorn, fastapi, pydantic, pytest, httpx"],
        capture_output=True, text=True, timeout=30, env=ambiente_execucao())
    if r.returncode:
        raise RuntimeError("dependências do ambiente indisponíveis: " + r.stderr[-2000:])


def rodar_testes(caso: str, porta: int, arquivo_junit: Path) -> subprocess.CompletedProcess:
    ambiente = {**ambiente_execucao(), "BASE_URL": f"http://127.0.0.1:{porta}"}
    return subprocess.run(
        [str(PYTHON), "-B", "-m", "pytest", str(RAIZ / "casos" / caso / "testes"),
         "-q", "--no-header", "-p", "no:cacheprovider", f"--junitxml={arquivo_junit}"],
        capture_output=True, text=True, timeout=TEMPO_LIMITE_TESTES, env=ambiente)


def ler_junit(arquivo: Path) -> dict[str, bool]:
    resultados = {}
    criterios = set()
    for teste in ET.parse(arquivo).getroot().iter("testcase"):
        nome = teste.get("name", "")
        if nome in resultados:
            raise ValueError(f"teste duplicado no JUnit: {nome}")
        m = PADRAO_CA.match(nome)
        if m:
            ca = f"CA-{int(m[1]):02d}.{int(m[2])}"
            if ca in criterios:
                raise ValueError(f"critério duplicado no JUnit: {ca}")
            criterios.add(ca)
        resultados[nome] = not any(c.tag in ("failure", "error", "skipped") for c in teste)
    return resultados


def medir(dir_run: Path, caso: str, logs: Path | None = None) -> dict:
    esperados = criterios_do_documento(caso)
    r = {
        "execucao": dir_run.name, "caso": caso, "app_subiu": False,
        "motivo_falha_subida": None, "medicao_valida": True,
        "categoria": "concluida", "diagnostico": None,
        "criterios": dict.fromkeys(esperados, False), "rnf": {},
        "total_criterios": len(esperados), "criterios_atendidos": 0, "conformidade": 0.0,
    }
    processo = None
    try:
        problemas = {k: v for k, v in rastreabilidade.problemas_do_caso(caso).items() if v}
        if problemas or not esperados:
            raise ValueError(f"rastreabilidade inválida: {problemas}")
        base = pasta_da_aplicacao(dir_run)
        if base is None:
            r.update(categoria="ponto_entrada_ausente", motivo_falha_subida="app/main.py não encontrado")
            return r
        verificar_ambiente()
        porta = porta_livre()
        with tempfile.TemporaryDirectory(prefix="aed-medicao-") as temp:
            pasta = Path(temp)
            junit = pasta / "junit.xml"
            servidor = pasta / "servidor.log"
            try:
                # Arquivo evita bloqueio pelo enchimento de um pipe de logs.
                with servidor.open("w+", encoding="utf-8") as saida:
                    processo = subprocess.Popen(
                        [str(PYTHON), "-B", "-m", "uvicorn", "app.main:app",
                         "--host", "127.0.0.1", "--port", str(porta)], cwd=base,
                        stdout=saida, stderr=subprocess.STDOUT, text=True, env=ambiente_execucao())
                    if not esperar_subida(porta, processo):
                        saida.flush()
                        diagnostico = servidor.read_text(encoding="utf-8")
                        if any(s in diagnostico.lower() for s in (
                            "permission denied", "operation not permitted", "address already in use")):
                            raise RuntimeError(diagnostico)
                        r.update(categoria="falha_aplicacao", motivo_falha_subida=(
                            diagnostico[-2000:] or "tempo limite de subida excedido"))
                        return r
                    r["app_subiu"] = True
                    try:
                        teste = rodar_testes(caso, porta, junit)
                    except subprocess.TimeoutExpired as exc:
                        # Regra histórica: timeout da suíte reprova todos os CAs.
                        r.update(categoria="timeout_suite", diagnostico="tempo limite da suíte excedido")
                        parcial = exc.stdout or ""
                        (pasta / "pytest.log").write_text(
                            parcial.decode(errors="replace") if isinstance(parcial, bytes) else parcial,
                            encoding="utf-8")
                        return r
                    (pasta / "pytest.log").write_text(teste.stdout + teste.stderr, encoding="utf-8")
                    if teste.returncode not in (0, 1):
                        raise RuntimeError(f"pytest terminou com código {teste.returncode}: {teste.stderr}")
                    por_nome = ler_junit(junit)
                    observados = set()
                    for nome, aprovado in por_nome.items():
                        m = PADRAO_CA.match(nome)
                        if m:
                            ca = f"CA-{int(m[1]):02d}.{int(m[2])}"
                            observados.add(ca)
                            r["criterios"][ca] = aprovado
                        elif m := PADRAO_RNF.match(nome):
                            r["rnf"][f"RNF-{int(m[1]):02d}"] = aprovado
                    if observados != set(esperados):
                        raise ValueError("JUnit incompleto ou com critérios fora da especificação")
            finally:
                if processo is not None:
                    processo.terminate()
                    try:
                        processo.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        processo.kill()
                        processo.wait()
                if logs is not None:
                    logs.mkdir(parents=True, exist_ok=True)
                    for arquivo in pasta.iterdir():
                        (logs / arquivo.name).write_bytes(arquivo.read_bytes())
        r["criterios_atendidos"] = sum(r["criterios"].values())
        r["conformidade"] = round(100 * r["criterios_atendidos"] / len(esperados), 2)
    except (OSError, RuntimeError, ValueError, ET.ParseError, subprocess.TimeoutExpired) as exc:
        r.update(medicao_valida=False, categoria="infraestrutura_ou_instrumento",
                 diagnostico=str(exc), conformidade=None, criterios_atendidos=None,
                 criterios=dict.fromkeys(esperados, None), rnf={})
    return r


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", required=True, type=Path)
    ap.add_argument("--caso", default="biblioteca")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if not args.run.is_dir():
        ap.error("diretório da execução não encontrado")
    r = medir(args.run.resolve(), args.caso)
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(f"{r['execucao']}: {r['conformidade']}% ({r['categoria']})")
        if r["diagnostico"] or r["motivo_falha_subida"]:
            print(r["diagnostico"] or r["motivo_falha_subida"])
    return 0 if r["medicao_valida"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
