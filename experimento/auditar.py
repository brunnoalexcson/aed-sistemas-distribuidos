#!/usr/bin/env python3
"""Audita integridade histórica, rastreabilidade e concordância da reavaliação."""
import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import rastreabilidade

RAIZ = Path(__file__).resolve().parent.parent


def auditar(pasta: Path) -> dict:
    manifesto = json.loads((RAIZ / 'experimento/historico/v1/manifesto.json').read_text())
    erros = []
    for nome, esperado in manifesto['arquivos_protegidos'].items():
        arquivo = RAIZ / nome
        if not arquivo.is_file() or hashlib.sha256(arquivo.read_bytes()).hexdigest() != esperado:
            erros.append(f'arquivo protegido alterado/ausente: {nome}')
    for nome, esperado in manifesto['arquivos_arquivados'].items():
        arquivo = RAIZ / 'experimento/historico/v1' / nome
        if not arquivo.is_file() or hashlib.sha256(arquivo.read_bytes()).hexdigest() != esperado:
            erros.append(f'arquivo arquivado alterado/ausente: {nome}')
    for caso in ['biblioteca','estoque']:
        for problema, itens in rastreabilidade.problemas_do_caso(caso).items():
            if itens:
                erros.append(f'{caso}: {problema}: {itens}')
    historico = list(csv.DictReader((RAIZ / 'experimento/resultados/bruto.csv').open()))
    novas = list(csv.DictReader((pasta / 'bruto.csv').open()))
    chaves = lambda linhas: [(r['braco'],r['execucao']) for r in linhas]
    if sorted(chaves(historico)) != sorted(chaves(novas)) or len(set(chaves(novas))) != len(novas):
        erros.append('execuções divergentes ou duplicadas entre CSV histórico e reavaliação')
    campos = ['caso','app_subiu','criterios','rnf','total_criterios','criterios_atendidos','conformidade']
    divergencias = []
    for linha in novas:
        relativo = Path('execucoes') / linha['braco'] / f"{linha['execucao']}.resultado.json"
        antigo = json.loads((RAIZ / 'experimento/resultados' / relativo).read_text())
        novo = json.loads((pasta / relativo).read_text())
        if not novo['medicao_valida']:
            erros.append(f'medição inválida: {relativo}')
        divergentes = [c for c in campos if antigo[c] != novo[c]]
        if divergentes:
            divergencias.append({'execucao':str(relativo),'campos':divergentes})
        if (int(linha['total_criterios']) != len(novo['criterios'])
                or int(linha['criterios_atendidos']) != sum(v is True for v in novo['criterios'].values())
                or float(linha['conformidade']) != novo['conformidade']):
            erros.append(f'CSV e JSON inconsistentes: {relativo}')
    return {'auditado_em':datetime.now(timezone.utc).isoformat(),
            'arquivos_protegidos':len(manifesto['arquivos_protegidos']),
            'arquivos_arquivados':len(manifesto['arquivos_arquivados']),
            'execucoes_comparadas':len(novas), 'divergencias_historicas':divergencias,
            'erros':erros,'aprovado':not erros and not divergencias,
            'alcance':'Integridade desde o início desta revisão; não comprova procedência anterior das gerações.'}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--reavaliacao',required=True,type=Path)
    ap.add_argument('--saida',type=Path)
    args=ap.parse_args()
    r=auditar(args.reavaliacao)
    texto=json.dumps(r,ensure_ascii=False,indent=2)+'\n'
    print(texto)
    if args.saida:
        with args.saida.open('x',encoding='utf-8') as f:
            f.write(texto)
    return 0 if r['aprovado'] else 1


if __name__=='__main__':
    raise SystemExit(main())
