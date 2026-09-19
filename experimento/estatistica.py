#!/usr/bin/env python3
"""Análise v1.1: descrição A/B, hipótese sobre média e exploração binomial.

Unidade amostral: uma geração (não os 40 critérios). Variância zero não
constitui rejeição determinística de H0. A análise binomial é pós-hoc,
condicionada à independência das gerações, não comprovada pelos registros.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

RAIZ = Path(__file__).resolve().parent.parent
LIMIAR = 85.0
ALFA = 0.05


def amostra_valida(valores) -> np.ndarray:
    a = np.asarray(valores, dtype=float)
    if a.ndim != 1 or not np.isfinite(a).all() or np.any((a < 0) | (a > 100)):
        raise ValueError("amostra deve conter taxas finitas entre 0 e 100")
    return a


def descrever(valores) -> dict:
    a = amostra_valida(valores)
    n = len(a)
    return {
        "n": n, "media": float(a.mean()) if n else None,
        "desvio": float(a.std(ddof=1)) if n > 1 else None,
        "mediana": float(np.median(a)) if n else None,
        "minimo": float(a.min()) if n else None, "maximo": float(a.max()) if n else None,
        "execucoes_acima_85": int(np.sum(a > LIMIAR)),
        "execucoes_pelo_menos_85": int(np.sum(a >= LIMIAR)),
    }


def testar_limiar(valores) -> dict:
    a = amostra_valida(valores)
    r = {"n": len(a), "h0": "mu <= 85", "h1": "mu > 85", "alfa": ALFA,
         "teste": "t unilateral de uma amostra", "decisao": "inconclusivo",
         "rejeita_h0": None, "t": None, "p": None, "ic95_media": None}
    if len(a) < 3:
        r["motivo"] = "amostra insuficiente (menos de três execuções)"
    elif np.std(a, ddof=1) == 0:
        r["motivo"] = "variância amostral zero: erro padrão nulo; teste t e IC t não reportados"
    else:
        sw = stats.shapiro(a)
        r.update(shapiro_W=float(sw.statistic), shapiro_p=float(sw.pvalue))
        if sw.pvalue < ALFA:
            r["motivo"] = "normalidade rejeitada; não substituir teste da média por teste de outra hipótese"
        else:
            t = stats.ttest_1samp(a, LIMIAR, alternative="greater")
            margem = float(stats.sem(a) * stats.t.ppf(0.975, len(a) - 1))
            r.update(t=float(t.statistic), p=float(t.pvalue), gl=len(a)-1,
                     ic95_media=[float(a.mean()-margem), float(a.mean()+margem)],
                     rejeita_h0=bool(t.pvalue < ALFA),
                     decisao="rejeitar" if t.pvalue < ALFA else "não rejeitar",
                     motivo="condicionado a observações independentes e pressupostos do teste; Shapiro não comprova normalidade")
    return r


def explorar_proporcao(valores) -> dict:
    a = amostra_valida(valores)
    n, k = len(a), int(np.sum(a > LIMIAR))
    r = {"n": n, "k": k, "definicao": "q = P(conformidade > 85%)",
         "h0": "q <= 0.5", "h1": "q > 0.5", "alfa": ALFA,
         "natureza": "exploratória pós-hoc; não testa a média nem q > 0.85",
         "pressuposto": "gerações independentes com mesma probabilidade de sucesso",
         "p": None, "proporcao": None, "ic95_exato_bilateral": None, "rejeita_h0": None}
    if not n:
        return r
    teste = stats.binomtest(k, n, p=0.5, alternative="greater")
    ic = stats.binomtest(k, n).proportion_ci(confidence_level=0.95, method="exact")
    r.update(p=float(teste.pvalue), proporcao=k/n,
             ic95_exato_bilateral=[float(ic.low), float(ic.high)],
             rejeita_h0=bool(teste.pvalue < ALFA))
    return r


def comparar(tratamento, controle) -> dict:
    a, b = amostra_valida(tratamento), amostra_valida(controle)
    return {"natureza": "comparação exclusivamente descritiva; controle sem contrato de execução equivalente",
            "diferenca_medias_pp": float(a.mean()-b.mean()) if len(a) and len(b) else None}


def carregar(entrada: Path) -> pd.DataFrame:
    df = pd.read_csv(entrada)
    if df.empty or df.duplicated(["braco", "execucao"]).any():
        raise ValueError("CSV vazio ou com execuções duplicadas")
    if "medicao_valida" in df and not (df["medicao_valida"] == 1).all():
        raise ValueError("há medições inválidas; resolva a infraestrutura antes da análise")
    amostra_valida(df["conformidade"])
    for _, linha in df.iterrows():
        arquivo = entrada.parent / "execucoes" / linha["braco"] / f"{linha['execucao']}.resultado.json"
        r = json.loads(arquivo.read_text(encoding="utf-8"))
        n, k = len(r["criterios"]), sum(r["criterios"].values())
        if not n or n != r["total_criterios"] or k != r["criterios_atendidos"]:
            raise ValueError(f"contagem inconsistente: {arquivo}")
        taxa = round(100*k/n, 2)
        if (n != linha["total_criterios"] or k != linha["criterios_atendidos"]
                or taxa != linha["conformidade"] or taxa != r["conformidade"]):
            raise ValueError(f"CSV e JSON divergentes: {arquivo}")
    return df


def graficos(df: pd.DataFrame, saida: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
    pasta = saida / "graficos"
    pasta.mkdir(exist_ok=True)
    cores = {"A": "#206a83", "B": "#a45528"}
    fig, ax = plt.subplots(figsize=(8, 4.8), layout="constrained")
    for i, (braco, grupo) in enumerate(df.groupby("braco"), 1):
        valores = grupo["conformidade"].to_numpy()
        ax.scatter(i + np.linspace(-.16, .16, len(valores)), valores,
                   s=50, color=cores.get(braco, "gray"), zorder=3)
        ax.hlines(valores.mean(), i-.23, i+.23, color=cores.get(braco, "gray"), linewidth=2)
    bracos = sorted(df["braco"].unique())
    ax.set_xticks(range(1, len(bracos)+1), [f"{b} — {'estruturado' if b=='A' else 'texto livre'}" for b in bracos])
    ax.axhline(LIMIAR, color="#666666", linestyle="--", label="Meta observada: 85%")
    ax.set(ylabel="Conformidade funcional (%)", ylim=(-5, 108), xlim=(.5,len(bracos)+.5),
           title="Biblioteca: 10 artefatos por grupo")
    ax.legend(loc="center right")
    fig.savefig(pasta / "conformidade-por-braco.png", dpi=170)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 4.8), layout="constrained")
    for braco, grupo in df.groupby("braco"):
        grupo = grupo.sort_values("execucao")
        ax.plot(range(1,len(grupo)+1), grupo["conformidade"], marker="o", color=cores.get(braco), label=braco)
    ax.axhline(LIMIAR, color="#666666", linestyle="--", label="85%")
    ax.set(xlabel="Execução (identificador, não série temporal)", ylabel="Conformidade funcional (%)",
           ylim=(-5,108), title="Reavaliação das implementações preservadas")
    ax.set_xticks(range(1, int(df.groupby("braco").size().max())+1))
    ax.legend(loc="center right")
    fig.savefig(pasta / "conformidade-por-execucao.png", dpi=170)
    plt.close(fig)


def analisar(entrada: Path, saida: Path, sem_graficos: bool = False) -> dict:
    df = carregar(entrada)
    resumo = {"limiar": LIMIAR, "unidade": "execução de geração", "grupos": {}}
    for braco, grupo in df.groupby("braco"):
        a = grupo["conformidade"].to_numpy()
        r = {"descritiva": descrever(a), "nao_subiram": int((grupo["app_subiu"] == 0).sum())}
        if not grupo["especificacao"].str.contains("livre").any():
            r.update(hipotese_media=testar_limiar(a), exploratoria_proporcao=explorar_proporcao(a))
        resumo["grupos"][braco] = r
    resumo["comparacao_AB"] = comparar(df.loc[df.braco == "A", "conformidade"], df.loc[df.braco == "B", "conformidade"])
    saida.mkdir(parents=True, exist_ok=True)
    (saida / "estatisticas.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2, allow_nan=False)+"\n")
    linhas = ["# Resultados calculados", "", "| Grupo | n | Média (%) | Desvio (pp) | Mínimo | Máximo | Não iniciaram |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for b,r in resumo["grupos"].items():
        d=r["descritiva"]
        linhas.append(f"| {b} | {d['n']} | {d['media']} | {d['desvio']} | {d['minimo']} | {d['maximo']} | {r['nao_subiram']} |")
    linhas += ["", "Dados completos e hipóteses: [estatisticas.json](estatisticas.json).", "",
               "O grupo B não iniciou pelo protocolo fixo; isso não avalia individualmente suas funcionalidades.",
               "Comparação descritiva, sem atribuição causal ao formato Markdown."]
    (saida / "estatisticas.md").write_text("\n".join(linhas)+"\n")
    if not sem_graficos:
        graficos(df, saida)
    return resumo


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--entrada", required=True, type=Path, help="bruto.csv da reavaliação")
    ap.add_argument("--saida", type=Path, help="pasta da análise (padrão: junto ao CSV)")
    ap.add_argument("--sem-graficos", action="store_true")
    args=ap.parse_args()
    saida=(args.saida or args.entrada.parent).resolve()
    historico=RAIZ / "experimento/resultados"
    if saida==historico or historico in saida.parents:
        ap.error("não grave análise nova nos resultados históricos")
    resumo=analisar(args.entrada.resolve(), saida, args.sem_graficos)
    print(json.dumps(resumo, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
