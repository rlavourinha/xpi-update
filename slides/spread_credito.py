# -*- coding: utf-8 -*-
"""Slide: spread de crédito privado (IDEX-CDI ex-distressed diário desde 2019 + mediana DI+ da ANBIMA desde set/26), receita de renda fixa
do varejo da XP por trimestre e, lado a lado, a variação trimestral do spread e da curva pré. Explica a "marcação negativa" do 1T26 e 2T26.
Dados: data/idex_cdi_spread_diario.csv, data/anbima_debentures_spread_diario.csv, data/historical_financials.json, data/_curva_delta_tri.csv,
data/_xp_tes_pnl_diario.csv (Scorpio). Gera slides/spread_credito.html."""
import csv, os, json, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "..", "data")
VERSAO = "v1.8 · 11/10/2026"
def br(x, d=1): return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".").replace("-", "−")
idx = [(dt.date.fromisoformat(r["data"]), float(r["spread_exdist"])) for r in csv.DictReader(open(os.path.join(DATA, "idex_cdi_spread_diario.csv"), encoding="utf-8")) if r["spread_exdist"] and r["data"] >= "2019-01-01"]
anb = [(dt.date.fromisoformat(r["data"]), float(r["di_mediana"])) for r in csv.DictReader(open(os.path.join(DATA, "anbima_debentures_spread_diario.csv"), encoding="utf-8")) if r["di_mediana"]]
P = json.load(open(os.path.join(DATA, "historical_financials.json"), encoding="utf-8"))["3. Managerial P&L - new"]["Fixed Income"]
Q = [q for q in P if len(q) == 4 and q[1] == "Q" and int(q[2:]) >= 22]; RF = [float(P[q]) for q in Q]
CV = {r[""]: r for r in csv.DictReader(open(os.path.join(DATA, "_curva_delta_tri.csv"), encoding="utf-8"))}
# Δ spread IDEX por trimestre (bp), fim de trimestre; 2T26 = até 30/04 (fim do arquivo público)
import collections
qend = collections.OrderedDict()
for d, v in idx: qend[f"{(d.month-1)//3+1}Q{str(d.year)[2:]}"] = v
qk = list(qend); dsp = {qk[i]: (qend[qk[i]] - qend[qk[i-1]]) * 100 for i in range(1, len(qk))}
QC = Q + ["3Q26"]
# Scorpio
sc = collections.defaultdict(float)
for r in csv.DictReader(open(os.path.join(DATA, "_xp_tes_pnl_diario.csv"), encoding="utf-8")):
    if r["F"] == "SCORPIO" and r["pnl"]:
        d = dt.date.fromisoformat(r["DT_COMPTC"][:10]); sc[f"{(d.month-1)//3+1}Q{str(d.year)[2:]}"] += float(r["pnl"]) / 1e6
def ql(q): return f"{q[0]}T{q[2:]}"

# ---- A: spread diário ----
W, H, ML, MR, MT, MB = 700, 300, 40, 16, 14, 28
d0, d1 = dt.date(2019, 1, 1), dt.date(2026, 12, 31); smin, smax = 0, 6
def X(d): return ML + (d - d0).days / (d1 - d0).days * (W - ML - MR)
def Y(v): return MT + (smax - v) / (smax - smin) * (H - MT - MB)
g = "".join(f'<line x1="{ML}" y1="{Y(t):.1f}" x2="{W-MR}" y2="{Y(t):.1f}" class="grid"/><text x="{ML-6}" y="{Y(t)+4:.1f}" class="ax" text-anchor="end">{t}</text>' for t in range(0, 7, 2))
for y in range(2019, 2027): g += f'<text x="{X(dt.date(y,7,1)):.1f}" y="{H-8}" class="ax" text-anchor="middle">{y}</text>'
g += f'<rect x="{X(dt.date(2026,1,1)):.1f}" y="{MT}" width="{X(dt.date(2026,6,30))-X(dt.date(2026,1,1)):.1f}" height="{H-MT-MB}" fill="var(--s2)" opacity=".10"/>'
pts = " ".join(f"{X(d):.1f},{Y(min(smax,v)):.1f}" for d, v in idx)
g += f'<polyline points="{pts}" fill="none" stroke="var(--s1)" stroke-width="1.6" stroke-linejoin="round"/>'
for d, v in anb: g += f'<circle cx="{X(d):.1f}" cy="{Y(v):.1f}" r="2.6" fill="var(--s3)"/>'
for d, v, lab, dx in [(dt.date(2020, 4, 30), 5.74, "abr/20: 5,74", -6), (dt.date(2023, 3, 31), 3.02, "mar/23 (Americanas): 3,02", -6), (dt.date(2025, 10, 31), 1.31, "out/25: 1,31", -6), (dt.date(2026, 4, 30), 1.69, "30/04/26: 1,69", -6)]:
    # rótulo acima da linha: y pelo máximo da série no vão horizontal que o texto ocupa (~5,8 un./caractere), p/ não cruzar picos próximos (ex.: abr/26 = 2,04)
    xa, xb = sorted((X(d) + dx, X(d) + dx + (1 if dx > 0 else -1) * len(lab) * 5.8)); vtop = max([v] + [w for e, w in idx if xa <= X(e) <= xb])
    g += f'<text x="{X(d)+dx:.1f}" y="{Y(min(smax,vtop))-8 if lab[:6]!="out/25" else Y(v)+18:.1f}" class="lab2" text-anchor="{"start" if dx>0 else "end"}">{lab}</text>'
