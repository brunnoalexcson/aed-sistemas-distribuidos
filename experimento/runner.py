#!/usr/bin/env python3
"""
Orquestrador do experimento — Etapas 6 e 7 do processo.

Responsabilidades:
  preparar  — cria o diretório de cada execução e materializa o prompt EXATO
              (prompt padrão + especificação do braço). O prompt fica fora do
              diretório da execução, para que este contenha apenas o código
              entregue pela LLM.
  medir     — roda o medidor de conformidade sobre todas as execuções de um
              braço e consolida os resultados em um novo diretório de reavaliação (nunca sobrescreve os resultados v1).

A geração propriamente dita (Etapa 6) é feita fora deste script, por sessões
independentes da LLM, cada uma recebendo o prompt materializado por `preparar`.

Uso:
    python experimento/runner.py preparar --braco A
    python experimento/runner.py preparar --todos
    python experimento/runner.py medir --braco A
    python experimento/runner.py medir --todos
    python experimento/runner.py status
"""

from __future__ import annotations

import argparse
import csv
import json
import hashlib
import importlib.metadata
import platform
import sys

import inspecao
from datetime import datetime, timezone
from pathlib import Path

import medir as medidor

RAIZ = Path(__file__).resolve().parent.parent
RESULTADOS = RAIZ / "experimento" / "resultados"
EXECUCOES = RESULTADOS / "execucoes"
PROMPTS = RESULTADOS / "prompts"
BRUTO = RESULTADOS / "bruto.csv"

# --------------------------------------------------------------------------
# Desenho do experimento.
#
# Variável independente: `especificacao` (documento estruturado x texto livre).
# Variáveis controladas: prompt, modelo, número de execuções, suíte de testes.
# --------------------------------------------------------------------------
BRACOS: dict[str, dict] = {
    "A": {
        "rotulo": "Tratamento — documento estruturado (Biblioteca)",
        "caso": "biblioteca",
        "especificacao": "casos/biblioteca/requisitos-biblioteca.md",
        "modelo": "sonnet",
        "n": 10,
    },
    "B": {
        "rotulo": "Controle — texto livre (Biblioteca)",
        "caso": "biblioteca",
        "especificacao": "casos/biblioteca/descricao-livre.md",
        "modelo": "sonnet",
        "n": 10,
    },
    "C": {
        "rotulo": "Generalização — documento estruturado (Estoque)",
        "caso": "estoque",
        "especificacao": "casos/estoque/requisitos-estoque.md",
        "modelo": "sonnet",
        "n": 10,
    },
    "D": {
        "rotulo": "Robustez entre modelos — documento estruturado (Biblioteca)",
        "caso": "biblioteca",
        "especificacao": "casos/biblioteca/requisitos-biblioteca.md",
        "modelo": "haiku",
        "n": 10,
    },
}

CAMPOS_CSV = [
    "braco", "rotulo", "caso", "modelo", "execucao", "especificacao",
    "app_subiu", "criterios_atendidos", "total_criterios", "conformidade",
    "rnf_atendidos", "rnf_total", "medido_em", "medicao_valida", "categoria",
]


def texto_do_prompt() -> str:
    """Extrai o texto do prompt padrão do bloco de código de prompt-padrao.md."""
    md = (RAIZ / "experimento" / "prompt-padrao.md").read_text(encoding="utf-8")
    inicio = md.index("```", md.index("## Texto do prompt")) + 3
    fim = md.index("```", inicio)
    return md[inicio:fim].strip("\n")


def dir_execucao(braco: str, numero: int) -> Path:
    return EXECUCOES / braco / f"run-{numero:02d}"


def preparar(braco: str) -> None:
    cfg = BRACOS[braco]
    especificacao = (RAIZ / cfg["especificacao"]).read_text(encoding="utf-8")
    modelo_prompt = texto_do_prompt()
    PROMPTS.mkdir(parents=True, exist_ok=True)

    for numero in range(1, cfg["n"] + 1):
        destino = dir_execucao(braco, numero)
        destino.mkdir(parents=True, exist_ok=True)
        prompt = (modelo_prompt
                  .replace("{DIRETORIO}", str(destino))
                  .replace("{ESPECIFICACAO}", especificacao))
        (PROMPTS / f"{braco}-run-{numero:02d}.txt").write_text(prompt, encoding="utf-8")

    print(f"braço {braco} ({cfg['rotulo']}): {cfg['n']} execuções preparadas")
    print(f"  diretórios: {EXECUCOES / braco}/run-01 .. run-{cfg['n']:02d}")
    print(f"  prompts:    {PROMPTS}/{braco}-run-NN.txt")


def gerado(destino: Path) -> bool:
    """Uma execução foi gerada quando há qualquer arquivo .py dentro dela."""
    return destino.is_dir() and any(destino.rglob("*.py"))


