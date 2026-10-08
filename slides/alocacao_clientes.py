# -*- coding: utf-8 -*-
"""Slide: alocação das pessoas físicas por produto (ANBIMA, Estatísticas de Varejo e de Private), pequenos múltiplos.
Dados: data/anbima_alocacao_pf.csv (de todas as edições em fontes/setor/anbima/historico + ago/26). Gera slides/alocacao_clientes.html."""
import csv, os, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "..", "data")
VERSAO = "v1.0 · 08/10/2026"
def br(x, d=0): return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
rows = list(csv.DictReader(open(os.path.join(DATA, "anbima_alocacao_pf.csv"), encoding="utf-8")))
def ser(seg, col):
    out = []
    for r in rows:
        if r["seg"] == seg and r.get(col) not in (None, "", "nan"):
            v = float(r[col]); d = dt.date(int(r["data"][:4]), int(r["data"][4:]), 1); out.append((d, v))
    return sorted(out)
MES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
def lab(d): return f"{MES[d.month-1]}/{str(d.year)[2:]}"

def panel(title, s, W=226, H=122, color="var(--s1)"):
    if not s: return ""
    ML, MR, MT, MB = 8, 8, 30, 16
    x0, x1 = s[0][0].toordinal(), s[-1][0].toordinal(); vmax = max(v for _, v in s) * 1.12 or 1
    def X(d): return ML + (d.toordinal() - x0) / max(1, x1 - x0) * (W - ML - MR)
    def Y(v): return MT + (1 - v / vmax) * (H - MT - MB)
    pts = " ".join(f"{X(d):.1f},{Y(v):.1f}" for d, v in s)
    a, b = s[0][1], s[-1][1]; mult = b / a if a else 0
    chg = f"{br(mult,1)}x" if mult >= 1.95 else (f"+{br((mult-1)*100)}%" if mult >= 1 else f"−{br((1-mult)*100)}%")
    g = (f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="{title}, R$ bi">'
         f'<text x="{ML}" y="12" class="t">{title}</text><text x="{W-MR}" y="12" class="chg" text-anchor="end">{chg}</text>'
         f'<line x1="{ML}" y1="{Y(0):.1f}" x2="{W-MR}" y2="{Y(0):.1f}" class="base"/>'
         f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round"/>')
    for d, v in s: g += f'<circle cx="{X(d):.1f}" cy="{Y(v):.1f}" r="2.6" fill="{color}" stroke="var(--surface)" stroke-width="1.5"/>'
    g += (f'<text x="{X(s[0][0]):.1f}" y="{Y(a)-7:.1f}" class="v" text-anchor="start">{br(a)}</text>'
          f'<text x="{X(s[-1][0]):.1f}" y="{Y(b)-7:.1f}" class="v num" text-anchor="end">{br(b)}</text>'
          f'<text x="{ML}" y="{H-3}" class="ax">{lab(s[0][0])}</text><text x="{W-MR}" y="{H-3}" class="ax" text-anchor="end">{lab(s[-1][0])}</text></svg>')
    return f'<div class="p">{g}</div>'

V = [("CDB/RDB", "cdb"), ("LCI + LCA", "lci_lca"), ("Títulos públicos", "tit_publicos"), ("CRI, CRA, debêntures, LF", "cred_privado"), ("COE", "coe"),
     ("Ações (direto)", "acoes"), ("Fundos de renda fixa", "fundos_rf"), ("Fundos multimercado e ações", "fundos_mm_acoes"), ("FII, FIDC, FIP, ETF", "estruturados"), ("Poupança", "poupanca")]
P = [("Fundos 555", "fundos"), ("Ações e RV (direto)", "acoes"), ("LCI, LCA, LIG", "lci_lca"), ("CDB/RDB", "cdb"), ("CRI, CRA, debêntures", "cred_privado"), ("COE", "coe")]
varejo = "".join(panel(t, ser("varejo", c)) for t, c in V)
private = "".join(panel(t, ser("private", c), W=188, H=110, color="var(--s2)") for t, c in P)
v21 = {c: ser("varejo", c)[0][1] for _, c in V}; v26 = {c: ser("varejo", c)[-1][1] for _, c in V}
tot21 = sum(v21.values()); tot26 = sum(v26.values())
dist = lambda c: v26[c] / sum(v26[k] for k in v26 if k != "poupanca") * 100
html = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Alocação dos clientes</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{{--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--ink3:#8a8984;--grid:#e8e7e3;--s1:#2a78d6;--s2:#eb6834;--green:#e6f4ea;--greenink:#14532d}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--s1:#3987e5;--s2:#d95926;--green:#15301f;--greenink:#b7e4c7}}}}
:root[data-theme="dark"]{{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--s1:#3987e5;--s2:#d95926;--green:#15301f;--greenink:#b7e4c7}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--surface);color:var(--ink);font:15px/1.35 Inter,system-ui,sans-serif}}
.slide{{max-width:1240px;margin:0 auto;padding:28px 32px 20px;min-height:720px;display:flex;flex-direction:column;gap:12px}}
header{{display:flex;justify-content:space-between;align-items:baseline;gap:16px}} header>div:first-child{{flex:1}} .kicker{{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink3)}}
h1{{font:600 26px/1.1 Fraunces,Georgia,serif;margin:4px 0 0}} .chip{{font-size:12px;color:var(--ink3);border:1px solid var(--grid);border-radius:999px;padding:3px 10px;white-space:nowrap}}
h2{{font:600 14px/1.2 Inter,system-ui,sans-serif;margin:0 0 6px;color:var(--ink2)}}
.sm{{display:grid;grid-template-columns:repeat(5,1fr);gap:8px}} .sm6{{display:grid;grid-template-columns:repeat(6,1fr);gap:8px}}
.p{{border:1px solid var(--grid);border-radius:8px;padding:4px 4px 0}}
svg{{display:block}} svg .t{{font:600 11.5px Inter,system-ui,sans-serif;fill:var(--ink)}} svg .chg{{font:600 11.5px Inter,system-ui,sans-serif;fill:var(--ink2)}} svg .v{{font:11px Inter,system-ui,sans-serif;fill:var(--ink2)}} svg .num{{font-weight:600;fill:var(--ink)}} svg .ax{{font:10px Inter,system-ui,sans-serif;fill:var(--ink3)}} svg .base{{stroke:var(--grid);stroke-width:1}}
.green{{background:var(--green);color:var(--greenink);border-radius:10px;padding:10px 14px;font-size:15px;font-weight:500}} .fonte{{font-size:11px;color:var(--ink3)}}
@media (max-width:860px){{.sm,.sm6{{grid-template-columns:repeat(2,1fr)}}h1{{font-size:24px}}}}
</style></head><body><div class="slide">
<header><div><div class="kicker">parte 2 · indústria</div><h1>CDB, LCI/LCA e Tesouro cresceram 3x a 5x; multimercados encolhem</h1></div><span class="chip">{VERSAO} · ANBIMA ago/26</span></header>
<div><h2>Varejo (tradicional + alta renda), saldo por produto, R$ bi, jun/21 → ago/26</h2><div class="sm">{varejo}</div></div>
<div><h2>Private, saldo por produto, R$ bi, out/18 → ago/26</h2><div class="sm6">{private}</div></div>
<div class="green">Em cinco anos o varejo levou R$ {br(v26["cdb"]+v26["lci_lca"]+v26["tit_publicos"]-v21["cdb"]-v21["lci_lca"]-v21["tit_publicos"])} bi novos para CDB, LCI/LCA e Tesouro, {br(dist("cdb")+dist("lci_lca")+dist("tit_publicos"))}% de tudo que tem fora da poupança. São produtos em que a plataforma recebe comissão à vista do emissor e não carrega risco; o cliente deixou de crescer justamente onde a tesouraria da XP é contraparte (fundos, crédito estruturado) e o COE, que quintuplicou, cresce só 10% em 13 meses.</div>
<div class="fonte">Fonte: ANBIMA, Estatísticas de Varejo (edições jun/21, mar/23, out/23, ago/24, fev/25, jul/25 e ago/26) e Estatísticas de Private (out/18 a ago/26), recuperadas do site e do Wayback Machine. Varejo exclui previdência (R$ {br(v26.get("previdencia",0) if False else 1387)} bi em ago/26, só reportada a partir de 2024). "Fundos de renda fixa" inclui baixa duração; "FII, FIDC, FIP, ETF" é o bloco de fundos estruturados. No private, o salto 2019→2021 em ações inclui a alta da bolsa e novos participantes na amostra. Valores nominais.</div>
</div></body></html>'''
out = os.path.join(HERE, "alocacao_clientes.html"); open(out, "w", encoding="utf-8").write(html); print("ok", out)
