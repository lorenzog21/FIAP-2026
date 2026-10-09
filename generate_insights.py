"""
Camada de "IA generativa simulada".

Substitui a antiga statusLeaves() (lookup fixo de faixa de %) por uma
sintese de texto que combina MULTIPLAS variaveis -- classe prevista,
confiança do modelo, % de area infectada e o contexto ambiental do
talhao (quando disponivel) -- via um sistema de templates parametrizados.
Nao chama nenhuma API paga: a "geracao" e um motor de templates com
sentencas escolhidas por um indice de risco continuo (nao apenas por
faixas fixas) e variacao de fraseado seedada pelo id da imagem.
"""
import os
import json
import random
import hashlib

GOLD_DIR = os.path.join("data", "gold")

ABERTURAS_SAUDAVEL = [
    "A análise de imagem não encontrou sinais relevantes de Podridão Negra nesta folha.",
    "O modelo classificou esta folha como saudavel, sem indícios visuais significativos da doença.",
    "Nenhuma lesão característica de Podridão Negra foi detectada na área foliar analisada.",
]

ABERTURAS_DOENTE = [
    "A análise identificou sinais de Podridão Negra (Botryosphaeria obtusa) nesta folha.",
    "O modelo detectou padrões de coloração compatíveis com Podridão Negra na folha analisada.",
    "Foram encontradas lesões fúngicas características de Podridão Negra na imagem processada.",
]


def _seeded_rng(chave):
    seed = int(hashlib.md5(chave.encode("utf-8")).hexdigest(), 16) % (2**32)
    return random.Random(seed)


def _descrever_severidade(area_pct):
    if area_pct <= 0:
        return "sem comprometimento perceptível da área foliar"
    if area_pct <= 20:
        return f"comprometendo cerca de {area_pct:.1f}% da área foliar, um estágio inicial"
    if area_pct <= 40:
        return f"avançando sobre {area_pct:.1f}% da área foliar, em estágio moderado"
    if area_pct <= 60:
        return f"já atingindo {area_pct:.1f}% da área foliar, em estágio severo"
    if area_pct <= 80:
        return f"comprometendo {area_pct:.1f}% da folha, em estado crítico"
    return f"tomando {area_pct:.1f}% da folha, com necrose praticamente total"


def _risco_ambiental(sensor):
    """Combina umidade do ar, temperatura e umidade do solo num indice 0-1,
    em vez de checar um unico limiar isolado -- o objetivo e que a saida
    reflita a interacao entre variaveis, nao uma unica regra fixa."""
    if not sensor:
        return 0.0, []

    risco = 0.0
    fatores = []
    umidade_ar = sensor.get("umidade_ar_pct")
    temperatura = sensor.get("temperatura_c")
    umidade_solo = sensor.get("umidade_solo_pct")

    if umidade_ar is not None:
        if umidade_ar >= 75:
            risco += 0.4
            fatores.append(f"umidade do ar elevada ({umidade_ar:.0f}%)")
        elif umidade_ar <= 35:
            fatores.append(f"ar seco ({umidade_ar:.0f}% de umidade)")

    if temperatura is not None:
        if 24 <= temperatura <= 32:
            risco += 0.35
            fatores.append(f"temperatura na faixa favorável à proliferação fúngica ({temperatura:.1f}°C)")
        elif temperatura > 32:
            risco += 0.1
            fatores.append(f"temperatura elevada ({temperatura:.1f}°C)")

    if umidade_solo is not None and 0 <= umidade_solo <= 100 and umidade_solo >= 70:
        risco += 0.25
        fatores.append(f"solo com alta retenção de umidade ({umidade_solo:.0f}%)")

    if sensor.get("flag_anomalia"):
        fatores.append("leitura de sensor sinalizada como anômala nesta janela -- considerar com cautela")

    return round(min(risco, 1.0), 2), fatores


def _recomendacao_por_severidade(area_pct):
    if area_pct <= 20:
        return "Recomenda-se remover as folhas afetadas e monitorar a evolução nos próximos dias."
    if area_pct <= 40:
        return "Recomenda-se poda sanitária das partes afetadas e avaliação de fungicida preventivo à base de cobre."
    if area_pct <= 60:
        return "Recomenda-se intervenção com fungicida sistêmico e limpeza do material caído ao redor da planta."
    if area_pct <= 80:
        return "Recomenda-se poda drástica das áreas afetadas e aplicação urgente de fungicida de ação curativa."
    return "Recomenda-se remoção imediata do material infectado, descartado longe da plantação."


