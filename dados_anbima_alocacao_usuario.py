# -*- coding: utf-8 -*-
"""Lê a compilação mensal do usuário das Estatísticas de Varejo e de Private da ANBIMA ("ANBIMA Historical Distribution AuC.xlsx",
copiada para fontes/setor/anbima/usuario/), abas "Retail -AuC" (blocos TOTAL / TRADITIONAL RETAIL / HIGH INCOME RETAIL, rótulos na col C,
datas na linha 7) e "Private Banking - AuC" (rótulos na col B), e converte para o mesmo esquema de classes de dados_anbima_alocacao_segmentos.py.
R$ mil no arquivo → R$ mi na saída. Saída: data/anbima_alocacao_usuario_long.csv (seg, data AAAAMM, classe, valor, fonte)."""
import os, re, shutil, unicodedata, openpyxl, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
SRC = r"C:\Users\rlavourinha\Downloads\ANBIMA Historical Distribution AuC.xlsx"; DST = os.path.join(HERE, "fontes", "setor", "anbima", "usuario", "ANBIMA_Historical_Distribution_AuC.xlsx")
MES = {"jan": 1, "fev": 2, "feb": 2, "mar": 3, "abr": 4, "apr": 4, "mai": 5, "may": 5, "jun": 6, "jul": 7, "ago": 8, "aug": 8, "set": 9, "sep": 9, "out": 10, "oct": 10, "nov": 11, "dez": 12, "dec": 12}
def norm(s): return re.sub(r"\s+", " ", re.sub(r"\[\d\]", "", unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower())).strip()
def ref(v):
    if hasattr(v, "year"): return v.year * 100 + v.month
    m = re.match(r"^([a-z]{3})[a-z]*\s*/\s*(\d{2,4})$", norm(v))
    if not m or m.group(1) not in MES: return None
    y = int(m.group(2)); return (y + 2000 if y < 100 else y) * 100 + MES[m.group(1)]
def num(v): return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None

R_SEC = [("1. investment funds", "1", "fundos_555"), ("2. structured funds", "2", "estruturados"), ("3. securities", "3", "tvm"), ("4. saving", "4", "poupanca"), ("5. pension", "5", "previdencia")]
R_MAP = {"1": [("fixed income", "fundos_rf"), ("multimarket", "fundos_mm"), ("equit", "fundos_acoes"), ("fmp", "fmp"), ("fx", "fundos_cambial")],
         "2": [("fidc", "fidc"), ("fii", "fii"), ("fip", "fip"), ("etf fixed", "etf_rf"), ("etf variable", "etf_rv"), ("etf", "etf")],
         "3": [("stocks", "acoes"), ("equity", "acoes"), ("equities", "tvm_rv"), ("variable income", "tvm_rv"), ("public bonds", "tit_publicos"), ("pre-fixed", "tp_pre"), ("post-fixed", "tp_pos"), ("hybrid", "tp_hibrido"),
               ("private bonds", "tit_privados"), ("time deposits", "cdb"), ("repo", "compromissada"), ("lca", "lca"), ("cra", "cra"), ("lh", "lh"), ("lci", "lci"), ("cri", "cri"), ("lf", "lf"), ("debentures", "debentures"),
               ("box", "box"), ("lig", "lig"), ("lam", "lam"), ("lc -", "lc"), ("other", "tvm_outros"), ("structured operations", "coe"), ("coe", "coe"), ("fixed income", "tvm_rf")]}
R_BLOCOS = [("traditional retail", "varejo_tradicional"), ("high income retail", "varejo_alta_renda")]

def parse_retail(ws):
    G = [list(r) for r in ws.iter_rows(values_only=True, max_col=100)]; hdr = G[6]; cols = [(j, ref(v)) for j, v in enumerate(hdr) if v is not None and ref(v)]
    out = []; seg = None; sec = None; vistos = set()
    for row in G[7:]:
        lab = row[2]
        if not (isinstance(lab, str) and lab.strip()): continue
        n = norm(lab)
        if seg is None and n == "total": seg = "varejo_total"; sec = None; vistos = set(); cl = "total"
        else:
            hit = next((s for k, s in R_BLOCOS if n.startswith(k)), None)
            if hit: seg = hit; sec = None; vistos = set(); cl = "total"
            else:
                sh = next((s, c) for k, s, c in R_SEC if n.startswith(k)) if any(n.startswith(k) for k, _, _ in R_SEC) else None
                if sh: sec = sh[0]; cl = sh[1]
                elif sec in R_MAP:
                    cl = next((c for k, c in R_MAP[sec] if n.startswith(k)), None)
                    if cl is None or (seg, cl) in vistos: continue
                    if n == "hybrid" and sec == "3" and (seg, "tp_hibrido") in vistos: continue  # 2º "Hybrid" = COE
                else: continue
        if cl in ("total", "fundos_555", "estruturados", "tvm", "poupanca", "previdencia") or cl.startswith(("fundos_", "tp_", "tvm_")) or True: vistos.add((seg, cl))
        for j, d in cols:
            v = num(row[j]) if j < len(row) else None
            if v is not None: out.append(dict(seg=seg, data=d, classe=cl, valor=v / 1e3))
    return out

