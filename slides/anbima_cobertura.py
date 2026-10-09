# -*- coding: utf-8 -*-
"""Linha do tempo da cobertura dos dados ANBIMA de alocação da PF por segmento: que meses temos, de qual fonte e com que abertura.
Lê data/anbima_alocacao_segmentos_long.csv (edições), data/anbima_alocacao_segmentos_anual_long.csv (anexo), data/anbima_alocacao_coletivas.csv
e data/anbima_pf_total_mensal_2020.csv. Gera slides/anbima_cobertura.html (diagnóstico, fora do deck)."""
import os, datetime as dt, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "..", "data")
E = pd.read_csv(os.path.join(DATA, "anbima_alocacao_segmentos_long.csv")); A = pd.read_csv(os.path.join(DATA, "anbima_alocacao_segmentos_anual_long.csv"))
C = pd.read_csv(os.path.join(DATA, "anbima_alocacao_coletivas.csv")); T = pd.read_csv(os.path.join(DATA, "anbima_pf_total_mensal_2020.csv"))
SEGS = [("varejo_tradicional", "Varejo tradicional"), ("varejo_alta_renda", "Varejo alta renda"), ("private", "Private")]
pts = {s: {"edicao": sorted(E[E.seg == s].data.unique()), "anexo": sorted(A[A.seg == s].ano.unique() * 100 + 12), "coletiva": sorted(C[C.seg == s].data.unique())} for s, _ in SEGS}
def t(d): y, m = divmod(int(d), 100); return y + (m - 0.5) / 12
X0, X1 = 2013.5, 2026.9; W, H = 1180, 250; ML, MR, MT, MB = 150, 20, 34, 30
def X(v): return ML + (v - X0) / (X1 - X0) * (W - ML - MR)
ROWH = (H - MT - MB) / (len(SEGS) + 1)
COR = {"anexo": "var(--s1)", "edicao": "var(--s2)", "coletiva": "var(--s3)"}
svg = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Linha do tempo dos pontos de dados ANBIMA por segmento e fonte, 2013 a 2026">']
for y in range(2014, 2027):
    svg.append(f'<line x1="{X(y-1):.1f}" y1="{MT}" x2="{X(y-1):.1f}" y2="{H-MB}" stroke="var(--grid)" stroke-width="1"/>')
    svg.append(f'<text x="{X(y-0.5):.1f}" y="{H-MB+16}" class="ax" text-anchor="middle">{y}</text>')
svg.append(f'<line x1="{X(X1):.1f}" y1="{MT}" x2="{X(X1):.1f}" y2="{H-MB}" stroke="var(--grid)" stroke-width="1"/>')
for i, (s, nome) in enumerate(SEGS + [("pf_total", "Total PF (só o total)")]):
    yc = MT + ROWH * (i + 0.5)
    svg.append(f'<line x1="{ML}" y1="{yc:.1f}" x2="{W-MR}" y2="{yc:.1f}" stroke="var(--grid)" stroke-width="1" stroke-dasharray="2 4"/>')
    svg.append(f'<text x="{ML-10}" y="{yc+4:.1f}" class="lab" text-anchor="end">{nome}</text>')
    if s == "pf_total":
        for d in T.data: svg.append(f'<rect x="{X(t(d))-2.5:.1f}" y="{yc-7:.1f}" width="5" height="14" fill="{COR["coletiva"]}" rx="1"/>')
        continue
    for d in pts[s]["coletiva"]: svg.append(f'<rect x="{X(t(d))-5:.1f}" y="{yc-5:.1f}" width="10" height="10" fill="{COR["coletiva"]}" transform="rotate(45 {X(t(d)):.1f} {yc:.1f})"/>')
    for d in pts[s]["edicao"]: svg.append(f'<rect x="{X(t(d))-2.5:.1f}" y="{yc-9:.1f}" width="5" height="18" fill="{COR["edicao"]}" rx="1"/>')
    for d in pts[s]["anexo"]: svg.append(f'<circle cx="{X(t(d)):.1f}" cy="{yc:.1f}" r="6.5" fill="{COR["anexo"]}" stroke="var(--surface)" stroke-width="1.5"/>')
    ne, na, nc = len(pts[s]["edicao"]), len(pts[s]["anexo"]), len(set(pts[s]["coletiva"]) - set(pts[s]["edicao"]) - set(pts[s]["anexo"]))
    svg.append(f'<text x="{W-MR}" y="{yc-12:.1f}" class="n" text-anchor="end">{na} dez · {ne} edições · {nc} coletivas</text>')
