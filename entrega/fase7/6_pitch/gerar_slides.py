"""
Gera os slides do pitch do AgroSmart:
  slides/AgroSmart_Pitch.pptx       apresentacao (PowerPoint)
  slides/preview/slide_N.png        imagens de cada slide (para conferir e para o video)

Os slides sao descritos UMA vez (lista de formas, em polegadas) e renderizados em dois formatos:
.pptx (python-pptx) e HTML -> PNG (Chrome headless). Uso: python gerar_slides.py
Requer python-pptx (pip install python-pptx) e Google Chrome para as imagens.
"""
import os
import html
import subprocess
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
SAIDA = os.path.join(AQUI, "slides")
PREVIEW = os.path.join(SAIDA, "preview")
IMG_DASH = os.path.join(RAIZ, "entrega", "fase7", "2_execucao", "prints", "dashboard_container_topo.png")

W, H = 13.333, 7.5
VERDE_ESC, VERDE, VERMELHO, AMBAR = "1F4D2B", "2E7D32", "C62828", "F9A825"
SALVIA, TINTA, MUDO, BRANCO, CARTAO = "E8F0E6", "1B2A22", "55665B", "FFFFFF", "F3F7F2"
TITULO, CORPO = "Cambria", "Calibri"
EQUIPE = ("Turma ESOA4 · Cayo Gonçalves de Morais Malara · Igor Nunes Teixeira · "
          "Lorenzo Guimarães · Thiago Bullara Leite")


# ------------------------------------------------------------------ construtores de formas
def txt(x, y, w, h, paras, size=16, bold=False, color=TINTA, font=CORPO, align="l", valign="t", space=6):
    """paras: str ou lista de str/(str, dict) com sobrescritas de size/bold/color/font."""
    if isinstance(paras, str):
        paras = [paras]
    return dict(t="text", x=x, y=y, w=w, h=h, paras=paras, size=size, bold=bold, color=color, font=font,
                align=align, valign=valign, space=space)


def caixa(x, y, w, h, fill, forma="round"):
    return dict(t=forma, x=x, y=y, w=w, h=h, fill=fill)


def circulo(x, y, d, fill, texto="", size=20, color=BRANCO):
    f = dict(t="circle", x=x, y=y, w=d, h=d, fill=fill)
    f["texto"] = dict(paras=[texto], size=size, bold=True, color=color, font=CORPO)
    return f


def imagem(x, y, w, h, caminho):
    return dict(t="img", x=x, y=y, w=w, h=h, path=caminho)


def titulo(texto, cor=VERDE_ESC):
    return txt(0.6, 0.4, 12.1, 0.95, texto, size=34, bold=True, color=cor, font=TITULO, valign="m")


def rodape(n, cor=MUDO):
    return [txt(0.6, 7.0, 9, 0.3, "AgroSmart · Fase 7 · Turma ESOA4", size=11, color=cor),
            txt(11.7, 7.0, 1.0, 0.3, str(n), size=11, color=cor, align="r")]


