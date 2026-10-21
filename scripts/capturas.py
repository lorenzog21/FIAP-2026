"""
Gera capturas de evidencia para a entrega (precisa de playwright e do Chrome instalado;
nao faz parte do requirements do projeto).

  python scripts/capturas.py dashboard <pasta_saida> [prefixo] [url]
  python scripts/capturas.py terminal  <arquivo_texto> <png_saida> "<titulo>"

'terminal' renderiza o conteudo de um arquivo de texto (saida real de um comando) como
imagem estilo terminal. Nao e um print da janela do terminal.
"""
import sys
import html
from playwright.sync_api import sync_playwright

SECOES = [("topo", None), ("series", "Evolução dos sensores"), ("folhas", "Folhas analisadas"),
          ("alertas", "Alertas e recomendações automáticas")]


def dashboard(saida, prefixo="dashboard", url="http://localhost:8501"):
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome")
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        pg.goto(url)
        pg.wait_for_selector("text=Monitoramento e apoio", timeout=60000)
        pg.wait_for_timeout(5000)
        for nome, titulo in SECOES:
            if titulo:
                pg.get_by_role("heading", name=titulo).first.scroll_into_view_if_needed()
                pg.evaluate("window.scrollBy(0,-20)")
                pg.wait_for_timeout(1500)
            pg.screenshot(path=f"{saida}/{prefixo}_{nome}.png")
        b.close()


def terminal(arquivo, png, titulo, largura=1200):
    texto = open(arquivo, encoding="utf-8").read()
    doc = (f"<html><body style='margin:0;background:#1e1e1e'><div style='width:{largura}px;font-family:Menlo,monospace;"
           f"font-size:13px;color:#d4d4d4'><div style='background:#323233;padding:8px 14px;color:#aaa;font-family:Helvetica;"
           f"font-size:13px'>● ● ●&nbsp;&nbsp; {html.escape(titulo)}</div><pre style='margin:0;padding:14px;line-height:1.45;"
           f"white-space:pre-wrap'>{html.escape(texto)}</pre></div></body></html>")
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome")
        pg = b.new_page(viewport={"width": largura, "height": 200})
        pg.set_content(doc)
        pg.screenshot(path=png, full_page=True)
        b.close()


if __name__ == "__main__":
    modo = sys.argv[1]
    if modo == "dashboard":
        dashboard(*sys.argv[2:])
    elif modo == "terminal":
        terminal(*sys.argv[2:5])
    else:
        sys.exit(__doc__)
