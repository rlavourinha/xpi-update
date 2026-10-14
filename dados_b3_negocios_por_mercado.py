# -*- coding: utf-8 -*-
"""Negócios por dia e por mercado no segmento de ações da B3, a partir do COTAHIST anual (bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_A{ano}.ZIP).
Conta TOTNEG (pos 147-152) por TPMERC (pos 24-27): 010 vista, 020 fracionário, 030 termo, 070 call, 080 put, 012/013 exercícios, 017 leilão, 050 futuro c/ ret., 060 futuro s/ ret.
Saída: data/b3_negocios_por_mercado_diario.csv (data, vista, fracionario, termo, opcoes, outros, total). ZIPs ficam em fontes/setor/b3/cotahist_raw/ (fora do git)."""
import os, sys, io, zipfile, urllib.request, collections, csv, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, "fontes", "setor", "b3", "cotahist_raw"); OUT = os.path.join(HERE, "data", "b3_negocios_por_mercado_diario.csv")
URL = "https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_A{ano}.ZIP"
GRUPO = {b"010": "vista", b"020": "fracionario", b"030": "termo", b"070": "opcoes", b"080": "opcoes"}
def baixa(ano):
    p = os.path.join(RAW, f"COTAHIST_A{ano}.ZIP")
    if os.path.exists(p) and os.path.getsize(p) > 1e6 and ano < dt.date.today().year: return p
    req = urllib.request.Request(URL.format(ano=ano), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=600) as r: blob = r.read()
    open(p, "wb").write(blob); print(ano, "baixado", len(blob) // 1e6, "MB", flush=True); return p
def conta(p):
    acc = collections.defaultdict(lambda: collections.Counter())
    with zipfile.ZipFile(p) as zf:
        with zf.open(zf.namelist()[0]) as f:
            for raw in f:
                if raw[:2] != b"01": continue
                d = raw[2:10].decode(); g = GRUPO.get(raw[24:27], "outros")
                acc[d][g] += int(raw[147:152]); 
    return acc
def main():
    anos = range(2019, dt.date.today().year + 1); tot = {}
    for a in anos:
        try: p = baixa(a)
        except Exception as e: print(a, "ERRO", e, flush=True); continue
        acc = conta(p); tot.update(acc); print(a, "dias", len(acc), flush=True)
    cols = ["vista", "fracionario", "termo", "opcoes", "outros"]
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["data"] + cols + ["total"])
        for d in sorted(tot):
            dd = f"{d[:4]}-{d[4:6]}-{d[6:]}"; v = [tot[d].get(c, 0) for c in cols]; w.writerow([dd] + v + [sum(v)])
    print("ok", OUT, len(tot), "dias")
if __name__ == "__main__": main()