# ------------------------------------------------------------------ slides
def slides():
    S = []

    # 1. capa
    S.append(dict(bg=VERDE_ESC, notas=(
        "(0:00-0:20) Somos o grupo da turma ESOA4. Este é o AgroSmart: uma plataforma que acompanha o pomar com sensores e "
        "fotos de folhas e diz, talhão por talhão, o que fazer. Vamos mostrar o problema, a solução, o diferencial, "
        "para quem é e como vira negócio."), formas=[
        caixa(8.7, 1.5, 3.6, 3.6, VERMELHO, "circle"), caixa(10.2, 0.9, 1.3, 0.75, VERDE, "circle"),
        txt(0.8, 1.7, 7.6, 1.4, "AgroSmart", size=66, bold=True, color=BRANCO, font=TITULO, valign="m"),
        txt(0.8, 3.2, 7.4, 1.6, "Da folha à decisão: diagnóstico precoce de doenças em pomares de maçã", size=26, color="DCEBD9"),
        txt(0.8, 5.5, 11.5, 0.9, [EQUIPE, ("Entrega final · Fase 7", dict(bold=True))], size=14, color="DCEBD9"),
    ]))

    # 2. problema
    cards = [("Pouca mão de obra qualificada", "Reconhecer a doença cedo exige quem entenda de campo, e esse profissional é escasso."),
             ("Trabalho dobrado e desperdício", "Sem saber onde está o problema, o produtor trata o pomar inteiro e gasta pesticida à toa."),
             ("Sem previsão da safra", "Sem dado contínuo, não há como antecipar perdas nem planejar o manejo.")]
    f = [titulo("A Podridão Negra avança entre inspeções"),
         txt(0.6, 1.7, 4.6, 4.6, [
             "A Podridão Negra (Black Rot) ataca folhas, frutos e galhos da macieira.",
             "Em pomares grandes, a inspeção manual é lenta e cara; a doença pode avançar entre uma visita e a próxima.",
             ("Resultado: tratar tarde, tratar demais, ou os dois.", dict(bold=True, color=VERMELHO))], size=19, space=14)]
    for i, (t, d) in enumerate(cards):
        y = 1.7 + i * 1.65
        f += [caixa(5.6, y, 7.1, 1.45, CARTAO), circulo(5.85, y + 0.4, 0.65, VERMELHO, str(i + 1)),
              txt(6.8, y + 0.15, 5.7, 0.45, t, size=19, bold=True, color=VERDE_ESC),
              txt(6.8, y + 0.62, 5.7, 0.8, d, size=14, color=MUDO)]
    S.append(dict(bg=BRANCO, formas=f + rodape(2), notas=(
        "(0:20-0:50) A Podridão Negra afeta folhas, frutos e galhos. As dores que ouvimos do produtor são três: falta de gente "
        "qualificada, trabalho dobrado e desperdício de insumos, e falta de previsão da safra.")))

    # 3. solução
    passos = [("Medir", "Sensores de solo, ar, temperatura e luz, mais fotos das folhas de cada talhão."),
              ("Analisar", "Visão computacional mede a área doente; o ambiente do talhão mede o quanto o fungo é favorecido."),
              ("Decidir", "Alerta, nível de risco e ação recomendada, em linguagem natural, por talhão.")]
    f = [titulo("Uma plataforma que mede, analisa e decide")]
    for i, (t, d) in enumerate(passos):
        x = 0.6 + i * 4.25
        f += [caixa(x, 1.9, 3.85, 3.9, CARTAO), circulo(x + 0.35, 2.2, 0.9, VERDE, str(i + 1), size=28),
              txt(x + 0.35, 3.3, 3.2, 0.6, t, size=28, bold=True, color=VERDE_ESC, font=TITULO),
              txt(x + 0.35, 4.0, 3.2, 1.7, d, size=16, color=TINTA)]
        if i < 2:
            f.append(txt(x + 3.85, 3.4, 0.4, 0.8, "›", size=44, bold=True, color=VERDE, align="c", valign="m"))
    f.append(txt(0.6, 6.15, 12.1, 0.6, "Um único fluxo, do campo ao dashboard, rodando em container e sem intervenção manual.",
                 size=18, color=MUDO))
    S.append(dict(bg=BRANCO, formas=f + rodape(3), notas=(
        "(0:50-1:20) A solução tem três passos. Medir: sensores e fotos. Analisar: visão computacional na folha mais o ambiente do "
        "talhão. Decidir: alerta, risco e ação recomendada. Tudo roda de ponta a ponta, em container, sem intervenção manual.")))

    # 4. funcionando
    itens = [("Valor atual e média", "de cada sensor, com comparação"), ("Decisão por talhão", "prioridade e ação recomendada"),
             ("Alertas com ação", "gerados na hora, também ao vivo"), ("Diagnóstico escrito", "em linguagem natural, por folha")]
    f = [titulo("Funcionando: o que o produtor vê"), imagem(0.6, 1.6, 8.1, 5.06, IMG_DASH)]
    for i, (t, d) in enumerate(itens):
        y = 1.6 + i * 1.28
        f += [caixa(9.0, y, 3.75, 1.12, CARTAO), txt(9.2, y + 0.1, 3.4, 0.45, t, size=17, bold=True, color=VERDE_ESC),
              txt(9.2, y + 0.55, 3.4, 0.5, d, size=13, color=MUDO)]
    f.append(txt(0.6, 6.72, 8.1, 0.3, "Dashboard real servido pelo container; dados de sensores simulados.", size=11, color=MUDO))
    S.append(dict(bg=BRANCO, formas=f + rodape(4), notas=(
        "(1:20-2:00) Este é o dashboard real. Mostra o valor atual e a média de cada sensor, a decisão por talhão, os alertas com a "
        "ação recomendada e o diagnóstico escrito de cada folha. Os dados de sensor são simulados nesta fase.")))

    # 5. diferencial
    dif = [("Imagem + ambiente", "O risco da folha soma a lesão (70%) ao ambiente do talhão: umidade, temperatura e solo (30%)."),
           ("Decisão, não só dado", "Cada talhão recebe prioridade e ação concreta, em vez de gráficos para interpretar."),
           ("Opera e se monitora", "Container, execução agendada, painel de saúde, logs e pipeline de segurança."),
           ("Melhora com os próprios dados", "A análise de processo achou o gargalo; a predição por folha ficou 3,7× mais rápida.")]
    f = [titulo("O que nos diferencia")]
    for i, (t, d) in enumerate(dif):
        x, y = 0.6 + (i % 2) * 6.15, 1.7 + (i // 2) * 2.55
        f += [caixa(x, y, 5.95, 2.35, CARTAO), circulo(x + 0.3, y + 0.3, 0.7, VERDE, str(i + 1), size=22),
              txt(x + 1.2, y + 0.3, 4.5, 0.7, t, size=20, bold=True, color=VERDE_ESC, valign="m"),
              txt(x + 0.3, y + 1.15, 5.4, 1.1, d, size=15, color=TINTA)]
    S.append(dict(bg=BRANCO, formas=f + rodape(5), notas=(
        "(2:00-2:40) Quatro diferenciais. Um: combinamos imagem e ambiente. Dois: entregamos decisão, não só dado. Três: o sistema "
        "opera e se monitora sozinho. Quatro: usamos o log do próprio sistema para achar e corrigir gargalos; a predição por folha ficou "
        "3,7 vezes mais rápida.")))

    # 6. pronto para operar
    est = [("39", "execuções automáticas monitoradas", "0 falhas registradas"),
           ("9", "verificações no pipeline DevSecOps", "ruff, testes, bandit, pip-audit, trivy e container"),
           ("3,7×", "predição por folha mais rápida", "de 46 ms para 13 ms após a análise de processo")]
    f = [titulo("Pronto para operar, não só para demonstrar")]
    for i, (n, t, d) in enumerate(est):
        x = 0.6 + i * 4.25
        f += [caixa(x, 1.8, 3.85, 3.9, VERDE_ESC), txt(x + 0.3, 2.1, 3.3, 1.3, n, size=64, bold=True, color=BRANCO, font=TITULO, valign="m"),
              txt(x + 0.3, 3.5, 3.3, 0.9, t, size=20, bold=True, color="DCEBD9"), txt(x + 0.3, 4.4, 3.3, 1.2, d, size=14, color="B9D3B6")]
    f.append(txt(0.6, 6.05, 12.1, 0.7, "Números reais da nossa base de execuções e do pipeline local. Dados de campo ainda são simulados.", size=14, color=MUDO))
    S.append(dict(bg=BRANCO, formas=f + rodape(6), notas=(
        "(2:40-3:10) Não é só um protótipo de tela. Temos 39 execuções automáticas monitoradas sem falha, um pipeline com 9 verificações "
        "de qualidade e segurança, e uma melhoria de desempenho medida no log. Deixamos claro que os dados de campo ainda são simulados.")))

    # 7. público-alvo
    pub = [("Quem paga", "Fruticultores de maçã", "Produtores médios e grandes, com vários talhões, que não conseguem inspecionar tudo com frequência."),
           ("Como chegamos", "Cooperativas e consultorias", "Compram para vários produtores e usam o painel para priorizar as visitas dos agrônomos."),
           ("Quem usa os dados", "Seguradoras agrícolas", "Usam o índice de risco agregado e anônimo para precificar melhor, e podem dar desconto a quem monitora.")]
    f = [titulo("Para quem é")]
    for i, (r, t, d) in enumerate(pub):
        x = 0.6 + i * 4.25
        f += [caixa(x, 1.8, 3.85, 4.3, CARTAO), txt(x + 0.35, 2.05, 3.2, 0.4, r.upper(), size=12, bold=True, color=VERDE),
              txt(x + 0.35, 2.5, 3.2, 1.2, t, size=24, bold=True, color=VERDE_ESC, font=TITULO), txt(x + 0.35, 3.8, 3.2, 2.2, d, size=16)]
    S.append(dict(bg=BRANCO, formas=f + rodape(7), notas=(
        "(3:10-3:40) Três públicos. Quem paga: fruticultores de maçã com vários talhões. O canal: cooperativas e consultorias, que "
        "compram para muitos produtores. E as seguradoras, que usam o índice de risco agregado e anônimo.")))

    # 8. valor e receita
    f = [titulo("Proposta de valor e como gera receita"),
         caixa(0.6, 1.7, 5.9, 4.9, CARTAO), txt(0.9, 1.85, 5.3, 0.5, "Proposta de valor", size=22, bold=True, color=VERDE_ESC, font=TITULO),
         txt(0.9, 2.5, 5.3, 4.0, [("Detectar cedo e tratar com precisão", dict(bold=True)), "Menos safra perdida.",
                                  ("Tratar só onde precisa", dict(bold=True)), "Menos desperdício de pesticida.",
                                  ("Operar em escala, sem equipe grande", dict(bold=True)), "Um painel para todos os talhões."], size=17, space=8),
         caixa(6.85, 1.7, 5.9, 4.9, VERDE_ESC), txt(7.15, 1.85, 5.3, 0.5, "Fontes de receita (hipóteses)", size=22, bold=True, color=BRANCO, font=TITULO),
         txt(7.15, 2.5, 5.3, 4.0, [("Assinatura por talhão monitorado", dict(bold=True)), "Básico: imagem. Pro: sensores e alertas.",
                                   ("Kit de sensores", dict(bold=True)), "Venda ou locação, mais manutenção.",
                                   ("Consultoria automatizada", dict(bold=True)), "Relatórios e comparativo entre safras.",
                                   ("Dados e parcerias", dict(bold=True)), "Índice de risco para seguradoras e insumos."], size=16, color="E6F0E4", space=7)]
    S.append(dict(bg=BRANCO, formas=f + rodape(8), notas=(
        "(3:40-4:20) A proposta de valor: detectar cedo, tratar só onde precisa e operar em escala. Para a receita temos quatro "
        "hipóteses: assinatura por talhão, kit de sensores, consultoria automatizada e dados e parcerias. São hipóteses a validar com "
        "produtores, não resultados.")))

    # 9. hoje e próximos passos
    f = [titulo("Onde estamos e para onde vamos"),
         caixa(0.6, 1.7, 5.9, 4.4, CARTAO), txt(0.9, 1.85, 5.3, 0.5, "Hoje", size=22, bold=True, color=VERDE_ESC, font=TITULO),
         txt(0.9, 2.5, 5.3, 3.5, ["Protótipo funcional ponta a ponta", "Sensores e cenários simulados", "Modelo treinado com imagens públicas de folhas",
                                  "Container, CI, monitoramento e análise de processo"], size=17, space=10),
         caixa(6.85, 1.7, 5.9, 4.4, CARTAO), txt(7.15, 1.85, 5.3, 0.5, "Próximos passos", size=22, bold=True, color=VERMELHO, font=TITULO),
         txt(7.15, 2.5, 5.3, 3.5, ["Sensores reais em um pomar-piloto", "Validar o modelo com fotos e agrônomos de campo",
                                   "Ajustar os limiares de risco com dados reais", "Testar o modelo de assinatura com cooperativas"], size=17, space=10),
         txt(0.6, 6.25, 12.1, 0.6, "AgroSmart: tratar o pomar certo, na hora certa.", size=24, bold=True, color=VERDE_ESC, font=TITULO)]
    S.append(dict(bg=BRANCO, formas=f + rodape(9), notas=(
        "(4:20-4:50) Hoje temos um protótipo funcional com dados simulados. O próximo passo é um pomar-piloto com sensores reais, "
        "validar o modelo com agrônomos e testar a assinatura com cooperativas. AgroSmart: tratar o pomar certo, na hora certa. Obrigado.")))
    return S



# ------------------------------------------------------------------ render PPTX
def rgb(h):
    return RGBColor.from_string(h)


def _estilo_run(run, size, bold, color, font):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = rgb(color)
    run.font.name = font


def _paras(tf, paras, base, align="l", space=6):
    tf.word_wrap = True
    for i, p in enumerate(paras):
        texto, ov = (p, {}) if isinstance(p, str) else p
        par = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        par.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[align]
        par.space_after = Pt(space)
        r = par.add_run()
        r.text = texto
        _estilo_run(r, ov.get("size", base["size"]), ov.get("bold", base["bold"]), ov.get("color", base["color"]),
                    ov.get("font", base["font"]))


def para_pptx(specs, destino):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(W), Inches(H)
    for s in specs:
        sl = prs.slides.add_slide(prs.slide_layouts[6])
        fundo = sl.background.fill
        fundo.solid()
        fundo.fore_color.rgb = rgb(s["bg"])
        for f in s["formas"]:
            x, y, w, h = (Inches(f[k]) for k in ("x", "y", "w", "h"))
            if f["t"] == "text":
                tb = sl.shapes.add_textbox(x, y, w, h)
                tf = tb.text_frame
                tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
                tf.vertical_anchor = {"t": MSO_ANCHOR.TOP, "m": MSO_ANCHOR.MIDDLE}[f["valign"]]
                _paras(tf, f["paras"], f, f["align"], f["space"])
            elif f["t"] == "img":
                sl.shapes.add_picture(f["path"], x, y, width=w, height=h)
            else:
                tipo = {"rect": MSO_SHAPE.RECTANGLE, "round": MSO_SHAPE.ROUNDED_RECTANGLE, "circle": MSO_SHAPE.OVAL}[f["t"]]
                sh = sl.shapes.add_shape(tipo, x, y, w, h)
                if f["t"] == "round":
                    sh.adjustments[0] = 0.06
                sh.fill.solid()
                sh.fill.fore_color.rgb = rgb(f["fill"])
                sh.line.fill.background()
                sh.shadow.inherit = False
                if "texto" in f:
                    tf = sh.text_frame
                    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
                    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
                    _paras(tf, f["texto"]["paras"], f["texto"], "c", 0)
        sl.notes_slide.notes_text_frame.text = s["notas"]
    prs.save(destino)


# ------------------------------------------------------------------ render HTML -> PNG
def para_html(s, caminho):
    css = ("<style>body{margin:0}#s{position:relative;width:1280px;height:720px;overflow:hidden;font-family:Calibri,Carlito,"
           "'Helvetica Neue',Arial,sans-serif}.a{position:absolute;box-sizing:border-box}p{margin:0}</style>")
    out = [f'<html><head><meta charset="utf-8">{css}</head><body><div id="s" style="background:#{s["bg"]}">']
    px = 96
    for f in s["formas"]:
        pos = f'left:{f["x"] * px:.1f}px;top:{f["y"] * px:.1f}px;width:{f["w"] * px:.1f}px;height:{f["h"] * px:.1f}px'
        if f["t"] == "img":
            out.append(f'<img class="a" src="file://{f["path"]}" style="{pos}">')
            continue
        if f["t"] == "text":
            ali = {"t": "flex-start", "m": "center"}[f["valign"]]
            ps = ""
            for p in f["paras"]:
                t, ov = (p, {}) if isinstance(p, str) else p
                sz = ov.get("size", f["size"]) * px / 72
                fonte = ov.get("font", f["font"])
                familia = "Georgia,serif" if fonte == TITULO else "inherit"
                alin = {"l": "left", "c": "center", "r": "right"}[f["align"]]
                ps += (f'<p style="font-size:{sz:.1f}px;font-weight:{700 if ov.get("bold", f["bold"]) else 400};'
                       f'color:#{ov.get("color", f["color"])};font-family:{familia};'
                       f'margin-bottom:{f["space"] * px / 72:.1f}px;text-align:{alin}">{html.escape(t)}</p>')
            out.append(f'<div class="a" style="{pos};display:flex;flex-direction:column;justify-content:{ali};align-items:stretch;'
                       f'line-height:1.2">{ps}</div>')
            continue
        radius = "50%" if f["t"] == "circle" else ("10px" if f["t"] == "round" else "0")
        inner = ""
        if "texto" in f:
            tx = f["texto"]
            inner = (f'<span style="font-size:{tx["size"] * px / 72:.1f}px;font-weight:700;color:#{tx["color"]}">'
                     f'{html.escape(tx["paras"][0])}</span>')
        out.append(f'<div class="a" style="{pos};background:#{f["fill"]};border-radius:{radius};display:flex;align-items:center;'
                   f'justify-content:center">{inner}</div>')
    out.append("</div></body></html>")
    with open(caminho, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))


def main():
    specs = slides()
    os.makedirs(PREVIEW, exist_ok=True)
    para_pptx(specs, os.path.join(SAIDA, "AgroSmart_Pitch.pptx"))
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if os.path.exists(chrome):
        for i, s in enumerate(specs, start=1):
            h = os.path.join(PREVIEW, f"slide_{i}.html")
            para_html(s, h)
            subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=1280,720",
                            f"--screenshot={os.path.join(PREVIEW, f'slide_{i}.png')}", "file://" + h], capture_output=True)
            os.remove(h)
    print(f"[slides] {len(specs)} slides em {SAIDA}")


if __name__ == "__main__":
    main()
