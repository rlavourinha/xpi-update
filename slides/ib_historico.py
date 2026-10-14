# -*- coding: utf-8 -*-
"""Slide: histórico de mercado de capitais e M&A no Brasil e a receita de Mercado de Capitais (Issuer Services) da XP.
Painéis: A DCM anual (ANBIMA, 2011-2025 + jan-ago/26); B ECM anual, IPO e follow-on lado a lado; C M&A, nº de transações (KPMG, 2005-2025);
D receita anual de Mercado de Capitais da XP (2018-2025 + 1S26) com a receita sobre o volume emitido, e a posição da XP nos rankings ANBIMA.
Dados: data/mercado_capitais_anual.csv, data/mercado_capitais_tri.csv, data/ma_kpmg_anual.csv, data/xp_mercado_capitais_tri.csv,
data/xp_rankings_anbima.csv (todos gerados por dados_ib_historico.py). Gera slides/ib_historico.html."""
import csv, os
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "..", "data")
VERSAO = "v1.9 · 14/10/2026"
def br(x, d=1): return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".").replace("-", "−")
A = {int(r["ano"]): r for r in csv.DictReader(open(os.path.join(DATA, "mercado_capitais_anual.csv"), encoding="utf-8"))}
TQ = {r[""]: r for r in csv.DictReader(open(os.path.join(DATA, "mercado_capitais_tri.csv"), encoding="utf-8"))}
K = {int(r["ano"]): int(r["transacoes"]) for r in csv.DictReader(open(os.path.join(DATA, "ma_kpmg_anual.csv"), encoding="utf-8"))}
XQ = {r[""]: float(r["issuer_services"]) for r in csv.DictReader(open(os.path.join(DATA, "xp_mercado_capitais_tri.csv"), encoding="utf-8")) if r["issuer_services"]}
ANOS = list(range(2011, 2027))
f = lambda r, k: float(r[k] or 0)

def barras(vals, W, H, vmax, ticks, rotulos, cor, parcial=(), largura=0.72, ML=38, MR=8, MT=16, MB=24, fmt=lambda v: br(v, 0), anos_eixo=None, ano_y=None):
    """vals: lista de (ano, [v1, v2...]) com séries lado a lado; rótulos: anos que levam valor em cima."""
    n = len(vals); slot = (W - ML - MR) / n
    def Y(v): return MT + (vmax - v) / vmax * (H - MT - MB)
    g = "".join(f'<line x1="{ML}" y1="{Y(t):.1f}" x2="{W-MR}" y2="{Y(t):.1f}" class="grid"/><text x="{ML-6}" y="{Y(t)+4:.1f}" class="ax" text-anchor="end">{fmt(t)}</text>' for t in ticks)
    for i, (ano, vs) in enumerate(vals):
        k = len(vs); bw = slot * largura / k; x0 = ML + i * slot + slot * (1 - largura) / 2
        for j, v in enumerate(vs):
            x = x0 + j * bw + (1 if k > 1 else 0)
            op = ' opacity=".5"' if ano in parcial else ""
            g += f'<rect x="{x:.1f}" y="{Y(v):.1f}" width="{bw-(2 if k>1 else 0):.1f}" height="{max(0.5,Y(0)-Y(v)):.1f}" rx="2" fill="{cor[j]}"{op}><title>{ano}: {fmt(v)}</title></rect>'
            if ano in rotulos and (k == 1 or v == max(vs)):
                g += f'<text x="{x+(bw-(2 if k>1 else 0))/2:.1f}" y="{Y(v)-4:.1f}" class="v" text-anchor="middle">{fmt(v)}{"*" if ano in parcial else ""}</text>'
        if anos_eixo is None or ano in anos_eixo:
            g += f'<text x="{ML+i*slot+slot/2:.1f}" y="{ano_y or H-8}" class="ax" text-anchor="middle">{str(ano)[2:] if isinstance(ano,int) else ano}</text>'
    return g

