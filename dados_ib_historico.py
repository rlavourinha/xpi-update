# -*- coding: utf-8 -*-
"""Histórico de mercado de capitais (ECM/DCM) e M&A no Brasil + receita de Mercado de Capitais (Issuer Services) da XP.
Fontes: ANBIMA Boletim de Mercado de Capitais — dez/2017 (anos 2011-2015), dez/2022 (2016-2019) e anexo consolidado atual
(mensal jan/20-ago/26, sempre a versão mais recente de cada ano); KPMG Pesquisa de Fusões e Aquisições (nº de transações
2005-2025); XP: releases 4T19-2T26 (Issuer Services 2018-2020, segmentação antiga) e planilha histórica do RI (1T21+).
Saídas: data/mercado_capitais_anual.csv, data/mercado_capitais_tri.csv, data/ma_kpmg_anual.csv, data/xp_mercado_capitais_tri.csv"""
import os, re, json, openpyxl, pandas as pd, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data"); MK = os.path.join(HERE, "fontes", "setor", "anbima")
MAP = {"debentures": r"^deb", "nc": r"^notas comerciais", "np": r"^notas promiss", "lf": r"^letras financeiras", "cr": r"^cr$", "cra": r"^cra", "cri": r"^cri",
       "fidc": r"^fidc", "cprf": r"^cpr", "cdca": r"^cdca", "ipo": r"ipo", "follow_on": r"follow", "fiagro": r"^fiagro", "fii": r"^fii"}
def nrm(s): return re.sub(r"\s+", " ", str(s)).strip().lower()
def pag2(path, sheet):
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True)[sheet]; G = [list(r) for r in ws.iter_rows(max_row=60, max_col=40, values_only=True)]
    hi = next(i for i, r in enumerate(G) if any(isinstance(v, str) and nrm(v).startswith("deb") for v in r))
    cols = {}
    for j, v in enumerate(G[hi]):
        if v is None: continue
        for k, p in MAP.items():
            if re.search(p, nrm(v)) and k not in cols: cols[k] = j; break
    rows = []
    for r in G[hi + 1:]:
        if isinstance(r[0], (int, float)) and 2000 < r[0] < 2100:
            rows.append({"ano": int(r[0]), **{k: (float(r[j]) / 1e3 if isinstance(r[j], (int, float)) else 0.0) for k, j in cols.items()}})  # R$ mi -> bi
    return pd.DataFrame(rows).set_index("ano")
def consolidado():
    ws = openpyxl.load_workbook(os.path.join(MK, "Boletim_MK_Anexo_consolidado.xlsx"), read_only=True, data_only=True)["02-02-Vlr"]
    G = [list(r) for r in ws.iter_rows(max_row=120, max_col=20, values_only=True)]
    hi = next(i for i, r in enumerate(G) if any(isinstance(v, str) and nrm(v).startswith("deb") for v in r))
    cols = {}
    for j, v in enumerate(G[hi]):
        if v is None: continue
        for k, p in MAP.items():
            if re.search(p, nrm(v)) and k not in cols: cols[k] = j; break
    MES = dict(jan=1, fev=2, mar=3, abr=4, mai=5, jun=6, jul=7, ago=8, set=9, out=10, nov=11, dez=12); rows = []
    for r in G[hi + 1:]:
        m = re.match(r"^([A-Za-z]{3})/(\d{2})$", str(r[1] or "").strip())
        if m: rows.append({"mes": pd.Timestamp(2000 + int(m.group(2)), MES[m.group(1).lower()], 1), **{k: (float(r[j]) / 1e9 if isinstance(r[j], (int, float)) else 0.0) for k, j in cols.items()}})
    return pd.DataFrame(rows).set_index("mes").sort_index()
def agrega(D):
    D = D.copy()
    for k in MAP:
        if k not in D: D[k] = 0.0
    D["ecm"] = D.ipo + D.follow_on
    D["dcm"] = D[["debentures", "nc", "np", "lf", "cr", "cra", "cri", "fidc", "cprf", "cdca"]].sum(axis=1)
    D["securitizacao"] = D[["cra", "cri", "cr", "fidc"]].sum(axis=1)
    D["fundos_listados"] = D.fii + D.fiagro
    return D
