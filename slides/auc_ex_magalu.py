# -*- coding: utf-8 -*-
"""Slide: valorização implícita do AuC de varejo da XP (nossa conta: ΔAuC − captação, sem as captações extraordinárias) e a mesma série
sem as custódias dos controladores da Magalu (entrada de R$ 78 bi no 3T20) e do grupo Ometto (R$ 26 bi no 1T21: CSAN3 do controlador e
bloco da Rumo da Cosan); marcação a mercado tirada do numerador e os blocos tirados da base. Mais o acumulado e o impacto anual em R$ bi.
Dados: data/xp_auc_valorizacao_ex_magalu.csv (analise_custodias_controladores.py). Gera slides/auc_ex_magalu.html."""
import csv, os
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "..", "data")
VERSAO = "v2.0 · 16/10/2026"
def br(x, d=1): return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".").replace("-", "−")
T = list(csv.DictReader(open(os.path.join(DATA, "xp_auc_valorizacao_ex_magalu.csv"), encoding="utf-8")))
Q = [r[""] for r in T]; n = len(Q)
S = {k: [float(r[k]) for r in T] for k in ["nossa_conta_pct", "ajustada_pct", "bottom_up_pct", "magalu_pct_auc", "magalu_bloco_bi", "magalu_mtm_bi", "ajustada_mo_pct", "ometto_mtm_bi", "ometto_pct_auc"]}
COL = {"nossa_conta_pct": "var(--s1)", "ajustada_mo_pct": "var(--s2)", "bottom_up_pct": "var(--ink3)"}
NOME = {"nossa_conta_pct": "Nossa conta", "ajustada_mo_pct": "Sem Magalu e Ometto", "bottom_up_pct": "Bottom-up"}
def lab(q): return q[0] + "T" + q[2:]  # 1Q21 -> 1T21

# ---- A: trimestral, barras lado a lado ----
W, H, ML, MR, MT, MB = 720, 444, 36, 8, 22, 28
vmin, vmax = -16, 12
def Y(v): return MT + (vmax - v) / (vmax - vmin) * (H - MT - MB)
gw = (W - ML - MR) / n; bw = (gw - 3) / 2
g = "".join(f'<line x1="{ML}" y1="{Y(t):.1f}" x2="{W-MR}" y2="{Y(t):.1f}" class="grid"/><text x="{ML-6}" y="{Y(t)+4:.1f}" class="ax" text-anchor="end">{br(t,0)}</text>' for t in range(-15, 11, 5))
# faixa em que os blocos dos controladores passaram de 5% do AuC de varejo
fx = [i for i in range(n) if S["magalu_pct_auc"][i] + S["ometto_pct_auc"][i] > 5]
x0, x1 = ML + fx[0] * gw, ML + (fx[-1] + 1) * gw
g += f'<rect x="{x0:.1f}" y="{MT-14}" width="{x1-x0:.1f}" height="{H-MB-MT+14}" class="band"/><text x="{(x0+x1)/2:.1f}" y="{MT-4}" class="ax" text-anchor="middle">custódias &gt; 5% do AuC de varejo</text>'
g += f'<line x1="{ML}" y1="{Y(0):.1f}" x2="{W-MR}" y2="{Y(0):.1f}" class="base"/>'
for i, q in enumerate(Q):
    for j, k in enumerate(["nossa_conta_pct", "ajustada_mo_pct"]):
        v = S[k][i]; vc = max(vmin, min(vmax, v)); x = ML + i * gw + 1.5 + j * bw
        g += (f'<rect x="{x:.1f}" y="{min(Y(0),Y(vc)):.1f}" width="{bw-1:.1f}" height="{max(abs(Y(vc)-Y(0)),0.8):.1f}" rx="1.5" fill="{COL[k]}">'
              f'<title>{lab(q)} · {NOME[k]}: {br(v,1)}%</title></rect>')
    if q.startswith("1Q"): g += f'<text x="{ML+i*gw+gw/2:.1f}" y="{H-8}" class="ax" text-anchor="middle">{"20"+q[2:]}</text>'