# ---- A: DCM ----
W, H = 560, 170
gA = barras([(a, [f(A[a], "dcm")]) for a in ANOS], W, H, 800, (0, 200, 400, 600, 800), {2011, 2019, 2021, 2024, 2025, 2026}, ["var(--s1)"], parcial={2026})
svgA = f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Emissões domésticas de dívida por ano, R$ bilhões, 2011 a agosto de 2026">{gA}</svg>'
# ---- B: ECM, IPO e follow-on lado a lado ----
gB = barras([(a, [f(A[a], "ipo"), f(A[a], "follow_on")]) for a in ANOS], W, H, 80, (0, 20, 40, 60, 80), {2013, 2017, 2019, 2021, 2026}, ["var(--s2)", "var(--s1)"], parcial={2026})
svgB = f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Ofertas de ações por ano, IPO e follow-on, R$ bilhões, 2011 a agosto de 2026">{gB}</svg>'
# ---- C: M&A KPMG ----
AC = list(range(2005, 2026))
gC = barras([(a, [K[a]]) for a in AC], W, H, 2000, (0, 500, 1000, 1500, 2000), {2005, 2009, 2019, 2021, 2025}, ["var(--s3)"], fmt=lambda v: br(v, 0), anos_eixo={a for a in AC if a % 2 == 1})
svgC = f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Número de transações de fusões e aquisições no Brasil por ano, 2005 a 2025">{gC}</svg>'
# ---- D: receita XP + receita sobre volume emitido ----
xa = {}
for q, v in XQ.items(): xa.setdefault(2000 + int(q[2:]), 0); xa[2000 + int(q[2:])] += v
xa[2018] = 178.0
AD = list(range(2018, 2027))
WD, HD, MLD = 310, 184, 33
gD = barras([(a if a < 2026 else "1S26", [xa[a]]) for a in AD], WD, HD, 1400, (0, 500, 1000), set(AD[:-1]) | {"1S26"}, ["var(--s1)"], ML=MLD, MR=4, MB=40, ano_y=HD-24, largura=0.8)
mk = {a: f(A[a], "dcm") + f(A[a], "ecm") for a in range(2019, 2026)}
mk[2026] = sum(f(TQ[q], "dcm") + f(TQ[q], "ecm") for q in ("1Q26", "2Q26"))
take = {a: xa[a] / mk[a] / 10 * 100 for a in range(2019, 2027)}  # R$ mi / R$ bi → % ; ×100 → bp
slot = (WD - MLD - 4) / len(AD)
gD += f'<text x="{MLD-6}" y="{HD-6}" class="tk" text-anchor="end">bp</text>'
for i, a in enumerate(AD):
    if a in take: gD += f'<text x="{MLD+i*slot+slot/2:.1f}" y="{HD-6}" class="tk" text-anchor="middle">{br(take[a],0)}</text>'
svgD = f'<svg class="dsvg" viewBox="0 0 {WD} {HD}" width="100%" role="img" aria-label="Receita de Mercado de Capitais da XP por ano, R$ milhões, e receita sobre o volume emitido no mercado, pontos-base">{gD}</svg>'
# ---- rankings ANBIMA (últimos 12 meses) ----
RK = [("ago/21", "6º · 5,7%", "4º · 10,9%", "7º · 7,5%"), ("dez/22", "6º · 6,9%", "4º · 10,7%", "5º · 8,1%¹"), ("jan/24", "5º · 8,7%", "3º · 14,1%", "6º · 6,7%²"), ("ago/26", "5º · 9,2%", "4º · 7,8%", "9º · 1,0%")]
tab = '<table><tr><th>12&nbsp;meses até</th><th>Originação RF</th><th>Distribuição RF</th><th>Ações</th></tr>' + "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td><td>{d}</td></tr>" for a, b, c, d in RK) + "</table>"

