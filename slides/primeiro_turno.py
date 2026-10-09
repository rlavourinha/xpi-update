# -*- coding: utf-8 -*-
"""Slide: a atividade na B3 pregão a pregão antes e depois do 1º turno (04/10/2026), pelo Boletim Diário da B3.
Dados: data/b3_bdi_diario.csv (dados_b3_bdi_diario.py) e data/_ibov_diario.csv. Gera slides/primeiro_turno.html."""
import csv, os, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "..", "data")
VERSAO = "v1.3 · 09/10/2026"
def br(x, d=1): return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".").replace("-", "−")
rows = sorted(csv.DictReader(open(os.path.join(DATA, "b3_bdi_diario.csv"), encoding="utf-8")), key=lambda r: r["data"])
ibov = {r["data"]: float(r["ibov"]) for r in csv.DictReader(open(os.path.join(DATA, "_ibov_diario.csv"), encoding="utf-8")) if r["ibov"]}
D = [r["data"] for r in rows]; n = len(D); ELEICAO = "2026-10-05"; iE = D.index(ELEICAO)
def f(r, k):
    try: return float(r[k])
    except Exception: return None
S = {
 "ibov": [ibov.get(d) for d in D],
 "acoes": [f(r, "acoes_negocios") / 1e6 for r in rows], "vol": [f(r, "acoes_vol_mi") / 1e3 for r in rows],
 "opcoes": [f(r, "opcoes_negocios") / 1e3 for r in rows], "win": [f(r, "win_negocios") / 1e6 for r in rows], "wdo": [f(r, "wdo_negocios") / 1e3 for r in rows],
 "btc": [f(r, "btc_negocios") / 1e3 for r in rows], "xp": [f(r, "btc_xp_tomador") / f(r, "btc_negocios") * 100 for r in rows], "pf": [f(r, "pf_compras_pct") for r in rows],
}
PAINEIS = [("ibov", "Ibovespa, pontos", 0), ("acoes", "Negócios em ações, mi/dia", 1), ("vol", "Volume em ações, R$ bi/dia", 1), ("opcoes", "Negócios em opções, mil/dia", 0),
           ("win", "Negócios em mini-índice (WIN), mi/dia", 1), ("wdo", "Negócios em mini-dólar (WDO), mil/dia", 0), ("btc", "Negócios de aluguel de ações, mil/dia", 0), ("xp", "XP tomadora no aluguel, % dos negócios", 0), ("pf", "Pessoa física nas compras à vista, % (acum. mês)", 1)]
def lab(d): return f"{d[8:10]}/{d[5:7]}"
def media(v, a, b):
    x = [t for t in v[a:b] if t is not None]; return sum(x) / len(x) if x else None
def panel(k, title, dec):
    v = S[k]; W, H, ML, MR, MT, MB = 376, 140, 8, 8, 40, 20
    vals = [t for t in v if t is not None]; lo, hi = min(vals), max(vals); pad = (hi - lo) * 0.15 or 1; lo -= pad
    if k in ("acoes", "vol", "opcoes", "win", "wdo", "btc"): lo = 0
    HEAD = 14  # px reservados acima do máximo para o rótulo do valor
    def X(i): return ML + i / (n - 1) * (W - ML - MR)
    def Y(t): return MT + HEAD + (hi - t) / (hi - lo) * (H - MT - HEAD - MB)
    m1, m2 = media(v, 0, iE), media(v, iE, n); chg = (m2 / m1 - 1) * 100 if m1 else 0
    pts = " ".join(f"{X(i):.1f},{Y(t):.1f}" for i, t in enumerate(v) if t is not None)
    g = (f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="{title}, pregão a pregão de {lab(D[0])} a {lab(D[-1])}">'
         f'<text x="{ML}" y="13" class="t">{title}</text>'
         f'<text x="{W-MR}" y="13" class="chg{" neg" if chg < 0 else ""}" text-anchor="end">{"+" if chg >= 0 else ""}{br(chg, 0)}%</text>'
         f'<text x="{ML}" y="28" class="sub">média antes {br(m1, dec)} · depois {br(m2, dec)}</text>'
         f'<line x1="{ML}" y1="{H-MB}" x2="{W-MR}" y2="{H-MB}" stroke="var(--grid)" stroke-width="1"/>'
         f'<rect x="{X(iE)-X(1)/2+X(0)/2:.1f}" y="{MT}" width="{X(n-1)-X(iE)+ (X(1)-X(0))/2:.1f}" height="{H-MT-MB}" fill="var(--s2)" opacity="var(--shade)"/>'
         f'<line x1="{X(iE):.1f}" y1="{MT}" x2="{X(iE):.1f}" y2="{H-MB}" stroke="var(--s2)" stroke-width="1" stroke-dasharray="3 3"/>'
         f'<line x1="{ML}" y1="{Y(m1):.1f}" x2="{X(iE-1):.1f}" y2="{Y(m1):.1f}" stroke="var(--ink3)" stroke-width="1" stroke-dasharray="2 3"/>'
         f'<line x1="{X(iE):.1f}" y1="{Y(m2):.1f}" x2="{W-MR}" y2="{Y(m2):.1f}" stroke="var(--ink3)" stroke-width="1" stroke-dasharray="2 3"/>'
         f'<polyline points="{pts}" fill="none" stroke="var(--s1)" stroke-width="2" stroke-linejoin="round"/>')
    for i, t in enumerate(v):
        if t is None: continue
        g += f'<circle cx="{X(i):.1f}" cy="{Y(t):.1f}" r="{3 if i>=iE else 2.2}" fill="{"var(--s2)" if i>=iE else "var(--s1)"}" stroke="var(--surface)" stroke-width="1.2"/>'
    imx = max(range(n), key=lambda i: (v[i] if v[i] is not None else -1e18)); xm = X(imx)
    anc, xl = ("end", xm + 3) if xm > W - MR - 26 else ("start", xm - 3) if xm < ML + 26 else ("middle", xm)
    g += f'<text x="{xl:.1f}" y="{Y(v[imx])-8:.1f}" class="v num" text-anchor="{anc}">{br(v[imx], dec)}</text>'
    g += f'<text x="{ML}" y="{H-5}" class="ax">{lab(D[0])}</text><text x="{X(iE)-4:.1f}" y="{H-5}" class="ax" text-anchor="end">1º turno · {lab(ELEICAO)} →</text><text x="{W-MR}" y="{H-5}" class="ax" text-anchor="end">{lab(D[-1])}</text></svg>'
    return f'<div class="p">{g}</div>'
