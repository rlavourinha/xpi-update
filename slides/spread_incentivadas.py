# -*- coding: utf-8 -*-
"""Slide: spread das debêntures incentivadas com gross-up × spread das debêntures DI, diário desde out/2021 (o gráfico da Régia
Capital publicado no Valor em 13/10/2026, refeito com dados públicos papel a papel), mais o último mês sem gross-up e a tabela
de hoje comparando IDEX, ANBIMA IDA e o número da matéria. Dados: data/spread_incentivadas_diario.csv (dados_spread_incentivadas.py).
Gera slides/spread_incentivadas.html."""
import csv, os, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "..", "data")
VERSAO = "v1.0 · 13/10/2026"
def br(x, d=2): return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".").replace("-", "−")
R = list(csv.DictReader(open(os.path.join(DATA, "spread_incentivadas_diario.csv"), encoding="utf-8")))
def f(r, k): return float(r[k]) if r.get(k) not in ("", None) else None
D0 = "2021-10-01"
I = [r for r in R if r["fonte"] == "IDEX" and r["data"] >= D0]
A = [r for r in R if r["fonte"] == "ANBIMA IDA"]
ult = I[-1]; ua = A[-1]
hist = [f(r, "dif") for r in I if f(r, "dif") is not None]
pct_acima = 100 * sum(1 for x in hist if x >= f(ult, "dif")) / len(hist)
mx = max((r for r in I if f(r, "dif") is not None), key=lambda r: f(r, "dif"))
a0 = next(r for r in A)                                             # 1º dia da janela ANBIMA

# ---- A: 5 anos, IDEX (gross-up × DI × diferença) ----
W, H, ML, MR, MT, MB = 760, 410, 34, 46, 14, 28
d0, d1 = dt.date(2021, 10, 1), dt.date(2026, 10, 31); vmax = 5.5
def X(d): return ML + (d - d0).days / (d1 - d0).days * (W - ML - MR)
def Y(v): return MT + (vmax - v) / vmax * (H - MT - MB)
def segs(k, gap=10):
    """Listas de pontos contínuos (quebra a linha onde faltam mais de `gap` dias: buraco do arquivo público)."""
    out, cur, ant = [], [], None
    for r in I:
        v = f(r, k)
        if v is None: continue
        d = dt.date.fromisoformat(r["data"])
        if ant and (d - ant).days > gap: out.append(cur); cur = []
        cur.append((d, v)); ant = d
    if cur: out.append(cur)
    return out
g = "".join(f'<line x1="{ML}" y1="{Y(t):.1f}" x2="{W-MR}" y2="{Y(t):.1f}" class="grid"/><text x="{ML-6}" y="{Y(t)+4:.1f}" class="ax" text-anchor="end">{br(t,0)}</text>' for t in range(0, 6))
for y in range(2022, 2027): g += f'<text x="{X(dt.date(y,1,1)):.1f}" y="{H-8}" class="ax" text-anchor="middle">{y}</text><line x1="{X(dt.date(y,1,1)):.1f}" y1="{H-MB}" x2="{X(dt.date(y,1,1)):.1f}" y2="{H-MB+4}" class="base"/>'
# buraco do arquivo público (incentivadas: 26/03 a 08/09/26)
gx0, gx1 = X(dt.date(2026, 3, 26)), X(dt.date(2026, 9, 8))
g += f'<rect x="{gx0:.1f}" y="{MT}" width="{gx1-gx0:.1f}" height="{H-MT-MB}" fill="var(--ink3)" opacity=".08"/><text x="{(gx0+gx1)/2:.1f}" y="{MT+12}" class="lab2" text-anchor="middle">sem dado</text><text x="{(gx0+gx1)/2:.1f}" y="{MT+25}" class="lab2" text-anchor="middle">público</text>'
for s in segs("dif"):                                               # área da diferença, a partir de zero
    pts = " ".join(f"{X(d):.1f},{Y(v):.1f}" for d, v in s)
    g += f'<polygon points="{X(s[0][0]):.1f},{Y(0):.1f} {pts} {X(s[-1][0]):.1f},{Y(0):.1f}" fill="var(--s3)" opacity=".18"/>'
