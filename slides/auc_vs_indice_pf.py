# -*- coding: utf-8 -*-
"""Slide: valorização implícita do AuC de varejo da XP vs o "índice da pessoa física" (Ibovespa ponderado por nº de acionistas PF),
Ibovespa e CDI, trimestral desde 1T20. Dados: data/xp_auc_vs_indice_pf.csv (de dados_indice_pf.py + xp_auc_nowcast). Gera slides/auc_vs_indice_pf.html."""
import csv, os
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "..", "data")
VERSAO = "v1.4 · 09/10/2026"
def br(x, d=1): return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".").replace("-", "−")
rows = list(csv.DictReader(open(os.path.join(DATA, "xp_auc_vs_indice_pf.csv"), encoding="utf-8")))
Q = [r[""] for r in rows]; n = len(Q)
S = {k: [float(r[k]) for r in rows] for k in ["auc_xp", "pf_count", "ibov", "ex_petr_vale", "cdi", "bottom_up_pf", "gap_pf", "gap_cvm"]}
def cum(v):
    out, a = [], 100.0
    for x in v: a *= 1 + x / 100; out.append(a)
    return out
C = {k: cum(S[k]) for k in ["auc_xp", "pf_count", "ibov", "cdi", "ex_petr_vale"]}
NOME = {"auc_xp": "AuC de varejo da XP (implícita)", "pf_count": "Índice da pessoa física", "ibov": "Ibovespa", "cdi": "CDI", "ex_petr_vale": "Ibov ex-PETR/VALE"}
COL = {"auc_xp": "var(--s1)", "pf_count": "var(--s2)", "ibov": "var(--ink3)", "cdi": "var(--s3)"}
def ql(q): return f"{q[0]}T{q[2:]}"

# ---- A: acumulado base 100 ----
W, H, ML, MR, MT, MB = 700, 412, 40, 200, 14, 30
cmin, cmax = 50, 200
def Y(v): return MT + (cmax - v) / (cmax - cmin) * (H - MT - MB)
def X(i): return ML + i / (n - 1) * (W - ML - MR)
g = "".join(f'<line x1="{ML}" y1="{Y(t):.1f}" x2="{W-MR}" y2="{Y(t):.1f}" class="grid"/><text x="{ML-6}" y="{Y(t)+4:.1f}" class="ax" text-anchor="end">{t}</text>' for t in range(cmin, cmax + 1, 50))
for i, q in enumerate(Q):
    if q.startswith("1Q"): g += f'<text x="{X(i):.1f}" y="{H-8}" class="ax" text-anchor="middle">20{q[2:]}</text>'
ln = ""; ylab = []
for k in ["ibov", "pf_count", "cdi", "auc_xp"]:
    pts = " ".join(f"{X(i):.1f},{Y(max(cmin,min(cmax,C[k][i]))):.1f}" for i in range(n))
    ln += f'<polyline points="{pts}" fill="none" stroke="{COL[k]}" stroke-width="{2.5 if k=="auc_xp" else 2}" stroke-linejoin="round"/>'
for k in sorted(COL, key=lambda k: -C[k][-1]):
    y = Y(C[k][-1])
    while any(abs(y - z) < 15 for z in ylab): y += 15
    ylab.append(y); ln += f'<circle cx="{X(n-1):.1f}" cy="{Y(C[k][-1]):.1f}" r="3.5" fill="{COL[k]}" stroke="var(--surface)" stroke-width="1.5"/><text x="{X(n-1)+8:.1f}" y="{y+4:.1f}" class="lab"><tspan class="num">{br(C[k][-1],0)}</tspan> {NOME[k]}</text>'
svgA = f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Acumulado desde o fim de 2019, base 100: AuC da XP, índice da pessoa física, Ibovespa e CDI">{g}{ln}</svg>'