def medir_braco(braco: str, saida: Path) -> list[dict]:
    cfg = BRACOS[braco]
    linhas: list[dict] = []
    for numero in range(1, cfg["n"] + 1):
        destino = dir_execucao(braco, numero)
        if not gerado(destino):
            print(f"  run-{numero:02d}: ainda não gerada, ignorada")
            continue
        r = medidor.medir(destino, cfg["caso"], saida / "logs" / braco / destino.name)
        r["inspecao"] = inspecao.inspecionar(destino)
        pasta = saida / "execucoes" / braco
        pasta.mkdir(parents=True, exist_ok=True)
        (pasta / f"run-{numero:02d}.resultado.json").write_text(
            json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
        linhas.append({
            "braco": braco,
            "rotulo": cfg["rotulo"],
            "caso": cfg["caso"],
            "modelo": cfg["modelo"],
            "execucao": f"run-{numero:02d}",
            "especificacao": cfg["especificacao"],
            "app_subiu": int(r["app_subiu"]),
            "criterios_atendidos": r["criterios_atendidos"],
            "total_criterios": r["total_criterios"],
            "conformidade": r["conformidade"],
            "rnf_atendidos": sum(r["rnf"].values()),
            "rnf_total": len(r["rnf"]),
            "medicao_valida": int(r["medicao_valida"]),
            "categoria": r["categoria"],
            "medido_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        })
        marca = "subiu" if r["app_subiu"] else "NÃO SUBIU"
        print(f"  run-{numero:02d}: {r['conformidade']}%  "
              f"({r['criterios_atendidos']}/{r['total_criterios']}, {marca})")
    return linhas


def gravar_csv(linhas: list[dict], saida: Path) -> None:
    with (saida / "bruto.csv").open("x", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS_CSV)
        escritor.writeheader()
        escritor.writerows(sorted(linhas, key=lambda l: (l["braco"], l["execucao"])))


def hashes_protegidos() -> dict[str, str]:
    manifesto = json.loads((RAIZ / "experimento/historico/v1/manifesto.json").read_text())
    return {nome: hashlib.sha256((RAIZ / nome).read_bytes()).hexdigest()
            for nome in manifesto["arquivos_protegidos"]}


def registrar_ambiente(saida: Path, antes: dict) -> None:
    manifesto = json.loads((RAIZ / "experimento/historico/v1/manifesto.json").read_text())
    depois = hashes_protegidos()
    alterados = [nome for nome in antes
                 if antes[nome] != depois[nome] or antes[nome] != manifesto["arquivos_protegidos"][nome]]
    arquivos = [*sorted((RAIZ / "experimento").glob("*.py")), RAIZ / "requirements.txt"]
    registro = {
        "registrado_em": datetime.now(timezone.utc).isoformat(),
        "python": sys.version, "executavel": sys.executable, "plataforma": platform.platform(),
        "pacotes": {p: importlib.metadata.version(p) for p in
                    ["fastapi", "uvicorn", "pydantic", "pytest", "httpx", "numpy", "scipy", "pandas", "matplotlib"]},
        "arquivos_protegidos": depois, "arquivos_alterados": alterados,
        "instrumentos_sha256": {str(p.relative_to(RAIZ)): hashlib.sha256(p.read_bytes()).hexdigest() for p in arquivos},
        "modelo_historico": "sonnet (alias registrado; versão exata não documentada)",
        "natureza": "Reavaliação de artefatos existentes; não representa novas gerações de LLM.",
    }
    (saida / "ambiente.json").write_text(json.dumps(registro, ensure_ascii=False, indent=2) + "\n")
    if alterados:
        raise RuntimeError(f"arquivos históricos alterados: {alterados}")


def status() -> None:
    print(f"{'braço':<6}{'modelo':<9}{'geradas':<10}{'rótulo'}")
    for braco, cfg in BRACOS.items():
        n_geradas = sum(1 for i in range(1, cfg["n"] + 1) if gerado(dir_execucao(braco, i)))
        print(f"{braco:<6}{cfg['modelo']:<9}{f'{n_geradas}/{cfg["n"]}':<10}{cfg['rotulo']}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Orquestra o experimento.")
    sub = ap.add_subparsers(dest="comando", required=True)

    p_prep = sub.add_parser("preparar", help="cria diretórios e prompts")
    p_prep.add_argument("--braco", choices=sorted(BRACOS))
    p_prep.add_argument("--todos", action="store_true")

    p_med = sub.add_parser("medir", help="mede as execuções já geradas")
    p_med.add_argument("--braco", choices=sorted(BRACOS))
    p_med.add_argument("--todos", action="store_true")
    p_med.add_argument("--saida", type=Path, help="diretório NOVO da reavaliação")

    sub.add_parser("status", help="mostra quantas execuções já foram geradas")

    args = ap.parse_args()

    if args.comando == "status":
        status()
        return 0

    alvos = sorted(BRACOS) if getattr(args, "todos", False) else [args.braco]
    if alvos == [None]:
        ap.error("informe --braco ou --todos")

    if args.comando == "preparar":
        for braco in alvos:
            preparar(braco)
        return 0

    saida = (args.saida or (RAIZ / "experimento/reavaliacoes" /
             datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))).resolve()
    if saida == RESULTADOS or RESULTADOS in saida.parents:
        ap.error("use uma pasta fora dos resultados históricos")
    saida.mkdir(parents=True, exist_ok=False)
    antes = hashes_protegidos()
    todas: list[dict] = []
    for braco in alvos:
        print(f"\nbraço {braco} — {BRACOS[braco]['rotulo']}")
        todas.extend(medir_braco(braco, saida))
    if todas:
        gravar_csv(todas, saida)
    else:
        print("\nnenhuma execução medida")
    registrar_ambiente(saida, antes)
    print(f"Reavaliação salva em {saida}")
    return 0 if all(l["medicao_valida"] for l in todas) else 2


if __name__ == "__main__":
    raise SystemExit(main())
