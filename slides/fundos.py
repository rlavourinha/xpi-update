# -*- coding: utf-8 -*-
"""Slide: a indústria de fundos no Brasil (CVM, informes diários agregados em dados_cvm_fundos.py + agrega_cvm_fundos.py).
Gera slides/industria_fundos.html — HTML autocontido, SVG inline, sem JS externo."""
import json, os, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "..", "data")
VERSAO = "v1.0 · 08/10/2026"

cl = pd.read_csv(f"{DATA}/cvm_fundos_mensal_classe_exfic.csv")
tot = pd.read_csv(f"{DATA}/cvm_fundos_mensal_total.csv", index_col=0)
fic = pd.read_csv(f"{DATA}/cvm_fundos_mensal_fic.csv")
ges = pd.read_csv(f"{DATA}/cvm_fundos_mensal_gestor.csv"); adm = pd.read_csv(f"{DATA}/cvm_fundos_mensal_admin.csv")
import datetime as _dt
_hoje = _dt.date.today().strftime("%Y-%m")
ult = max(m for m in cl.mes.unique() if m < _hoje)  # último mês completo
cl = cl[cl.mes <= ult]; fic = fic[fic.mes <= ult]; ges = ges[ges.mes <= ult]; adm = adm[adm.mes <= ult]
exfic = fic[~fic.fic.astype(bool)].set_index("mes")

# ---- séries por classe (R$ tri), mensal ----
SER = ["Renda Fixa", "Multimercado", "Ações"]
piv = cl[cl.classe_n.isin(SER)].pivot(index="mes", columns="classe_n", values="pl").fillna(0) / 1e12
piv = piv.sort_index()
meses = list(piv.index)
# ---- captação líquida anual ex-FIC (R$ bi) ----
exf = fic[~fic.fic.astype(bool)].copy(); exf["ano"] = exf.mes.str[:4]
cap = (exf.groupby("ano")[["captacao", "resgate"]].sum().pipe(lambda d: (d.captacao - d.resgate) / 1e9)).loc["2006":]
# ---- KPIs ----
pl_ex = exfic.loc[ult, "pl"] / 1e12; cot = tot.loc[ult, "cotistas"] / 1e6; nf = tot.loc[ult, "n_fundos"]
pl_tot = tot.loc[ult, "pl"] / 1e12
xpf = pd.read_csv(f"{DATA}/cvm_fundos_mensal_xp.csv", index_col=0)
xg = xpf.loc[ult, "gestor_pl"] / 1e9
xa = xpf.loc[ult, "admin_pl"] / 1e9
sh_rf = piv.loc[ult, "Renda Fixa"] / pl_ex * 100
mes_fmt = lambda m: {"01":"jan","02":"fev","03":"mar","04":"abr","05":"mai","06":"jun","07":"jul","08":"ago","09":"set","10":"out","11":"nov","12":"dez"}[m[5:7]] + "/" + m[2:4]
def br(x, d=1): return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ---- SVG helpers ----
W, H = 760, 420; ML, MR, MT, MB = 44, 122, 18, 34  # MR comporta "Multimercado 1,8" em Inter (102px) sem cortar no viewBox
def sx(i): return ML + i / (len(meses) - 1) * (W - ML - MR)
ymax = max(1.0, float(piv.max().max())); ymax = (int(ymax / 2) + 1) * 2
def sy(v): return MT + (1 - v / ymax) * (H - MT - MB)
COL = {"Renda Fixa": "var(--s1)", "Multimercado": "var(--s2)", "Ações": "var(--s3)"}
g = []
for t in range(0, ymax + 1, 2):
    g.append(f'<line x1="{ML}" y1="{sy(t):.1f}" x2="{W-MR}" y2="{sy(t):.1f}" class="grid"/><text x="{ML-6}" y="{sy(t)+4:.1f}" class="ax" text-anchor="end">{t}</text>')
for y in range(2006, 2027, 2):
    idx = next((i for i, m in enumerate(meses) if m.startswith(str(y))), None)
    if idx is not None: g.append(f'<text x="{sx(idx):.1f}" y="{H-12}" class="ax" text-anchor="middle">{y}</text>')
paths = []
for s in SER:
    pts = " ".join(f"{sx(i):.1f},{sy(v):.1f}" for i, v in enumerate(piv[s]))
    end = piv[s].iloc[-1]
    paths.append(f'<polyline points="{pts}" fill="none" stroke="{COL[s]}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>'
                 f'<circle cx="{sx(len(meses)-1):.1f}" cy="{sy(end):.1f}" r="4" fill="{COL[s]}" stroke="var(--surface)" stroke-width="2"/>'
                 f'<text x="{W-MR+10}" y="{sy(end)+4:.1f}" class="lab">{s} <tspan class="num">{br(end)}</tspan></text>')
