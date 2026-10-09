# -*- coding: utf-8 -*-
"""Monta o deck "XPI Update" (index.html): capa + slides em slides/*.html, cada um num <iframe> (autocontido, sem CSS cruzado).
Navegação: scroll-snap, setas/PageDown, pontos à direita, deep-link por hash (#s2). Sem JS externo."""
import os, re, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__))
VERSAO = "v1.4"; DATA = dt.date.today().strftime("%d/%m/%Y")
SLIDES = [  # (arquivo, título curto para os pontos)
    ("slides/industria_fundos.html", "Indústria de fundos"),
    ("slides/fundos_concentracao.html", "Concentração"),
    ("slides/alocacao_clientes.html", "Alocação dos clientes"),
    ("slides/primeiro_turno.html", "1º turno na B3"),
    ("slides/auc_vs_fundos.html", "AuC vs fundos"),
    ("slides/auc_vs_indice_pf.html", "AuC vs índice PF"),
    ("slides/xp_tesouraria.html", "Tesouraria da XP"),
    ("slides/xp_tesouraria_carteira.html", "Livros da tesouraria"),
]
for f, _ in SLIDES: assert os.path.exists(os.path.join(HERE, f)), f
def titulo(f):
    t = open(os.path.join(HERE, f), encoding="utf-8").read()
    m = re.search(r"<h1>(.*?)</h1>", t, re.S); return re.sub(r"<[^>]+>", "", m.group(1)) if m else ""
agenda = "".join(f'<li><span class="n">{i+2}</span>{titulo(f)}</li>' for i, (f, _) in enumerate(SLIDES))
dots = '<a href="#s1" title="Capa"></a>' + "".join(f'<a href="#s{i+2}" title="{t}"></a>' for i, (_, t) in enumerate(SLIDES))
frames = "".join(f'<section class="sl" id="s{i+2}"><iframe src="{f}" title="{t}" loading="lazy"></iframe></section>' for i, (f, t) in enumerate(SLIDES))
html = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>XPI Update</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{{--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--ink3:#8a8984;--grid:#e8e7e3;--s1:#2a78d6}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--s1:#3987e5}}}}
:root[data-theme="dark"]{{--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--ink3:#8a8984;--grid:#2e2e2b;--s1:#3987e5}}
*{{box-sizing:border-box}} html,body{{margin:0;height:100%;background:var(--surface);color:var(--ink);font:15px/1.4 Inter,system-ui,sans-serif}}
.deck{{height:100vh;overflow-y:auto;scroll-snap-type:y mandatory;scroll-behavior:smooth}}
.sl{{height:100vh;scroll-snap-align:start;position:relative}}
.sl iframe{{width:100%;height:100%;border:0;display:block;background:var(--surface)}}
.capa{{display:flex;flex-direction:column;justify-content:center;max-width:1240px;margin:0 auto;padding:40px 32px;height:100%}}
.kicker{{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink3)}}
h1{{font:600 64px/1.05 Fraunces,Georgia,serif;margin:12px 0 8px}} .sub{{font-size:20px;color:var(--ink2);max-width:760px}}
.chip{{display:inline-block;font-size:12px;color:var(--ink3);border:1px solid var(--grid);border-radius:999px;padding:3px 10px;margin-top:18px}}
ol{{list-style:none;padding:0;margin:36px 0 0;display:grid;grid-template-columns:repeat(3,1fr);gap:14px;max-width:1000px}}
ol li{{border:1px solid var(--grid);border-radius:10px;padding:12px 14px;font-size:14px;color:var(--ink2)}} ol .n{{display:block;font:600 22px/1 Fraunces,Georgia,serif;color:var(--ink);margin-bottom:6px}}
.dots{{position:fixed;right:14px;top:50%;transform:translateY(-50%);display:flex;flex-direction:column;gap:8px;z-index:5}}
.dots a{{width:9px;height:9px;border-radius:50%;background:var(--grid);display:block}} .dots a.on{{background:var(--s1)}}
.hint{{position:fixed;left:16px;bottom:12px;font-size:11px;color:var(--ink3)}}
@media (max-width:860px){{h1{{font-size:38px}} ol{{grid-template-columns:1fr}}}}
</style></head><body>
<nav class="dots" id="dots">{dots}</nav>
<div class="deck" id="deck">
<section class="sl" id="s1"><div class="capa"><div class="kicker">update · XP Inc. (XPBR31) · referência 2T26</div><h1>XPI Update</h1>
<div class="sub">A indústria de fundos pela CVM, para onde a pessoa física levou o dinheiro, e os fundos onde mora a tesouraria da XP: quanto rende, o que carrega e para quem é contraparte.</div>
<span class="chip">{VERSAO} · {DATA} · fontes primárias: CVM, SEC, RI</span><ol>{agenda}</ol></div></section>
{frames}
</div>
<div class="hint">setas ou PageDown para avançar</div>
<script>
(function(){{var deck=document.getElementById('deck'),sl=[].slice.call(document.querySelectorAll('.sl')),dots=[].slice.call(document.querySelectorAll('#dots a'));
function cur(){{var h=deck.clientHeight;return Math.round(deck.scrollTop/h)}}
function mark(){{var i=cur();dots.forEach(function(d,j){{d.className=j===i?'on':''}});if(sl[i]&&location.hash!=='#'+sl[i].id)history.replaceState(null,'','#'+sl[i].id)}}
deck.addEventListener('scroll',function(){{clearTimeout(deck._t);deck._t=setTimeout(mark,80)}});
function go(i){{i=Math.max(0,Math.min(sl.length-1,i));sl[i].scrollIntoView({{behavior:'smooth'}})}}
document.addEventListener('keydown',function(e){{if(['ArrowDown','PageDown',' ','ArrowRight'].indexOf(e.key)>=0){{e.preventDefault();go(cur()+1)}}else if(['ArrowUp','PageUp','ArrowLeft'].indexOf(e.key)>=0){{e.preventDefault();go(cur()-1)}}}});
dots.forEach(function(d,j){{d.addEventListener('click',function(e){{e.preventDefault();go(j)}})}});
if(location.hash){{var t=document.querySelector(location.hash);if(t)setTimeout(function(){{t.scrollIntoView()}},50)}}mark();
window.addEventListener('message',function(e){{if(e.data&&e.data.key)document.dispatchEvent(new KeyboardEvent('keydown',{{key:e.data.key}}))}});
}})();
</script></body></html>'''
open(os.path.join(HERE, "index.html"), "w", encoding="utf-8").write(html)
# repassa setas de dentro dos iframes para o deck
for f, _ in SLIDES:
    p = os.path.join(HERE, f); t = open(p, encoding="utf-8").read()
    if "parent.postMessage" not in t:
        t = t.replace("</body>", "<script>document.addEventListener('keydown',function(e){if(['ArrowDown','PageDown',' ','ArrowRight','ArrowUp','PageUp','ArrowLeft'].indexOf(e.key)>=0&&window.parent!==window){e.preventDefault();parent.postMessage({key:e.key},'*')}});</script></body>")
        open(p, "w", encoding="utf-8").write(t)
print("ok index.html com", len(SLIDES), "slides")