# ---- B: anual, barras lado a lado ----
anos = sorted({"20" + q[2:] for q in Q}); ser = ["auc_xp", "pf_count", "ibov", "cdi"]
A = {k: {a: (cum([S[k][i] for i, q in enumerate(Q) if q.endswith(a[2:])])[-1] - 100) for a in anos} for k in ser}
W2, H2, ML2, MR2, MT2, MB2 = 440, 168, 36, 10, 16, 26
vmin, vmax = -20, 40
def Y2(v): return MT2 + (vmax - v) / (vmax - vmin) * (H2 - MT2 - MB2)
gw = (W2 - ML2 - MR2) / len(anos); bw = (gw - 8) / len(ser)
g2 = "".join(f'<line x1="{ML2}" y1="{Y2(t):.1f}" x2="{W2-MR2}" y2="{Y2(t):.1f}" class="grid"/><text x="{ML2-6}" y="{Y2(t)+4:.1f}" class="ax" text-anchor="end">{br(t,0)}</text>' for t in range(-20, 41, 20))
g2 += f'<line x1="{ML2}" y1="{Y2(0):.1f}" x2="{W2-MR2}" y2="{Y2(0):.1f}" class="base"/>'
for i, a in enumerate(anos):
    for j, k in enumerate(ser):
        v = max(vmin, min(vmax, A[k][a])); x = ML2 + i * gw + 4 + j * bw
        g2 += f'<rect x="{x:.1f}" y="{min(Y2(0),Y2(v)):.1f}" width="{bw-1:.1f}" height="{abs(Y2(v)-Y2(0)):.1f}" rx="2" fill="{COL[k]}"/>'
    g2 += f'<text x="{ML2+i*gw+gw/2:.1f}" y="{H2-8}" class="ax" text-anchor="middle">{a}{"*" if a=="2026" else ""}</text>'
svgB = f'<svg viewBox="0 0 {W2} {H2}" width="100%" role="img" aria-label="Retorno anual, %: AuC da XP, índice da pessoa física, Ibovespa e CDI">{g2}</svg>'

# ---- C: gap trimestral AuC − bottom-up com índice PF ----
W3, H3, ML3, MR3, MT3, MB3 = 440, 136, 36, 10, 16, 26
gmin, gmax = -12, 6
def Y3(v): return MT3 + (gmax - v) / (gmax - gmin) * (H3 - MT3 - MB3)
bw3 = (W3 - ML3 - MR3) / n
g3 = "".join(f'<line x1="{ML3}" y1="{Y3(t):.1f}" x2="{W3-MR3}" y2="{Y3(t):.1f}" class="grid"/><text x="{ML3-6}" y="{Y3(t)+4:.1f}" class="ax" text-anchor="end">{br(t,0)}</text>' for t in range(-12, 7, 6))
g3 += f'<line x1="{ML3}" y1="{Y3(0):.1f}" x2="{W3-MR3}" y2="{Y3(0):.1f}" class="base"/>'
for i, v in enumerate(S["gap_pf"]):
    v = max(gmin, min(gmax, v)); x = ML3 + i * bw3 + 1
    g3 += f'<rect x="{x:.1f}" y="{min(Y3(0),Y3(v)):.1f}" width="{bw3-2:.1f}" height="{abs(Y3(v)-Y3(0)):.1f}" rx="1.5" fill="{"var(--neg)" if v<0 else "var(--pos)"}"/>'
for i, q in enumerate(Q):
    if q.startswith("1Q"): g3 += f'<text x="{ML3+i*bw3+bw3/2:.1f}" y="{H3-8}" class="ax" text-anchor="middle">20{q[2:]}</text>'
k23 = [i for i, q in enumerate(Q) if int(q[2:]) >= 23]; gm = sum(S["gap_pf"][i] for i in k23) / len(k23); gm_cvm = sum(S["gap_cvm"][i] for i in k23) / len(k23)
g3 += f'<line x1="{ML3+k23[0]*bw3:.1f}" y1="{Y3(gm):.1f}" x2="{W3-MR3}" y2="{Y3(gm):.1f}" stroke="var(--ink2)" stroke-width="1" stroke-dasharray="3 3"/><text x="{ML3+4}" y="{MT3+10}" class="lab2">média 2023+: {br(gm,1)} pp/tri (linha pontilhada)</text>'
svgC = f'<svg viewBox="0 0 {W3} {H3}" width="100%" role="img" aria-label="Gap trimestral entre a valorização do AuC e o bottom-up com o índice da pessoa física, pontos percentuais">{g3}</svg>'

