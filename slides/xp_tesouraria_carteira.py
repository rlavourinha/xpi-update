# -*- coding: utf-8 -*-
"""Slide: o que a tesouraria da XP carrega (CDA da CVM, posição de fim de mês) e qual produto do cliente cada livro enfrenta.
Dados: data/xp_tesouraria_cda_resumo.json (de dados_xp_tesouraria_cda.py + agregação) e data/_xp_tes_pnl_diario.csv. Gera slides/xp_tesouraria_carteira.html."""
import json, os, csv, statistics as st
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "..", "data")
VERSAO = "v1.0 · 08/10/2026"
def br(x, d=1): return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
R = json.load(open(os.path.join(DATA, "xp_tesouraria_cda_resumo.json"), encoding="utf-8"))
T6 = {r["F"]: r for r in R["202606"]["tabela"]}; T4 = {r["F"]: r for r in R["202412"]["tabela"]}
# perfil diário 2026 por fundo
P = defaultdict(list); PLU = {}
for r in csv.DictReader(open(os.path.join(DATA, "_xp_tes_pnl_diario.csv"), encoding="utf-8")):
    if r["DT_COMPTC"] >= "2026-01-01" and r["DT_COMPTC"] <= "2026-09-30":
        f = r["F"].title().replace("Xp Nix", "XP Nix"); P[f].append(float(r["pnl"] or 0)); PLU[f] = float(r["VL_PATRIM_LIQ"] or 0)
def perfil(f):
    v = P.get(f, []);
    if not v: return dict(pos=0, tot=0, sd=0)
    return dict(pos=round(100 * sum(1 for x in v if x > 0) / len(v)), tot=sum(v) / 1e9, sd=st.pstdev(v) / 1e6)

ROWS = ["Nimrod", "Gladius", "Scorpio", "Falx", "Aspis", "Coliseu", "Macadâmia"]
OUTROS = ["Javelin", "Kopis", "Harpe", "XP Nix"]
COLS = [("tit_publicos", "Títulos públicos"), ("compromissadas", "Compro-missadas"), ("swaps", "Swaps (2 pontas)"), ("opcoes", "Opções (2 pontas)"), ("acoes_tomadas", "Ações tomadas em aluguel"), ("credito", "Crédito privado e FIDC"), ("exterior", "Exterior"), ("passivos", "Passivos (venda/ compro-missada)")]
def val(t, k):
    if k == "swaps": return t.get("swap_receber", 0) + t.get("swap_pagar", 0)
    if k == "opcoes": return t.get("opcoes_compradas", 0) + t.get("opcoes_vendidas", 0)
    if k == "acoes_tomadas": return t.get("acoes_tomadas", 0) + t.get("acoes", 0)
    return t.get(k, 0)
def row(f):
    if f == "Outros 4":
        t6 = {k: sum(val(T6.get(x, {}), k) for x in OUTROS) for k, _ in COLS}; t6["PL"] = sum(T6.get(x, {}).get("PL", 0) for x in OUTROS); pl4 = sum(T4.get(x, {}).get("PL", 0) for x in OUTROS)
        return t6, pl4
    t = T6.get(f, {}); return {k: val(t, k) for k, _ in COLS} | {"PL": t.get("PL", 0)}, T4.get(f, {}).get("PL", 0)
tab = [(f, *row(f)) for f in ROWS + ["Outros 4"]]
vmax = max(v[k] for _, v, _ in tab for k, _ in COLS)

# ---- heatmap SVG ----
# larguras por coluna (viewBox ~ largura renderizada do painel, ~674px, para que as fontes fiquem em escala 1:1)
CWS = {"tit_publicos": 54, "compromissadas": 54, "swaps": 54, "opcoes": 54, "acoes_tomadas": 60, "credito": 54, "exterior": 46, "passivos": 86, "PL": 50, "DPL": 60}
LW, RH, HH, HLH = 78, 30, 44, 12
ALL = COLS + [("PL", "PL jun/26"), ("DPL", "Δ PL vs dez/24")]
X0 = {}; x = LW
for k, _ in ALL: X0[k] = x; x += CWS[k]
W = x + 4; H = HH + RH * len(tab) + 8
def wrap(lab, cw, px=5.5):
    """quebra o cabeçalho em até 3 linhas: nos espaços e depois de hífens; limite por largura estimada (px por caractere)."""
    toks = []
    for w in lab.split(" "):
        parts = w.split("-")
        for i, pt in enumerate(parts):
            toks.append((pt + ("-" if i < len(parts) - 1 else ""), " " if i == 0 else ""))
    lines, cur = [], ""
    for t, sep in toks:
        cand = (cur + sep + t) if cur else t
        if cur and len(cand) * px > cw - 2: lines.append(cur); cur = t
        else: cur = cand
    lines.append(cur); return lines[:3]
def cell(v):
    a = 0.06 + 0.84 * (v / vmax) ** 0.6 if v > 0 else 0
    return f'rgba(42,120,214,{a:.2f})'