svg.append("</svg>")
# anos sem nenhuma edição completa (só o dezembro do anexo)
def anos_sem_edicao(s): return [y for y in range(2014, 2027) if not any(d // 100 == y for d in pts[s]["edicao"])]
falta = {nome: anos_sem_edicao(s) for s, nome in SEGS}
VERSAO = "diagnóstico · " + dt.date.today().strftime("%d/%m/%Y")
html = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Cobertura ANBIMA</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{{--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--ink3:#8a8984;--grid:#e8e7e3;--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--green:#e6f4ea;--greenink:#14532d}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--s1:#3987e5;--s2:#d95926;--s3:#2bc48a;--green:#15301f;--greenink:#b7e4c7}}}}
:root[data-theme="dark"]{{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--s1:#3987e5;--s2:#d95926;--s3:#2bc48a;--green:#15301f;--greenink:#b7e4c7}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--surface);color:var(--ink);font:15px/1.35 Inter,system-ui,sans-serif}}
.slide{{max-width:1240px;margin:0 auto;padding:24px 32px 16px;min-height:720px;display:flex;flex-direction:column;gap:12px}}
header{{display:flex;justify-content:space-between;align-items:baseline;gap:16px}} header>div:first-child{{flex:1}} .kicker{{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink3)}}
h1{{font:600 26px/1.1 Fraunces,Georgia,serif;margin:4px 0 0}} .chip{{font-size:12px;color:var(--ink3);border:1px solid var(--grid);border-radius:999px;padding:3px 10px;white-space:nowrap}}
svg{{display:block}} svg .ax{{font:11px Inter,system-ui,sans-serif;fill:var(--ink3)}} svg .lab{{font:600 13px Inter,system-ui,sans-serif;fill:var(--ink)}} svg .n{{font:11px Inter,system-ui,sans-serif;fill:var(--ink2)}}
.leg{{display:flex;gap:22px;flex-wrap:wrap;font-size:13px;color:var(--ink2)}} .leg span{{display:inline-flex;align-items:center;gap:7px}} .sw{{width:12px;height:12px;display:inline-block;border-radius:50%}} .sw.b{{border-radius:1px;width:5px;height:16px}} .sw.d{{border-radius:1px;transform:rotate(45deg);width:10px;height:10px}}
table{{border-collapse:collapse;width:100%;font-size:12.5px}} th,td{{padding:4px 10px;border-bottom:1px solid var(--grid);text-align:left;vertical-align:top}} th{{color:var(--ink3);font-weight:500;font-size:12px}} td:first-child{{font-weight:600;white-space:nowrap}}
.ok{{color:var(--greenink)}} .green{{background:var(--green);color:var(--greenink);border-radius:10px;padding:10px 14px;font-size:14px;font-weight:500}} .fonte{{font-size:11px;color:var(--ink3)}}
</style></head><body><div class="slide">
<header><div><div class="kicker">anbima · alocação da pessoa física · cobertura da base</div><h1>Dezembros completos desde 2013; meses soltos faltam em 2019-20 e 2024-26</h1></div><span class="chip">{VERSAO}</span></header>
{"".join(svg)}
<div class="leg"><span><i class="sw" style="background:var(--s1)"></i>Anexo do Boletim (dezembros, série revisada)</span><span><i class="sw b" style="background:var(--s2)"></i>Edição mensal da Estatística (o seu Excel)</span><span><i class="sw d" style="background:var(--s3)"></i>Coletiva em PDF (% por produto × total)</span></div>
<table><tr><th>fonte</th><th>abertura por produto</th><th>regiões / UF</th><th>nº de contas</th><th>observação</th></tr>
<tr><td>Anexo do Boletim</td><td class="ok">completa: 25 instrumentos por segmento</td><td>por região (Págs. 7-10) e por UF na "Base Varejo"</td><td>por segmento e região (Págs. 11-15)</td><td>só dezembro; cada edição reapresenta 2013→ revisado; previdência do varejo só desde dez/23</td></tr>
<tr><td>Edição mensal (seu Excel)</td><td class="ok">completa: mesmo layout do seu arquivo de dez/16</td><td class="ok">SP capital/interior, RJ, MG, ES, Sul, CO, NE, N</td><td class="ok">por produto e região</td><td>varejo: {len(pts["varejo_tradicional"]["edicao"])} meses (sem nenhuma edição em {", ".join(map(str, falta["Varejo tradicional"])) or "—"}); private: {len(pts["private"]["edicao"])} meses, com pelo menos uma edição em todo ano; 2014-15 com classes agregadas</td></tr>
<tr><td>Coletiva em PDF</td><td>parcial: 7 produtos no varejo, 9 no private; "demais" fechado</td><td>não</td><td>só total</td><td>jun/16 a jun/20; legenda conferida contra as edições de mar/17 e jun/19</td></tr></table>
<div class="green">Para a análise por produto, a resposta é sim para todos os anos: há dezembro completo de 2013 a 2025 nos três segmentos. O que falta são os meses intermediários de 2019-20 (só as coletivas semestrais) e de 2024-26 (a ANBIMA deixou de guardar edições antigas no site novo; só o que o Wayback capturou). Regiões e número de contas existem apenas nas edições e nos anexos anuais.</div>
<div class="fonte">Fontes: ANBIMA, Estatísticas de Varejo e de Private (edições 2014-2026, recuperadas do Wayback, do portal antigo, do site atual e dos seus arquivos de dez/16), Anexo do Boletim de Private e Varejo (2018-2025) e coletivas de imprensa (2017-2024). Scripts: dados_anbima_alocacao_*.py.</div>
</div></body></html>'''
out = os.path.join(HERE, "anbima_cobertura.html"); open(out, "w", encoding="utf-8").write(html); print("ok", out, {s: {k: len(v) for k, v in p.items()} for s, p in pts.items()}, falta)
