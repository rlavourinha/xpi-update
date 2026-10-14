# -*- coding: utf-8 -*-
"""Baixa os relatórios públicos de RLP (Retail Liquidity Provider) da página da B3 (PUMA > regras e parâmetros > oferta RLP):
acompanhamento diário do CAP por corretora (minis WIN/WDO desde ago/19; ações desde a extensão), histórico do CAP e métricas de risco de day trade.
Página sem cláusula de vedação a coleta automatizada (conferido em 11/10/26). Pausa de 1,5 s entre downloads. Arquivos em fontes/setor/b3/rlp/raw/ (fora do git).
Saída do inventário: fontes/setor/b3/rlp/_inventario.csv (período, rótulo, url, arquivo)."""
import os, re, html, time, csv, urllib.request, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); DIR = os.path.join(HERE, "fontes", "setor", "b3", "rlp"); RAW = os.path.join(DIR, "raw"); os.makedirs(RAW, exist_ok=True)
PAG = "https://www.b3.com.br/pt_br/solucoes/plataformas/puma-trading-system/para-participantes-e-traders/regras-e-parametros-de-negociacao/oferta-retail-liquidity-provider-rlp/"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128 Safari/537.36"}
def get(u): 
    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=120) as r: return r.read()
def main():
    s = open(os.path.join(DIR, "b3_rlp_pagina.html"), encoding="utf-8").read()
    toks = re.finditer(r'(?:(?:Per[íi]odo|M[êe]s)\s*:\s*([^<]{3,40}))|<a[^>]+href="([^"]+\.(?:csv|xlsx|pdf|xls|zip))"[^>]*>(.*?)</a>', s, re.S | re.I)
    per = None; inv = []; vistos = set()
    for m in toks:
        if m.group(1): per = html.unescape(m.group(1)).strip(); continue
        href = html.unescape(m.group(2)); lab = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", m.group(3)))).strip()
        url = urllib.parse.urljoin(PAG, href)
        if url in vistos: continue
        vistos.add(url); pl = re.sub(r"^M[êe]s\s*:\s*", "", lab) if re.match(r"^M[êe]s\s*:", lab) else (per or "sem"); nome = re.sub(r"[^\w.\-]+", "_", f"{pl}__{os.path.basename(urllib.parse.unquote(href))}")
        inv.append(dict(periodo=per, rotulo=lab, url=url, arquivo=nome))
    with open(os.path.join(DIR, "_inventario.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["periodo", "rotulo", "url", "arquivo"]); w.writeheader(); w.writerows(inv)
    print("links:", len(inv), flush=True); ok = 0
    for d in inv:
        p = os.path.join(RAW, d["arquivo"])
        if os.path.exists(p) and os.path.getsize(p) > 500: ok += 1; continue
        try: open(p, "wb").write(get(d["url"])); ok += 1
        except Exception as e: print("ERRO", d["arquivo"], e, flush=True)
        time.sleep(1.5)
    print("baixados:", ok, "/", len(inv))
if __name__ == "__main__": main()