g += f'<text x="{X(anb[-1][0])-6:.1f}" y="{Y(anb[-1][1])+20:.1f}" class="lab2" text-anchor="end">ANBIMA, mediana DI+: {br(anb[-1][1],2)}</text>'  # +20 (não +16): folga de 4 px abaixo do rótulo out/25, que também fica abaixo da linha
svgA = f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Spread de crédito privado sobre o CDI, diário, 2019 a 2026">{g}</svg>'

# ---- B: receita de renda fixa do varejo ----
W2, H2, ML2, MR2, MT2, MB2 = 440, 150, 40, 10, 18, 26
vmax = 1100
def Y2(v): return MT2 + (vmax - v) / vmax * (H2 - MT2 - MB2)
bw = (W2 - ML2 - MR2) / len(Q)
g2 = "".join(f'<line x1="{ML2}" y1="{Y2(t):.1f}" x2="{W2-MR2}" y2="{Y2(t):.1f}" class="grid"/><text x="{ML2-6}" y="{Y2(t)+4:.1f}" class="ax" text-anchor="end">{t}</text>' for t in (0, 500, 1000))
for i, (q, v) in enumerate(zip(Q, RF)):
    x = ML2 + i * bw + 1.5; hot = q in ("1Q26", "2Q26")
    g2 += f'<rect x="{x:.1f}" y="{Y2(v):.1f}" width="{bw-3:.1f}" height="{Y2(0)-Y2(v):.1f}" rx="2" fill="{"var(--s2)" if hot else "var(--s1)"}"/>'
    if hot or q in ("1Q25", "4Q25"): g2 += f'<text x="{x+(bw-3)/2:.1f}" y="{Y2(v)-4:.1f}" class="v" text-anchor="middle">{br(v,0)}</text>'
    if q.startswith("1Q"): g2 += f'<text x="{x+(bw-3)/2:.1f}" y="{H2-8}" class="ax" text-anchor="middle">20{q[2:]}</text>'
svgB = f'<svg viewBox="0 0 {W2} {H2}" width="100%" role="img" aria-label="Receita de renda fixa do varejo da XP por trimestre, R$ milhões">{g2}</svg>'

# ---- C: emissões primárias de crédito privado (ANBIMA), R$ bi por trimestre ----
EM = {r["tri"]: float(r["emissoes_rs_bi"]) for r in csv.DictReader(open(os.path.join(DATA, "anbima_emissoes_credito_tri.csv"), encoding="utf-8"))}
QE = [q for q in EM if int(q[2:]) >= 22]
W3, H3, ML3, MR3, MT3, MB3 = 440, 150, 40, 10, 18, 26
emax = 250
def Y3(v): return MT3 + (emax - v) / emax * (H3 - MT3 - MB3)
bw3 = (W3 - ML3 - MR3) / len(QE)
g3 = "".join(f'<line x1="{ML3}" y1="{Y3(t):.1f}" x2="{W3-MR3}" y2="{Y3(t):.1f}" class="grid"/><text x="{ML3-6}" y="{Y3(t)+4:.1f}" class="ax" text-anchor="end">{t}</text>' for t in (0, 100, 200))
for i, q in enumerate(QE):
    v = EM[q]; x = ML3 + i * bw3 + 1.5; hot = q in ("1Q26", "2Q26", "3Q26")
    g3 += f'<rect x="{x:.1f}" y="{Y3(v):.1f}" width="{bw3-3:.1f}" height="{Y3(0)-Y3(v):.1f}" rx="2" fill="{"var(--s2)" if hot else "var(--s1)"}"{" opacity=\".55\"" if q=="3Q26" else ""}/>'
    if q in ("4Q25", "1Q26", "2Q26", "3Q26"): g3 += f'<text x="{x+(bw3-3)/2:.1f}" y="{Y3(v)-4:.1f}" class="v" text-anchor="middle">{br(v,0)}{"*" if q=="3Q26" else ""}</text>'
    if q.startswith("1Q"): g3 += f'<text x="{x+(bw3-3)/2:.1f}" y="{H3-8}" class="ax" text-anchor="middle">20{q[2:]}</text>'
