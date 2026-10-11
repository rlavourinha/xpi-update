# -*- coding: utf-8 -*-
"""Slide: CDI, valorização implícita do AuC de varejo da XP e uma carteira teórica de renda fixa marcada na curva (pré 2a + IPCA+ 5a,
originada mês a mês à ETTJ da ANBIMA), trimestral desde 1T19. Testa a hipótese "a XP marca na curva e o pré antigo rende menos que o CDI".
Dados: data/xp_auc_gap_vs_curva_accrual.csv e data/xp_auc_nowcast.csv. Gera slides/auc_vs_curva.html."""
import csv, os
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "..", "data")
VERSAO = "v1.5 · 11/10/2026"
def br(x, d=1): return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".").replace("-", "−")
T = {r[""]: r for r in csv.DictReader(open(os.path.join(DATA, "xp_auc_gap_vs_curva_accrual.csv"), encoding="utf-8"))}
N = {r[""]: r for r in csv.DictReader(open(os.path.join(DATA, "xp_auc_nowcast.csv"), encoding="utf-8"))}
Q = sorted(T); n = len(Q)
def nq(q): return q[5] + "Q" + q[2:4]  # 2019Q1 -> 1Q19 (chave do nowcast)
S = {"cdi": [float(T[q]["CDI"]) for q in Q], "auc": [float(N[nq(q)]["AuC varejo"]) for q in Q], "gap": [float(T[q]["gap"]) for q in Q],
     "pre": [float(T[q]["pre2y"]) for q in Q], "ipca": [float(T[q]["ipca5y"]) for q in Q]}
S["curva"] = [0.5 * a + 0.5 * b for a, b in zip(S["pre"], S["ipca"])]; S["curva_cdi"] = [c - d for c, d in zip(S["curva"], S["cdi"])]
def cum(v):
    out, a = [], 100.0
    for x in v: a *= 1 + x / 100; out.append(a)
    return out
C = {k: cum(S[k]) for k in ["cdi", "auc", "curva", "pre", "ipca"]}
COL = {"auc": "var(--s1)", "curva": "var(--s2)", "cdi": "var(--s3)", "pre": "var(--ink3)", "ipca": "var(--ink3)"}
NOME = {"auc": "AuC XP (implícita)", "curva": "Carteira na curva", "cdi": "CDI", "pre": "só pré 2a", "ipca": "só IPCA+ 5a"}

# ---- A: acumulado base 100 ----
W, H, ML, MR, MT, MB = 700, 400, 40, 190, 14, 30
cmin, cmax = 90, 230
def Y(v): return MT + (cmax - v) / (cmax - cmin) * (H - MT - MB)
def X(i): return ML + i / (n - 1) * (W - ML - MR)
g = "".join(f'<line x1="{ML}" y1="{Y(t):.1f}" x2="{W-MR}" y2="{Y(t):.1f}" class="grid"/><text x="{ML-6}" y="{Y(t)+4:.1f}" class="ax" text-anchor="end">{t}</text>' for t in range(100, cmax + 1, 25))
for i, q in enumerate(Q):
    if q.endswith("Q1"): g += f'<text x="{X(i):.1f}" y="{H-8}" class="ax" text-anchor="middle">{q[:4]}</text>'
ln = ""
for k in ["pre", "ipca", "cdi", "curva", "auc"]:
    pts = " ".join(f"{X(i):.1f},{Y(max(cmin,min(cmax,C[k][i]))):.1f}" for i in range(n))
    ln += f'<polyline points="{pts}" fill="none" stroke="{COL[k]}" stroke-width="{2.5 if k in("auc","curva") else 1.2 if k in("pre","ipca") else 2}" stroke-linejoin="round"{" stroke-dasharray=\"3 3\"" if k in ("pre","ipca") else ""}/>'
ylab = []
for k in sorted(COL, key=lambda k: -C[k][-1]):
    y = Y(C[k][-1])
    while any(abs(y - z) < 14 for z in ylab): y += 14
    ylab.append(y); ln += f'<circle cx="{X(n-1):.1f}" cy="{Y(C[k][-1]):.1f}" r="3" fill="{COL[k]}" stroke="var(--surface)" stroke-width="1.5"/><text x="{X(n-1)+8:.1f}" y="{y+4:.1f}" class="lab"><tspan class="num">{br(C[k][-1],0)}</tspan> {NOME[k]}</text>'
svgA = f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Acumulado desde o fim de 2018, base 100: CDI, AuC da XP e carteira de renda fixa na curva">{g}{ln}</svg>'

