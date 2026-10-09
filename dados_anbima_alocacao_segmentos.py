# -*- coding: utf-8 -*-
"""Alocação por classe de ativo dos segmentos do varejo bancário (ANBIMA, "Estatística de Varejo"):
Varejo consolidado, Varejo Tradicional e Varejo Alta Renda, em cada edição baixada (fontes/setor/anbima/historico/varejo_*.xlsx
e Estatistica_de_Varejo_AAAAMM.xlsx). Lê a aba "Volume Financeiro" (rótulos na coluna C, TOTAL Brasil na coluna D) e separa os
três blocos pelos cabeçalhos "TOTAL [1] [2]", "VAREJO TRADICIONAL" e "VAREJO ALTA RENDA"; o Private vem de data/anbima_alocacao_pf.csv.
Saídas: data/anbima_alocacao_segmentos_long.csv (seg, data, classe, valor R$ mi) e data/anbima_alocacao_segmentos.csv (largo, R$ mi)."""
import os, re, glob, unicodedata, openpyxl, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); AN = os.path.join(HERE, "fontes", "setor", "anbima"); DATA = os.path.join(HERE, "data")

def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\[\d\]", "", s).strip()

# (seção, rótulo normalizado começa com) -> classe
MAPA = [("1", "renda fixa (baixa", "fundos_rf_baixa_dur"), ("1", "renda fixa (exceto", "fundos_rf_exceto_bd"), ("1", "renda fixa", "fundos_rf"), ("1", "multimercados", "fundos_mm"),
        ("1", "acoes", "fundos_acoes"), ("1", "fmp", "fmp"), ("1", "cambial", "fundos_cambial"),
        ("2", "fundo de investimento em direitos", "fidc"), ("2", "fundo de investimento imobiliario", "fii"), ("2", "fundo de investimento em participacoes", "fip"), ("2", "etf renda fixa", "etf_rf"), ("2", "etf renda variavel", "etf_rv"), ("2", "etf", "etf"),
        ("3", "acoes", "acoes"), ("3", "titulos publicos", "tit_publicos"), ("3", "pre-fixado", "tp_pre"), ("3", "pos-fixado", "tp_pos"), ("3", "hibrido", "tp_hibrido"), ("3", "titulos privados", "tit_privados"),
        ("3", "cdb/rdb", "cdb"), ("3", "op. compromissada", "compromissada"), ("3", "letras de credito agr", "lca"), ("3", "certificado de recebiveis agr", "cra"), ("3", "letras de credito imob", "lci"),
        ("3", "certificado de recebiveis imob", "cri"), ("3", "letras financeiras", "lf"), ("3", "debentures tradicionais", "deb_tradicionais"), ("3", "debentures incentivadas", "deb_incentivadas"), ("3", "debentures", "debentures"),
        ("3", "letra imobiliaria garantida", "lig"), ("3", "letra de cambio", "lc"), ("3", "outros", "tvm_outros"), ("3", "certificado de operacoes estruturadas", "coe"), ("3", "renda fixa", "tvm_rf"), ("3", "renda variavel", "tvm_rv")]
SECOES = {"1. fundos de investimento": ("1", "fundos_555"), "2. fundos estruturados": ("2", "estruturados"), "3. titulos e valores": ("3", "tvm"), "4. poupanca": ("4", "poupanca"), "5. previdencia": ("5", "previdencia")}
BLOCOS = {"total": "varejo_total", "varejo tradicional": "varejo_tradicional", "varejo alta renda": "varejo_alta_renda"}

def parse(path):
    data = int(re.search(r"(\d{6})\.xlsx$", path).group(1)); wb = openpyxl.load_workbook(path, read_only=True, data_only=True); ws = wb[wb.sheetnames[0]]
    rows = []; seg = None; sec = None; vistos = set()
    for row in ws.iter_rows(values_only=True):
        lab = row[2]; val = row[3]
        if lab is None: continue
        n = norm(lab)
        if n.startswith("total") and isinstance(val, (int, float)) and seg is None: seg = "varejo_total"; rows.append((seg, "total", val)); sec = None; continue
        for k, s in BLOCOS.items():
            if n.startswith(k) and k != "total" and isinstance(val, (int, float)): seg = s; rows.append((seg, "total", val)); sec = None; vistos = set(); break
        else:
            if seg is None: continue
            hit = [v for k, v in SECOES.items() if n.startswith(k)]
            if hit:
                sec = hit[0][0]; rows.append((seg, hit[0][1], val)); continue
            if sec is None or not isinstance(val, (int, float)): continue
            for s, pref, cl in MAPA:
                if s == sec and n.startswith(pref) and (seg, cl) not in vistos:
                    rows.append((seg, cl, val)); vistos.add((seg, cl)); break
    return pd.DataFrame(rows, columns=["seg", "classe", "valor"]).assign(data=data)

def main():
    files = sorted(glob.glob(os.path.join(AN, "historico", "varejo_*.xlsx")) + glob.glob(os.path.join(AN, "Estatistica_de_Varejo_*.xlsx")))
    L = pd.concat([parse(f) for f in files]).drop_duplicates(["seg", "data", "classe"])
    # Private: reaproveita o parser anterior (classes já agregadas)
    P = pd.read_csv(os.path.join(DATA, "anbima_alocacao_pf.csv")); P = P[P.seg == "private"].drop(columns=["seg", "poupanca", "fundos_rf", "fundos_mm_acoes", "outros"])
    P = P.melt(id_vars="data", var_name="classe", value_name="valor").dropna(); P["seg"] = "private"; P["valor"] *= 1e3  # private estava em R$ bi
    P["classe"] = P.classe.replace({"cred_privado": "credito_privado", "fundos": "fundos_555"})
    L = pd.concat([L, P[["seg", "classe", "valor", "data"]]]).sort_values(["seg", "data", "classe"])
    L.to_csv(os.path.join(DATA, "anbima_alocacao_segmentos_long.csv"), index=False)
    W = L.pivot_table(index=["seg", "data"], columns="classe", values="valor").reset_index()
    for s in ["varejo_total", "varejo_tradicional", "varejo_alta_renda"]:
        m = W.seg == s
        W.loc[m, "lci_lca"] = W.loc[m, "lci"] + W.loc[m, "lca"]
        W.loc[m, "credito_privado"] = W.loc[m, ["cra", "cri", "lf", "debentures", "lig", "lc", "tvm_outros", "compromissada"]].fillna(0).sum(axis=1)
        W.loc[m, "estruturados"] = W.loc[m, ["fidc", "fii", "fip", "etf"]].fillna(0).sum(axis=1)
    W.round(1).to_csv(os.path.join(DATA, "anbima_alocacao_segmentos.csv"), index=False)
    chk = W[W.seg != "private"].assign(soma=lambda d: d[["fundos_555", "estruturados", "tvm", "poupanca", "previdencia"]].fillna(0).sum(axis=1))
    print("checagem total vs soma dos blocos (R$ bi):"); print((chk[["seg", "data", "total", "soma"]].assign(total=lambda d: d.total / 1e3, soma=lambda d: d.soma / 1e3)).round(1).to_string(index=False))
    return W

if __name__ == "__main__": main()
