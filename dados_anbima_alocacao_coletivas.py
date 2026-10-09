# -*- coding: utf-8 -*-
"""Pontos semestrais extraídos dos PDFs das coletivas de imprensa da ANBIMA (fontes/setor/anbima/historico/pdf_*.pdf), que cobrem o
buraco de 2019-20 das edições mensais. Os PDFs trazem o total por segmento (R$ bi) e a distribuição % por produto; o valor em R$ mi
é % x total. Fonte principal: "Coletiva de Distribuição - 1º semestre de 2020" (pdf_Estatisticas_de_Distribuicao_202006.pdf), págs. 3, 7, 8 e 11.
Legenda das barras conferida contra as edições xlsx de mar/17 e jun/19 (ordem: ver dicionários abaixo). "demais" = demais produtos (não alocado).
Saída: data/anbima_alocacao_coletivas.csv (seg, data, fonte, classes em R$ mi) e data/anbima_pf_total_mensal_2020.csv (total PF mensal dez/19-dez/20)."""
import os, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
# totais por segmento, R$ bi (pág. 3 e 7)
TOT = {"varejo_tradicional": {201706: 878.5, 201806: 919.3, 201906: 912.7, 202006: 1065.6},
       "varejo_alta_renda": {201706: 742.7, 201806: 821.5, 201906: 968.7, 202006: 995.7},
       "private": {201606: 764.4, 201706: 892.3, 201806: 1010.0, 201906: 1176.3, 202006: 1306.1}}
# distribuição %, pág. 8 (varejo, jun/17..jun/20) e pág. 11 (private, jun/16..jun/20)
PCT = {"varejo_tradicional": {"fundos_rf": [14.6, 15.7, 13.5, 11.1], "fundos_mm": [1.0, 1.1, 1.0, 1.3], "cdb": [8.7, 9.2, 9.4, 9.4], "lci_lca": [9.8, 6.9, 5.0, 5.3],
                              "acoes": [1.0, 0.9, 1.2, 1.4], "poupanca": [61.5, 63.3, 67.1, 68.8], "demais": [3.5, 2.9, 2.7, 2.7]},
       "varejo_alta_renda": {"fundos_rf": [38.6, 37.4, 36.1, 27.1], "fundos_mm": [5.4, 9.3, 9.8, 11.0], "cdb": [12.4, 12.0, 11.6, 16.2], "lci_lca": [15.7, 12.4, 11.3, 9.4],
                             "acoes": [3.8, 4.5, 6.6, 8.1], "poupanca": [10.8, 12.3, 12.1, 13.8], "demais": [13.4, 12.1, 12.4, 14.2]},
       "private": {"fundos_rf": [11.3, 12.3, 10.9, 10.1, 7.2], "fundos_acoes": [2.5, 2.2, 5.2, 6.7, 7.6], "fundos_mm": [24.9, 27.1, 32.1, 31.1, 32.2], "cdb": [1.9, 2.2, 2.7, 2.8, 3.9],
                   "debentures": [1.4, 1.5, 1.7, 2.0, 2.2], "lci_lca": [19.3, 15.4, 13.2, 11.5, 8.9], "acoes": [12.0, 12.6, 12.3, 14.7, 17.3], "previdencia": [8.9, 9.6, 10.5, 10.7, 10.8], "demais": [17.7, 17.0, 11.5, 9.8, 9.9]}}
# total PF mensal (R$ bi), pág. 2 da coletiva de 2020 (pdf_Estatisticas_de_Distribuicao_202012.pdf); private inclui previdência
MENSAL = {201912: 3263.0, 202001: 3275.5, 202002: 3257.7, 202003: 3090.8, 202004: 3187.3, 202005: 3272.2, 202006: 3370.3, 202007: 3493.9, 202008: 3515.5, 202009: 3522.2, 202010: 3549.4, 202011: 3618.3, 202012: 3701.1}
# totais por segmento em datas intermediárias sem distribuição (pág. 3): dez/17, jun/18, dez/18, jun/19, dez/19, jun/20 — só os jun/ entram (dez vem do anexo)
rows = []
for seg, tot in TOT.items():
    datas = sorted(tot)
    for i, d in enumerate(datas):
        r = dict(seg=seg, data=d, fonte="coletiva pdf (% x total)", total=tot[d] * 1e3)
        for cl, v in PCT[seg].items(): r[cl] = v[i] / 100 * tot[d] * 1e3
        if seg != "private": r["fundos_555"] = r["fundos_rf"] + r["fundos_mm"]
        else: r["fundos_555"] = r["fundos_rf"] + r["fundos_mm"] + r["fundos_acoes"]
        rows.append(r)
C = pd.DataFrame(rows); C.round(1).to_csv(os.path.join(DATA, "anbima_alocacao_coletivas.csv"), index=False)
pd.DataFrame([dict(data=k, total_pf_bi=v, fonte="coletiva dez/20, pág. 2") for k, v in MENSAL.items()]).to_csv(os.path.join(DATA, "anbima_pf_total_mensal_2020.csv"), index=False)
pd.set_option("display.width", 250); print((C.set_index(["seg", "data"]).drop(columns="fonte") / 1e3).round(0).to_string())