svg = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Carteira dos fundos de tesouraria da XP por tipo de posição, jun/26, R$ bi">']
for k, lab in ALL:
    x = X0[k] + CWS[k] / 2
    for li, ln in enumerate(wrap(lab, CWS[k])): svg.append(f'<text x="{x}" y="{12 + li * HLH}" class="hd" text-anchor="middle">{ln}</text>')
for i, (f, v, pl4) in enumerate(tab):
    y = HH + i * RH
    if i % 2 == 0: svg.append(f'<rect x="0" y="{y}" width="{W}" height="{RH}" fill="var(--grid)" opacity=".35"/>')
    svg.append(f'<text x="6" y="{y + RH / 2 + 4}" class="lab num">{f}</text>')
    for k, _ in COLS:
        x = X0[k]; cw = CWS[k]; vv = v[k]
        svg.append(f'<rect x="{x + 2}" y="{y + 3}" width="{cw - 4}" height="{RH - 6}" rx="4" fill="{cell(vv)}"/>')
        if vv >= 0.05: svg.append(f'<text x="{x + cw / 2}" y="{y + RH / 2 + 4}" class="cv{" inv" if vv / vmax > 0.45 else ""}" text-anchor="middle">{br(vv, 1)}</text>')
        else: svg.append(f'<text x="{x + cw / 2}" y="{y + RH / 2 + 4}" class="cv dim" text-anchor="middle">·</text>')
    x = X0["PL"]; svg.append(f'<text x="{x + CWS["PL"] / 2}" y="{y + RH / 2 + 4}" class="lab num" text-anchor="middle">{br(v["PL"], 1)}</text>')
    d = v["PL"] - pl4; x = X0["DPL"] + CWS["DPL"] / 2
    # texto em tinta; o sinal vai no marcador colorido, não na fonte
    svg.append(f'<circle cx="{x - 22}" cy="{y + RH / 2}" r="3" fill="{"var(--pos)" if d >= 0 else "var(--neg)"}"/><text x="{x + 4}" y="{y + RH / 2 + 4}" class="lab" text-anchor="middle">{"+" if d >= 0 else "−"}{br(abs(d), 1)}</text>')
svg.append("</svg>"); svgT = "".join(svg)

# ---- cartões por livro ----
pf = {f: perfil(f) for f in ["Nimrod", "Gladius", "Scorpio", "Aspis", "XP Nix", "Coliseu"]}
g6 = T6["Gladius"]; n6 = T6["Nimrod"]; s6 = T6["Scorpio"]
cards = [
 ("Nimrod · livro de juros", f'R$ {br(n6["tit_publicos"],0)} bi em NTN-B/NTN-F financiados por R$ {br(n6["passivos"],0)} bi de compromissadas e vendas, mais R$ {br(n6["swap_receber"]+n6["swap_pagar"],0)} bi de swaps DI (2 pontas) e R$ {br(n6["cotas_grupo"],0)} bi em cotas de Gladius e Scorpio. Faz o hedge da renda fixa vendida ao cliente. Em jun/26: 155 mil mini-índice e 25 mil índice comprados.', pf["Nimrod"]),
 ("Gladius · derivativos de ações", f'Opções: R$ {br(g6["opcoes_compradas"],1)} bi compradas e {br(g6["opcoes_vendidas"],1)} bi vendidas (3.200 posições em IBOV, BOVA, PETR, VALE); R$ {br(g6["acoes_tomadas"],1)} bi de ações tomadas em aluguel; 2,8 mi de futuros de ações; R$ {br(g6["exterior"],1)} bi no exterior. Contraparte das estruturadas, do COE e do aluguel do varejo.', pf["Gladius"]),
 ("Scorpio · crédito corporativo", f'R$ {br(s6["credito"],1)} bi em debêntures, CRA e cotas de FIDC (ER, ER 2030, Frade III). De R$ 1,6 bi (dez/24) para R$ {br(s6["PL"],1)} bi: o estoque de crédito que a XP origina antes de distribuir. Carrego, quase sem dia negativo.', pf["Scorpio"]),
 ("Aspis, XP Nix, Coliseu", f'Aspis: FIDC de consignado (XP Return I, R$ 1,5 bi). XP Nix: debêntures de infraestrutura, de R$ 6,0 bi (jun/25) para R$ 0,1 bi: o papel foi para o cliente, que compra isento. Coliseu era o fundo-mãe de Gladius e Scorpio até dez/25.', pf["Aspis"]),
]
def card(t, txt, p):
    return f'<div class="card"><h3>{t}</h3><p>{txt}</p><div class="st"><span><b>{p["pos"]}%</b> dias positivos em 2026</span><span><b>R$ {br(p["tot"],1)} bi</b> resultado jan–set/26</span><span><b>R$ {br(p["sd"],0)} mi</b> vol. diária</span></div></div>'
cardsH = "".join(card(*c) for c in cards)

html = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Livros da tesouraria</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{{--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--ink3:#8a8984;--grid:#e8e7e3;--s1:#2a78d6;--pos:#1baf7a;--neg:#e34948;--green:#e6f4ea;--greenink:#14532d}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--s1:#3987e5;--pos:#3ccf96;--neg:#e66767;--green:#15301f;--greenink:#b7e4c7}}}}
:root[data-theme="dark"]{{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--s1:#3987e5;--pos:#3ccf96;--neg:#e66767;--green:#15301f;--greenink:#b7e4c7}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--surface);color:var(--ink);font:15px/1.35 Inter,system-ui,sans-serif}}
.slide{{max-width:1240px;margin:0 auto;padding:28px 32px 20px;min-height:720px;display:flex;flex-direction:column;gap:14px}}
header{{display:flex;justify-content:space-between;align-items:baseline;gap:16px}} header>div:first-child{{flex:1}} .kicker{{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink3)}}
h1{{font:600 26px/1.1 Fraunces,Georgia,serif;margin:4px 0 0}} .chip{{font-size:12px;color:var(--ink3);border:1px solid var(--grid);border-radius:999px;padding:3px 10px;white-space:nowrap}}
.grid2{{display:grid;grid-template-columns:1.55fr 1fr;gap:20px;align-items:start}}
.panel{{border:1px solid var(--grid);border-radius:10px;padding:12px 14px}} .panel h2{{font:600 14px/1.2 Inter,system-ui,sans-serif;margin:0 0 8px;color:var(--ink2)}}
.cards{{display:grid;grid-template-columns:1fr;gap:8px}} .card{{border:1px solid var(--grid);border-radius:10px;padding:8px 12px}} .card h3{{font:600 14px/1.2 Inter,system-ui,sans-serif;margin:0 0 4px}} .card p{{margin:0;font-size:12px;color:var(--ink2);line-height:1.32}}
.st{{display:flex;gap:12px;margin-top:6px;font-size:11.5px;color:var(--ink3);flex-wrap:wrap}} .st b{{color:var(--ink);font-weight:600}}
.green{{background:var(--green);color:var(--greenink);border-radius:10px;padding:10px 14px;font-size:15px;font-weight:500}} .fonte{{font-size:11px;color:var(--ink3)}}
svg{{display:block}} svg .hd{{font:10.5px/1 Inter,system-ui,sans-serif;fill:var(--ink3)}} svg .lab{{font:12.5px Inter,system-ui,sans-serif;fill:var(--ink)}} svg .num{{font-weight:600}} svg .cv{{font:12px Inter,system-ui,sans-serif;fill:var(--ink)}} svg .cv.inv{{fill:#fff}} svg .cv.dim{{fill:var(--ink3)}}
@media (max-width:860px){{.grid2{{grid-template-columns:1fr}}h1{{font-size:24px}}}}
</style></head><body><div class="slide">
<header><div><div class="kicker">parte 4 · qualidade do lucro</div><h1>Três livros: juros, derivativos de ações e crédito. Só ações cresceu</h1></div><span class="chip">{VERSAO} · CDA jun/26</span></header>
<div class="grid2">
 <div class="panel"><h2>Posições brutas por fundo em 30/06/2026, R$ bi (valor de mercado; swaps e opções somam as duas pontas)</h2>{svgT}
 <div class="fonte" style="margin-top:8px">Dez/24 → jun/26 as posições brutas (ex-cotas internas) foram de R$ 240 bi para R$ 350 bi sobre R$ 46 bi de capital. Futuros entram pelo ajuste, não pelo nocional (Gladius: 5,5 mi de contratos de DI e 2,8 mi de futuros de ações). O RLP, provedor de liquidez do varejo em minicontratos, é intradiário e não aparece na foto de fim de mês.</div></div>
 <div class="cards">{cardsH}</div>
</div>
<div class="green">O cliente de varejo migrou para CDB, LCI/LCA e Tesouro, produtos em que a XP só distribui e não é contraparte; o estoque de crédito que a tesouraria carregava para ele (XP Nix, Coliseu) foi vendido e não reposto. O que ainda cresce é o livro de derivativos de ações (Gladius), contraparte das estruturadas e do COE.</div>
<div class="fonte">Fonte: CVM, Composição e Diversificação das Aplicações (CDA) de 12/2024 e 06/2026 dos fundos geridos pela XP Investimentos CCTVM; informes diários (resultado = ΔPL − captação + resgate). Posições de fim de mês; nocional de futuros e de swaps não é divulgado no CDA de forma homogênea. "Passivos" = outras operações passivas e exigibilidades (venda de títulos com compromisso de recompra e vendas a descoberto). Resultado por fundo em 2026 inclui, no Nimrod, o que vem das cotas de Gladius e Scorpio.</div>
</div></body></html>'''
out = os.path.join(HERE, "xp_tesouraria_carteira.html"); open(out, "w", encoding="utf-8").write(html); print("ok", out)