dcm25, dcm19, ecm21, ecm25 = f(A[2025], "dcm"), f(A[2019], "dcm"), f(A[2021], "ecm"), f(A[2025], "ecm")
html = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Mercado de capitais e a XP</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{{--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--ink3:#8a8984;--grid:#e8e7e3;--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--green:#e6f4ea;--greenink:#14532d}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--s1:#3987e5;--s2:#d95926;--s3:#3ccf96;--green:#15301f;--greenink:#b7e4c7}}}}
:root[data-theme="dark"]{{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--s1:#3987e5;--s2:#d95926;--s3:#3ccf96;--green:#15301f;--greenink:#b7e4c7}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--surface);color:var(--ink);font:15px/1.35 Inter,system-ui,sans-serif}}
.slide{{max-width:1240px;margin:0 auto;padding:24px 32px 16px;min-height:720px;display:flex;flex-direction:column;gap:10px}}
header{{display:flex;justify-content:space-between;align-items:baseline;gap:16px}} header>div:first-child{{flex:1}} .kicker{{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink3)}}
h1{{font:600 26px/1.1 Fraunces,Georgia,serif;margin:4px 0 0}} .chip{{font-size:12px;color:var(--ink3);border:1px solid var(--grid);border-radius:999px;padding:3px 10px;white-space:nowrap}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:12px;align-items:start}}
.card{{border:1px solid var(--grid);border-radius:10px;padding:8px 12px}} .card h2{{font:600 13.5px/1.2 Inter,system-ui,sans-serif;margin:0 0 4px;color:var(--ink2)}}
.legend{{display:flex;gap:14px;font-size:12px;color:var(--ink2);margin:0 0 2px;flex-wrap:wrap}} .legend i{{display:inline-block;width:12px;height:12px;vertical-align:-2px;margin-right:5px;border-radius:3px}}
.dflex{{display:grid;grid-template-columns:minmax(0,1fr) min-content;gap:10px;align-items:center}}
table{{border-collapse:collapse;font-size:11px;width:100%}} th,td{{padding:3px 4px;border-bottom:1px solid var(--grid);text-align:left;white-space:nowrap}} th{{color:var(--ink3);font-weight:500;white-space:normal;line-height:1.15;vertical-align:bottom}} td:first-child{{color:var(--ink2)}}
.nota{{font-size:10.5px;color:var(--ink3);margin-top:3px;white-space:normal}}
.green{{background:var(--green);color:var(--greenink);border-radius:10px;padding:9px 14px;font-size:14.5px;font-weight:500}} .fonte{{font-size:10.5px;color:var(--ink3)}}
svg{{display:block}} svg .grid{{stroke:var(--grid);stroke-width:1}} svg .ax{{font:11px Inter,system-ui,sans-serif;fill:var(--ink3)}} svg .v{{font:600 11px Inter,system-ui,sans-serif;fill:var(--ink)}} svg .tk{{font:11px Inter,system-ui,sans-serif;fill:var(--ink2)}} svg.dsvg .v,svg.dsvg .ax{{font-size:10.5px}}
@media (max-width:860px){{.grid2,.dflex{{grid-template-columns:1fr}}h1{{font-size:24px}}}}
</style></head><body><div class="slide">
<header><div><div class="kicker">parte 3 · companhia · banco de investimento</div><h1>DCM em recorde, ECM fechado: o banco de investimento da XP vive de dívida</h1></div><span class="chip">{VERSAO}</span></header>
<div class="grid2">
 <div class="card"><h2>DCM: emissões domésticas de dívida, R$ bi por ano (* 2026 = jan-ago)</h2><div class="legend"><span><i style="background:var(--s1)"></i>debêntures, notas comerciais e promissórias, LF, CRI, CRA, FIDC e outros</span></div>{svgA}</div>
 <div class="card"><h2>ECM: ofertas de ações, R$ bi por ano (* 2026 = jan-ago)</h2><div class="legend"><span><i style="background:var(--s2)"></i>IPO</span><span><i style="background:var(--s1)"></i>follow-on</span></div>{svgB}</div>
 <div class="card"><h2>M&amp;A: número de transações no Brasil por ano</h2><div class="legend"><span><i style="background:var(--s3)"></i>transações anunciadas (KPMG); valor não tem série pública desde que a ANBIMA parou o ranking</span></div>{svgC}</div>
 <div class="card"><h2>XP: receita de Mercado de Capitais (R$ mi) e receita ÷ volume emitido (DCM + ECM, bp)</h2>
  <div class="dflex"><div>{svgD}</div><div>{tab}<div class="nota">Posição e participação da XP nos rankings ANBIMA, 12 meses.<br>¹&nbsp;jun/22. ²&nbsp;abr/24.</div></div></div></div>
</div>
<div class="green">O DCM foi de R$ {br(dcm19,0)} bi em 2019 para R$ {br(dcm25,0)} bi em 2025, e o ECM de R$ {br(ecm21,0)} bi em 2021 para R$ {br(ecm25,0)} bi. A receita da XP acompanha a dívida, entre 13 e 21 bp do volume emitido, e no 1S26 caiu para {br(take[2026],0)} bp, com a XP originando mais do que distribui.</div>
<div class="fonte">Fontes: ANBIMA, Boletim de Mercado de Capitais (dez/17 para 2011-15, dez/22 para 2016-19, anexo consolidado de ago/26 para 2020-26; ofertas encerradas, emissões domésticas; DCM inclui debêntures, notas comerciais, notas promissórias, letras financeiras, CRI, CRA, CR, FIDC, CPR-F e CDCA; ECM = IPO + follow-on; FII e Fiagro fora); ANBIMA, Rankings de Renda Fixa e Híbridos e de Renda Variável (originação e distribuição, últimos 12 meses; edições recuperadas do arquivo público da ANBIMA e do Wayback); KPMG, Pesquisa de Fusões e Aquisições (1T25 e 4T25); XP, releases 4T19-4T20 (Issuer Services 2018-20) e Historical Financials 2T26 (Issuer Services 2021-26). Receita sobre volume = receita de Mercado de Capitais ÷ (DCM + ECM) do ano. Script: dados_ib_historico.py.</div>
</div></body></html>'''
out = os.path.join(HERE, "ib_historico.html"); open(out, "w", encoding="utf-8").write(html)
print("ok", out, "| take bp", {a: round(v, 1) for a, v in take.items()}, "| XP anual", {a: round(v) for a, v in xa.items()})