g += f'<line x1="{ML}" y1="{Y(f(ult,"dif")):.1f}" x2="{W-MR}" y2="{Y(f(ult,"dif")):.1f}" stroke="var(--s2)" stroke-width="1.3" stroke-dasharray="5 4"/>'
for k, cor, sw in (("di_spread", "var(--s1)", 1.5), ("infra_gu", "var(--s3)", 1.8)):
    for s in segs(k):
        g += f'<polyline points="{" ".join(f"{X(d):.1f},{Y(v):.1f}" for d, v in s)}" fill="none" stroke="{cor}" stroke-width="{sw}" stroke-linejoin="round"/>'
xe = X(dt.date.fromisoformat(ult["data"])) + 6
g += f'<text x="{xe:.1f}" y="{Y(f(ult,"infra_gu"))+4:.1f}" class="v">{br(f(ult,"infra_gu"))}</text>'
g += f'<text x="{xe:.1f}" y="{Y(f(ult,"dif"))-3:.1f}" class="v" style="fill:var(--s2)">{br(f(ult,"dif"))}</text>'
g += f'<text x="{xe:.1f}" y="{Y(f(ult,"di_spread"))+12:.1f}" class="v">{br(f(ult,"di_spread"))}</text>'
pk = max((r for r in I if r["data"] < "2023-06-01" and f(r, "infra_gu")), key=lambda r: f(r, "infra_gu"))
g += f'<text x="{X(dt.date.fromisoformat(pk["data"]))+6:.1f}" y="{Y(f(pk,"infra_gu"))+4:.1f}" class="lab2">fev/23 (Americanas): {br(f(pk,"infra_gu"))}</text>'
lo = min((r for r in I if "2025-06-01" <= r["data"] <= "2026-03-25" and f(r, "infra_gu")), key=lambda r: f(r, "infra_gu"))
g += f'<text x="{X(dt.date.fromisoformat(lo["data"]))-5:.1f}" y="{Y(f(lo,"infra_gu"))+4:.1f}" class="lab2" text-anchor="end">{dt.date.fromisoformat(lo["data"]).strftime("%m/%y").replace("10/25","out/25")}: {br(f(lo,"infra_gu"))}</text>'
svgA = f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Spread das debêntures incentivadas com gross-up e das debêntures DI, diário, out/2021 a out/2026">{g}</svg>'

# ---- B: último mês, sem gross-up ----
W2, H2, ML2, MR2, MT2, MB2 = 440, 190, 34, 44, 12, 24
b0, b1 = dt.date(2026, 9, 8), dt.date(2026, 10, 10); bmin, bmax = 0, 1.6
def X2(d): return ML2 + (d - b0).days / (b1 - b0).days * (W2 - ML2 - MR2)
def Y2(v): return MT2 + (bmax - v) / (bmax - bmin) * (H2 - MT2 - MB2)
g2 = "".join(f'<line x1="{ML2}" y1="{Y2(t):.1f}" x2="{W2-MR2}" y2="{Y2(t):.1f}" class="grid"/><text x="{ML2-6}" y="{Y2(t)+4:.1f}" class="ax" text-anchor="end">{br(t,1)}</text>' for t in (0, 0.5, 1.0, 1.5))
for d in (dt.date(2026, 9, 15), dt.date(2026, 9, 22), dt.date(2026, 9, 29), dt.date(2026, 10, 6)):
    g2 += f'<text x="{X2(d):.1f}" y="{H2-6}" class="ax" text-anchor="middle">{d.strftime("%d/%m")}</text>'
g2 += f'<line x1="{X2(dt.date(2026,10,4)):.1f}" y1="{MT2}" x2="{X2(dt.date(2026,10,4)):.1f}" y2="{H2-MB2}" stroke="var(--ink3)" stroke-dasharray="2 3"/><text x="{X2(dt.date(2026,10,4))-4:.1f}" y="{MT2+10}" class="lab2" text-anchor="end">1º turno</text>'
recI = [r for r in I if r["data"] >= "2026-09-09"]
for serie, k, cor, dash in ((recI, "infra_spread", "var(--s3)", ""), (A, "infra_spread", "var(--s3)", ' stroke-dasharray="4 3"'), (recI, "di_spread", "var(--s1)", ""), (A, "di_spread", "var(--s1)", ' stroke-dasharray="4 3"')):
    pts = " ".join(f"{X2(dt.date.fromisoformat(r['data'])):.1f},{Y2(f(r,k)):.1f}" for r in serie if f(r, k) is not None)
    g2 += f'<polyline points="{pts}" fill="none" stroke="{cor}" stroke-width="1.7"{dash}/>'