# rótulos seletivos onde a diferença é grande: empilhados na área vazia abaixo das barras, com linha-guia
# (4T21 na linha de cima, 1T21 na de baixo -> as guias não se cruzam)
lx = ML + Q.index("4Q21") * gw + gw + 8  # começa logo à direita do grupo do 4T21
for q, row in (("4Q21", -8.7), ("3Q21", -11.3), ("1Q21", -13.9)):
    i = Q.index(q); a, b = S["nossa_conta_pct"][i], S["ajustada_mo_pct"][i]
    cx, yb, yr = ML + i * gw + gw / 2, Y(min(a, b)) + 3, Y(row) - 3.5
    g += f'<polyline points="{cx:.1f},{yb:.1f} {cx:.1f},{yr:.1f} {lx-4:.1f},{yr:.1f}" fill="none" class="lead"/>'
    g += f'<text x="{lx:.1f}" y="{Y(row):.1f}" class="lab sm">{lab(q)}: <tspan class="num">{br(a,1)}</tspan> → <tspan class="num">{br(b,1)}</tspan></text>'
svgA = f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Valorização trimestral do AuC de varejo, %: nossa conta e sem Magalu e Ometto">{g}</svg>'

# ---- B: acumulado base 100 ----
def cum(v):
    out, a = [100.0], 100.0
    for x in v: a *= 1 + x / 100; out.append(a)
    return out
C = {k: cum(S[k]) for k in COL}
W2, H2, ML2, MR2, MT2, MB2 = 440, 200, 34, 150, 10, 26
cmin, cmax = 80, 220
def Y2(v): return MT2 + (cmax - v) / (cmax - cmin) * (H2 - MT2 - MB2)
def X2(i): return ML2 + i / n * (W2 - ML2 - MR2)
g2 = "".join(f'<line x1="{ML2}" y1="{Y2(t):.1f}" x2="{W2-MR2}" y2="{Y2(t):.1f}" class="grid"/><text x="{ML2-6}" y="{Y2(t)+4:.1f}" class="ax" text-anchor="end">{t}</text>' for t in range(100, cmax + 1, 40))
for i, q in enumerate(Q):
    if q.startswith("1Q") and q[2:] in ("19", "21", "23", "25"): g2 += f'<text x="{X2(i):.1f}" y="{H2-8}" class="ax" text-anchor="middle">{"20"+q[2:]}</text>'
ylab = []
for k in sorted(COL, key=lambda k: -C[k][-1]):
    pts = " ".join(f"{X2(i):.1f},{Y2(C[k][i]):.1f}" for i in range(n + 1))
    g2 += f'<polyline points="{pts}" fill="none" stroke="{COL[k]}" stroke-width="{1.5 if k=="bottom_up_pct" else 2.2}" stroke-linejoin="round"{" stroke-dasharray=\"4 3\"" if k=="bottom_up_pct" else ""}/>'
    y = Y2(C[k][-1])
    while any(abs(y - z) < 14 for z in ylab): y += 14
    ylab.append(y)
    g2 += f'<circle cx="{X2(n):.1f}" cy="{Y2(C[k][-1]):.1f}" r="3" fill="{COL[k]}" stroke="var(--surface)" stroke-width="1.5"><title>{NOME[k]}: {br(C[k][-1],1)}</title></circle><text x="{X2(n)+8:.1f}" y="{y+4:.1f}" class="lab"><tspan class="num">{br(C[k][-1],0)}</tspan> {NOME[k]}</text>'
svgB = f'<svg viewBox="0 0 {W2} {H2}" width="100%" role="img" aria-label="Acumulado desde o fim de 2018, base 100">{g2}</svg>'

