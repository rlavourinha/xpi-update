# -*- coding: utf-8 -*-
"""Slide: os fundos de tesouraria da XP (geridos pela XP Investimentos CCTVM) — PL diário, resultado diário e acumulado vs CDI.
Dados: data/xp_tesouraria_slide.json (de dados_xp_tesouraria_diario.py + agregação). Gera slides/xp_tesouraria.html."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); D = json.load(open(os.path.join(HERE, "..", "data", "xp_tesouraria_slide.json"), encoding="utf-8"))
VERSAO = "v1.0 · 08/10/2026"
def br(x, d=1): return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
dd = D["diario"]; K = D["kpi"]; AN = D["anual"]
datas = dd["datas"]; n = len(datas)
def xpos(i, ML, W, MR): return ML + i / (n - 1) * (W - ML - MR)
def ticks_anos(ML, W, MR, H, MB):
    out = []
    for y in range(2019, 2027):
        idx = next((i for i, d in enumerate(datas) if d.startswith(str(y))), None)
        if idx is not None: out.append(f'<text x="{xpos(idx,ML,W,MR):.1f}" y="{H-7}" class="ax" text-anchor="middle">{y}</text>')
    return "".join(out)

# ---- A: PL diário (área) ----
W, H, ML, MR, MT, MB = 760, 180, 40, 150, 14, 28
ymax = 60
def syA(v): return MT + (1 - v / ymax) * (H - MT - MB)
g = "".join(f'<line x1="{ML}" y1="{syA(t):.1f}" x2="{W-MR}" y2="{syA(t):.1f}" class="grid"/><text x="{ML-6}" y="{syA(t)+4:.1f}" class="ax" text-anchor="end">{t}</text>' for t in range(0, ymax + 1, 20))
pts = " ".join(f"{xpos(i,ML,W,MR):.1f},{syA(v):.1f}" for i, v in enumerate(dd["pl_bi"]))
area = f'<polygon points="{ML},{syA(0):.1f} {pts} {xpos(n-1,ML,W,MR):.1f},{syA(0):.1f}" fill="var(--s1)" opacity=".1"/><polyline points="{pts}" fill="none" stroke="var(--s1)" stroke-width="2" stroke-linejoin="round"/>'
end = dd["pl_bi"][-1]
area += f'<circle cx="{xpos(n-1,ML,W,MR):.1f}" cy="{syA(end):.1f}" r="4" fill="var(--s1)" stroke="var(--surface)" stroke-width="2"/><text x="{W-MR+10}" y="{syA(end)+4:.1f}" class="lab"><tspan class="num">R$ {br(end)} bi</tspan> em set/26</text>'
# marcos anuais
for y in ("2021", "2024"):
    idx = max(i for i, d in enumerate(datas) if d.startswith(y))
    v = dd["pl_bi"][idx]; area += f'<text x="{xpos(idx,ML,W,MR):.1f}" y="{syA(v)-8:.1f}" class="lab2" text-anchor="middle">{br(v,0)}</text>'
svgA = f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="PL diário dos fundos de tesouraria da XP, R$ bi">{g}{ticks_anos(ML,W,MR,H,MB)}{area}</svg>'

# ---- B: resultado diário (barras finas), desde 2024 ----
i0 = next(i for i, d in enumerate(datas) if d >= "2024-01-01"); sub = dd["pnl_mi"][i0:]; subd = datas[i0:]; nb = len(sub)
W2, H2, ML2, MR2, MT2, MB2 = 760, 172, 40, 150, 12, 28
vmax = 1000
def syB(v): return MT2 + (1 - (v + vmax) / (2 * vmax)) * (H2 - MT2 - MB2)
def xb(i): return ML2 + i / (nb - 1) * (W2 - ML2 - MR2)
gb = "".join(f'<line x1="{ML2}" y1="{syB(t):.1f}" x2="{W2-MR2}" y2="{syB(t):.1f}" class="grid"/><text x="{ML2-6}" y="{syB(t)+4:.1f}" class="ax" text-anchor="end">{br(t/1000,1).replace("-", "−") if t else "0"}</text>' for t in range(-vmax, vmax + 1, 500))
gb += f'<line x1="{ML2}" y1="{syB(0):.1f}" x2="{W2-MR2}" y2="{syB(0):.1f}" class="base"/>'
bw = max(0.8, (W2 - ML2 - MR2) / nb * 0.8)
bars = "".join(f'<rect x="{xb(i)-bw/2:.2f}" y="{min(syB(0),syB(max(-vmax,min(vmax,v)))):.1f}" width="{bw:.2f}" height="{abs(syB(max(-vmax,min(vmax,v)))-syB(0)):.1f}" fill="{"var(--pos)" if v>=0 else "var(--neg)"}"/>' for i, v in enumerate(sub))
for y in ("2024", "2025", "2026"):
    j = next(i for i, d in enumerate(subd) if d.startswith(y)); gb += f'<text x="{xb(j):.1f}" y="{H2-7}" class="ax" text-anchor="start">{y}</text>'
# melhor e pior dia
imx = max(range(nb), key=lambda i: sub[i]); imn = min(range(nb), key=lambda i: sub[i])
ann = (f'<text x="{min(xb(imx)+6, W2-MR2-10):.1f}" y="{syB(min(vmax,sub[imx]))-4:.1f}" class="lab2">+{br(sub[imx]/1000,1)} bi · {subd[imx][8:10]}/{subd[imx][5:7]}/{subd[imx][2:4]}</text>'
       f'<text x="{min(xb(imn)+6, W2-MR2-10):.1f}" y="{syB(max(-vmax,sub[imn]))+12:.1f}" class="lab2">{br(sub[imn]/1000,1).replace("-", "−")} bi · {subd[imn][8:10]}/{subd[imn][5:7]}/{subd[imn][2:4]}</text>')
svgB = f'<svg viewBox="0 0 {W2} {H2}" width="100%" role="img" aria-label="Resultado diário dos fundos, R$ bi">{gb}{bars}{ann}<text x="{W2-MR2+10}" y="{syB(0)-14:.1f}" class="lab2">vol. diária 2026</text><text x="{W2-MR2+10}" y="{syB(0)+4:.1f}" class="lab"><tspan class="num">R$ {br(K["vol_dia_2026_mi"],0)} mi</tspan></text><text x="{W2-MR2+10}" y="{syB(0)+20:.1f}" class="lab2">{K["dias_neg_2026_pct"]}% dos dias negativos</text></svg>'

# ---- C: resultado acumulado vs CDI sobre o mesmo capital ----
W3, H3, ML3, MR3, MT3, MB3 = 420, 176, 36, 120, 14, 28
cmax = 40
def syC(v): return MT3 + (1 - v / cmax) * (H3 - MT3 - MB3)
gc = "".join(f'<line x1="{ML3}" y1="{syC(t):.1f}" x2="{W3-MR3}" y2="{syC(t):.1f}" class="grid"/><text x="{ML3-6}" y="{syC(t)+4:.1f}" class="ax" text-anchor="end">{t}</text>' for t in range(0, cmax + 1, 20))
l1 = " ".join(f"{xpos(i,ML3,W3,MR3):.1f},{syC(v):.1f}" for i, v in enumerate(dd["cum_pnl_bi"])); l2 = " ".join(f"{xpos(i,ML3,W3,MR3):.1f},{syC(v):.1f}" for i, v in enumerate(dd["cum_cdi_bi"]))
e1, e2 = dd["cum_pnl_bi"][-1], dd["cum_cdi_bi"][-1]
lines = (f'<polyline points="{l1}" fill="none" stroke="var(--s1)" stroke-width="2"/><polyline points="{l2}" fill="none" stroke="var(--s2)" stroke-width="2"/>'
         f'<circle cx="{xpos(n-1,ML3,W3,MR3):.1f}" cy="{syC(e1):.1f}" r="4" fill="var(--s1)" stroke="var(--surface)" stroke-width="2"/><text x="{W3-MR3+8}" y="{syC(e1)+4:.1f}" class="lab">Resultado <tspan class="num">{br(e1,0)}</tspan></text>'
         f'<circle cx="{xpos(n-1,ML3,W3,MR3):.1f}" cy="{syC(e2):.1f}" r="4" fill="var(--s2)" stroke="var(--surface)" stroke-width="2"/><text x="{W3-MR3+8}" y="{syC(e2)+4:.1f}" class="lab">CDI <tspan class="num">{br(e2,0)}</tspan></text>')
for y in ("2019", "2021", "2023", "2025"):
    idx = next(i for i, d in enumerate(datas) if d.startswith(y)); gc += f'<text x="{xpos(idx,ML3,W3,MR3):.1f}" y="{H3-7}" class="ax" text-anchor="middle">{y}</text>'
svgC = f'<svg viewBox="0 0 {W3} {H3}" width="100%" role="img" aria-label="Resultado acumulado vs CDI sobre o mesmo capital, R$ bi">{gc}{lines}</svg>'

x25 = AN["2025"]["pnl_bi"] / AN["2025"]["cdi_bi"]; x12 = K["pnl_12m_bi"] / K["cdi_12m_bi"]
html = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Tesouraria da XP</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{{--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--ink3:#8a8984;--grid:#e8e7e3;--s1:#2a78d6;--s2:#eb6834;--pos:#2a78d6;--neg:#e34948;--green:#e6f4ea;--greenink:#14532d}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--s1:#3987e5;--s2:#d95926;--pos:#3987e5;--neg:#e66767;--green:#15301f;--greenink:#b7e4c7}}}}
:root[data-theme="dark"]{{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--s1:#3987e5;--s2:#d95926;--pos:#3987e5;--neg:#e66767;--green:#15301f;--greenink:#b7e4c7}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--surface);color:var(--ink);font:15px/1.35 Inter,system-ui,sans-serif}}
.slide{{max-width:1240px;margin:0 auto;padding:24px 32px 16px;min-height:720px;display:flex;flex-direction:column;gap:12px}}
header{{display:flex;justify-content:space-between;align-items:baseline;gap:16px}} header>div:first-child{{flex:1}} .kicker{{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink3)}}
h1{{font:600 26px/1.1 Fraunces,Georgia,serif;margin:4px 0 0}} .chip{{font-size:12px;color:var(--ink3);border:1px solid var(--grid);border-radius:999px;padding:3px 10px;white-space:nowrap}}
.grid2{{display:grid;grid-template-columns:1.8fr 1fr;gap:20px;align-items:stretch}} .col{{display:flex;flex-direction:column;gap:14px}}
.card{{border:1px solid var(--grid);border-radius:10px;padding:12px 14px}} .card h2{{font:600 14px/1.2 Inter,system-ui,sans-serif;margin:0 0 6px;color:var(--ink2)}}
.kpis{{display:grid;grid-template-columns:1fr 1fr;grid-auto-rows:1fr;gap:12px;flex:1}} .kpi{{border:1px solid var(--grid);border-radius:10px;padding:10px 12px}} .kpi b{{display:block;font:600 22px/1.1 Fraunces,Georgia,serif}} .kpi span{{font-size:12px;color:var(--ink2)}}
.legend{{display:flex;gap:14px;font-size:12px;color:var(--ink2);margin:4px 0 0}} .legend i{{display:inline-block;width:14px;height:3px;vertical-align:middle;margin-right:5px;border-radius:2px}}
.green{{background:var(--green);color:var(--greenink);border-radius:10px;padding:10px 14px;font-size:15px;font-weight:500}} .fonte{{font-size:11px;color:var(--ink3)}}
svg{{display:block}} svg .grid{{stroke:var(--grid);stroke-width:1}} svg .base{{stroke:var(--ink3);stroke-width:1}} svg .ax{{font:11px Inter,system-ui,sans-serif;fill:var(--ink3)}} svg .lab{{font:12.5px Inter,system-ui,sans-serif;fill:var(--ink)}} svg .lab2{{font:11.5px Inter,system-ui,sans-serif;fill:var(--ink2)}} svg .num{{font-weight:600}}
@media (max-width:860px){{.grid2{{grid-template-columns:1fr}}h1{{font-size:24px}}}}
</style></head><body><div class="slide">
<header><div><div class="kicker">parte 4 · qualidade do lucro</div><h1>Tesouraria: R$ {br(K["pl_set26_bi"],0)} bi, R$ {br(K["pnl_2025_bi"],1)} bi em 2025 e abaixo do CDI em 2026</h1></div><span class="chip">{VERSAO} · cotas até set/26</span></header>
<div class="grid2">
 <div class="col">
  <div class="card"><h2>Patrimônio consolidado dos fundos geridos pela XP Investimentos CCTVM (sem cotas de um fundo no outro), R$ bi, diário</h2>{svgA}</div>
  <div class="card"><h2>Resultado diário dos fundos (variação do PL líquida de captações e resgates), R$ bi</h2>{svgB}</div>
 </div>
 <div class="col">
  <div class="card"><h2>Resultado acumulado desde 2019 vs CDI sobre o mesmo capital, R$ bi</h2>{svgC}</div>
  <div class="kpis">
   <div class="kpi"><b>R$ {br(K["pnl_2025_bi"])} bi</b><span>resultado em 2025, {br(x25)}x o CDI sobre o capital</span></div>
   <div class="kpi"><b>R$ {br(K["pnl_12m_bi"])} bi</b><span>últimos 12 meses, {br(x12)}x o CDI (R$ {br(K["cdi_12m_bi"])} bi)</span></div>
   <div class="kpi"><b>R$ {br(K["pnl_3t26_bi"],2)} bi</b><span>no 3T26, {br(K["pnl_3t26_bi"]/K["cdi_3t26_bi"])}x o CDI (R$ {br(K["cdi_3t26_bi"],2)} bi); pior trimestre desde 2024</span></div>
   <div class="kpi"><b>{br(K["pl_set26_bi"]/K["securities_2q26_bi"]*100,0)}%</b><span>da carteira de títulos da XP (R$ {br(K["securities_2q26_bi"],0)} bi no 2T26)</span></div>
  </div>
 </div>
</div>
<div class="green">O excesso sobre o CDI encolheu: R$ {br(AN["2024"]["pnl_bi"]-AN["2024"]["cdi_bi"])} bi em 2024, R$ {br(AN["2025"]["pnl_bi"]-AN["2025"]["cdi_bi"])} bi em 2025 e {br(K["pnl_2026_bi"]-K["cdi_2026_bi"]).replace("-","−")} bi em 2026 até setembro. Com Selic a 15%, o capital da tesouraria (R$ {br(K["pl_set26_bi"],0)} bi) já não rende mais que o CDI; o resultado de 2025 (R$ {br(K["pnl_2025_bi"])} bi) foi maior que o EBT da XP (R$ {br(D["xp_ebt_bi"]["2025"])} bi).</div>
<div class="fonte">Fonte: CVM, informes diários de fundos (cota, PL, captação e resgate) dos fundos cujo gestor é a XP Investimentos CCTVM: Nimrod, Gladius, Scorpio, Aspis, Falx, Coliseu, Macadâmia, Kopis, Harpe, Javelin, Labris, XP Nix, Odysseus (todos com um cotista; 20-F os lista como entidades consolidadas e "proprietary treasury funds"). Consolidação: Gladius, Scorpio e Makhaira são 100% detidos por outro fundo do grupo (Coliseu até dez/25, Nimrod desde jan/26: R$ 24 bi em cotas no CDA de jun/26); PL e resultado deles são excluídos para não contar duas vezes (soma bruta dos 13: R$ {br(K["pl_bruto_set26_bi"],0)} bi e R$ {br(K["pnl_bruto_2025_bi"])} bi em 2025). Resultado diário = ΔPL − captação + resgate; dias de reorganização (cota e PL divergem) zerados. CDI sobre o capital = PL do dia anterior × CDI diário (BCB SGS 12). Resultado acumulado 2019–set/26: R$ {br(e1,1)} bi contra R$ {br(e2,1)} bi de CDI. Melhor dia: +R$ {br(K["melhor_dia_mi"]/1000,2)} bi ({K["melhor_dia"]}); pior: −R$ {br(abs(K["pior_dia_mi"])/1000,2)} bi ({K["pior_dia"]}).</div>
</div></body></html>'''
out = os.path.join(HERE, "xp_tesouraria.html"); open(out, "w", encoding="utf-8").write(html); print("ok", out)
