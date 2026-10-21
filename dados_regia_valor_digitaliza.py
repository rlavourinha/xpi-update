# -*- coding: utf-8 -*-
"""Digitaliza o gráfico da Régia Capital publicado no Valor (13/10/2026, "Após recorde, spread de papel incentivado supera o do comum"):
IDA-IPCA Infraestrutura com gross-up e IDA-DI, % a.a., out/21 a out/26. A arte é um JPG de 1000 px (a maior versão publicada):
fontes/setor/valor/regia_spread_1000.jpg.

Calibração:
  eixo Y: linhas de grade de 0,0 a 5,0 detectadas por linha de pixels escuros (passo ~32,9 px por 0,5 p.p.), ajuste linear;
  eixo X: linhas pontilhadas de abr/22 a out/26 (dia 1º do mês), ajuste linear dias → pixel (~0,46 px por dia, ~2,2 dias por coluna).
Cor: linha verde-escura (incentivadas com gross-up) e azul-clara (DI), separadas da área verde-clara da diferença e da grade.
Por coluna de pixel, o valor é a média das linhas de pixel da cor. Resolução: ~0,015 p.p. por pixel no eixo Y, mais a espessura
da linha (~3 px); erro típico ±0,03-0,05 p.p. Os rótulos da matéria (2,89; 1,40; 1,50) servem de conferência no fim da série.
Saída: data/regia_valor_digitalizado.csv (data, infra_gu, di_spread, dif)."""
import os, datetime as dt
import numpy as np, pandas as pd
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
im = np.asarray(Image.open(os.path.join(HERE, "fontes", "setor", "valor", "regia_spread_1000.jpg")).convert("RGB")).astype(int)
R, G, B = im[..., 0], im[..., 1], im[..., 2]
# ---- eixo Y: grade
dark = im.sum(axis=2) < 450
lin = [y for y in range(230, 600) if dark[y, 60:990].mean() > 0.8]
grupos = []
for y in lin:
    if grupos and y - grupos[-1][-1] <= 2: grupos[-1].append(y)
    else: grupos.append([y])
yg = [float(np.mean(g)) for g in grupos]                       # de cima (5,0) para baixo (0,0); falta a de 1,5 (sob o tracejado laranja)
vals = []
for y in yg:                                                    # atribui o valor pela distância ao topo em passos de ~32,9 px
    vals.append(round(5.0 - round((y - yg[0]) / 32.85) * 0.5, 1))
ay = np.polyfit(yg, vals, 1)                                    # valor = a*y + b
# ---- eixo X: pontilhadas (frequência alta de pixels escuros na coluna), ignora a borda esquerda
cols = [x for x in range(100, 995) if dark[250:580, x].mean() > 0.25]
gx = []
for x in cols:
    if gx and x - gx[-1][-1] <= 2: gx[-1].append(x)
    else: gx.append([x])
xs = [float(np.mean(g)) for g in gx]
datas = [dt.date(2022, 4, 1), dt.date(2022, 10, 1), dt.date(2023, 4, 1), dt.date(2023, 10, 1), dt.date(2024, 4, 1), dt.date(2024, 10, 1),
         dt.date(2025, 4, 1), dt.date(2025, 10, 1), dt.date(2026, 4, 1), dt.date(2026, 10, 1)]
assert len(xs) == len(datas), (xs, len(datas))
d0 = dt.date(2021, 10, 1)
ax = np.polyfit([(d - d0).days for d in datas], xs, 1)          # pixel = a*dias + b
res_x = np.array(xs) - np.polyval(ax, [(d - d0).days for d in datas])
# ---- cores
verde = (G - R > 50) & (G - B > 20) & (im.sum(axis=2) < 420)    # linha verde-escura
azul = (B - R > 60) & (B >= G) & (R < 190)                      # linha azul-clara
rows = []
for x in range(70, 925):
    yv = [y for y in range(240, 590) if verde[y, x]]; yb = [y for y in range(240, 590) if azul[y, x]]
    dias = (x - ax[1]) / ax[0]
    d = d0 + dt.timedelta(days=float(dias))
    rows.append({"x": x, "data": d.isoformat(), "infra_gu": float(np.polyval(ay, np.mean(yv))) if len(yv) >= 2 else None,
                 "di_spread": float(np.polyval(ay, np.mean(yb))) if len(yb) >= 2 else None})
D = pd.DataFrame(rows)
D = D[D.infra_gu.notna() | D.di_spread.notna()]
D["dif"] = D.infra_gu - D.di_spread
D.drop(columns="x").round(3).to_csv(os.path.join(HERE, "data", "regia_valor_digitalizado.csv"), index=False)
print("grade Y:", [round(y, 1) for y in yg], "→", vals, "| p.p./px", round(-ay[0], 4))
print("pontilhadas X:", [round(x, 1) for x in xs], "| px/dia", round(ax[0], 4), "| resíduo máx", round(abs(res_x).max(), 2), "px")
print("pontos:", len(D), D.data.min(), "→", D.data.max())
print(D.tail(6).round(2).to_string(index=False))
