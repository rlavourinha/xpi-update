# -*- coding: utf-8 -*-
"""Slide: valorização implícita do AuC de varejo da XP (ΔAuC − captação líquida, do RI) vs retorno dos fundos na CVM
(bottom-up: classes CVM ponderadas pelo mix da XP; fundos administrados pela XP ex-tesouraria) e CDI.
Dados: data/xp_auc_nowcast.csv. Gera slides/auc_vs_fundos.html."""
import csv, os
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "..", "data")
VERSAO = "v1.1 · 08/10/2026"
def br(x, d=1): return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".").replace("-", "−")
rows = [r for r in csv.DictReader(open(os.path.join(DATA, "xp_auc_nowcast.csv"), encoding="utf-8")) if r["bottom-up"] and r["AuC varejo"]]
Q = [r[""] for r in rows]; n = len(Q)
S = {"xp": [float(r["AuC varejo"]) for r in rows], "bu": [float(r["bottom-up"]) for r in rows], "cdi": [float(r["CDI"]) for r in rows], "adm": [float(r["admin XP ex-tes"]) for r in rows]}
COL = {"xp": "var(--s1)", "bu": "var(--s2)", "cdi": "var(--s3)", "adm": "var(--ink3)"}
NOME = {"xp": "AuC de varejo da XP (implícita)", "bu": "Carteira do cliente (CVM)", "cdi": "CDI", "adm": "Fundos administrados pela XP"}
def cum(v):
    out, a = [], 100.0
    for x in v: a *= 1 + x / 100; out.append(a)
    return out
C = {k: cum(v) for k, v in S.items()}

# ---- A: trimestral, barras lado a lado (XP vs bottom-up) + linha do CDI ----
W, H, ML, MR, MT, MB = 1176, 200, 40, 16, 22, 24
vmin, vmax = -16, 12
def Y(v): return MT + (vmax - v) / (vmax - vmin) * (H - MT - MB)
def X(i): return ML + i / n * (W - ML - MR)
bw = (W - ML - MR) / n
g = "".join(f'<line x1="{ML}" y1="{Y(t):.1f}" x2="{W-MR}" y2="{Y(t):.1f}" class="grid"/><text x="{ML-6}" y="{Y(t)+4:.1f}" class="ax" text-anchor="end">{br(t,0)}</text>' for t in range(-15, 11, 5))
g += f'<line x1="{ML}" y1="{Y(0):.1f}" x2="{W-MR}" y2="{Y(0):.1f}" class="base"/>'
bars = ""
for i in range(n):
    for j, k in enumerate(["xp", "bu"]):
        v = max(vmin, min(vmax, S[k][i])); x = X(i) + 2 + j * (bw - 4) / 2
        bars += f'<rect x="{x:.1f}" y="{min(Y(0),Y(v)):.1f}" width="{(bw-4)/2-1:.1f}" height="{abs(Y(v)-Y(0)):.1f}" rx="2" fill="{COL[k]}"/>'
cdi = "".join(f'{X(i)+bw/2:.1f},{Y(S["cdi"][i]):.1f} ' for i in range(n))
bars += f'<polyline points="{cdi}" fill="none" stroke="{COL["cdi"]}" stroke-width="2" stroke-linejoin="round"/>'
for i, q in enumerate(Q):
    if q.startswith("1Q"): g += f'<text x="{X(i)+bw/2:.1f}" y="{H-8}" class="ax" text-anchor="middle">20{q[2:]}</text>'
# anotação covid
i20 = Q.index("1Q20"); g += f'<text x="{X(i20)+bw+4:.1f}" y="{Y(vmin)+4:.1f}" class="lab2">1T20: −15,0% vs −3,2%</text>'
svgA = f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Valorização trimestral do AuC de varejo da XP vs carteira do cliente pela CVM e CDI, % por trimestre">{g}{bars}</svg>'

# ---- B: acumulado base 100 ----
W2, H2, ML2, MR2, MT2, MB2 = 560, 188, 40, 206, 8, 28
cmax = 260
def Y2(v): return MT2 + (cmax - v) / (cmax - 100) * (H2 - MT2 - MB2)
def X2(i): return ML2 + i / (n - 1) * (W2 - ML2 - MR2)
g2 = "".join(f'<line x1="{ML2}" y1="{Y2(t):.1f}" x2="{W2-MR2}" y2="{Y2(t):.1f}" class="grid"/><text x="{ML2-6}" y="{Y2(t)+4:.1f}" class="ax" text-anchor="end">{t}</text>' for t in range(100, cmax + 1, 40))
for i, q in enumerate(Q):
    if q.startswith("1Q"): g2 += f'<text x="{X2(i):.1f}" y="{H2-8}" class="ax" text-anchor="middle">20{q[2:]}</text>'