def gerar_diagnostico(registro):
    rng = _seeded_rng(registro["image"])
    predicted_class = registro["predicted_class"]
    area_pct = registro["analysis_infected_area"]["real_infected_area_percentage"]
    prob = registro["probabilities_ml"].get(predicted_class, 0.0)
    sensor = registro.get("sensor_context")

    risco_ambiental, fatores = _risco_ambiental(sensor)

    if predicted_class == "Apple___healthy":
        abertura = rng.choice(ABERTURAS_SAUDAVEL)
        corpo = f"O modelo tem {prob * 100:.0f}% de confiança nesse diagnostico."
        if fatores and risco_ambiental >= 0.4:
            corpo += (
                f" Ainda assim, as condições do talhão ({', '.join(fatores)}) sugerem um ambiente "
                f"favorável ao fungo -- vale manter monitoramento preventivo mesmo sem sintomas visíveis."
            )
        recomendacao = "Manter inspeção periódica e boas práticas de circulação de ar entre as plantas."
        return f"{abertura} {corpo} {recomendacao}".strip()

    abertura = rng.choice(ABERTURAS_DOENTE)
    severidade_desc = _descrever_severidade(area_pct)
    corpo = f"A lesão está {severidade_desc}, com confiança do modelo de {prob * 100:.0f}%."

    indice_combinado = round(min(1.0, (area_pct / 100) * 0.7 + risco_ambiental * 0.3), 2)

    if fatores:
        talhao_txt = f" talhão {sensor['talhao_id']}" if sensor and sensor.get("talhao_id") else ""
        clausula_ambiental = (
            f" Combinado com {', '.join(fatores)} registrada(s) no{talhao_txt}, "
            f"o índice de risco de progressão calculado é {indice_combinado:.2f} (escala 0 a 1), "
        )
        if indice_combinado >= 0.6:
            clausula_ambiental += "indicando risco elevado de avanço rápido da doença."
        elif indice_combinado >= 0.35:
            clausula_ambiental += "indicando risco moderado de progressão nos próximos dias."
        else:
            clausula_ambiental += "indicando risco relativamente controlado no curto prazo, mas que exige acompanhamento."
    elif sensor:
        clausula_ambiental = (
            f" As condicoes registradas no talhão {sensor['talhao_id']} "
            f"(temperatura {sensor['temperatura_c']:.1f}°C, umidade do ar {sensor['umidade_ar_pct']:.0f}%, "
            f"umidade do solo {sensor['umidade_solo_pct']:.0f}%) não indicam fator ambiental de risco adicional."
        )
    else:
        clausula_ambiental = " Não há dados de sensor disponíveis para este talhão nesta janela de tempo."

    recomendacao = _recomendacao_por_severidade(area_pct)
    return f"{abertura} {corpo}{clausula_ambiental} {recomendacao}".strip()


def gerar_insights(gold_results_path):
    with open(gold_results_path, encoding="utf-8") as f:
        results = json.load(f)

    insights = []
    for registro in results:
        entrada = {
            "image": registro["image"],
            "predicted_class": registro["predicted_class"],
            "probabilities_ml": registro["probabilities_ml"],
            "real_infected_area_percentage": registro["analysis_infected_area"]["real_infected_area_percentage"],
            "sensor_context": registro.get("sensor_context"),
        }
        insights.append({"entrada": entrada, "diagnostico_gerado": gerar_diagnostico(registro)})

    insights_path = os.path.join(GOLD_DIR, "insights.json")
    with open(insights_path, "w", encoding="utf-8") as f:
        json.dump(insights, f, indent=4, ensure_ascii=False)

    _gerar_exemplos_md(insights)

    print(f"[insights] gerou {len(insights)} diagnosticos em {insights_path}")
    return insights


def _escolher_exemplos(insights):
    """Seleciona 3 exemplos que mostram a variacao real do gerador: um
    diagnostico saudavel, o caso doente mais severo disponivel no lote de
    teste e o caso doente mais leve -- para evidenciar que o texto muda de
    tom com a combinacao de variaveis, nao so entre saudavel/doente."""
    saudavel = next((i for i in insights if i["entrada"]["predicted_class"] == "Apple___healthy"), None)

    doentes = [i for i in insights if i["entrada"]["predicted_class"] == "Apple___Black_rot"]
    doentes_ordenados = sorted(doentes, key=lambda i: i["entrada"]["real_infected_area_percentage"])
    mais_leve = doentes_ordenados[0] if doentes_ordenados else None
    mais_severo = doentes_ordenados[-1] if doentes_ordenados else None

    exemplos = []
    for candidato in (saudavel, mais_severo, mais_leve):
        if candidato is not None and candidato not in exemplos:
            exemplos.append(candidato)
    for i in insights:
        if len(exemplos) >= 3:
            break
        if i not in exemplos:
            exemplos.append(i)
    return exemplos[:3]


def _gerar_exemplos_md(insights):
    exemplos = _escolher_exemplos(insights)
    linhas = [
        "# Exemplos de saida da IA generativa simulada",
        "",
        "Cada exemplo mostra o registro de entrada (saida do modelo de ML combinada",
        "com o contexto de sensor do talhao, quando disponivel) e o texto gerado pela",
        "camada de sintese de linguagem natural (`generate_insights.gerar_diagnostico`).",
        "",
    ]
    for idx, exemplo in enumerate(exemplos, start=1):
        linhas.append(f"## Exemplo {idx} -- {exemplo['entrada']['image']}")
        linhas.append("")
        linhas.append("**Entrada (JSON):**")
        linhas.append("```json")
        linhas.append(json.dumps(exemplo["entrada"], indent=2, ensure_ascii=False))
        linhas.append("```")
        linhas.append("")
        linhas.append("**Texto gerado:**")
        linhas.append("")
        linhas.append(f"> {exemplo['diagnostico_gerado']}")
        linhas.append("")

    with open("exemplos_ia_generativa.md", "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))


if __name__ == "__main__":
    gerar_insights(os.path.join(GOLD_DIR, "results.json"))
