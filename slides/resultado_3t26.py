# -*- coding: utf-8 -*-
"""Slide: resultado do 3T26 (XP Inc., 6-K de 16/11/2026). Quatro números, receita por linha 3T25 x 3T26 (barras lado a lado) e o
yield da renda fixa sem o efeito da captação (decomposição de analise_receita_originacao.py, coeficientes estimados até 2T26).
Dados: data/historical_financials.json (planilha do RI 3Q26), data/xp_rf_decomposicao_tri.csv, preço XPBR31 de 16/11/26.
Só dado público: nada do modelo do usuário nem de sell-side. Gera slides/resultado_3t26.html."""
import csv, json, os
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "..", "data")
VERSAO = "v1.0 · 16/11/2026"
PRECO, ACOES = 85.79, 506.778525          # XPBR31 em 16/11/26; ações em circulação em 30/09/26 (DFs, nota 1.1)
DIV, RECOMPRA = 1.3, 1.5                   # R$ bi anunciados em 16/11/26 (6-K): dividendo de US$ 0.46/ação e programa de recompra
def br(x, d=1): return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".").replace("-", "−")
J = json.load(open(os.path.join(DATA, "historical_financials.json"), encoding="utf-8"))
P, K, H = J["3. Managerial P&L - new"], J["2. KPIs"], J["1. Highlights - new"]
LL = P["Adjusted Net Income"]  # release: R$ 1.382 mi, +4% a/a
RA = K["Retail Client's Assets (in R$ million)"] if "Retail Client's Assets (in R$ million)" in K else K[[k for k in K if k.startswith("Retail Client")][0]]
def tr(q, q0): return P["Retail"][q] * 4 / ((RA[q] + RA[q0]) / 2) * 100   # take rate = receita de varejo anualizada ÷ AuC médio (bate com o release)
NNM = K["Total Retail Net Inflow (in R$ million)"]
ll3, ll3a = LL["3Q26"], LL["3Q25"]; tr3, tr2 = tr("3Q26", "2Q26"), tr("2Q26", "1Q26"); nnm3 = NNM["3Q26"] / 1e3
mcap = PRECO * ACOES / 1e3; ret = (DIV + RECOMPRA) / mcap * 100
LIN = [("Equities", "Ações"), ("Fixed Income", "Renda fixa"), ("Funds Platform", "Fundos"), ("Other Retail Revenue", "Outros varejo"),
       ("Cards", "Cartões"), ("Retirement Plans", "Previdência"), ("Credit", "Crédito"), ("Insurance", "Seguros"),
       ("Corporate", "Corporate"), ("Institutional", "Institucional"), ("Issuer Services", "Issuer services")]
V = [(nome, P[k]["3Q25"], P[k]["3Q26"]) for k, nome in LIN]
# ---- A: barras horizontais lado a lado ----
W, ROW, ML, MR, MT = 560, 24, 108, 70, 6; H_ = MT + ROW * len(V) + 22
vmax = 1300
def X(v): return ML + v / vmax * (W - ML - MR)
g = "".join(f'<line x1="{X(t):.1f}" y1="{MT}" x2="{X(t):.1f}" y2="{H_-18}" class="grid"/><text x="{X(t):.1f}" y="{H_-4}" class="ax" text-anchor="middle">{br(t,0)}</text>' for t in range(0, vmax + 1, 250))
for i, (nome, a, b) in enumerate(V):
    y = MT + i * ROW; var = (b / a - 1) * 100
    g += f'<text x="{ML-8}" y="{y+16}" class="lab" text-anchor="end">{nome}</text>'
    g += f'<rect x="{ML}" y="{y+3}" width="{X(a)-ML:.1f}" height="10" rx="2" fill="var(--s4)"><title>{nome} 3T25: R$ {br(a,0)} mi</title></rect>'
    g += f'<rect x="{ML}" y="{y+13}" width="{X(b)-ML:.1f}" height="10" rx="2" fill="var(--s1)"><title>{nome} 3T26: R$ {br(b,0)} mi</title></rect>'
    cor = "var(--pos)" if var >= 0 else "var(--neg)"
    g += f'<text x="{max(X(a),X(b))+6:.1f}" y="{y+16}" class="lab sm"><tspan class="num">{br(b,0)}</tspan> <tspan fill="{cor}">{"+" if var>=0 else ""}{br(var,0)}%</tspan></text>'