def main():
    a = pag2(os.path.join(MK, "mk", "wb", "BoletimMK_1217.xlsx"), "Pág 2 - Mercado de capitais").loc[2011:2015]; a["fonte"] = "ANBIMA boletim dez/17"
    b = pag2(os.path.join(MK, "mk", "wb", "Anexo_BoletimMK_1222.xlsx"), "Pág 2 - Mercado de capitais"); chk = b.loc[[2020, 2021]].copy(); b = b.loc[2016:2019]; b["fonte"] = "ANBIMA boletim dez/22"
    M = consolidado(); c = M.groupby(M.index.year).sum(); c["fonte"] = "ANBIMA anexo consolidado (ago/26)"; c.loc[2026, "fonte"] = "ANBIMA anexo consolidado, jan-ago/26"
    A = agrega(pd.concat([a, b, c]).fillna(0.0)); A.index.name = "ano"
    ytd = agrega(M[M.index.month <= 8].groupby(M[M.index.month <= 8].index.year).sum())
    A["ecm_jan_ago"] = ytd.ecm; A["dcm_jan_ago"] = ytd.dcm
    A.round(2).to_csv(os.path.join(DATA, "mercado_capitais_anual.csv"))
    Q = agrega(M.resample("QE").sum()); Q.index = [f"{d.quarter}Q{str(d.year)[2:]}" for d in Q.index]; Q.round(2).to_csv(os.path.join(DATA, "mercado_capitais_tri.csv"))
    print("checagem 2020-21 (boletim dez/22 vs consolidado), DCM e ECM:", {y: (round(agrega(chk).loc[y, "dcm"], 1), round(A.loc[y, "dcm"], 1), round(agrega(chk).loc[y, "ecm"], 1), round(A.loc[y, "ecm"], 1)) for y in (2020, 2021)})
    K = pd.Series({2005: 363, 2006: 473, 2007: 699, 2008: 663, 2009: 454, 2010: 726, 2011: 817, 2012: 816, 2013: 796, 2014: 818, 2015: 773, 2016: 740, 2017: 830, 2018: 967, 2019: 1231,
                   2020: 1117, 2021: 1963, 2022: 1728, 2023: 1505, 2024: 1582, 2025: 1581}, name="transacoes"); K.index.name = "ano"
    K.to_frame().assign(fonte="KPMG Pesquisa de Fusões e Aquisições (1T25 p/ 2005-24; 4T25 p/ 2025)").to_csv(os.path.join(DATA, "ma_kpmg_anual.csv"))
    j = json.load(open(os.path.join(DATA, "historical_financials.json"), encoding="utf-8"))["3. Managerial P&L - new"]
    old = {"1Q19": 56, "2Q19": 87, "3Q19": 143, "4Q19": 221, "1Q20": 132, "2Q20": 65, "3Q20": 169, "4Q20": 323}
    deals = {"4Q19": (8, 51), "3Q20": (14, None), "4Q20": (11, 55), "1Q20": (5, 36), "2Q20": (2, 22), "1Q21": (12, 43), "2Q21": (8, 62), "3Q21": (15, 48), "3Q19": (4, None)}
    X = pd.DataFrame({"issuer_services": pd.Series({**old, **{k: v for k, v in j["Issuer Services"].items() if re.match(r"\dQ\d\d", k)}}),
                      "corporate": pd.Series({k: v for k, v in j["Corporate"].items() if re.match(r"\dQ\d\d", k)})})
    X["ecm_deals"] = pd.Series({k: v[0] for k, v in deals.items()}); X["dcm_deals"] = pd.Series({k: v[1] for k, v in deals.items() if v[1]})
    X = X.loc[sorted(X.index, key=lambda q: (int(q[2:]), int(q[0])))]
    X["fonte"] = ["releases 2019-20 (segmentação antiga)" if q in old else "planilha histórica do RI" for q in X.index]
    X.round(1).to_csv(os.path.join(DATA, "xp_mercado_capitais_tri.csv"))
    pd.set_option("display.width", 250)
    print(A[["ipo", "follow_on", "ecm", "debentures", "nc", "np", "lf", "securitizacao", "dcm", "fundos_listados", "ecm_jan_ago", "dcm_jan_ago", "fonte"]].round(1).to_string())
    print(Q[["ecm", "dcm"]].round(1).T.to_string())
    xa = X.issuer_services.groupby(lambda q: 2000 + int(q[2:])).sum(); print("XP Issuer Services anual:", {**{2018: 178}, **xa.round(0).to_dict()})
if __name__ == "__main__": main()
