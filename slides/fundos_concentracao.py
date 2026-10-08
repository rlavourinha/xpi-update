# -*- coding: utf-8 -*-
"""Slide: concentração da indústria de fundos (CVM, set/26). Gera slides/fundos_concentracao.html.
Dados: data/fundos_concentracao.json (de uma passada sobre data/_cvm_fundos_painel.csv.gz + cadastros)."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); D = json.load(open(os.path.join(HERE, "..", "data", "fundos_concentracao.json"), encoding="utf-8"))
VERSAO = "v1.0 · 08/10/2026"
def br(x, d=0): return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
A, B, C = D["2010-12"], D["2018-12"], D["2026-09"]; U = D["um_cotista"]

# ---- gráfico 1: curva de concentração (eixo x em log: fração dos fundos) ----
import math
W, H = 560, 395; ML, MR, MT, MB = 44, 16, 14, 34
xs = [0.001, 0.01, 0.1, 1.0]
def sx(f): return ML + (math.log10(f) + 3) / 3 * (W - ML - MR)
def sy(v): return MT + (1 - v) * (H - MT - MB)
g = [f'<line x1="{ML}" y1="{sy(t):.1f}" x2="{W-MR}" y2="{sy(t):.1f}" class="grid"/><text x="{ML-6}" y="{sy(t)+4:.1f}" class="ax" text-anchor="end">{int(t*100)}%</text>' for t in (0, .25, .5, .75, 1)]
for f, lab in zip(xs, ["0,1% dos fundos", "1%", "10%", "100%"]):
    g.append(f'<line x1="{sx(f):.1f}" y1="{MT}" x2="{sx(f):.1f}" y2="{H-MB}" class="grid"/><text x="{sx(f):.1f}" y="{H-12}" class="ax" text-anchor="middle">{lab}</text>')
COL = {"2010-12": "var(--s3)", "2018-12": "var(--s2)", "2026-09": "var(--s1)"}
lines = []
for k, S in (("2010-12", A), ("2018-12", B), ("2026-09", C)):
    pts = " ".join(f"{sx(f):.1f},{sy(v):.1f}" for f, v in S["lorenz"])
    lines.append(f'<polyline points="{pts}" fill="none" stroke="{COL[k]}" stroke-width="2" stroke-linejoin="round"/>')
# anotações 2026: 50% e 75%
for q in (0.5, 0.75):
    n = C["fundos_para"][str(q)]; f = n / C["n"]
    lines.append(f'<circle cx="{sx(f):.1f}" cy="{sy(q):.1f}" r="4" fill="var(--s1)" stroke="var(--surface)" stroke-width="2"/>'
                 f'<text x="{sx(f)-9:.1f}" y="{sy(q)-7:.1f}" class="lab" text-anchor="end"><tspan class="num">{n} fundos</tspan> = {int(q*100)}% do PL</text>')
svg1 = f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Curva de concentração do PL">{"".join(g)}{"".join(lines)}</svg>'
leg1 = '<div class="legend"><span><i style="background:var(--s1)"></i>set/26</span><span><i style="background:var(--s2)"></i>dez/18</span><span><i style="background:var(--s3)"></i>dez/10</span></div>'

# ---- gráfico 2: fundos de um cotista por faixa de PL (barras horizontais: nº e PL) ----
fx = U["faixas"]; rows = list(fx.items())
W2, H2 = 420, 200; bh = 22; gap = 18; y0 = 30
maxpl = max(v[1] for _, v in rows)
b = [f'<text x="0" y="14" class="lab">Fundos de um cotista só por tamanho, R$ bi (nº de fundos)</text>']
for i, (k, (n, pl)) in enumerate(rows):
    y = y0 + i * (bh + gap); w = pl / maxpl * (W2 - 170 - 125)
    b.append(f'<text x="0" y="{y+15}" class="lab2">{k}</text><rect x="170" y="{y}" width="{w:.1f}" height="{bh}" fill="var(--s1)" rx="3"/>'
             f'<text x="{170+w+8:.1f}" y="{y+15}" class="lab"><tspan class="num">{br(pl)}</tspan> ({br(n)} fundos)</text>')
svg2 = f'<svg viewBox="0 0 {W2} {H2}" width="100%" role="img" aria-label="Fundos de um cotista por faixa de PL">{"".join(b)}</svg>'

top = "".join(f'<tr><td>{i+1}</td><td>{t["gestor"]}</td><td>{t["classe"]}</td><td class="r">{br(t["pl_bi"],1)}</td><td class="r">{br(t["cotistas"])}</td></tr>' for i, t in enumerate(D["top10"][:8]))

html = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Concentração dos fundos</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{{--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--ink3:#8a8984;--grid:#e8e7e3;--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--green:#e6f4ea;--greenink:#14532d}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--s1:#3987e5;--s2:#d95926;--s3:#199e70;--green:#15301f;--greenink:#b7e4c7}}}}
:root[data-theme="dark"]{{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--s1:#3987e5;--s2:#d95926;--s3:#199e70;--green:#15301f;--greenink:#b7e4c7}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--surface);color:var(--ink);font:15px/1.35 Inter,system-ui,sans-serif}}
.slide{{max-width:1240px;margin:0 auto;padding:28px 32px 20px;min-height:720px;display:flex;flex-direction:column;gap:14px}}
header{{display:flex;justify-content:space-between;align-items:baseline;gap:16px}} header>div:first-child{{flex:1}} .kicker{{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink3)}}
h1{{font:600 28px/1.1 Fraunces,Georgia,serif;margin:4px 0 0}} .chip{{font-size:12px;color:var(--ink3);border:1px solid var(--grid);border-radius:999px;padding:3px 10px;white-space:nowrap}}
.grid2{{display:grid;grid-template-columns:1.35fr 1fr;gap:20px;align-items:stretch}} .col{{display:flex;flex-direction:column;gap:14px}}
.card{{border:1px solid var(--grid);border-radius:10px;padding:12px 14px}} .card h2{{font:600 14px/1.2 Inter,system-ui,sans-serif;margin:0 0 6px;color:var(--ink2)}}
.legend{{display:flex;gap:14px;font-size:12px;color:var(--ink2);margin:4px 0 0}} .legend i{{display:inline-block;width:14px;height:3px;vertical-align:middle;margin-right:5px;border-radius:2px}}
table{{width:100%;border-collapse:collapse;font-size:12.5px}} td,th{{padding:3px 6px;border-bottom:1px solid var(--grid);text-align:left}} th{{color:var(--ink3);font-weight:500}} .r{{text-align:right}}
.green{{background:var(--green);color:var(--greenink);border-radius:10px;padding:10px 14px;font-size:15px;font-weight:500}} .fonte{{font-size:11px;color:var(--ink3)}}
svg{{display:block}} svg .grid{{stroke:var(--grid);stroke-width:1}} svg .ax{{font:11px Inter,system-ui,sans-serif;fill:var(--ink3)}} svg .lab{{font:12.5px Inter,system-ui,sans-serif;fill:var(--ink)}} svg .lab2{{font:12.5px Inter,system-ui,sans-serif;fill:var(--ink2)}} svg .num{{font-weight:600}}
@media (max-width:860px){{.grid2{{grid-template-columns:1fr}}h1{{font-size:26px}}}}
</style></head><body><div class="slide">
<header><div><div class="kicker">parte 2 · a indústria</div><h1>{C["fundos_para"]["0.5"]} fundos têm metade do PL; metade dos fundos tem um só cotista</h1></div><span class="chip">{VERSAO} · set/26</span></header>
<div class="grid2">
 <div class="col"><div class="card" style="flex:1"><h2>Parcela do PL acumulada pelos maiores fundos (fundos 555, sem fundos de cotas)</h2>{svg1}{leg1}</div></div>
 <div class="col">
  <div class="card"><h2>Os maiores são renda fixa de banco</h2><table><tr><th>#</th><th>Gestor</th><th>Classe</th><th class="r">R$ bi</th><th class="r">Cotistas</th></tr>{top}</table></div>
  <div class="card">{svg2}</div>
 </div>
</div>
<div class="green">A concentração é a mesma de 2010: a indústria cresceu seis vezes sem mudar de formato, e o topo continua nos masters de renda fixa dos cinco bancos.</div>
<div class="fonte">Fonte: CVM, informes diários de fundos e cadastros, set/26; {br(C["n"])} fundos 555 sem fundos de cotas, PL R$ {br(C["pl_tri"],2).replace(".",",")} tri. Fundos de um cotista: {br(U["n"])} ({br(U["n"]/U["n_tot"]*100)}% dos fundos), R$ {br(U["pl_tri"],2).replace(".",",")} tri ({br(U["pl_tri"]/U["pl_tot"]*100)}% do PL): renda fixa R$ {br(U["por_classe"]["Renda Fixa"][1])} bi, multimercado R$ {br(U["por_classe"]["Multimercado"][1])} bi, ações R$ {br(U["por_classe"]["Ações"][1])} bi. Em dez/10 e dez/18, 50% do PL estava em {A["fundos_para"]["0.5"]} e {B["fundos_para"]["0.5"]} fundos. Gestoras XP: R$ {br(D["xp_gestor_bi"])} bi.</div>
</div></body></html>'''
out = os.path.join(HERE, "fundos_concentracao.html"); open(out, "w", encoding="utf-8").write(html); print("ok", out)