ln = ""; ends = sorted(["bu", "cdi", "adm", "xp"], key=lambda k: -C[k][-1]); ylab = []
for k in ["adm", "cdi", "bu", "xp"]:
    pts = " ".join(f"{X2(i):.1f},{Y2(min(cmax,C[k][i])):.1f}" for i in range(n))
    ln += f'<polyline points="{pts}" fill="none" stroke="{COL[k]}" stroke-width="2" stroke-linejoin="round"/>'
for k in ends:
    y = Y2(C[k][-1])
    while any(abs(y - z) < 14 for z in ylab): y += 14
    ylab.append(y)
    ln += f'<circle cx="{X2(n-1):.1f}" cy="{Y2(C[k][-1]):.1f}" r="3.5" fill="{COL[k]}" stroke="var(--surface)" stroke-width="1.5"/><text x="{X2(n-1)+8:.1f}" y="{y+4:.1f}" class="lab"><tspan class="num">{br(C[k][-1],0)}</tspan> {NOME[k]}</text>'
svgB = f'<svg viewBox="0 0 {W2} {H2}" width="100%" role="img" aria-label="Acumulado desde o fim de 2018, base 100">{g2}{ln}</svg>'

# ---- C: gap anual ----
anos = sorted({"20" + q[2:] for q in Q}); gap = {a: sum(S["xp"][i] - S["bu"][i] for i, q in enumerate(Q) if q.endswith(a[2:])) for a in anos}
W3, H3, ML3, MR3, MT3, MB3 = 560, 128, 40, 16, 18, 24
gmin, gmax = -16, 4
def Y3(v): return MT3 + (gmax - v) / (gmax - gmin) * (H3 - MT3 - MB3)
bw3 = (W3 - ML3 - MR3) / len(anos)
g3 = "".join(f'<line x1="{ML3}" y1="{Y3(t):.1f}" x2="{W3-MR3}" y2="{Y3(t):.1f}" class="grid"/><text x="{ML3-6}" y="{Y3(t)+4:.1f}" class="ax" text-anchor="end">{br(t,0)}</text>' for t in range(-16, 5, 4))
g3 += f'<line x1="{ML3}" y1="{Y3(0):.1f}" x2="{W3-MR3}" y2="{Y3(0):.1f}" class="base"/>'
for i, a in enumerate(anos):
    v = gap[a]; x = ML3 + i * bw3 + 8
    g3 += f'<rect x="{x:.1f}" y="{min(Y3(0),Y3(v)):.1f}" width="{bw3-16:.1f}" height="{abs(Y3(v)-Y3(0)):.1f}" rx="3" fill="{"var(--neg)" if v < 0 else "var(--pos)"}"/>'
    g3 += f'<text x="{x+(bw3-16)/2:.1f}" y="{(Y3(v) if v > 0 else Y3(0))-5:.1f}" class="lab2" text-anchor="middle">{br(v,1)}</text><text x="{x+(bw3-16)/2:.1f}" y="{H3-8}" class="ax" text-anchor="middle">{a}{" (1S)" if a=="2026" else ""}</text>'
svgC = f'<svg viewBox="0 0 {W3} {H3}" width="100%" role="img" aria-label="Diferença anual entre a valorização do AuC e a carteira do cliente pela CVM, pontos percentuais">{g3}</svg>'