# tooltip data
tip = json.dumps({"meses": meses, "s": {s: [round(float(v), 2) for v in piv[s]] for s in SER}}, ensure_ascii=False)
svgA = f'''<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="PL por classe, R$ tri, mensal desde 2005" id="chA">
<g>{"".join(g)}</g>{"".join(paths)}
<g id="hover" style="display:none"><line id="hv" y1="{MT}" y2="{H-MB}" class="cross"/><rect id="hb" class="tipbox" rx="4"/><text id="ht" class="tip"></text></g>
<rect x="{ML}" y="{MT}" width="{W-ML-MR}" height="{H-MT-MB}" fill="transparent" id="hit"/></svg>'''

# captação anual (barras, diverging azul/vermelho)
W2, H2 = 420, 330; ML2, MR2, MT2, MB2 = 40, 12, 14, 30  # H2 calibrado p/ o painel direito (gráfico + caixa verde) fechar na mesma base do esquerdo
anos = list(cap.index); vmax = max(abs(cap.min()), abs(cap.max())); vmax = (int(vmax / 100) + 1) * 100
def sy2(v): return MT2 + (1 - (v + vmax) / (2 * vmax)) * (H2 - MT2 - MB2)
bw = (W2 - ML2 - MR2) / len(anos); bars = []
for t in range(-vmax, vmax + 1, 200):
    bars.append(f'<line x1="{ML2}" y1="{sy2(t):.1f}" x2="{W2-MR2}" y2="{sy2(t):.1f}" class="grid"/><text x="{ML2-5}" y="{sy2(t)+4:.1f}" class="ax" text-anchor="end">{t}</text>')
bars.append(f'<line x1="{ML2}" y1="{sy2(0):.1f}" x2="{W2-MR2}" y2="{sy2(0):.1f}" class="base"/>')
for i, (a, v) in enumerate(cap.items()):
    x = ML2 + i * bw + bw * 0.2; w = bw * 0.6; y0 = sy2(0); y1 = sy2(v)
    top, hgt = (min(y0, y1), abs(y1 - y0))
    colr = "var(--pos)" if v >= 0 else "var(--neg)"
    bars.append(f'<rect x="{x:.1f}" y="{top:.1f}" width="{w:.1f}" height="{max(hgt,1):.1f}" fill="{colr}" rx="2"><title>{a}: R$ {br(v,0)} bi</title></rect>')
    if int(a) % 4 == 2 or a == anos[-1]: bars.append(f'<text x="{x+w/2:.1f}" y="{H2-10}" class="ax" text-anchor="middle">{a if a!=anos[-1] else a+"*"}</text>')
vmx = cap.idxmax(); vmn = cap.idxmin()
for a in (vmx, vmn):
    i = anos.index(a); v = cap[a]; x = ML2 + i * bw + bw * 0.5; y = sy2(v) + (-6 if v >= 0 else 14)
    bars.append(f'<text x="{x:.1f}" y="{y:.1f}" class="lab" text-anchor="middle">{br(v,0)}</text>')
svgB = f'<svg viewBox="0 0 {W2} {H2}" width="100%" role="img" aria-label="Captação líquida anual, R$ bi">{"".join(bars)}</svg>'

