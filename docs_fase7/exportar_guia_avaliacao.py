"""Gera GUIA_AVALIACAO.html: o guia sem os blocos 'time' (amarelo) e 'rm' (vermelho).
Os blocos removiveis estao entre <!--CUT:tipo--> e <!--/CUT--> no HTML de origem."""
import re
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
origem = open(os.path.join(AQUI, "GUIA_DA_ENTREGA.html"), encoding="utf-8").read()
limpo = re.sub(r"<!--CUT:(?:time|rm)-->.*?<!--/CUT-->", "", origem, flags=re.S)
# remove os controles de visibilidade, que nao fazem sentido na versao de avaliacao
limpo = re.sub(r'<div class="ctrl">.*?</div>', "", limpo, flags=re.S)
limpo = limpo.replace("Guia da entrega", "Guia da entrega (avaliação)")
saida = os.path.join(AQUI, "GUIA_AVALIACAO.html")
open(saida, "w", encoding="utf-8").write(limpo)
print(f"Gerado {saida}: {len(origem)} -> {len(limpo)} bytes; blocos removidos: "
      f"{len(re.findall(r'<!--CUT:', origem))}")