# ---- B: anual ----
anos = sorted({q[:4] for q in Q}); ser = ["auc", "curva", "cdi"]
A = {k: {a: cum([S[k][i] for i, q in enumerate(Q) if q.startswith(a)])[-1] - 100 for a in anos} for k in ser}
W2, H2, ML2, MR2, MT2, MB2 = 440, 160, 36, 10, 16, 26
vmin, vmax = -10, 20
def Y2(v): return MT2 + (vmax - v) / (vmax - vmin) * (H2 - MT2 - MB2)
gw = (W2 - ML2 - MR2) / len(anos); bw = (gw - 8) / len(ser)
g2 = "".join(f'<line x1="{ML2}" y1="{Y2(t):.1f}" x2="{W2-MR2}" y2="{Y2(t):.1f}" class="grid"/><text x="{ML2-6}" y="{Y2(t)+4:.1f}" class="ax" text-anchor="end">{br(t,0)}</text>' for t in range(-10, 21, 10))
g2 += f'<line x1="{ML2}" y1="{Y2(0):.1f}" x2="{W2-MR2}" y2="{Y2(0):.1f}" class="base"/>'
for i, a in enumerate(anos):
    for j, k in enumerate(ser):
        v = max(vmin, min(vmax, A[k][a])); x = ML2 + i * gw + 4 + j * bw
        g2 += f'<rect x="{x:.1f}" y="{min(Y2(0),Y2(v)):.1f}" width="{bw-1:.1f}" height="{abs(Y2(v)-Y2(0)):.1f}" rx="2" fill="{COL[k]}"/>'
    g2 += f'<text x="{ML2+i*gw+gw/2:.1f}" y="{H2-8}" class="ax" text-anchor="middle">{a}{"*" if a=="2026" else ""}</text>'
svgB = f'<svg viewBox="0 0 {W2} {H2}" width="100%" role="img" aria-label="Retorno anual, %: AuC da XP, carteira na curva e CDI">{g2}</svg>'

# ---- C: trimestral, carteira na curva − CDI vs gap do AuC ----
W3, H3, ML3, MR3, MT3, MB3 = 440, 150, 36, 10, 16, 26
gmin, gmax = -8, 4
def Y3(v): return MT3 + (gmax - v) / (gmax - gmin) * (H3 - MT3 - MB3)
bw3 = (W3 - ML3 - MR3) / n
g3 = "".join(f'<line x1="{ML3}" y1="{Y3(t):.1f}" x2="{W3-MR3}" y2="{Y3(t):.1f}" class="grid"/><text x="{ML3-6}" y="{Y3(t)+4:.1f}" class="ax" text-anchor="end">{br(t,0)}</text>' for t in range(-8, 5, 4))
g3 += f'<line x1="{ML3}" y1="{Y3(0):.1f}" x2="{W3-MR3}" y2="{Y3(0):.1f}" class="base"/>'
for i in range(n):
    for j, (k, col) in enumerate([("curva_cdi", COL["curva"]), ("gap", COL["auc"])]):
        v = max(gmin, min(gmax, S[k][i])); x = ML3 + i * bw3 + 1 + j * (bw3 - 2) / 2
        g3 += f'<rect x="{x:.1f}" y="{min(Y3(0),Y3(v)):.1f}" width="{(bw3-2)/2-0.5:.1f}" height="{abs(Y3(v)-Y3(0)):.1f}" fill="{col}"/>'
for i, q in enumerate(Q):
    if q.endswith("Q1"): g3 += f'<text x="{ML3+i*bw3+bw3/2:.1f}" y="{H3-8}" class="ax" text-anchor="middle">{q[:4]}</text>'
