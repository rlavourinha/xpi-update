# -*- coding: utf-8 -*-
"""Slide: volume do mercado à vista da B3 por tipo de investidor, mensal desde 2000 (ADTV à vista × participação de cada tipo no
mercado à vista e derivativos de ações, B3 RI). Dado mensal fino e média móvel de 12 meses forte; participação em %; tabela de períodos.
Dados: data/b3_adtv_mensal.csv (dados_b3_adtv.py). Gera slides/b3_volume_investidor.html."""
import csv, os, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "..", "data")
VERSAO = "v2.3 · 23/10/2026"
def br(x, d=1): return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".").replace("-", "−")
R = [r for r in csv.DictReader(open(os.path.join(DATA, "b3_adtv_mensal.csv"), encoding="utf-8")) if r["pf_part"] and r["adtv_avista"]]
TIPOS = [("estr_part", "Estrangeiro", "var(--s1)"), ("inst_part", "Institucional local", "var(--s2)"), ("pf_part", "Pessoa física", "var(--s3)"),
         ("ifin_part", "Instituições financeiras", "var(--s4)"), ("emp_part", "Empresas", "var(--s5)")]
M = [dt.date(int(r["mes"][:4]), int(r["mes"][5:7]), 15) for r in R]
VOL = {k: [float(r["adtv_avista"]) * float(r[k] or 0) / 1e9 for r in R] for k, _, _ in TIPOS}
PCT = {k: [float(r[k] or 0) * 100 for r in R] for k, _, _ in TIPOS}
def mm12(v):
    out = []
    for i in range(len(v)):
        j = [x for x in v[max(0, i - 11):i + 1]]
        out.append(sum(j) / len(j) if i >= 11 else None)
    return out
VM = {k: mm12(v) for k, v in VOL.items()}; PM = {k: mm12(v) for k, v in PCT.items()}
def lay(ys, gap, ymax):
    """rótulos de fim de linha: ys em ordem de cima para baixo; espaçamento >= gap e nada abaixo de ymax."""
    out = []
    for y in ys: out.append(max(y, out[-1] + gap) if out else y)
    for i in range(len(out) - 1, -1, -1):
        lim = ymax if i == len(out) - 1 else out[i + 1] - gap
        out[i] = min(out[i], lim)
    return out
n = len(R); d0, d1 = dt.date(2000, 1, 1), dt.date(2026, 12, 31)

# ---- A: R$ bi por dia, por tipo ----
W, H, ML, MR, MT, MB = 720, 450, 34, 150, 12, 26
vmax = 24
def X(d): return ML + (d - d0).days / (d1 - d0).days * (W - ML - MR)
def Y(v): return MT + (vmax - min(v, vmax)) / vmax * (H - MT - MB)
g = "".join(f'<line x1="{ML}" y1="{Y(t):.1f}" x2="{W-MR}" y2="{Y(t):.1f}" class="grid"/><text x="{ML-6}" y="{Y(t)+4:.1f}" class="ax" text-anchor="end">{t}</text>' for t in range(0, vmax + 1, 4))
for y in range(2000, 2027, 4): g += f'<text x="{X(dt.date(y,1,1)):.1f}" y="{H-8}" class="ax" text-anchor="middle">{y}</text>'
for k, nome, cor in TIPOS:                                                # mensal, fino e claro
    g += f'<polyline points="{" ".join(f"{X(M[i]):.1f},{Y(VOL[k][i]):.1f}" for i in range(n))}" fill="none" stroke="{cor}" stroke-width=".7" opacity=".35"/>'
# co-location (HFT e algoritmos): recorte transversal aos tipos, desde set/2010; linha tracejada, não soma com as demais
COLOC = [float(r["adtv_avista"]) * float(r["coloc_part"]) / 1e9 if r.get("coloc_part") not in ("", None) and float(r["coloc_part"]) > 0 else None for r in R]
def mm12n(v):
    return [sum(v[i - 11:i + 1]) / 12 if i >= 11 and all(x is not None for x in v[i - 11:i + 1]) else None for i in range(len(v))]