grid = "".join(panel(*p) for p in PAINEIS)
m = {k: (media(S[k], 0, iE), media(S[k], iE, n)) for k in S}
html = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Primeiro turno na B3</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{{--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--ink3:#8a8984;--grid:#e8e7e3;--s1:#2a78d6;--s2:#eb6834;--neg:#e34948;--green:#e6f4ea;--greenink:#14532d;--shade:.08}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--s1:#3987e5;--s2:#d95926;--neg:#e66767;--green:#15301f;--greenink:#b7e4c7;--shade:.16}}}}
:root[data-theme="dark"]{{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--s1:#3987e5;--s2:#d95926;--neg:#e66767;--green:#15301f;--greenink:#b7e4c7;--shade:.16}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--surface);color:var(--ink);font:15px/1.35 Inter,system-ui,sans-serif}}
.slide{{max-width:1240px;margin:0 auto;padding:24px 32px 16px;min-height:720px;display:flex;flex-direction:column;gap:12px}}
header{{display:flex;justify-content:space-between;align-items:baseline;gap:16px}} header>div:first-child{{flex:1}} .kicker{{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink3)}}
h1{{font:600 26px/1.1 Fraunces,Georgia,serif;margin:4px 0 0}} .chip{{font-size:12px;color:var(--ink3);border:1px solid var(--grid);border-radius:999px;padding:3px 10px;white-space:nowrap}}
.sm{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}} .p{{border:1px solid var(--grid);border-radius:8px;padding:4px 4px 0}}
svg{{display:block}} svg .t{{font:600 12px Inter,system-ui,sans-serif;fill:var(--ink)}} svg .sub{{font:11px Inter,system-ui,sans-serif;fill:var(--ink2)}} svg .chg{{font:600 13px Inter,system-ui,sans-serif;fill:var(--ink)}} svg .chg.neg{{fill:var(--neg)}} svg .v{{font:11px Inter,system-ui,sans-serif;fill:var(--ink2)}} svg .num{{font-weight:600;fill:var(--ink)}} svg .ax{{font:10px Inter,system-ui,sans-serif;fill:var(--ink3)}}
.green{{background:var(--green);color:var(--greenink);border-radius:10px;padding:10px 14px;font-size:15px;font-weight:500}} .fonte{{font-size:11px;color:var(--ink3)}}
@media (max-width:860px){{.sm{{grid-template-columns:1fr}}h1{{font-size:24px}}}}
</style></head><body><div class="slide">
<header><div><div class="kicker">parte 2 · indústria · monitor diário</div><h1>1º turno: a bolsa dobrou de negócios e os minis subiram um terço</h1></div><span class="chip">{VERSAO} · BDI até {lab(D[-1])}</span></header>
<div class="sm">{grid}</div>
<div class="green">Nos quatro pregões após o 1º turno, ações fizeram {br(m["acoes"][1],1)} milhões de negócios por dia contra {br(m["acoes"][0],1)} antes, com volume de R$ {br(m["vol"][1],0)} bi contra {br(m["vol"][0],0)}; o mini-índice foi de {br(m["win"][0],1)} para {br(m["win"][1],1)} milhões e o aluguel dobrou, com a XP tomando {br(m["xp"][1],0)}% dos contratos contra {br(m["xp"][0],0)}% antes. A pessoa física não acompanhou: sua fatia nas compras caiu de {br(m["pf"][0],1)}% para {br(m["pf"][1],1)}%.</div>
<div class="fonte">Fonte: B3, Boletim Diário do Mercado (API arquivos.b3.com.br/bdi): negócios por mercado em ações, negócios por contrato em derivativos, aluguel de ações negócio a negócio com o participante tomador (XP = XP Investimentos CCTVM, que já inclui Rico e Clear) e participação dos investidores (acumulado do mês, lado comprador); Ibovespa pelo fechamento diário. "Antes" = {lab(D[0])} a {lab(D[iE-1])} ({iE} pregões); "depois" = {lab(ELEICAO)} a {lab(D[-1])} ({n-iE} pregões). A área sombreada marca os pregões após o 1º turno de 04/10/2026.</div>
</div></body></html>'''
out = os.path.join(HERE, "primeiro_turno.html"); open(out, "w", encoding="utf-8").write(html); print("ok", out, n, "pregões; eleição idx", iE)