svgA = f'<svg viewBox="0 0 {W} {H_}" width="100%" role="img" aria-label="Receita bruta por linha, R$ milhões, 3T25 contra 3T26">{g}</svg>'
# ---- B: yield da renda fixa sem o efeito da captação, % a.a. ----
R = [r for r in csv.DictReader(open(os.path.join(DATA, "xp_rf_decomposicao_tri.csv"), encoding="utf-8")) if r["avg"]]
Q = [r[""] for r in R]; Y = [(float(r["R"]) - float(r["n"])) / float(r["avg"]) * 400 for r in R]
OBS = [float(r["R"]) / float(r["avg"]) * 400 for r in R]
W2, H2, ML2, MR2, MT2, MB2 = 440, 290, 34, 64, 12, 24; y0, y1 = 0.3, 1.3   # H2: mesma altura renderizada do gráfico A a 1280 px; y1 cobre o máximo observado (1,24 no 2T21)
def X2(i): return ML2 + i / (len(Q) - 1) * (W2 - ML2 - MR2)
def Y2(v): return MT2 + (y1 - min(max(v, y0), y1)) / (y1 - y0) * (H2 - MT2 - MB2)
g2 = "".join(f'<line x1="{ML2}" y1="{Y2(t):.1f}" x2="{W2-MR2}" y2="{Y2(t):.1f}" class="grid"/><text x="{ML2-5}" y="{Y2(t)+4:.1f}" class="ax" text-anchor="end">{br(t,1)}</text>' for t in (0.3, 0.5, 0.7, 0.9, 1.1, 1.3))
for i, q in enumerate(Q):
    if q.endswith("Q1"): g2 += f'<text x="{X2(i):.1f}" y="{H2-6}" class="ax" text-anchor="middle">{q[:4]}</text>'
g2 += f'<polyline points="{" ".join(f"{X2(i):.1f},{Y2(v):.1f}" for i, v in enumerate(OBS))}" fill="none" stroke="var(--ink3)" stroke-width="1.2" stroke-dasharray="4 3"/>'
g2 += f'<polyline points="{" ".join(f"{X2(i):.1f},{Y2(v):.1f}" for i, v in enumerate(Y))}" fill="none" stroke="var(--s1)" stroke-width="2.2" stroke-linejoin="round"/>'
i25 = Q.index("2025Q1")
for i in (len(Q) - 1, len(Q) - 2, i25):
    g2 += f'<circle cx="{X2(i):.1f}" cy="{Y2(Y[i]):.1f}" r="4" fill="var(--s1)" stroke="var(--surface)" stroke-width="2"><title>{Q[i]}: {br(Y[i],2)}% a.a.</title></circle>'
g2 += f'<text x="{X2(len(Q)-1)+8:.1f}" y="{Y2(Y[-1])+4:.1f}" class="lab"><tspan class="num">{br(Y[-1],2)}%</tspan></text>'
g2 += f'<text x="{X2(i25):.1f}" y="{Y2(max(OBS[i25-1:i25+2]))-7:.1f}" class="lab sm" text-anchor="middle">{br(Y[i25],2)}%</text>'   # acima da linha tracejada
svgB = f'<svg viewBox="0 0 {W2} {H2}" width="100%" role="img" aria-label="Receita de renda fixa sobre o AuC de renda fixa, % ao ano, com e sem o efeito da captação líquida">{g2}</svg>'
TILES = [(f"R$ {br(ll3/1e3,2)} bi", f"lucro ajustado, {'+' if ll3>=ll3a else ''}{br((ll3/ll3a-1)*100,0)}% a/a", "EPS diluído +9%: menos ações"),
         (f"{br(tr3,2)}%", f"take rate do varejo ({'+' if tr3>=tr2 else ''}{br((tr3-tr2)*100,0)} bps t/t)", "mais dias úteis, ações e fundos"),
         (f"R$ {br(nnm3,1)} bi", "captação líquida do varejo", "menor desde o 2T25"),
         (f"{br(ret,1)}%", "do valor de mercado volta ao acionista", f"R$ {br(DIV,1)} bi de dividendo + R$ {br(RECOMPRA,1)} bi de recompra")]