# ---- C: impacto anual na valorização, R$ bi (barras lado a lado) ----
anos = sorted({"20" + q[2:] for q in Q if q[2:] >= "20"})
IMP = {k: {a: sum(S[k][i] for i, q in enumerate(Q) if "20" + q[2:] == a) for a in anos} for k in ("magalu_mtm_bi", "ometto_mtm_bi")}
CI = {"magalu_mtm_bi": "var(--s3)", "ometto_mtm_bi": "var(--s4)"}; NI = {"magalu_mtm_bi": "Magalu", "ometto_mtm_bi": "Grupo Ometto"}
W3, H3, ML3, MR3, MT3, MB3 = 440, 172, 34, 6, 16, 24
imin, imax = -80, 20  # folga abaixo de −67 (2021) para o rótulo não encostar no eixo
def Y3(v): return MT3 + (imax - v) / (imax - imin) * (H3 - MT3 - MB3)
gw3 = (W3 - ML3 - MR3) / len(anos); bw3 = (gw3 - 10) / 2
g3 = "".join(f'<line x1="{ML3}" y1="{Y3(t):.1f}" x2="{W3-MR3}" y2="{Y3(t):.1f}" class="grid"/><text x="{ML3-6}" y="{Y3(t)+4:.1f}" class="ax" text-anchor="end">{br(t,0)}</text>' for t in range(-60, 21, 20))
g3 += f'<line x1="{ML3}" y1="{Y3(0):.1f}" x2="{W3-MR3}" y2="{Y3(0):.1f}" class="base"/>'
for i, a in enumerate(anos):
    for j, k in enumerate(CI):
        v = IMP[k][a]; x = ML3 + i * gw3 + 5 + j * bw3
        g3 += f'<rect x="{x:.1f}" y="{min(Y3(0),Y3(v)):.1f}" width="{bw3-1:.1f}" height="{max(abs(Y3(v)-Y3(0)),0.8):.1f}" rx="2" fill="{CI[k]}"><title>{a} · {NI[k]}: R$ {br(v,1)} bi</title></rect>'
        if abs(v) >= 3: g3 += f'<text x="{x+bw3/2:.1f}" y="{(Y3(v)+12) if v < 0 else (Y3(v)-4):.1f}" class="lab sm" text-anchor="middle"><tspan class="num">{br(v,0)}</tspan></text>'
    g3 += f'<text x="{ML3+i*gw3+gw3/2:.1f}" y="{H3-6}" class="ax" text-anchor="middle">{a}{"*" if a=="2026" else ""}</text>'
svgC = f'<svg viewBox="0 0 {W3} {H3}" width="100%" role="img" aria-label="Impacto anual da marcação dos blocos na valorização do AuC de varejo, R$ bi: Magalu e grupo Ometto">{g3}</svg>'

