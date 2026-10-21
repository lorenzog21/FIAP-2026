"""Regras de decisao do motor de automacao."""
import automacao


def leitura(solo=50, temp=22, ar=50, luz=50):
    return {"umidade_solo_pct": solo, "temperatura_c": temp, "umidade_ar_pct": ar, "luminosidade_pct": luz}


def test_sem_alerta_em_condicao_normal():
    assert automacao._condicoes(leitura()) == {}


def test_solo_seco_media_e_alta():
    assert automacao._condicoes(leitura(solo=25)) == {"SOLO_SECO": "media"}
    assert automacao._condicoes(leitura(solo=15)) == {"SOLO_SECO": "alta"}


def test_risco_fungico_exige_ar_umido_e_temperatura_na_faixa():
    assert "RISCO_FUNGICO" not in automacao._condicoes(leitura(ar=80, temp=20))
    assert "RISCO_FUNGICO" not in automacao._condicoes(leitura(ar=60, temp=28))
    assert automacao._condicoes(leitura(ar=80, temp=28))["RISCO_FUNGICO"] == "media"
    assert automacao._condicoes(leitura(ar=90, temp=28))["RISCO_FUNGICO"] == "alta"


def test_solo_encharcado_e_calor_extremo():
    c = automacao._condicoes(leitura(solo=85, temp=36))
    assert c == {"SOLO_ENCHARCADO": "media", "CALOR_EXTREMO": "media"}


def test_folha_saudavel_nunca_passa_de_baixo():
    sensor = {"umidade_ar_pct": 95, "temperatura_c": 28, "umidade_solo_pct": 90}
    indice, nivel, _, _ = automacao.classificar_folha(0.0, "Apple___healthy", sensor)
    assert nivel == "baixo" and indice <= 0.3


def test_folha_doente_sobe_com_o_ambiente():
    sem = automacao.classificar_folha(30.0, "Apple___Black_rot", None)
    com = automacao.classificar_folha(30.0, "Apple___Black_rot",
                                      {"umidade_ar_pct": 90, "temperatura_c": 28, "umidade_solo_pct": 80})
    assert com[0] > sem[0]


def test_limiares_de_nivel():
    amb = {"umidade_ar_pct": 90, "temperatura_c": 28, "umidade_solo_pct": 80}  # risco ambiental 1.0
    assert automacao.classificar_folha(100.0, "Apple___Black_rot", amb)[1] == "alto"
    assert automacao.classificar_folha(0.0, "Apple___Black_rot", None)[1] == "baixo"