VM["coloc"] = mm12n(COLOC)
SERIES = TIPOS + [("coloc", "Co-location (HFT)", "var(--ink2)")]
ordA = sorted(SERIES, key=lambda t: -VM[t[0]][-1])
ylabA = lay([Y(VM[k][-1]) for k, _, _ in ordA], 16, Y(0) - 10)            # rótulo inteiro acima da linha do zero
for (k, nome, cor), y in zip(ordA, ylabA):                                   # MM12, forte, com rótulo no fim
    pts = [(M[i], VM[k][i]) for i in range(n) if VM[k][i] is not None]
    dash = ' stroke-dasharray="5 4"' if k == "coloc" else ""
    g += f'<polyline points="{" ".join(f"{X(d):.1f},{Y(v):.1f}" for d, v in pts)}" fill="none" stroke="{cor}" stroke-width="{1.6 if k == "coloc" else 2.2}" stroke-linejoin="round"{dash}/>'
    g += f'<circle cx="{X(pts[-1][0]):.1f}" cy="{Y(pts[-1][1]):.1f}" r="3" fill="{cor}" stroke="var(--surface)" stroke-width="1.5"><title>{nome}, MM12 ago/26: R$ {br(pts[-1][1])} bi/dia</title></circle>'
    g += f'<text x="{X(pts[-1][0])+8:.1f}" y="{y+4:.1f}" class="lab"><tspan class="num">{br(pts[-1][1])}</tspan> {nome}</text>'
svgA = f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Volume médio diário do mercado à vista da B3 por tipo de investidor, R$ bilhões, mensal desde 2000, com média móvel de 12 meses">{g}</svg>'

# ---- B: participação %, MM12 ----
W2, H2, ML2, MR2, MT2, MB2 = 440, 210, 30, 118, 10, 24
pmax = 60
def X2(d): return ML2 + (d - d0).days / (d1 - d0).days * (W2 - ML2 - MR2)
def Y2(v): return MT2 + (pmax - min(v, pmax)) / pmax * (H2 - MT2 - MB2)
g2 = "".join(f'<line x1="{ML2}" y1="{Y2(t):.1f}" x2="{W2-MR2}" y2="{Y2(t):.1f}" class="grid"/><text x="{ML2-5}" y="{Y2(t)+4:.1f}" class="ax" text-anchor="end">{t}</text>' for t in range(0, pmax + 1, 20))
for y in (2000, 2008, 2016, 2024): g2 += f'<text x="{X2(dt.date(y,1,1)):.1f}" y="{H2-6}" class="ax" text-anchor="middle">{y}</text>'
CURTO = {"estr_part": "Estrangeiro", "inst_part": "Institucional", "pf_part": "PF", "ifin_part": "Inst. financeiras", "emp_part": "Empresas"}
ordB = sorted(TIPOS, key=lambda t: -PM[t[0]][-1])
ylabB = lay([Y2(PM[k][-1]) for k, _, _ in ordB], 14, Y2(0) - 6)
for (k, nome, cor), y in zip(ordB, ylabB):
    pts = [(M[i], PM[k][i]) for i in range(n) if PM[k][i] is not None]
    g2 += f'<polyline points="{" ".join(f"{X2(d):.1f},{Y2(v):.1f}" for d, v in pts)}" fill="none" stroke="{cor}" stroke-width="1.8" stroke-linejoin="round"/>'
    g2 += f'<text x="{X2(pts[-1][0])+6:.1f}" y="{y+4:.1f}" class="lab sm"><tspan class="num">{br(pts[-1][1],0)}%</tspan> {CURTO[k]}<title>{nome}</title></text>'
svgB = f'<svg viewBox="0 0 {W2} {H2}" width="100%" role="img" aria-label="Participação de cada tipo de investidor no volume, média de 12 meses, %">{g2}</svg>'