tiles = "".join(f'<div class="tile"><div class="n">{n}</div><div class="l">{l}</div><div class="so">{s}</div></div>' for n, l, s in TILES)
iss = (P["Issuer Services"]["3Q26"] / P["Issuer Services"]["3Q25"] - 1) * 100
html = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Resultado 3T26</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{{--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--ink3:#8a8984;--grid:#e8e7e3;--s1:#2a78d6;--s4:#c9c6bd;--pos:#14804a;--neg:#c2410c;--green:#e6f4ea;--greenink:#14532d}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--s1:#3987e5;--s4:#5b5a55;--pos:#4ade80;--neg:#fb923c;--green:#15301f;--greenink:#b7e4c7}}}}
:root[data-theme="dark"]{{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--s1:#3987e5;--s4:#5b5a55;--pos:#4ade80;--neg:#fb923c;--green:#15301f;--greenink:#b7e4c7}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--surface);color:var(--ink);font:15px/1.35 Inter,system-ui,sans-serif}}
.slide{{max-width:1240px;margin:0 auto;padding:18px 32px 12px;min-height:700px;display:flex;flex-direction:column;gap:12px}}
header{{display:flex;justify-content:space-between;align-items:baseline;gap:16px}} header>div:first-child{{flex:1}} .kicker{{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink3)}}
h1{{font:600 26px/1.1 Fraunces,Georgia,serif;margin:4px 0 0}} .chip{{font-size:12px;color:var(--ink3);border:1px solid var(--grid);border-radius:999px;padding:3px 10px;white-space:nowrap}}
.tiles{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}} .tile{{border:1px solid var(--grid);border-radius:10px;padding:12px 16px}}
.tile .n{{font:600 30px/1 Fraunces,Georgia,serif}} .tile .l{{font-size:13px;color:var(--ink2);margin-top:6px}} .tile .so{{font-size:12px;color:var(--ink3);margin-top:4px}}
.grid2{{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,1fr);gap:16px;align-items:stretch}}
.card{{border:1px solid var(--grid);border-radius:10px;padding:10px 14px}} .card h2{{font:600 14px/1.2 Inter,system-ui,sans-serif;margin:0 0 6px;color:var(--ink2)}}
.legend{{display:flex;gap:14px;font-size:12px;color:var(--ink2);margin:0 0 4px;flex-wrap:wrap}} .legend i{{display:inline-block;width:12px;height:8px;margin-right:5px;border-radius:2px;vertical-align:0}} .legend i.ln{{height:3px;vertical-align:3px}} .legend i.dash{{height:0;border-top:2px dashed var(--ink3);vertical-align:3px}}
.green{{background:var(--green);color:var(--greenink);border-radius:10px;padding:10px 14px;font-size:15px;font-weight:500}} .fonte{{font-size:10.5px;color:var(--ink3)}}
svg{{display:block}} svg .grid{{stroke:var(--grid);stroke-width:1}} svg .ax{{font:11px Inter,system-ui,sans-serif;fill:var(--ink3)}} svg .lab{{font:12px Inter,system-ui,sans-serif;fill:var(--ink)}} svg .sm{{font-size:11px}} svg .num{{font-weight:600}}
@media (max-width:860px){{.grid2{{grid-template-columns:minmax(0,1fr)}}.tiles{{grid-template-columns:repeat(2,minmax(0,1fr))}}h1{{font-size:22px}}}} @media (max-width:520px){{.slide{{padding:16px 16px 12px}}}}
</style></head><body><div class="slide">
<header><div><div class="kicker">resultado · 3T26</div><h1>Lucro estável, take rate de volta a {br(tr3,2)}% e R$ {br(DIV+RECOMPRA,1)} bi de volta ao acionista</h1></div><span class="chip">{VERSAO}</span></header>
<div class="tiles">{tiles}</div>
<div class="grid2">
 <div class="card"><h2>Receita bruta por linha, R$ mi: 3T25 contra 3T26</h2><div class="legend"><span><i style="background:var(--s4)"></i>3T25</span><span><i style="background:var(--s1)"></i>3T26 e variação a/a</span></div>{svgA}</div>
 <div class="card"><h2>Renda fixa: receita sobre o AuC de renda fixa, % a.a.</h2><div class="legend"><span><i class="ln" style="background:var(--s1)"></i>sem o efeito da captação líquida</span><span><i class="dash"></i>observado</span></div>{svgB}</div>
</div>
<div class="green">A renda fixa subiu pela primeira vez em cinco trimestres, para {br(Y[-1],2)}% a.a. sem o efeito da captação (2T26: {br(Y[-2],2)}%; 1T25: {br(Y[i25],2)}%), ainda abaixo do previsto pelo modelo de 1T21-2T26. Crescimento em ações, fundos, outros varejo e corporate; issuer services {br(iss,0)}% a/a.</div>
<div class="fonte">Fonte: XP Inc., release do 3T26 e planilha Historical Financials 3Q26 do RI (DRE gerencial, KPIs); 6-K de 16/11/2026 (dividendo de US$ 0,46 por ação, cerca de R$ 1,3 bi, e recompra de até R$ 1,5 bi em 12 meses). Valor de mercado = XPBR31 a R$ {br(PRECO,2)} (16/11/26) × {br(ACOES,1)} mi de ações em circulação em 30/09/26. Renda fixa sem captação = (receita − 0,52% × captação líquida do trimestre) ÷ AuC médio de renda fixa, anualizado; captação = ΔAuC − CDI × AuC inicial; coeficiente estimado em 1T21-2T26 (o 3T26 fica fora da amostra).</div>
</div></body></html>'''
out = os.path.join(HERE, "resultado_3t26.html"); open(out, "w", encoding="utf-8").write(html)
print("ok", out, "| LL", ll3, "TR", tr3, "NNM", nnm3, "retorno", round(ret, 2), "| yield ex-captação", [round(v, 3) for v in Y[-3:]])