svgC = f'<svg viewBox="0 0 {W3} {H3}" width="100%" role="img" aria-label="Por trimestre: carteira na curva menos CDI e gap do AuC, pontos percentuais">{g3}</svg>'
k23 = [i for i, q in enumerate(Q) if int(q[:4]) >= 2023]; m_gap = sum(S["gap"][i] for i in k23) / len(k23); m_cur = sum(S["curva_cdi"][i] for i in k23) / len(k23)
k2021 = [i for i, q in enumerate(Q) if q[:4] in ("2020", "2021")]; s_gap = sum(S["gap"][i] for i in k2021); s_cur = sum(S["curva_cdi"][i] for i in k2021)
import statistics as st; corr = st.correlation(S["gap"], S["curva_cdi"])
cagr = lambda v: ((v[-1] / 100) ** (4 / n) - 1) * 100
html = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AuC vs carteira na curva</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{{--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--ink3:#8a8984;--grid:#e8e7e3;--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--green:#e6f4ea;--greenink:#14532d}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--s1:#3987e5;--s2:#d95926;--s3:#3ccf96;--green:#15301f;--greenink:#b7e4c7}}}}
:root[data-theme="dark"]{{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--s1:#3987e5;--s2:#d95926;--s3:#3ccf96;--green:#15301f;--greenink:#b7e4c7}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--surface);color:var(--ink);font:15px/1.35 Inter,system-ui,sans-serif}}
.slide{{max-width:1240px;margin:0 auto;padding:24px 32px 16px;min-height:720px;display:flex;flex-direction:column;gap:12px}}
header{{display:flex;justify-content:space-between;align-items:baseline;gap:16px}} header>div:first-child{{flex:1}} .kicker{{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink3)}}
h1{{font:600 26px/1.1 Fraunces,Georgia,serif;margin:4px 0 0}} .chip{{font-size:12px;color:var(--ink3);border:1px solid var(--grid);border-radius:999px;padding:3px 10px;white-space:nowrap}}
.grid2{{display:grid;grid-template-columns:1.5fr 1fr;gap:16px;align-items:start}} .col{{display:flex;flex-direction:column;gap:12px}}
.card{{border:1px solid var(--grid);border-radius:10px;padding:10px 14px}} .card h2{{font:600 14px/1.2 Inter,system-ui,sans-serif;margin:0 0 6px;color:var(--ink2)}}
.legend{{display:flex;gap:14px;font-size:12px;color:var(--ink2);margin:2px 0 4px;flex-wrap:wrap}} .legend i{{display:inline-block;width:12px;height:12px;vertical-align:-2px;margin-right:5px;border-radius:3px}}
.green{{background:var(--green);color:var(--greenink);border-radius:10px;padding:10px 14px;font-size:15px;font-weight:500}} .fonte{{font-size:11px;color:var(--ink3)}}
svg{{display:block}} svg .grid{{stroke:var(--grid);stroke-width:1}} svg .base{{stroke:var(--ink3);stroke-width:1}} svg .ax{{font:11px Inter,system-ui,sans-serif;fill:var(--ink3)}} svg .lab{{font:12px Inter,system-ui,sans-serif;fill:var(--ink)}} svg .num{{font-weight:600}}
@media (max-width:860px){{.grid2{{grid-template-columns:1fr}}h1{{font-size:24px}}}}
</style></head><body><div class="slide">
<header><div><div class="kicker">parte 3 · companhia · teste: marcação na curva</div><h1>Carteira na curva rendeu {br(cagr(C["curva"]),1)}% ao ano, o CDI {br(cagr(C["cdi"]),1)}%, o AuC da XP {br(cagr(C["auc"]),1)}%</h1></div><span class="chip">{VERSAO}</span></header>
<div class="grid2">
 <div class="card"><h2>Acumulado desde o fim de 2018, base 100, trimestral até o 2T26</h2>{svgA}</div>
 <div class="col">
  <div class="card"><h2>Retorno por ano, %  (* 2026 = 1º semestre)</h2><div class="legend"><span><i style="background:var(--s1)"></i>AuC XP</span><span><i style="background:var(--s2)"></i>Carteira na curva</span><span><i style="background:var(--s3)"></i>CDI</span></div>{svgB}</div>
  <div class="card"><h2>Por trimestre, pp: carteira na curva − CDI (laranja) e gap do AuC vs bottom-up (azul)</h2>{svgC}</div>
 </div>
</div>
<div class="green">Marcação na curva não explica o gap. Em 2020-21 os cupons antigos teriam feito a carteira bater o CDI em {br(s_cur,1)} pp, e o AuC ficou {br(-s_gap,1)} pp abaixo do esperado. Desde 2023 a carteira na curva rende {br(-m_cur,1)} pp por trimestre abaixo do CDI contra um gap de {br(-m_gap,1)}, e a correlação trimestral entre as duas séries é {br(corr,2)}.</div>
<div class="fonte">Fonte: carteira teórica na curva = 50% pré de 2 anos + 50% IPCA+ de 5 anos, cada um originado mês a mês à taxa da ETTJ da ANBIMA do mês e carregado até o vencimento (estoque = últimas 24 e 60 safras, pesos iguais), IPCA realizado (IBGE/BCB SGS 433); linhas pontilhadas = cada perna isolada. AuC XP = valorização implícita do Retail Client's Assets (ΔAuC − Net Inflow, XP RI). CDI: BCB SGS 12. Gap = AuC implícita − bottom-up (ações × Ibovespa + renda fixa × fundos RF CVM + fundos × fundos administrados pela XP + outros × RF).</div>
</div></body></html>'''
out = os.path.join(HERE, "auc_vs_curva.html"); open(out, "w", encoding="utf-8").write(html)
print("ok", out, "| cagr curva", round(cagr(C["curva"]), 2), "auc", round(cagr(C["auc"]), 2), "cdi", round(cagr(C["cdi"]), 2), "| 2020-21 curva-cdi", round(s_cur, 1), "gap", round(s_gap, 1), "| 2023+ médias", round(m_cur, 2), round(m_gap, 2), "| corr", round(corr, 2))