k23 = list(range(Q.index("1Q23"), n))
import statistics as st
corr = st.correlation([S["xp"][i] for i in k23], [S["bu"][i] for i in k23])
gm = sum(S["xp"][i] - S["bu"][i] for i in k23) / len(k23)
html = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AuC vs fundos</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{{--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--ink3:#8a8984;--grid:#e8e7e3;--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--pos:#1baf7a;--neg:#e34948;--green:#e6f4ea;--greenink:#14532d}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--s1:#3987e5;--s2:#d95926;--s3:#3ccf96;--pos:#3ccf96;--neg:#e66767;--green:#15301f;--greenink:#b7e4c7}}}}
:root[data-theme="dark"]{{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--s1:#3987e5;--s2:#d95926;--s3:#3ccf96;--pos:#3ccf96;--neg:#e66767;--green:#15301f;--greenink:#b7e4c7}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--surface);color:var(--ink);font:15px/1.35 Inter,system-ui,sans-serif}}
.slide{{max-width:1240px;margin:0 auto;padding:24px 32px 16px;min-height:720px;display:flex;flex-direction:column;gap:12px}}
header{{display:flex;justify-content:space-between;align-items:baseline;gap:16px}} header>div:first-child{{flex:1}} .kicker{{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink3)}}
h1{{font:600 26px/1.1 Fraunces,Georgia,serif;margin:4px 0 0}} .chip{{font-size:12px;color:var(--ink3);border:1px solid var(--grid);border-radius:999px;padding:3px 10px;white-space:nowrap}}
.card{{border:1px solid var(--grid);border-radius:10px;padding:10px 14px}} .card h2{{font:600 14px/1.2 Inter,system-ui,sans-serif;margin:0 0 6px;color:var(--ink2)}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.legend{{display:flex;gap:16px;font-size:12px;color:var(--ink2);margin:2px 0 4px;flex-wrap:wrap}} .legend i{{display:inline-block;width:12px;height:12px;vertical-align:-2px;margin-right:5px;border-radius:3px}} .legend i.l{{height:3px;vertical-align:3px;border-radius:2px}}
.green{{background:var(--green);color:var(--greenink);border-radius:10px;padding:10px 14px;font-size:15px;font-weight:500}} .fonte{{font-size:11px;color:var(--ink3)}}
svg{{display:block}} svg .grid{{stroke:var(--grid);stroke-width:1}} svg .base{{stroke:var(--ink3);stroke-width:1}} svg .ax{{font:11px Inter,system-ui,sans-serif;fill:var(--ink3)}} svg .lab{{font:12px Inter,system-ui,sans-serif;fill:var(--ink)}} svg .lab2{{font:11px Inter,system-ui,sans-serif;fill:var(--ink2)}} svg .num{{font-weight:600}}
@media (max-width:860px){{.grid2{{grid-template-columns:1fr}}h1{{font-size:24px}}}}
</style></head><body><div class="slide">
<header><div><div class="kicker">parte 3 · companhia</div><h1>O AuC da XP rende {br(-gm,1)} pp/tri menos que a carteira do cliente</h1></div><span class="chip">{VERSAO} · RI 2T26</span></header>
<div class="card"><h2>Por trimestre, %: valorização implícita do AuC de varejo (ΔAuC − captação líquida) vs retorno das classes de fundos na CVM ponderado pelo mix da XP</h2>
<div class="legend"><span><i style="background:var(--s1)"></i>AuC de varejo da XP (implícita)</span><span><i style="background:var(--s2)"></i>Carteira do cliente pela CVM (bottom-up)</span><span><i class="l" style="background:var(--s3)"></i>CDI</span></div>{svgA}</div>
<div class="grid2">
 <div class="card"><h2>Acumulado desde dez/18, base 100</h2>{svgB}</div>
 <div class="card"><h2>Diferença anual AuC − bottom-up, pontos percentuais</h2>{svgC}
 <div class="fonte" style="margin-top:6px">Correlação trimestral desde 2023: {br(corr,2)}. Correlação com o trimestre seguinte: zero. A cota diz o que o AuC fez, não o que fará.</div></div>
</div>
<div class="green">A direção bate (correlação {br(corr,2)}), o nível não: desde 2023 o AuC reportado valoriza {br(-gm,1)} pp por trimestre, uns 6 pp por ano, menos que a carteira do cliente pela CVM. Ou a captação líquida divulgada contém renda e rotação de produto, ou o AuC marca abaixo do mercado; nas duas leituras o NNM orgânico é menor que o reportado.</div>
<div class="fonte">Fonte: XP RI, planilha Historical Financials 2T26 (Retail Client's Assets, Total Retail Net Inflow, mix por produto); CVM, informes diários de fundos (retorno mensal = ΔPL − captação + resgate sobre o PL anterior, fundos ex-FIC) por classe (ações, renda fixa) e dos fundos administrados pela XP Investimentos CCTVM excluídos os 13 de tesouraria; BCB SGS 12 (CDI). Bottom-up = ações × classe Ações + renda fixa × classe Renda Fixa + fundos × fundos administrados pela XP + outros × Renda Fixa, pesos do início do trimestre. Valorização implícita inclui qualquer reclassificação de AuC.</div>
</div></body></html>'''
out = os.path.join(HERE, "auc_vs_fundos.html"); open(out, "w", encoding="utf-8").write(html); print("ok", out, "trimestres:", n, Q[0], Q[-1], "corr23", round(corr, 2), "gap", round(gm, 2))