cagr = lambda v: ((v[-1] / 100) ** (4 / n) - 1) * 100
html = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AuC vs índice da pessoa física</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{{--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--ink3:#8a8984;--grid:#e8e7e3;--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--pos:#1baf7a;--neg:#e34948;--green:#e6f4ea;--greenink:#14532d}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--s1:#3987e5;--s2:#d95926;--s3:#3ccf96;--pos:#3ccf96;--neg:#e66767;--green:#15301f;--greenink:#b7e4c7}}}}
:root[data-theme="dark"]{{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--s1:#3987e5;--s2:#d95926;--s3:#3ccf96;--pos:#3ccf96;--neg:#e66767;--green:#15301f;--greenink:#b7e4c7}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--surface);color:var(--ink);font:15px/1.35 Inter,system-ui,sans-serif}}
.slide{{max-width:1240px;margin:0 auto;padding:24px 32px 16px;min-height:720px;display:flex;flex-direction:column;gap:12px}}
header{{display:flex;justify-content:space-between;align-items:baseline;gap:16px}} header>div:first-child{{flex:1}} .kicker{{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink3)}}
h1{{font:600 26px/1.1 Fraunces,Georgia,serif;margin:4px 0 0}} .chip{{font-size:12px;color:var(--ink3);border:1px solid var(--grid);border-radius:999px;padding:3px 10px;white-space:nowrap}}
.grid2{{display:grid;grid-template-columns:1.5fr 1fr;gap:16px;align-items:start}} .col{{display:flex;flex-direction:column;gap:12px}}
.card{{border:1px solid var(--grid);border-radius:10px;padding:10px 14px}} .card h2{{font:600 14px/1.2 Inter,system-ui,sans-serif;margin:0 0 6px;color:var(--ink2)}}
.legend{{display:flex;gap:14px;font-size:12px;color:var(--ink2);margin:2px 0 4px;flex-wrap:wrap}} .legend i{{display:inline-block;width:12px;height:12px;vertical-align:-2px;margin-right:5px;border-radius:3px}}
.green{{background:var(--green);color:var(--greenink);border-radius:10px;padding:10px 14px;font-size:15px;font-weight:500}} .fonte{{font-size:11px;color:var(--ink3)}}
svg{{display:block}} svg .grid{{stroke:var(--grid);stroke-width:1}} svg .base{{stroke:var(--ink3);stroke-width:1}} svg .ax{{font:11px Inter,system-ui,sans-serif;fill:var(--ink3)}} svg .lab{{font:12px Inter,system-ui,sans-serif;fill:var(--ink)}} svg .lab2{{font:11px Inter,system-ui,sans-serif;fill:var(--ink2)}} svg .num{{font-weight:600}}
@media (max-width:860px){{.grid2{{grid-template-columns:1fr}}h1{{font-size:24px}}}}
</style></head><body><div class="slide">
<header><div><div class="kicker">parte 3 · companhia</div><h1>AuC da XP +{br(C["auc_xp"][-1]-100,0)}%, carteira da PF na bolsa +{br(C["pf_count"][-1]-100,0)}%, CDI +{br(C["cdi"][-1]-100,0)}% desde 2019</h1></div><span class="chip">{VERSAO}</span></header>
<div class="grid2">
 <div class="card"><h2>Acumulado desde o fim de 2019, base 100, trimestral até o 2T26</h2>{svgA}</div>
 <div class="col">
  <div class="card"><h2>Retorno por ano, %  (* 2026 = 1º semestre)</h2><div class="legend"><span><i style="background:var(--s1)"></i>AuC XP</span><span><i style="background:var(--s2)"></i>Índice PF</span><span><i style="background:var(--ink3)"></i>Ibovespa</span><span><i style="background:var(--s3)"></i>CDI</span></div>{svgB}</div>
  <div class="card"><h2>Gap trimestral: AuC implícita − bottom-up com o índice PF na fatia de ações, pp</h2>{svgC}</div>
 </div>
</div>
<div class="green">Trocar o Ibovespa pelo índice da pessoa física na fatia de ações não fecha a conta: o gap médio desde 2023 vai de {br(gm_cvm,1)} para {br(gm,1)} pp por trimestre. A carteira da PF na bolsa, com teto de 8% por nome e sem o peso de Petrobras, rendeu {br(cagr(C["pf_count"]),1)}% ao ano contra {br(cagr(C["ibov"]),1)}% do Ibovespa e {br(cagr(C["cdi"]),1)}% do CDI; o AuC reportado da XP, {br(cagr(C["auc_xp"]),1)}% ao ano, fica abaixo de todos.</div>
<div class="fonte">Fonte: XP RI (Retail Client's Assets e Total Retail Net Inflow; valorização implícita = ΔAuC − captação líquida, inclui reclassificações); "índice da pessoa física" = constituintes do Ibovespa ponderados pelo número de acionistas pessoa física de cada companhia no Formulário de Referência (CVM, item 15, dados abertos 2019–2025), rebalanceado todo ano com o FRE do ano anterior, teto de 8% por companhia, retorno total com preços ajustados (yfinance) corrigidos pelo COTAHIST; Ibovespa retorno total; CDI (BCB SGS 12). Bottom-up = ações × índice PF + renda fixa × classe Renda Fixa CVM + fundos × fundos administrados pela XP + outros × Renda Fixa, pesos do início do trimestre. Limites: contagem de CPFs não é valor (bases herdadas de Vivo e TIM), FRE anual com cinco meses de defasagem.</div>
</div></body></html>'''
out = os.path.join(HERE, "auc_vs_indice_pf.html"); open(out, "w", encoding="utf-8").write(html); print("ok", out, "gap_pf", round(gm, 2), "gap_cvm", round(gm_cvm, 2))
