"""Regressões do instrumento; não alteram a suíte experimental histórica."""
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import estatistica
import inspecao
import medir
import rastreabilidade
import runner


def test_rastreabilidade_detecta_duas_definicoes_para_mesmo_ca(tmp_path, monkeypatch):
    caso=tmp_path / 'casos/exemplo'
    (caso / 'testes').mkdir(parents=True)
    (caso / 'requisitos-exemplo.md').write_text('### RF-01\n**CA-01.1**\n## 12. Matriz\nRF-01\n')
    (caso / 'testes/test_a.py').write_text('def test_ca_01_1_a(): pass\ndef test_ca_01_1_a(): pass\n')
    monkeypatch.setattr(rastreabilidade, 'RAIZ', tmp_path)
    assert rastreabilidade.problemas_do_caso('exemplo')['critérios com múltiplos testes'] == ['CA-01.1']
    assert not rastreabilidade.verificar('exemplo')


def test_junit_rejeita_ca_duplicado(tmp_path):
    p=tmp_path / 'junit.xml'
    p.write_text('<testsuite><testcase name="test_ca_01_1_a"/><testcase name="test_ca_01_1_b"/></testsuite>')
    with pytest.raises(ValueError, match='critério duplicado'):
        medir.ler_junit(p)


def test_junit_falhas_e_pulados_nao_aprovam(tmp_path):
    p=tmp_path / 'junit.xml'
    p.write_text('<testsuite><testcase name="ok"/><testcase name="falha"><failure/></testcase>'
                 '<testcase name="erro"><error/></testcase><testcase name="pulado"><skipped/></testcase></testsuite>')
    assert medir.ler_junit(p)==dict(ok=True, falha=False, erro=False, pulado=False)


@pytest.fixture
def aplicacao(tmp_path, monkeypatch):
    (tmp_path / 'app').mkdir()
    (tmp_path / 'app/main.py').write_text('from fastapi import FastAPI\napp = FastAPI()\n')
    monkeypatch.setattr(medir, 'criterios_do_documento', lambda _: ['CA-01.1'])
    monkeypatch.setattr(rastreabilidade, 'problemas_do_caso', lambda _: {})
    monkeypatch.setattr(medir, 'verificar_ambiente', lambda: None)
    monkeypatch.setattr(medir, 'porta_livre', lambda: 12345)
    processo=SimpleNamespace(terminate=lambda: None, wait=lambda **_: None, kill=lambda: None)
    monkeypatch.setattr(medir.subprocess, 'Popen', lambda *a, **kw: processo)
    monkeypatch.setattr(medir, 'esperar_subida', lambda *a: True)
    return tmp_path


def test_sem_ponto_entrada_zero_valido(tmp_path):
    r=medir.medir(tmp_path,'biblioteca')
    assert r['medicao_valida'] and r['conformidade']==0
    assert r['categoria']=='ponto_entrada_ausente'


def test_falha_aplicacao_zero_valido(aplicacao, monkeypatch):
    monkeypatch.setattr(medir, 'esperar_subida', lambda *a: False)
    r=medir.medir(aplicacao, 'biblioteca')
    assert r['medicao_valida'] and r['conformidade']==0
    assert r['categoria']=='falha_aplicacao'


def test_bloqueio_de_porta_nao_e_nota_zero(aplicacao, monkeypatch):
    def bloqueio(): raise PermissionError('porta bloqueada')
    monkeypatch.setattr(medir, 'porta_livre', bloqueio)
    r=medir.medir(aplicacao,'biblioteca')
    assert not r['medicao_valida'] and r['conformidade'] is None
    assert set(r['criterios'].values())=={None}


def test_timeout_suite_mantem_regra_historica(aplicacao, monkeypatch):
    def timeout(*args): raise subprocess.TimeoutExpired('pytest', 600, output=b'parcial')
    monkeypatch.setattr(medir, 'rodar_testes', timeout)
    r=medir.medir(aplicacao, 'biblioteca', aplicacao.parent / 'logs')
    assert r['app_subiu'] and r['medicao_valida'] and r['conformidade']==0
    assert r['categoria']=='timeout_suite'


def test_erro_coleta_pytest_invalida_medicao(aplicacao, monkeypatch):
    monkeypatch.setattr(medir, 'rodar_testes', lambda *a: SimpleNamespace(returncode=2,stdout='',stderr='coleta'))
    r=medir.medir(aplicacao, 'biblioteca')
    assert not r['medicao_valida'] and r['conformidade'] is None


@pytest.mark.parametrize('xml,validade,taxa', [
    ('<testsuite><testcase name="test_ca_01_1_ok"/></testsuite>', True, 100),
    ('<testsuite><testcase name="test_ca_01_1_ok"><failure/></testcase></testsuite>', True, 0),
    ('<testsuite/>', False, None),
    ('<xml quebrado', False, None),
])
def test_medicao_interpreta_junit(aplicacao, monkeypatch, xml, validade, taxa):
    def rodar(caso,porta,arquivo):
        arquivo.write_text(xml)
        return SimpleNamespace(returncode=1,stdout='',stderr='')
    monkeypatch.setattr(medir, 'rodar_testes', rodar)
    r=medir.medir(aplicacao,'biblioteca')
    assert r['medicao_valida'] is validade and r['conformidade']==taxa


def test_modulos_locais_nao_sao_dependencias_externas(tmp_path):
    (tmp_path / 'services.py').write_text('')
    (tmp_path / 'pacote').mkdir()
    (tmp_path / 'pacote/__init__.py').write_text('')
    (tmp_path / 'app.py').write_text('import services\nimport pacote\nimport flask\n')
    assert inspecao.inspecionar(tmp_path)['RNF-03_externos']==['flask']


@pytest.mark.parametrize('valores', [[], [90], [90,95], [100]*10, [85]*10, [0]*10])
def test_amostras_insuficientes_ou_constantes_inconclusivas(valores):
    r=estatistica.testar_limiar(valores)
    assert r['decisao']=='inconclusivo' and r['rejeita_h0'] is None
    assert r['p'] is None and r['ic95_media'] is None
    json.dumps(r, allow_nan=False)


def test_binomial_hipotese_propria_e_empate_nao_e_sucesso():
    r=estatistica.explorar_proporcao([100]*10)
    assert r['p']==pytest.approx(1/1024)
    assert r['ic95_exato_bilateral'][0]==pytest.approx(.6915028922)
    assert estatistica.explorar_proporcao([85,90])['k']==1
    assert estatistica.explorar_proporcao([])['p'] is None


def test_media_variavel_e_comparacao():
    r=estatistica.testar_limiar([88,90,91,92,93,94,95,96,97,99])
    assert r['t'] is not None and r['ic95_media'] is not None
    assert estatistica.comparar([100]*10,[0]*10)['diferenca_medias_pp']==100


@pytest.mark.parametrize('valores', [[float('nan')], [float('inf')],[-1], [101]])
def test_taxas_invalidas_rejeitadas(valores):
    with pytest.raises(ValueError): estatistica.descrever(valores)


def test_historico_preservado():
    manifesto=json.loads((runner.RAIZ/'experimento/historico/v1/manifesto.json').read_text())
    assert runner.hashes_protegidos()==manifesto['arquivos_protegidos']
