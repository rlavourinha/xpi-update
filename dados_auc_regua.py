# -*- coding: utf-8 -*-
"""Régua de mercado (bottom-up) para a valorização do AuC de varejo da XP, trimestral desde 1T19.
Antes (bottom-up CVM): ações × classe Ações da CVM + renda fixa × classe Renda Fixa da CVM + fundos × fundos administrados pela XP
+ outros × classe Renda Fixa. Problemas: a classe Ações da CVM rendeu +122% contra +96% do Ibovespa em 1T19-2T26 (fundos de BDR,
exterior e small caps; retorno por fluxo), a classe Renda Fixa bateu o CDI (crédito e inflação) e o saldo parado em conta, que
rende zero, recebia retorno de renda fixa.
Agora (régua de mercado), pesos do mix da XP no início do trimestre:
    ações × Ibovespa + renda fixa × CDI + fundos × fundos administrados pela XP ex-tesouraria
    + (outros − saldo parado) × CDI + saldo parado × 0.
Saldo parado = passivo "Securities trading and intermediation" do balanço da XP (contas de clientes e liquidações a pagar;
teto, inclui institucional) ÷ AuC de varejo no início do trimestre; 2019 interpolado entre 4T18 e 4T19.
Fontes: data/xp_auc_nowcast.csv (pesos, AuC implícita, CDI, fundos XP), data/historical_financials.json (balanço, XP RI 2T26),
Ibovespa da série do screening (../monitor-investimentos/data/macro.json).
Grava por cima: 'bottom-up' e 'gap' em xp_auc_nowcast.csv; 'gap' em xp_auc_gap_vs_curva_accrual.csv; 'bottom_up', 'bottom_up_pf',
'gap_cvm' (gap da régua com Ibovespa) e 'gap_pf' em xp_auc_vs_indice_pf.csv. As versões antigas ficam em colunas '... CVM'."""
import os, json, pandas as pd, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, "data")
N = pd.read_csv(os.path.join(D, "xp_auc_nowcast.csv"), index_col=0)
if "bottom-up CVM" not in N: N["bottom-up CVM"] = N["bottom-up"]; N["gap CVM"] = N["gap"]
# Ibovespa trimestral
ib = pd.Series({pd.Timestamp(d): v for d, v in json.load(open(os.path.join(HERE, "..", "monitor-investimentos", "data", "macro.json"), encoding="utf-8"))["hist"]["Ibovespa"]}).sort_index()
ibq = ib.resample("QE").last().pct_change() * 100; ibq.index = [f"{d.quarter}Q{str(d.year)[2:]}" for d in ibq.index]
N["Ibovespa"] = ibq.reindex(N.index)
# saldo parado: passivo com clientes (fim de período) ÷ AuC de varejo (fim de período), aplicado ao trimestre seguinte
hf = json.load(open(os.path.join(D, "historical_financials.json"), encoding="utf-8"))
pas = pd.Series(hf["5. Balance Sheet"]["Securities trading and intermediation (None)"], dtype=float)
pas = pas.rename(index={"2018": "4Q18", "2019": "4Q19"})
for k, q in enumerate(["1Q19", "2Q19", "3Q19"], 1): pas[q] = pas["4Q18"] + (pas["4Q19"] - pas["4Q18"]) * k / 4
kp = hf["2. KPIs"]; aucr = pd.Series(kp[[k for k in kp if k.startswith("Retail Client's Assets")][0]], dtype=float)
ordem = [f"{q}Q{a}" for a in range(18, 27) for q in range(1, 5)]
fl = (pas / aucr).reindex(ordem).shift(1)                 # fração do início do trimestre
N["w_float"] = np.minimum(fl.reindex(N.index), N.w_ot)
N["outros_ex_float"] = N.w_ot - N.w_float
def regua(eq):
    return N.w_eq * eq + N.w_rf * N.CDI + N.w_fd * N["admin XP ex-tes"] + N.outros_ex_float * N.CDI
N["bottom-up"] = regua(N["Ibovespa"]); N["gap"] = N["AuC varejo"] - N["bottom-up"]
N.to_csv(os.path.join(D, "xp_auc_nowcast.csv"))
# slide da curva (índice 2019Q1)
G = pd.read_csv(os.path.join(D, "xp_auc_gap_vs_curva_accrual.csv"), index_col=0)
if "gap CVM" not in G: G["gap CVM"] = G["gap"]
G["gap"] = [N.loc[f"{q[5]}Q{q[2:4]}", "gap"] for q in G.index]; G.to_csv(os.path.join(D, "xp_auc_gap_vs_curva_accrual.csv"))
# slide do índice da pessoa física (fatia de ações = índice PF)
P = pd.read_csv(os.path.join(D, "xp_auc_vs_indice_pf.csv"), index_col=0)
if "bottom_up CVM" not in P: P["bottom_up CVM"] = P["bottom_up"]; P["bottom_up_pf CVM"] = P["bottom_up_pf"]; P["gap_cvm CVM"] = P["gap_cvm"]; P["gap_pf CVM"] = P["gap_pf"]
P["bottom_up"] = N["bottom-up"].reindex(P.index); P["gap_cvm"] = P.auc_xp - P.bottom_up
P["bottom_up_pf"] = (N.w_eq * P.pf_count + N.w_rf * N.CDI + N.w_fd * N["admin XP ex-tes"] + N.outros_ex_float * N.CDI).reindex(P.index)
P["gap_pf"] = P.auc_xp - P.bottom_up_pf; P.to_csv(os.path.join(D, "xp_auc_vs_indice_pf.csv"))
# resumo
q = N.loc["1Q19":"2Q26"]; f = lambda s: (np.prod(1 + s / 100) - 1) * 100
print("saldo parado, % do AuC de varejo:", (fl.loc["1Q19":"2Q26"] * 100).round(1).iloc[[0, 4, 8, 12, 16, 20, 24, 29]].to_dict())
print("acumulado 1T19-2T26: régua nova", round(f(q["bottom-up"]), 1), "| régua CVM", round(f(q["bottom-up CVM"]), 1), "| CDI", round(f(q.CDI), 1), "| Ibov", round(f(q.Ibovespa), 1), "| AuC", round(f(q["AuC varejo"]), 1))
print("gap médio por trimestre desde 2023: novo", round(N.loc["1Q23":"2Q26", "gap"].mean(), 2), "| CVM", round(N.loc["1Q23":"2Q26", "gap CVM"].mean(), 2))