html = f'''<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Indústria de fundos</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{{--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--ink3:#8a8984;--grid:#e8e7e3;--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--pos:#2a78d6;--neg:#e34948;--green:#e6f4ea;--greenink:#14532d}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--s1:#3987e5;--s2:#d95926;--s3:#199e70;--pos:#3987e5;--neg:#e66767;--green:#15301f;--greenink:#b7e4c7}}}}
:root[data-theme="dark"]{{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--s1:#3987e5;--s2:#d95926;--s3:#199e70;--pos:#3987e5;--neg:#e66767;--green:#15301f;--greenink:#b7e4c7}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--surface);color:var(--ink);font:15px/1.35 Inter,system-ui,sans-serif}}
.slide{{max-width:1240px;margin:0 auto;padding:28px 32px 20px;min-height:720px;display:flex;flex-direction:column;gap:14px}}
header{{display:flex;justify-content:space-between;align-items:baseline;gap:16px}}
.kicker{{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink3)}}
h1{{font:600 34px/1.1 Fraunces,Georgia,serif;margin:4px 0 0}}
.chip{{font-size:12px;color:var(--ink3);border:1px solid var(--grid);border-radius:999px;padding:3px 10px;white-space:nowrap}}
.grid2{{display:grid;grid-template-columns:1.8fr 1fr;gap:20px;align-items:stretch}}
.col{{display:flex;flex-direction:column;gap:14px}} .col .card{{flex:1}}
.card{{border:1px solid var(--grid);border-radius:10px;padding:12px 14px}} .card svg{{display:block}}
.card h2{{font:600 14px/1.2 Inter,system-ui,sans-serif;margin:0 0 6px;color:var(--ink2)}}
.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}
.kpi{{border:1px solid var(--grid);border-radius:10px;padding:10px 12px}} .kpi b{{display:block;font:600 26px/1.1 Fraunces,Georgia,serif}} .kpi span{{font-size:12px;color:var(--ink2)}}
.green{{background:var(--green);color:var(--greenink);border-radius:10px;padding:10px 14px;font-size:15px;font-weight:500}}
.fonte{{font-size:11px;color:var(--ink3)}}
svg .grid{{stroke:var(--grid);stroke-width:1}} svg .base{{stroke:var(--ink3);stroke-width:1}} svg .ax{{font:11px Inter,system-ui,sans-serif;fill:var(--ink3)}}
svg .lab{{font:12.5px Inter,system-ui,sans-serif;fill:var(--ink)}} svg .num{{font-weight:600}} svg .cross{{stroke:var(--ink3);stroke-width:1}}
svg .tipbox{{fill:var(--surface);stroke:var(--grid)}} svg .tip{{font:12px Inter,system-ui,sans-serif;fill:var(--ink)}}
@media (max-width:860px){{.grid2{{grid-template-columns:1fr}}.kpis{{grid-template-columns:repeat(2,1fr)}}h1{{font-size:26px}}}}
</style></head><body><div class="slide">
<header><div><div class="kicker">parte 2 · a indústria</div><h1>Fundos: R$ {br(pl_ex)} tri, e {br(sh_rf,0)}% disso é renda fixa</h1></div><span class="chip">{VERSAO} · dados até {mes_fmt(ult)}</span></header>
<div class="grid2">
 <div class="card"><h2>Patrimônio líquido por classe, R$ tri (sem fundos de cotas)</h2>{svgA}</div>
 <div class="col">
  <div class="card"><h2>Captação líquida por ano, R$ bi (sem fundos de cotas; *{ult[:4]} até {mes_fmt(ult)})</h2>{svgB}</div>
  <div class="green">Multimercados e ações pararam de crescer em 2021; desde então todo o PL novo da indústria é renda fixa.</div>
 </div>
</div>
<div class="kpis">
 <div class="kpi"><b>{br(cot,1)} mi</b><span>cotistas (contas) em {mes_fmt(ult)}</span></div>
 <div class="kpi"><b>{br(nf,0).replace(',0','')}</b><span>fundos ativos com informe</span></div>
 <div class="kpi"><b>R$ {br(xg,0)} bi</b><span>gestoras XP: {br(xg/1e3/pl_ex*100,1)}% do PL ex-cotas</span></div>
 <div class="kpi"><b>R$ {br(xa,0)} bi</b><span>XP como administradora: {br(xa/1e3/pl_ex*100,1)}% do PL</span></div>
</div>
<div class="fonte">Fonte: CVM, informes diários de fundos (INF_DIARIO) 2005–{ult[:4]} e cadastros (cad_fi, registro_fundo_classe), agregados por mês; PL de fim de mês, captação e resgate somados no mês. Cobre os fundos 555/FIF (renda fixa, multimercado, ações, cambial); FIDC, FIP e FII não entregam informe diário. Fundos de cotas excluídos para evitar dupla contagem (PL bruto com cotas: R$ {br(pl_tot)} tri). Classe = classificação CVM (Curto Prazo e Referenciado em Renda Fixa). Gestoras XP = XP Vista, XP Advisory, XP Allocation, XP Gestão, XP Vida e Previdência, XP CCTVM.</div>
</div>
<script>
(function(){{var D={tip};var svg=document.getElementById('chA'),hit=document.getElementById('hit'),hv=document.getElementById('hover'),ln=document.getElementById('hv'),bx=document.getElementById('hb'),tx=document.getElementById('ht');
var ML={ML},W={W},MR={MR},n=D.meses.length;function fmt(v){{return v.toFixed(2).replace('.',',')}}
hit.addEventListener('mousemove',function(e){{var pt=svg.createSVGPoint();pt.x=e.clientX;pt.y=e.clientY;var p=pt.matrixTransform(svg.getScreenCTM().inverse());var i=Math.round((p.x-ML)/(W-ML-MR)*(n-1));i=Math.max(0,Math.min(n-1,i));var x=ML+i/(n-1)*(W-ML-MR);
ln.setAttribute('x1',x);ln.setAttribute('x2',x);var lines=[D.meses[i]].concat(Object.keys(D.s).map(function(k){{return k+': '+fmt(D.s[k][i])}}));
while(tx.firstChild)tx.removeChild(tx.firstChild);lines.forEach(function(l,j){{var t=document.createElementNS('http://www.w3.org/2000/svg','tspan');t.setAttribute('x',x+(x>W-220?-150:12));t.setAttribute('dy',j?15:0);t.textContent=l;tx.appendChild(t)}});
tx.setAttribute('y',40);var b=tx.getBBox();bx.setAttribute('x',b.x-6);bx.setAttribute('y',b.y-4);bx.setAttribute('width',b.width+12);bx.setAttribute('height',b.height+8);hv.style.display=''}});
hit.addEventListener('mouseleave',function(){{hv.style.display='none'}})}})();
</script></body></html>'''
out = os.path.join(HERE, "industria_fundos.html"); open(out, "w", encoding="utf-8").write(html)
print("ok", out, "| PL ex-FIC", round(pl_ex, 2), "tri | RF", round(sh_rf, 1), "% | XP gestor", round(xg), "bi | XP admin", round(xa), "bi | cotistas", round(cot, 1), "mi")