# ---- C: tabela de períodos (média dos meses, R$ bi/dia) ----
def media(k, a, b):
    v = [VOL[k][i] for i in range(n) if a <= R[i]["mes"] <= b]; return sum(v) / len(v)
PER = [("2007", "2007-01", "2007-12"), ("2019", "2019-01", "2019-12"), ("2021", "2021-01", "2021-12"), ("2025", "2025-01", "2025-12"), ("12m até ago/26", "2025-09", "2026-08")]
cab = "".join(f"<th>{p.replace(' ago/', '<br>ago/')}</th>" for p, _, _ in PER)
lin = "".join(f'<tr><td><i style="background:{cor}"></i>{nome}</td>' + "".join(f"<td>{br(media(k, a, b))}</td>" for _, a, b in PER) + "</tr>" for k, nome, cor in TIPOS)
lin += '<tr class="tot"><td>Total</td>' + "".join(f"<td>{br(sum(media(k, a, b) for k, _, _ in TIPOS))}</td>" for _, a, b in PER) + "</tr>"
def media_coloc(a, b):
    v = [COLOC[i] for i in range(n) if a <= R[i]["mes"] <= b and COLOC[i] is not None]
    return sum(v) / len(v) if v else None
def cel_coloc(a, b):
    c = media_coloc(a, b)
    if c is None: return "<td>—</td>"
    return f"<td>{br(c)} <span class=\"pp\">({br(100 * c / sum(media(k, a, b) for k, _, _ in TIPOS), 0)}%)</span></td>"
