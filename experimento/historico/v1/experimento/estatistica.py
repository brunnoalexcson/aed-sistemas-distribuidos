#!/usr/bin/env python3
"""
Análise estatística do experimento — Etapa 8 do processo.

Reproduz, a partir de resultados/bruto.csv, todos os números e gráficos do
relatório técnico (Entregável 4).

TESTE DE HIPÓTESE PRINCIPAL (por braço com documento estruturado):
    H0: mu <= 85   (a conformidade média NÃO supera o limiar exigido)
    H1: mu  > 85   (a conformidade média supera o limiar exigido)
    Teste t unilateral para uma amostra, alfa = 0,05.
    Quando Shapiro-Wilk rejeita a normalidade (p < 0,05), o teste de Wilcoxon
    para uma amostra é usado no lugar, e ambos são reportados.

COMPARAÇÃO TRATAMENTO x CONTROLE:
    t de Welch (não assume variâncias iguais) e Mann-Whitney U, com d de Cohen
    como tamanho de efeito. É esta comparação que sustenta a atribuição causal
    ao artefato, e não apenas a superação do limiar.

Uso:
    python experimento/estatistica.py
    python experimento/estatistica.py --sem-graficos
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

RAIZ = Path(__file__).resolve().parent.parent
RESULTADOS = RAIZ / "experimento" / "resultados"
BRUTO = RESULTADOS / "bruto.csv"
GRAFICOS = RESULTADOS / "graficos"

LIMIAR = 85.0
ALFA = 0.05


def ic95(amostra: np.ndarray) -> tuple[float, float]:
    """Intervalo de confiança de 95% da média, pela distribuição t."""
    n = len(amostra)
    if n < 2:
        return (float("nan"), float("nan"))
    erro = stats.sem(amostra)
    if erro == 0:
        return (float(amostra.mean()), float(amostra.mean()))
    margem = erro * stats.t.ppf(0.975, n - 1)
    return (float(amostra.mean() - margem), float(amostra.mean() + margem))


def descrever(amostra: np.ndarray) -> dict:
    return {
        "n": len(amostra),
        "media": float(np.mean(amostra)),
        "desvio": float(np.std(amostra, ddof=1)) if len(amostra) > 1 else 0.0,
        "mediana": float(np.median(amostra)),
        "minimo": float(np.min(amostra)),
        "maximo": float(np.max(amostra)),
        "ic95_inf": ic95(amostra)[0],
        "ic95_sup": ic95(amostra)[1],
    }


def testar_limiar(amostra: np.ndarray) -> dict:
    """Testa H0: mu <= 85 contra H1: mu > 85."""
    n = len(amostra)
    saida: dict = {"n": n, "limiar": LIMIAR}

    if n < 3:
        saida["erro"] = "amostra pequena demais para teste de hipótese"
        return saida

    if np.std(amostra, ddof=1) == 0:
        # Variância nula: o teste t é indefinido. A decisão é determinística.
        saida["variancia_nula"] = True
        saida["todas_acima"] = bool(np.all(amostra > LIMIAR))
        saida["rejeita_h0"] = saida["todas_acima"]
        saida["observacao"] = (
            "Desvio-padrão zero: todas as execuções produziram a mesma taxa. "
            "O teste t é indefinido (divisão por zero); a decisão sobre H0 é "
            "determinística e não probabilística.")
        return saida

    sw_stat, sw_p = stats.shapiro(amostra)
    saida["shapiro_W"] = float(sw_stat)
    saida["shapiro_p"] = float(sw_p)
    saida["normal"] = bool(sw_p >= ALFA)

    t_stat, t_p = stats.ttest_1samp(amostra, LIMIAR, alternative="greater")
    saida["t"] = float(t_stat)
    saida["t_p"] = float(t_p)
    saida["gl"] = n - 1

    diferencas = amostra - LIMIAR
    if np.any(diferencas != 0):
        try:
            w_stat, w_p = stats.wilcoxon(diferencas, alternative="greater")
            saida["wilcoxon_W"] = float(w_stat)
            saida["wilcoxon_p"] = float(w_p)
        except ValueError as e:
            saida["wilcoxon_erro"] = str(e)

    p_decisivo = saida["t_p"] if saida["normal"] else saida.get("wilcoxon_p", saida["t_p"])
    saida["teste_aplicado"] = "t de uma amostra" if saida["normal"] else "Wilcoxon de uma amostra"
    saida["p_decisivo"] = float(p_decisivo)
    saida["rejeita_h0"] = bool(p_decisivo < ALFA)
    # d de Cohen contra o valor de referência
    saida["d_cohen"] = float((np.mean(amostra) - LIMIAR) / np.std(amostra, ddof=1))
    return saida


def comparar(tratamento: np.ndarray, controle: np.ndarray) -> dict:
    t_stat, t_p = stats.ttest_ind(tratamento, controle, equal_var=False, alternative="greater")
    u_stat, u_p = stats.mannwhitneyu(tratamento, controle, alternative="greater")
    n1, n2 = len(tratamento), len(controle)
    s1, s2 = np.std(tratamento, ddof=1), np.std(controle, ddof=1)
    s_agrupado = np.sqrt(((n1 - 1) * s1**2 + (n2 - 1) * s2**2) / (n1 + n2 - 2))
    d = (np.mean(tratamento) - np.mean(controle)) / s_agrupado if s_agrupado > 0 else float("inf")
    return {
        "diferenca_medias": float(np.mean(tratamento) - np.mean(controle)),
        "welch_t": float(t_stat), "welch_p": float(t_p),
        "mannwhitney_U": float(u_stat), "mannwhitney_p": float(u_p),
        "d_cohen": float(d),
    }


def formatar_p(p: float) -> str:
    return "< 0,0001" if p < 0.0001 else f"= {p:.4f}".replace(".", ",")


def graficos(df: pd.DataFrame) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    GRAFICOS.mkdir(parents=True, exist_ok=True)
    bracos = sorted(df["braco"].unique())

    # Boxplot da conformidade por braço
    fig, ax = plt.subplots(figsize=(8, 5))
    dados = [df.loc[df["braco"] == b, "conformidade"].to_numpy() for b in bracos]
    ax.boxplot(dados, tick_labels=bracos)
    for i, amostra in enumerate(dados, start=1):
        ax.scatter(np.random.normal(i, 0.04, len(amostra)), amostra, alpha=0.6, s=25, zorder=3)
    ax.axhline(LIMIAR, linestyle="--", linewidth=1.2, color="#c0392b",
               label=f"limiar de {LIMIAR:.0f}%")
    ax.set_ylabel("Conformidade (%)")
    ax.set_xlabel("Braço do experimento")
    ax.set_title("Conformidade por braço")
    ax.set_ylim(0, 105)
    ax.legend()
    fig.tight_layout()
    fig.savefig(GRAFICOS / "conformidade-por-braco.png", dpi=150)
    plt.close(fig)

    # Conformidade execução a execução
    fig, ax = plt.subplots(figsize=(9, 5))
    for b in bracos:
        sub = df[df["braco"] == b].sort_values("execucao")
        ax.plot(range(1, len(sub) + 1), sub["conformidade"], marker="o", label=b)
    ax.axhline(LIMIAR, linestyle="--", linewidth=1.2, color="#c0392b")
    ax.set_xlabel("Execução")
    ax.set_ylabel("Conformidade (%)")
    ax.set_title("Conformidade execução a execução")
    ax.set_ylim(0, 105)
    ax.legend()
    fig.tight_layout()
    fig.savefig(GRAFICOS / "conformidade-por-execucao.png", dpi=150)
    plt.close(fig)

    print(f"\ngráficos gravados em {GRAFICOS}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Analisa os resultados do experimento.")
    ap.add_argument("--sem-graficos", action="store_true")
    args = ap.parse_args()

    if not BRUTO.exists():
        print(f"erro: {BRUTO} não existe. Rode antes: runner.py medir --todos")
        return 2

    df = pd.read_csv(BRUTO)
    df["conformidade"] = df["conformidade"].astype(float)

    print("=" * 74)
    print("ANÁLISE ESTATÍSTICA DO EXPERIMENTO")
    print("=" * 74)

    print("\n--- Estatística descritiva por braço ---\n")
    linhas = []
    for braco in sorted(df["braco"].unique()):
        sub = df[df["braco"] == braco]
        d = descrever(sub["conformidade"].to_numpy())
        d["braco"] = braco
        d["rotulo"] = sub["rotulo"].iloc[0]
        d["nao_subiram"] = int((sub["app_subiu"] == 0).sum())
        linhas.append(d)

    print(f"{'braço':<7}{'n':>4}{'média':>9}{'desvio':>9}{'mín':>8}{'máx':>8}"
          f"{'IC95%':>20}{'não subiu':>11}")
    for d in linhas:
        ic = f"[{d['ic95_inf']:.2f}; {d['ic95_sup']:.2f}]"
        print(f"{d['braco']:<7}{d['n']:>4}{d['media']:>9.2f}{d['desvio']:>9.2f}"
              f"{d['minimo']:>8.2f}{d['maximo']:>8.2f}{ic:>20}{d['nao_subiram']:>11}")
    print()
    for d in linhas:
        print(f"  {d['braco']} = {d['rotulo']}")

    print("\n--- Teste de hipótese: H0: mu <= 85  vs  H1: mu > 85 (alfa = 0,05) ---")
    for braco in sorted(df["braco"].unique()):
        sub = df[df["braco"] == braco]
        if "livre" in sub["especificacao"].iloc[0]:
            continue  # o braço de controle não é objeto da hipótese
        amostra = sub["conformidade"].to_numpy()
        r = testar_limiar(amostra)
        print(f"\nbraço {braco} (n = {r['n']})")
        if r.get("erro"):
            print(f"  {r['erro']}")
            continue
        if r.get("variancia_nula"):
            print(f"  {r['observacao']}")
            print(f"  todas as execuções acima de {LIMIAR:.0f}%: "
                  f"{'sim' if r['todas_acima'] else 'não'}")
            print(f"  decisão: H0 {'REJEITADA' if r['rejeita_h0'] else 'NÃO rejeitada'}")
            continue
        print(f"  Shapiro-Wilk: W = {r['shapiro_W']:.4f}, p {formatar_p(r['shapiro_p'])} "
              f"-> {'normal' if r['normal'] else 'NÃO normal'}")
        print(f"  t({r['gl']}) = {r['t']:.4f}, p {formatar_p(r['t_p'])}")
        if "wilcoxon_p" in r:
            print(f"  Wilcoxon: W = {r['wilcoxon_W']:.1f}, p {formatar_p(r['wilcoxon_p'])}")
        print(f"  teste aplicado: {r['teste_aplicado']}  |  d de Cohen = {r['d_cohen']:.3f}")
        print(f"  decisão: H0 {'REJEITADA' if r['rejeita_h0'] else 'NÃO rejeitada'} "
              f"(alfa = {ALFA})")

    tratamento = df[df["braco"] == "A"]["conformidade"].to_numpy()
    controle = df[df["braco"] == "B"]["conformidade"].to_numpy()
    if len(tratamento) >= 3 and len(controle) >= 3:
        print("\n--- Tratamento (A) x Controle (B): efeito do artefato ---\n")
        c = comparar(tratamento, controle)
        print(f"  diferença de médias ... {c['diferenca_medias']:.2f} pontos percentuais")
        print(f"  t de Welch ............ t = {c['welch_t']:.4f}, p {formatar_p(c['welch_p'])}")
        print(f"  Mann-Whitney U ........ U = {c['mannwhitney_U']:.1f}, "
              f"p {formatar_p(c['mannwhitney_p'])}")
        print(f"  d de Cohen ............ {c['d_cohen']:.3f}")

    print("\n--- Critérios que mais falharam (braços com documento estruturado) ---\n")
    falhas = falhas_por_criterio(df)
    if falhas:
        for ca, (n_falhas, n_total) in falhas:
            print(f"  {ca}: {n_falhas}/{n_total} execuções falharam "
                  f"({100 * n_falhas / n_total:.0f}%)")
    else:
        print("  nenhum critério falhou")

    if not args.sem_graficos:
        graficos(df)
    return 0


def falhas_por_criterio(df: pd.DataFrame, limite: int = 12):
    """Conta falhas por critério, lendo os JSON de resultado de cada execução."""
    import json
    from collections import defaultdict

    falhas: dict[str, int] = defaultdict(int)
    totais: dict[str, int] = defaultdict(int)
    for _, linha in df.iterrows():
        if "livre" in str(linha["especificacao"]):
            continue
        caminho = (RESULTADOS / "execucoes" / str(linha["braco"])
                   / f"{linha['execucao']}.resultado.json")
        if not caminho.exists():
            continue
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        for ca, ok in dados["criterios"].items():
            chave = f"{linha['braco']}/{ca}"
            totais[chave] += 1
            if not ok:
                falhas[chave] += 1
    ordenado = sorted(((ca, (n, totais[ca])) for ca, n in falhas.items()),
                      key=lambda x: -x[1][0])
    return ordenado[:limite]


if __name__ == "__main__":
    raise SystemExit(main())
