# -*- coding: utf-8 -*-
"""Série combinada da alocação da PF por segmento (ANBIMA): pontos de dezembro do Anexo do Boletim de Private e Varejo (2013→, revisados,
dados_anbima_alocacao_anual.py) + pontos intra-ano das edições mensais das Estatísticas de Varejo/Private (dados_anbima_alocacao_segmentos.py).
Prioridade quando a mesma referência existe: anexo > estatística mensal > coletiva (PDF, % x total). Classes comuns: cdb, lci_lca, tit_publicos, credito_privado, coe, acoes,
fundos_rf, fundos_mm, fundos_acoes, fundos_555, fii, fidc, fip, estruturados, poupanca, previdencia, total (R$ mi).
Saída: data/anbima_alocacao_segmentos_serie.csv (seg, data AAAAMM, fonte, classes)."""
import os, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
CL = ["cdb", "lci_lca", "tit_publicos", "credito_privado", "coe", "acoes", "fundos_rf", "fundos_mm", "fundos_acoes", "fundos_555", "fii", "fidc", "fip", "etf", "estruturados", "poupanca", "previdencia", "caixa", "total"]
A = pd.read_csv(os.path.join(DATA, "anbima_alocacao_segmentos_anual.csv")); A = A[A.seg != "pf_total"].copy(); A["data"] = A.ano * 100 + 12; A["fonte"] = "anexo boletim"
M = pd.read_csv(os.path.join(DATA, "anbima_alocacao_segmentos.csv")); M["fonte"] = "estatística mensal"
M = M[M.seg != "varejo_total"]
C = pd.read_csv(os.path.join(DATA, "anbima_alocacao_coletivas.csv"))  # semestrais dos PDFs das coletivas (jun/16-jun/20); entram só onde não há edição
for d in (A, M, C):
    for c in CL:
        if c not in d: d[c] = float("nan")
S = pd.concat([A[["seg", "data", "fonte"] + CL], M[["seg", "data", "fonte"] + CL], C[["seg", "data", "fonte"] + CL]]).assign(_r=lambda d: d.fonte.map(lambda f: 0 if f.startswith("anexo") else 1 if f.startswith("estat") else 2)).sort_values(["seg", "data", "_r"]).drop_duplicates(["seg", "data"], keep="first").drop(columns="_r")
S.round(1).to_csv(os.path.join(DATA, "anbima_alocacao_segmentos_serie.csv"), index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
print(S.groupby("seg").data.agg(["count", "min", "max"]))
print((S.set_index(["seg", "data"])[["total", "poupanca", "cdb", "lci_lca", "tit_publicos", "credito_privado", "coe", "acoes", "fundos_555", "estruturados", "previdencia"]] / 1e3).round(0).to_string())
