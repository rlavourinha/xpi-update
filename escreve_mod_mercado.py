# -*- coding: utf-8 -*-
"""Preenche na aba MOD do XPMod.xlsx (Excel aberto, COM) as linhas 161 (Mercado | Contratos/dia em índices e câmbio, mi) e
162 (Mercado | Completo = 160 + 161) a partir de data/b3_ri_operacional_mensal.csv (adv_indices já inclui minis; adv_minis zerada).
Guardado por checagem dos rótulos da coluna A. Não salva a planilha."""
import time, re, os, pandas as pd, win32com.client
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
R_ACOES, R_DER, R_COMP = 160, 161, 162
def ret(f):
    for _ in range(40):
        try: return f()
        except Exception as e:
            s = str(e)
            if any(k in s for k in ("rejected", "-2147418111", "Workbooks", "-2146827284")): time.sleep(2)
            else: raise
    raise RuntimeError("Excel ocupado/em edição")
def col(c):
    s = ""
    while c: c, r = divmod(c - 1, 26); s = chr(65 + r) + s
    return s
B = pd.read_csv(os.path.join(DATA, "b3_ri_operacional_mensal.csv"), parse_dates=["mes"]).set_index("mes")
der = ((B.adv_indices + B.adv_cambio) / 1e6).dropna(); der = der[der.index >= "2019-01-01"]
q = der.resample("QE").mean(); y = der.resample("YE").mean(); nq = der.resample("QE").count(); ny = der.resample("YE").count()
ult = der.index.max()
def main():
    xl = ret(lambda: win32com.client.GetActiveObject("Excel.Application")); wb = ret(lambda: [w for w in xl.Workbooks if "XPMod" in w.Name][0]); m = wb.Sheets("MOD")
    la, ld, lc = (ret(lambda: str(m.Cells(r, 1).Value or "")) for r in (R_ACOES, R_DER, R_COMP))
    assert "Negócios/dia" in la and "Contratos/dia" in ld and "Completo" in lc, (la, ld, lc)
    nw = nf = 0
    for c in range(2, 200):
        h = ret(lambda: m.Cells(2, c).Value)
        if h is None: continue
        hs = str(h).strip(); mq = re.match(r"^(\d)Q(\d\d)$", hs); my = re.match(r"^(\d{4})(\.0)?$", hs)
        if mq:
            qn, yy = int(mq.group(1)), 2000 + int(mq.group(2)); key = pd.Timestamp(year=yy, month=3 * qn, day=1) + pd.offsets.MonthEnd(0)
            v = q.get(key); n = nq.get(key, 0)
            if v is not None and pd.notna(v) and n >= 3: ret(lambda: setattr(m.Cells(R_DER, c), "Value", round(float(v), 4))); nw += 1
        elif my:
            key = pd.Timestamp(year=int(my.group(1)), month=12, day=31); v = y.get(key); n = ny.get(key, 0)
            if v is not None and pd.notna(v) and n == 12: ret(lambda: setattr(m.Cells(R_DER, c), "Value", round(float(v), 4))); nw += 1
        else: continue
        if ret(lambda: m.Cells(R_ACOES, c).Value) is not None and ret(lambda: m.Cells(R_DER, c).Value) is not None:
            ret(lambda: setattr(m.Cells(R_COMP, c), "Formula", f"={col(c)}{R_ACOES}+{col(c)}{R_DER}")); nf += 1
    for r in (R_DER, R_COMP): ret(lambda: setattr(m.Range(m.Cells(r, 2), m.Cells(r, 199)), "NumberFormat", "0.00"))
    ret(lambda: setattr(m.Cells(R_DER, 2), "Value", f"B3 (kit de RI, planilha operacional mensal): ADV de contratos de futuros de índice (cheio+mini) e de câmbio (cheio+mini), média dos meses do período; 3T26 = média de jul+ago/26 (set ainda não publicado). Atenção: são contratos, não negócios. Script: escreve_mod_mercado.py"))
    ret(lambda: setattr(m.Cells(R_COMP, 2), "Value", "Soma: linha 160 (negócios/dia em ações, COTAHIST) + linha 161 (contratos/dia em índices e câmbio). Denominador 'completo' para market share dos DATs (linha 159), que contam todos os mercados."))
    print("linha 161 escrita em", nw, "colunas; fórmulas na 162 em", nf, "| último mês", ult.date(), "| salvo?", wb.Saved)
    for r in (159, 160, 161, 162, 163, 164): print(r, ret(lambda: m.Cells(r, 1).Value), "| AU:", ret(lambda: m.Cells(r, 47).Formula), "| AV:", ret(lambda: m.Cells(r, 48).Formula))
if __name__ == "__main__": main()