xe2 = X2(dt.date.fromisoformat(ua["data"])) + 5
ys = sorted([Y2(v) + 4, v] for v in (f(ult, "infra_spread"), f(ua, "infra_spread"), f(ua, "di_spread"), f(ult, "di_spread")))
for _ in range(20):                                                 # afasta rótulos colados (mín. 14 px entre linhas de base)
    for i in range(1, len(ys)):
        gap = ys[i][0] - ys[i-1][0]
        if gap < 14: ys[i-1][0] -= (14 - gap) / 2; ys[i][0] += (14 - gap) / 2
for y, v in ys:
    g2 += f'<text x="{xe2:.1f}" y="{y:.1f}" class="v">{br(v)}</text>'
svgB = f'<svg viewBox="0 0 {W2} {H2}" width="100%" role="img" aria-label="Spread sem gross-up das incentivadas e das debêntures DI nas últimas quatro semanas">{g2}</svg>'

linhas = [("Incentivadas, sem gross-up", f(ult, "infra_spread"), f(ua, "infra_spread"), None),
          ("Incentivadas, com gross-up", f(ult, "infra_gu"), f(ua, "infra_gu"), 2.89),
          ("DI", f(ult, "di_spread"), f(ua, "di_spread"), 1.40),
          ("Diferença (com gross-up − DI)", f(ult, "dif"), f(ua, "dif"), 1.50)]
tab = "".join(f'<tr><td>{n}</td><td>{br(a)}</td><td>{br(b)}</td><td>{br(c) if c is not None else "—"}</td></tr>' for n, a, b, c in linhas)

html = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Spread das incentivadas</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{{--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--ink3:#8a8984;--grid:#e8e7e3;--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--green:#e6f4ea;--greenink:#14532d}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--s1:#3987e5;--s2:#d95926;--s3:#3ccf96;--green:#15301f;--greenink:#b7e4c7}}}}
:root[data-theme="dark"]{{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--s1:#3987e5;--s2:#d95926;--s3:#3ccf96;--green:#15301f;--greenink:#b7e4c7}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--surface);color:var(--ink);font:15px/1.35 Inter,system-ui,sans-serif}}
.slide{{max-width:1240px;margin:0 auto;padding:24px 32px 16px;min-height:720px;display:flex;flex-direction:column;gap:12px}}
header{{display:flex;justify-content:space-between;align-items:baseline;gap:16px}} header>div:first-child{{flex:1}} .kicker{{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink3)}}
h1{{font:600 26px/1.1 Fraunces,Georgia,serif;margin:4px 0 0}} .chip{{font-size:12px;color:var(--ink3);border:1px solid var(--grid);border-radius:999px;padding:3px 10px;white-space:nowrap}}
.grid2{{display:grid;grid-template-columns:1.6fr 1fr;gap:16px;align-items:start}} .col{{display:flex;flex-direction:column;gap:12px}}
.card{{border:1px solid var(--grid);border-radius:10px;padding:10px 14px}} .card h2{{font:600 14px/1.2 Inter,system-ui,sans-serif;margin:0 0 6px;color:var(--ink2)}}
.legend{{display:flex;gap:14px;font-size:12px;color:var(--ink2);margin:2px 0 4px;flex-wrap:wrap}} .legend i{{display:inline-block;width:14px;height:3px;vertical-align:3px;margin-right:5px;border-radius:2px}} .legend i.area{{height:12px;vertical-align:-2px;opacity:.35}} .legend i.dash{{background:none!important;border-top:2px dashed currentColor;height:0}}
table{{width:100%;border-collapse:collapse;font-size:13px}} th,td{{padding:4px 6px;text-align:right;border-bottom:1px solid var(--grid)}} th:first-child,td:first-child{{text-align:left}} th{{font-weight:600;color:var(--ink2);font-size:12px}} tr:last-child td{{font-weight:600}}
.green{{background:var(--green);color:var(--greenink);border-radius:10px;padding:10px 14px;font-size:15px;font-weight:500}} .fonte{{font-size:11px;color:var(--ink3)}}
svg{{display:block}} svg .grid{{stroke:var(--grid);stroke-width:1}} svg .base{{stroke:var(--ink3);stroke-width:1}} svg .ax{{font:11px Inter,system-ui,sans-serif;fill:var(--ink3)}} svg .lab2{{font:11px Inter,system-ui,sans-serif;fill:var(--ink2)}} svg .v{{font:600 11px Inter,system-ui,sans-serif;fill:var(--ink)}}
@media (max-width:860px){{.grid2{{grid-template-columns:1fr}}h1{{font-size:24px}}}}
</style></head><body><div class="slide">
<header><div><div class="kicker">parte 2 · indústria · crédito incentivado</div><h1>Com gross-up, a incentivada paga {br(f(ult,"dif"),1)} p.p. acima da DI: prêmio no topo de cinco anos</h1></div><span class="chip">{VERSAO}</span></header>
<div class="grid2">
 <div class="card"><h2>Spread das debêntures, % a.a., diário</h2><div class="legend"><span><i style="background:var(--s3)"></i>incentivadas (IDEX-Infra), com gross-up</span><span><i style="background:var(--s1)"></i>DI (IDEX-CDI)</span><span><i class="area" style="background:var(--s3)"></i>diferença</span><span style="color:var(--s2)"><i class="dash"></i>diferença em {dt.date.fromisoformat(ult["data"]).strftime("%d/%m")}</span></div>{svgA}</div>
 <div class="col">
  <div class="card"><h2>Últimas quatro semanas, sem gross-up, % a.a.</h2><div class="legend"><span><i style="background:var(--s3)"></i>incentivadas</span><span><i style="background:var(--s1)"></i>DI</span><span><i class="dash" style="color:var(--ink2)"></i>ANBIMA IDA (linha cheia = IDEX)</span></div>{svgB}</div>
  <div class="card"><h2>Em {dt.date.fromisoformat(ult["data"]).strftime("%d/%m/%Y")}, % a.a.</h2><table><tr><th></th><th>IDEX</th><th>ANBIMA IDA</th><th>Régia (Valor)</th></tr>{tab}</table></div>
 </div>
</div>
<div class="green">Sem gross-up a incentivada abriu de {br(f(a0,"infra_spread"))} para {br(f(ua,"infra_spread"))} sobre a NTN-B em quatro semanas enquanto o DI ficou parado em {br(f(ua,"di_spread"),1)}: o estresse é só das incentivadas, e o 3T26 testa a promessa da XP de não marcar de novo o livro de crédito.</div>
<div class="fonte">Fonte: IDEX Analytics (ex-JGP), composição diária pública do IDEX-Infra Geral (MID spread sobre a NTN-B de referência; histórico pela captura de 27/03/26 do Wayback, até 25/03/26; arquivo atual desde 09/09/26) e do IDEX-CDI Geral (spread de compra, excluídos papéis acima de 10%; até 30/04/26 e desde 09/09/26); ANBIMA, carteira teórica diária do IDA-IPCA Infraestrutura e do IDA-DI (taxa indicativa e duration de cada papel, janela pública desde 14/09/26); ETTJ pré e real ANBIMA e curva do Tesouro via monitor. Gross-up com IR de 15%: taxa nominal do papel isento (taxa real × inflação implícita no prazo) ÷ 0,85, menos a taxa pré no mesmo prazo, papel a papel, média pelo peso no índice. Régia Capital via Valor (13/10/26). O histórico bate com o gráfico da Régia em 2021–24 (±0,1 p.p.); no trecho recente este cálculo fica ~0,4 p.p. acima, convenção de gross-up da Régia não publicada. Diferença maior ou igual à atual em {br(pct_acima,1)}% dos dias desde out/21; máximo {br(f(mx,"dif"))} em {dt.date.fromisoformat(mx["data"]).strftime("%d/%m/%y")}.</div>
</div></body></html>'''
out = os.path.join(HERE, "spread_incentivadas.html"); open(out, "w", encoding="utf-8").write(html)
print("ok", out, "| último", ult["data"], "gu", round(f(ult, "infra_gu"), 2), "DI", round(f(ult, "di_spread"), 2), "dif", round(f(ult, "dif"), 2), "| % dias >=:", round(pct_acima, 1))