# ---- números do texto ----
def acum(k, a, b): i, j = Q.index(a), Q.index(b) + 1; v = 1.0; [v := v * (1 + x / 100) for x in S[k][i:j]]; return (v - 1) * 100
mtm_m = sum(S["magalu_mtm_bi"]); mtm_o = sum(S["ometto_mtm_bi"])
cagr = lambda k: ((C[k][-1] / 100) ** (4 / n) - 1) * 100
html = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AuC sem custódias</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{{--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--ink3:#8a8984;--grid:#e8e7e3;--band:#f1f0ec;--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--s4:#eda100;--green:#e6f4ea;--greenink:#14532d}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--band:#232321;--s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500;--green:#15301f;--greenink:#b7e4c7}}}}
:root[data-theme="dark"]{{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--band:#232321;--s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500;--green:#15301f;--greenink:#b7e4c7}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--surface);color:var(--ink);font:15px/1.35 Inter,system-ui,sans-serif}}
.slide{{max-width:1240px;margin:0 auto;padding:24px 32px 16px;min-height:720px;display:flex;flex-direction:column;gap:12px}}
header{{display:flex;justify-content:space-between;align-items:baseline;gap:16px}} header>div:first-child{{flex:1}} .kicker{{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink3)}}
h1{{font:600 26px/1.1 Fraunces,Georgia,serif;margin:4px 0 0}} .chip{{font-size:12px;color:var(--ink3);border:1px solid var(--grid);border-radius:999px;padding:3px 10px;white-space:nowrap}}
.grid2{{display:grid;grid-template-columns:1.55fr 1fr;gap:16px;align-items:start}} .col{{display:flex;flex-direction:column;gap:12px}}
.card{{border:1px solid var(--grid);border-radius:10px;padding:10px 14px}} .card h2{{font:600 14px/1.2 Inter,system-ui,sans-serif;margin:0 0 6px;color:var(--ink2)}}
.legend{{display:flex;gap:14px;font-size:12px;color:var(--ink2);margin:2px 0 4px;flex-wrap:wrap}} .legend i{{display:inline-block;width:12px;height:12px;vertical-align:-2px;margin-right:5px;border-radius:3px}}
table{{border-collapse:collapse;width:100%;font-size:12px}} th{{text-align:left;vertical-align:bottom;white-space:nowrap;font-weight:600;color:var(--ink3);border-bottom:1px solid var(--grid);padding:3px 4px}} td{{padding:4px;border-bottom:1px solid var(--grid);vertical-align:top;color:var(--ink2)}} td.n{{text-align:right;white-space:nowrap;color:var(--ink);font-weight:600}} tr.top td{{color:var(--ink)}}
.green{{background:var(--green);color:var(--greenink);border-radius:10px;padding:10px 14px;font-size:15px;font-weight:500}} .fonte{{font-size:11px;color:var(--ink3)}}
svg{{display:block}} svg .grid{{stroke:var(--grid);stroke-width:1}} svg .base{{stroke:var(--ink3);stroke-width:1}} svg .lead{{stroke:var(--ink3);stroke-width:.8}} svg .band{{fill:var(--band)}} svg .ax{{font:11px Inter,system-ui,sans-serif;fill:var(--ink3)}} svg .lab{{font:12px Inter,system-ui,sans-serif;fill:var(--ink)}} svg .sm{{font-size:10.5px}} svg .num{{font-weight:600}}
@media (max-width:860px){{.grid2{{grid-template-columns:1fr}}h1{{font-size:22px}}}}
</style></head><body><div class="slide">
<header><div><div class="kicker">parte 3 · companhia · custódia de controladores</div><h1>Sem Magalu e Ometto, o AuC de varejo valorizou {br(C["ajustada_mo_pct"][-1]-100,0)}% desde 2019, e não {br(C["nossa_conta_pct"][-1]-100,0)}%</h1></div><span class="chip">{VERSAO}</span></header>
<div class="grid2">
 <div class="card"><h2>Valorização do AuC de varejo por trimestre, %</h2><div class="legend"><span><i style="background:var(--s1)"></i>Nossa conta (ΔAuC − captação, sem as captações extraordinárias)</span><span><i style="background:var(--s2)"></i>Sem Magalu e Ometto</span></div>{svgA}</div>
 <div class="col">
  <div class="card"><h2>Acumulado desde o fim de 2018, base 100, até o 2T26</h2>{svgB}</div>
  <div class="card"><h2>Impacto na valorização, R$ bi por ano  (* 2026 = 1º semestre)</h2><div class="legend"><span><i style="background:var(--s3)"></i>Magalu</span><span><i style="background:var(--s4)"></i>Grupo Ometto (Cosan + Rumo)</span></div>{svgC}</div>
 </div>
</div>
<div class="green">As duas custódias tiraram R$ {br(-mtm_m-mtm_o,0)} bi da valorização (Magalu R$ {br(-mtm_m,0)} bi, Ometto R$ {br(-mtm_o,0)} bi). Sem elas o AuC de varejo rende {br(cagr("ajustada_mo_pct"),1)}% ao ano desde 2019, contra {br(cagr("nossa_conta_pct"),1)}% na nossa conta e {br(cagr("bottom_up_pct"),1)}% no bottom-up.</div>
<div class="fonte">Fonte: XP RI (Retail Client Assets e Net Inflow; captação extraordinária de R$ 78 bi no 3T20, R$ 26 bi no 1T21 e R$ 34 bi da Modal no 3T23). Blocos: posição dos controladores no VLMO da CVM × fechamento no COTAHIST da B3. Magalu: 948,6 mi de MGLU3 (R$ 78 bi a R$ 82,2, preço de 10/07 a 17/08/20). Grupo Ometto, desde a reorganização da Cosan de 08/03/21: 140,5 mi de CSAN3 do controlador (562,7 mi após o desdobramento; o follow-on de nov/25 é dinheiro novo e fica fora) e 633,5 mi de RAIL3 da Cosan (448,8 mi após a venda via TRS em dez/25); ADS em Nova York fora. Ajustada = (valorização − marcação dos blocos) ÷ (AuC − blocos). Bottom-up como no slide anterior. A custódia em si não é pública: atribuição pelo tamanho e pela data.</div>
</div></body></html>'''
out = os.path.join(HERE, "auc_ex_magalu.html"); open(out, "w", encoding="utf-8").write(html)
print("ok", out, "| acum nossa", round(C["nossa_conta_pct"][-1], 1), "ajust", round(C["ajustada_mo_pct"][-1], 1), "bu", round(C["bottom_up_pct"][-1], 1), "| mtm", round(mtm_m, 1), round(mtm_o, 1), "| cagr", round(cagr("nossa_conta_pct"), 2), round(cagr("ajustada_mo_pct"), 2), round(cagr("bottom_up_pct"), 2))
