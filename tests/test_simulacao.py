"""Simulador de sensores."""
from simulacao import simulador_sensores as sim


def test_fluxo_tem_formato_e_dispara_as_duas_condicoes():
    cab = sim.CABECALHO.split(",")
    linhas = [linha_.split(",") for linha_ in sim.linhas()]
    assert len(linhas) == sim.N and all(len(linha_) == len(cab) for linha_ in linhas)
    solo = [float(linha_[2]) for linha_ in linhas]
    ar = [float(linha_[4]) for linha_ in linhas]
    assert min(solo) < 30 and max(ar) > 75


def test_simulador_e_deterministico():
    assert list(sim.linhas(seed=7)) == list(sim.linhas(seed=7))