lin += '<tr class="memo"><td><i class="dash"></i>dos quais co-location</td>' + "".join(cel_coloc(a, b) for _, a, b in PER) + "</tr>"
# números do título e da caixa
e12, p12, t12 = media("estr_part", "2025-09", "2026-08"), media("pf_part", "2025-09", "2026-08"), sum(media(k, "2025-09", "2026-08") for k, _, _ in TIPOS)
p21, t21 = media("pf_part", "2021-01", "2021-12"), sum(media(k, "2021-01", "2021-12") for k, _, _ in TIPOS)
html = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Volume por investidor</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{{--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--ink3:#8a8984;--grid:#e8e7e3;--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--s4:#eda100;--s5:#e87ba4;--green:#e6f4ea;--greenink:#14532d}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500;--s5:#d55181;--green:#15301f;--greenink:#b7e4c7}}}}
:root[data-theme="dark"]{{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500;--s5:#d55181;--green:#15301f;--greenink:#b7e4c7}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--surface);color:var(--ink);font:15px/1.35 Inter,system-ui,sans-serif}}
.slide{{max-width:1240px;margin:0 auto;padding:24px 32px 16px;min-height:720px;display:flex;flex-direction:column;gap:12px}}
header{{display:flex;justify-content:space-between;align-items:baseline;gap:16px}} header>div:first-child{{flex:1}} .kicker{{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink3)}}
h1{{font:600 26px/1.1 Fraunces,Georgia,serif;margin:4px 0 0}} .chip{{font-size:12px;color:var(--ink3);border:1px solid var(--grid);border-radius:999px;padding:3px 10px;white-space:nowrap}}
.grid2{{display:grid;grid-template-columns:minmax(0,1.55fr) minmax(0,1fr);gap:16px;align-items:stretch}} .col{{display:flex;flex-direction:column;gap:12px}}
.card{{border:1px solid var(--grid);border-radius:10px;padding:10px 14px}} .card h2{{font:600 14px/1.2 Inter,system-ui,sans-serif;margin:0 0 6px;color:var(--ink2)}}
.legend{{display:flex;gap:12px;font-size:12px;color:var(--ink2);margin:2px 0 4px;flex-wrap:wrap}} .legend i,td i{{display:inline-block;width:12px;height:3px;vertical-align:3px;margin-right:5px;border-radius:2px}}
table{{width:100%;border-collapse:collapse;font-size:11px}} th,td{{padding:3px 3px;text-align:right;border-bottom:1px solid var(--grid);white-space:nowrap}} th:first-child,td:first-child{{text-align:left}} th{{font-weight:600;color:var(--ink2);vertical-align:bottom;line-height:1.15}} tr.tot td{{font-weight:600}} .nota{{font-size:11.5px;color:var(--ink3);margin:-2px 0 2px}} tr.memo td{{color:var(--ink2);font-style:italic;border-bottom:0;vertical-align:top}} .pp{{display:block;color:var(--ink3);font-size:10px;line-height:1.1}} td i.dash{{background:none!important;border-top:2px dashed var(--ink2);height:0;vertical-align:3px}}
.green{{background:var(--green);color:var(--greenink);border-radius:10px;padding:10px 14px;font-size:15px;font-weight:500}} .fonte{{font-size:11px;color:var(--ink3)}}
svg{{display:block}} svg .grid{{stroke:var(--grid);stroke-width:1}} svg .ax{{font:11px Inter,system-ui,sans-serif;fill:var(--ink3)}} svg .lab{{font:12px Inter,system-ui,sans-serif;fill:var(--ink)}} svg .sm{{font-size:11px}} svg .num{{font-weight:600}}
@media (max-width:860px){{.grid2{{grid-template-columns:minmax(0,1fr)}}h1{{font-size:22px}}}} @media (max-width:520px){{.slide{{padding:16px 16px 12px}}th{{white-space:normal}}table{{font-size:11px}}.card{{overflow-x:auto}}}}
</style></head><body><div class="slide">
<header><div><div class="kicker">parte 1 · indústria · volume da bolsa</div><h1>O estrangeiro faz {br(PM["estr_part"][-1],0)}% do volume da B3; a pessoa física, {br(PM["pf_part"][-1],0)}%</h1></div><span class="chip">{VERSAO}</span></header>
<div class="grid2">
 <div class="card"><h2>Volume médio diário à vista por tipo de investidor, R$ bi (mensal fino, média 12m forte)</h2><div class="nota">tracejado: co-location (HFT e algoritmos), já incluído nos tipos</div>{svgA}</div>
 <div class="col">
  <div class="card"><h2>Participação no volume, % (média de 12 meses)</h2>{svgB}</div>
  <div class="card"><h2>Média do período, R$ bi por dia</h2><table><tr><th></th>{cab}</tr>{lin}</table></div>
 </div>
</div>
<div class="green">Nos 12 meses até ago/26 a bolsa girou R$ {br(t12)} bi por dia, e a pessoa física respondeu por R$ {br(p12)} bi, metade dos R$ {br(p21)} bi de 2021, com volume total parecido (R$ {br(t12)} bi contra R$ {br(t21)} bi): o volume que cresceu é de estrangeiro e de máquina, não da pessoa física, o público da XP.</div>
<div class="fonte">Fonte: B3 RI, planilha de dados operacionais (aba Renda Variável & Empréstimo): ADTV do mercado à vista (ações, ETFs, BDRs e fundos listados) e participação dos investidores no mercado à vista e derivativos sobre ações, mensal, jan/2000 a ago/2026 (último mês publicado). Volume por tipo = ADTV à vista × participação. Média móvel de 12 meses a partir de dez/2000. Co-location (HFT e algoritmos, linha tracejada e linha "dos quais") é um recorte transversal: o mesmo volume já está dentro dos tipos, sobretudo estrangeiro e institucional, e não soma com eles; série da B3 desde set/2010 (participação do co-location no volume à vista).</div>
</div></body></html>'''
out = os.path.join(HERE, "b3_volume_investidor.html"); open(out, "w", encoding="utf-8").write(html)
print("ok", out, "| 12m: total", round(t12, 1), "estr", round(e12, 1), "pf", round(p12, 1), "| 2021 total", round(t21, 1), "pf", round(p21, 1))