P_SEC = [("i - financial volume", "total"), ("1. investment funds", "fundos"), ("2. structured funds", "estruturados"), ("2. securities", "tvm"), ("3. cash", "caixa_poupanca"), ("4. open pension", "previdencia"), ("5. credit", "fim"), ("ii -client", "fim"), ("ii - client", "fim")]
P_MAP = {"fundos": [("open funds", "fundos_abertos_proprios"), ("third-party", "fundos_abertos_terceiros"), ("exclusive", "fundos_exclusivos")],
         "estruturados": [("fidc", "fidc"), ("real estate", "fii"), ("participations", "fip"), ("etf fixed", "etf_rf"), ("etf variable", "etf_rv"), ("etf", "etf"), ("fmp", "fmp")],
         "tvm": [("equity", "acoes"), ("variable income", "tvm_rv"), ("public bonds", "tit_publicos"), ("private bonds", "tit_privados"), ("time deposits", "cdb"), ("repurchase", "compromissada"), ("dpge", "dpge"), ("lca", "lca"), ("cra", "cra"),
                 ("mortgage notes", "lh"), ("lci", "lci"), ("cri", "cri"), ("financial letter", "lf"), ("debentures", "debentures"), ("box", "box"), ("lig", "lig"), ("leasing", "lam"), ("exchange letters", "lc"), ("structured operations", "coe"), ("others", "outros_tp"), ("fixed income", "tvm_rf")],
         "caixa_poupanca": [("cash", "caixa"), ("saving", "poupanca")]}

def parse_private(ws):
    G = [list(r) for r in ws.iter_rows(values_only=True, max_col=100)]; hdr = G[6]; cols = [(j, ref(v)) for j, v in enumerate(hdr) if v is not None and ref(v)]
    out = []; sec = None; vistos = set()
    for row in G[7:]:
        lab = row[1]
        if not (isinstance(lab, str) and lab.strip()): continue
        n = norm(lab); sh = next((s for k, s in P_SEC if n.startswith(k)), None)
        if sh == "fim": break
        if sh: sec = sh; cl = sh
        elif sec in P_MAP:
            cl = next((c for k, c in P_MAP[sec] if n.startswith(k)), None)
            if cl is None or ("private", cl) in vistos: continue
        else: continue
        vistos.add(("private", cl))
        for j, d in cols:
            v = num(row[j]) if j < len(row) else None
            if v is not None: out.append(dict(seg="private", data=d, classe=cl, valor=v / 1e3))
    return out

def main():
    os.makedirs(os.path.dirname(DST), exist_ok=True)
    if os.path.exists(SRC): shutil.copy2(SRC, DST)
    wb = openpyxl.load_workbook(DST, read_only=True, data_only=True)
    L = pd.DataFrame(parse_retail(wb["Retail -AuC"]) + parse_private(wb["Private Banking - AuC"])); L["fonte"] = "compilação do usuário (edições ANBIMA)"
    L = L.drop_duplicates(["seg", "data", "classe"]); L.to_csv(os.path.join(DATA, "anbima_alocacao_usuario_long.csv"), index=False)
    W = L.pivot_table(index=["seg", "data"], columns="classe", values="valor").reset_index()
    for c in ["lci", "lca", "cra", "cri", "lf", "debentures", "lig", "lc", "lam", "tvm_outros", "compromissada", "box", "dpge", "outros_tp", "fidc", "fii", "fip", "etf", "fmp", "fundos", "estruturados", "fundos_555", "caixa", "poupanca", "previdencia", "caixa_poupanca"]:
        if c not in W: W[c] = float("nan")
    W["lci_lca"] = W.lci.fillna(0) + W.lca.fillna(0)
    W["credito_privado"] = W[["cra", "cri", "lf", "debentures", "lig", "lc", "lam", "tvm_outros", "compromissada", "box", "dpge", "outros_tp"]].fillna(0).sum(axis=1)
    pv = W.seg == "private"; W.loc[pv, "fundos_555"] = W.loc[pv, "fundos"]; antigo = pv & (W.data < 202400); W.loc[antigo, "fundos_555"] = W.loc[antigo, "fundos"] - W.loc[antigo, "estruturados"].fillna(0)  # layout antigo: estruturados dentro de "1. INVESTMENT FUNDS"
    W.loc[~pv, "estruturados"] = W.loc[~pv, "estruturados"].fillna(W.loc[~pv, ["fidc", "fii", "fip", "etf"]].fillna(0).sum(axis=1))
    W.round(1).to_csv(os.path.join(DATA, "anbima_alocacao_usuario.csv"), index=False)
    chk = W.copy(); chk["soma"] = chk[[c for c in ["fundos_555", "estruturados", "tvm", "poupanca", "previdencia"] if c in chk]].fillna(0).sum(axis=1)
    pv = chk.seg == "private"; chk.loc[pv, "soma"] = chk.loc[pv, [c for c in ["fundos_555", "estruturados", "tvm", "caixa_poupanca", "previdencia"] if c in chk]].fillna(0).sum(axis=1)
    chk["dif"] = (chk.soma / chk.total - 1) * 100
    print(W.groupby("seg").data.agg(["count", "min", "max"])); print("máx |dif| total vs soma dos blocos, %:", chk.groupby("seg").dif.apply(lambda s: s.abs().max()).round(2).to_dict())
    print("private, dif por ano (%):", chk[chk.seg=="private"].assign(ano=lambda d: d.data//100).groupby("ano").dif.mean().round(1).to_dict())

if __name__ == "__main__": main()
