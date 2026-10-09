# -*- coding: utf-8 -*-
"""Série anual (dezembro, 2013→) da alocação da pessoa física por segmento e instrumento, do Anexo do Boletim de Private e Varejo
da ANBIMA (fontes/setor/anbima/historico/boletim_Anexo-Boletim-Distribuicao-AAAA.xlsx; usa o mais recente, que reapresenta toda a série).
Abas: "Pág. 2 PL por segmento" (totais), "Pág 4/5/6" (por instrumento: varejo tradicional, alta renda, private). R$ milhões.
Saídas: data/anbima_alocacao_segmentos_anual_long.csv (seg, ano, classe, valor) e data/anbima_alocacao_segmentos_anual.csv (largo)."""
import os, re, glob, unicodedata, openpyxl, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
def norm(s): return re.sub(r"\s+", " ", unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()).strip()
MAPA = [("fundos de renda fixa", "fundos_rf"), ("fundos multimercados", "fundos_mm"), ("fundos de acoes", "fundos_acoes"), ("fundo de investimento em parti", "fip"),
        ("fundo de investimento em direi", "fidc"), ("fundo de investimento imobili", "fii"), ("outros fundos", "fundos_outros"), ("titulos publicos", "tit_publicos"), ("cdb/rdb", "cdb"),
        ("letras financeiras", "lf"), ("operacoes compromissadas", "compromissada"), ("debentures", "debentures"), ("certificado de recebiveis imob", "cri"), ("letra de credito imobiliario", "lci"),
        ("letras hipotecarias", "lh"), ("letra imobiliaria garantida", "lig"), ("letra de credito agricola", "lca"), ("certificado de recebiveis agr", "cra"), ("letra de arrendamento", "lam"),
        ("letra de cambio", "lc"), ("certificado de operacoes estru", "coe"), ("acoes", "acoes"), ("poupanca", "poupanca"), ("outros", "outros"), ("previdencia", "previdencia"), ("total", "total")]
ABAS = {"varejo_tradicional": "varejo tradic", "varejo_alta_renda": "alta renda", "private": "por instr private"}

def main():
    f = sorted(glob.glob(os.path.join(HERE, "fontes", "setor", "anbima", "historico", "boletim_Anexo-Boletim-Distribuicao-*.xlsx")))[-1]
    wb = openpyxl.load_workbook(f, read_only=True, data_only=True); rows = []
    for seg, key in ABAS.items():
        ws = wb[[s for s in wb.sheetnames if key in norm(s)][0]]; R = list(ws.iter_rows(values_only=True)); hdr = R[4]
        cls = []
        for h in hdr[1:]:
            n = norm(h) if h is not None else ""; c = next((v for k, v in MAPA if n.startswith(k)), None); cls.append(c)
        for r in R[5:]:
            if not hasattr(r[0], "year"): continue
            for c, v in zip(cls, r[1:]):
                if c and isinstance(v, (int, float)): rows.append(dict(seg=seg, ano=r[0].year, classe=c, valor=float(v)))
    ws = wb[[s for s in wb.sheetnames if "por segmento" in norm(s)][0]]
    for r in list(ws.iter_rows(values_only=True))[5:]:
        if hasattr(r[0], "year") and isinstance(r[4], (int, float)): rows.append(dict(seg="pf_total", ano=r[0].year, classe="total", valor=float(r[4])))
    L = pd.DataFrame(rows).drop_duplicates(["seg", "ano", "classe"]); L.to_csv(os.path.join(DATA, "anbima_alocacao_segmentos_anual_long.csv"), index=False)
    W = L.pivot_table(index=["seg", "ano"], columns="classe", values="valor").reset_index()
    for c in ["lci", "lca", "cra", "cri", "lf", "debentures", "lig", "lc", "lam", "compromissada", "outros", "fundos_rf", "fundos_mm", "fundos_acoes", "fii", "fidc", "fip", "fundos_outros"]:
        if c not in W: W[c] = float("nan")
    W["lci_lca"] = W.lci.fillna(0) + W.lca.fillna(0)
    W["credito_privado"] = W[["cra", "cri", "lf", "debentures", "lig", "lc", "lam", "compromissada", "outros"]].fillna(0).sum(axis=1)
    W["fundos_555"] = W[["fundos_rf", "fundos_mm", "fundos_acoes", "fundos_outros"]].fillna(0).sum(axis=1)
    W["estruturados"] = W[["fii", "fidc", "fip"]].fillna(0).sum(axis=1)
    W.round(1).to_csv(os.path.join(DATA, "anbima_alocacao_segmentos_anual.csv"), index=False)
    print("fonte:", os.path.basename(f)); pd.set_option("display.width", 250)
    print((W[W.seg != "pf_total"].set_index(["seg", "ano"])[["total", "poupanca", "cdb", "lci_lca", "tit_publicos", "credito_privado", "coe", "acoes", "fundos_555", "estruturados", "previdencia"]] / 1e3).round(0).to_string())

if __name__ == "__main__": main()
