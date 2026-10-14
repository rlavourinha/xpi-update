# -*- coding: utf-8 -*-
"""Completa o denominador de market share dos DATs na aba MOD (XPMod.xlsx aberto, COM), em NEGÓCIOS:
  162 Mercado | Negócios/dia em opções e termo (COTAHIST, 070/080/030)            <- relabel da antiga 'Completo' em unidades mistas
  163 Mercado | Negócios/dia em derivativos de índices e câmbio, estimado         <- = 161 x FATOR (BDI set/26 negócios ÷ kit RI ago/26 contratos ponderados); 4T26 = BDI observado
  164 Mercado | Completo em negócios = 160 + 162 + 163
Insere 163-164 (Revenue per Trade -> 165, Dias Úteis -> 166). Não salva."""
import time, re, os, pandas as pd, win32com.client
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
def ret(f):
    for _ in range(40):
        try: return f()
        except Exception as e:
            if any(k in str(e) for k in ("rejected", "-2147418111", "Workbooks", "-2146827284")): time.sleep(2)
            else: raise
    raise RuntimeError("Excel ocupado/em edição")
def col(c):
    s = ""
    while c: c, r = divmod(c - 1, 26); s = chr(65 + r) + s
    return s
n = pd.read_csv(os.path.join(DATA, "b3_negocios_por_mercado_diario.csv"), parse_dates=["data"]).set_index("data") / 1e6; ot = n.opcoes + n.termo
q, y = ot.resample("QE").mean(), ot.resample("YE").mean(); ny = ot.resample("YE").count(); ult = ot.index.max()
b = pd.read_csv(os.path.join(DATA, "b3_bdi_diario.csv"), parse_dates=["data"]).set_index("data"); b["ic"] = (b.win_negocios + b.wdo_negocios + b.ind_negocios + b.dol_negocios) / 1e6
k = pd.read_csv(os.path.join(DATA, "b3_ri_operacional_mensal.csv"), parse_dates=["mes"]).set_index("mes")
FATOR = round(b.loc["2026-09-10":"2026-09-30", "ic"].mean() / ((k.loc["2026-08-01", "adv_indices"] + k.loc["2026-08-01", "adv_cambio"]) / 1e6), 2)
bdi_q = b.ic.resample("QE").mean()
def main():
    xl = ret(lambda: win32com.client.GetActiveObject("Excel.Application")); wb = ret(lambda: [w for w in xl.Workbooks if "XPMod" in w.Name][0]); m = wb.Sheets("MOD")
    l162 = ret(lambda: str(m.Cells(162, 1).Value or ""))
    if "Completo" in l162 and "opções" not in l162:  # primeira execução: relabel + inserir 163-164
        ret(lambda: m.Rows(163).Insert()); ret(lambda: m.Rows(164).Insert())
        ret(lambda: setattr(m.Cells(162, 1), "Value", "Mercado | Negócios/dia em opções e termo (in million)"))
        ret(lambda: setattr(m.Cells(163, 1), "Value", "Mercado | Negócios/dia em derivativos de índices e câmbio, estimado (in million)"))
        ret(lambda: setattr(m.Cells(164, 1), "Value", "Mercado | Completo em negócios: ações + opções/termo + derivativos índices/câmbio (in million)"))
        ret(lambda: m.Range(m.Cells(162, 3), m.Cells(162, 300)).ClearContents())
    assert "opções" in str(m.Cells(162, 1).Value) and "estimado" in str(m.Cells(163, 1).Value) and "Completo em negócios" in str(m.Cells(164, 1).Value)
    n162 = n163 = n164 = 0
    for c in range(3, 200):
        h = ret(lambda: m.Cells(2, c).Value)
        if h is None: continue
        hs = str(h).strip(); mq = re.match(r"^(\d)Q(\d\d)$", hs); my = re.match(r"^(\d{4})(\.0)?$", hs)
        if mq: key = pd.Timestamp(year=2000 + int(mq.group(2)), month=3 * int(mq.group(1)), day=1) + pd.offsets.MonthEnd(0); v = q.get(key)
        elif my: key = pd.Timestamp(year=int(my.group(1)), month=12, day=31); v = y.get(key) if ny.get(key, 0) == 12 else None
        else: continue
        if v is not None and pd.notna(v): ret(lambda: setattr(m.Cells(162, c), "Value", round(float(v), 4))); n162 += 1
        if ret(lambda: m.Cells(161, c).Value) is not None: ret(lambda: setattr(m.Cells(163, c), "Formula", f"={col(c)}161*{FATOR}")); n163 += 1
        elif mq and key in bdi_q.index and pd.notna(bdi_q[key]): ret(lambda: setattr(m.Cells(163, c), "Value", round(float(bdi_q[key]), 4))); n163 += 1
        if all(ret(lambda: m.Cells(r, c).Value) is not None for r in (160, 162, 163)): ret(lambda: setattr(m.Cells(164, c), "Formula", f"={col(c)}160+{col(c)}162+{col(c)}163")); n164 += 1
    for r in (162, 163, 164): ret(lambda: setattr(m.Range(m.Cells(r, 3), m.Cells(r, 199)), "NumberFormat", "0.00"))
    ret(lambda: setattr(m.Cells(162, 2), "Value", f"B3 COTAHIST (TPMERC 070/080 opções sobre ações e índice + 030 termo), soma de TOTNEG, média diária do período; 4T26 até {ult:%d/%m}. Bate com o BDI (06/10/26: 506.318 opções, 490 termo). Script: dados_b3_negocios_por_mercado.py / escreve_mod_mercado_negocios.py"))
    ret(lambda: setattr(m.Cells(163, 2), "Value", f"Estimativa: linha 161 (contratos ponderados do kit RI, minis a 1/5) x {FATOR} = razão negócios/dia WIN+WDO+IND+DOL do BDI (set/26) ÷ contratos índices+câmbio do kit (ago/26). Único fator observado; 4T26 = BDI observado (negócios WIN+WDO+IND+DOL). Exclui DI1, commodities e cripto."))
    ret(lambda: setattr(m.Cells(164, 2), "Value", "Soma 160 + 162 + 163, tudo em negócios/dia. Denominador para market share dos DATs (linha 159, todos os mercados). Falta DI1/commodities/cripto, onde o varejo quase não opera."))
    print("162:", n162, "| 163:", n163, "| 164:", n164, "| FATOR", FATOR, "| salvo?", wb.Saved)
    for r in range(159, 167): print(r, ret(lambda: m.Cells(r, 1).Value), "| AU:", ret(lambda: m.Cells(r, 47).Formula), "| AW:", ret(lambda: m.Cells(r, 49).Formula))
if __name__ == "__main__": main()