svgC = f'<svg viewBox="0 0 {W3} {H3}" width="100%" role="img" aria-label="Emissões primárias de debêntures, notas comerciais, CRI e CRA por trimestre, R$ bilhões">{g3}</svg>'
html = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Spread de crédito e renda fixa da XP</title>
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
svg{{display:block}} svg .grid{{stroke:var(--grid);stroke-width:1}} svg .base{{stroke:var(--ink3);stroke-width:1}} svg .ax{{font:11px Inter,system-ui,sans-serif;fill:var(--ink3)}} svg .lab2{{font:11px Inter,system-ui,sans-serif;fill:var(--ink2)}} svg .v{{font:600 11px Inter,system-ui,sans-serif;fill:var(--ink)}}
@media (max-width:860px){{.grid2{{grid-template-columns:1fr}}h1{{font-size:24px}}}}
</style></head><body><div class="slide">
<header><div><div class="kicker">parte 3 · companhia · renda fixa do varejo</div><h1>R$ 420 mi de marcação no 1S26: spread de crédito num livro de R$ 25 bi</h1></div><span class="chip">{VERSAO}</span></header>
<div class="grid2">
 <div class="card"><h2>Spread de crédito privado sobre o CDI, % a.a., diário</h2><div class="legend"><span><i style="background:var(--s1)"></i>IDEX-CDI, média ponderada ex-estresse (JGP, até 30/04/26)</span><span><i style="background:var(--s3)"></i>ANBIMA, mediana das debêntures DI+ (coleta diária desde 30/09/26)</span><span><i style="background:var(--s2);opacity:.4"></i>1S26</span></div>{svgA}</div>
 <div class="col">
  <div class="card"><h2>Receita de renda fixa do varejo da XP, R$ mi por trimestre</h2>{svgB}</div>
  <div class="card"><h2>Emissões de debêntures, notas comerciais, CRI e CRA, R$ bi por trimestre (* 3T26 = jul-ago)</h2>{svgC}</div>
 </div>
</div>
<div class="green">No call do 2T26 a XP pôs número na marcação: abaixo de R$ 300 mi no 1T26, R$ 150 a 160 mi no 2T26, R$ 420 mi no semestre, e a causa foi spread de crédito, "mesmo em AAA e AA", no livro de facilitação e do banco de investimento. Juros não entram: a sensibilidade publicada é de R$ 0,2 mi por ponto-base, o livro está hedgeado. A conta fecha: R$ 21 a 25 bi de debêntures, CRI, CRA e dívida externa no balanço, duration de 3 anos e os {br(dsp["1Q26"]+dsp["2Q26"],0)} bp que o IDEX abriu de janeiro a abril dão R$ 200 mi; o resto é o livro do IB, mais longo e mais largo que o índice. Por cima disso, o primário secou: R$ 219 bi no 4T25 para R$ 122 bi e R$ 109 bi. Para o 3T26 a XP diz que reduziu o livro e não espera nova marcação.</div>
<div class="fonte">Fonte: IDEX Analytics/JGP, arquivo público de composição do IDEX-CDI Geral (spread de compra ponderado pelo peso, excluídos papéis com spread acima de 10%; a série pública termina em 30/04/26); ANBIMA, taxas indicativas diárias de debêntures (mediana do spread DI+, {len(anb)} pregões desde 30/09/26, universo diferente do IDEX); XP RI, Historical Financials 2T26 (Retail Fixed Income) e release 2T26 ("impacto MtM em renda fixa"); ETTJ pré e real ANBIMA via monitor (fotografias de 02 e 09/10/26 para a semana do 1º turno); ITRs e 20-F, análise de sensibilidade da carteira de trading (cenário I, 1 bp) e nota de títulos (jun/26); teleconferências de resultados do 1T26 e 2T26 (transcrições); ANBIMA, Boletim de Mercado de Capitais (emissões domésticas); CVM, informes diários dos fundos da tesouraria.</div>
</div></body></html>'''
out = os.path.join(HERE, "spread_credito.html"); open(out, "w", encoding="utf-8").write(html)
print("ok", out, "| dsp", {k: round(v) for k, v in dsp.items() if k[2:] in ("25", "26")}, "| scorpio", {k: round(v) for k, v in sc.items() if k.endswith("26")})
