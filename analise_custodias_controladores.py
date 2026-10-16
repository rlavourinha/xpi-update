# -*- coding: utf-8 -*-
"""Teste: as captações extraordinárias e a valorização do AuC da XP conversam com a posição dos controladores de Magalu e Ambipar?
Entradas: data/vlmo_mglu_ambp_bruto.csv (CVM VLMO), data/precos_mglu_ambp_diario.csv (B3 COTAHIST), data/_mod_auc_tri.csv (XPMod, aba MOD).
Saída: data/xp_auc_custodias_controladores_tri.csv."""
import os, pandas as pd, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, "data")
X = pd.read_csv(os.path.join(D, "vlmo_mglu_ambp_bruto.csv"), dtype=str); X["Quantidade"] = pd.to_numeric(X.Quantidade)
c = X[(X.Tipo_Cargo == "Controlador ou Vinculado") & X.Tipo_Ativo.str.startswith("A") & (X.Tipo_Movimentacao == "Saldo Inicial")]
S = c.groupby([c.Nome_Companhia.str[:4], "Data_Referencia"]).Quantidade.sum().unstack(0).rename(columns={"AMBI": "AMBP3", "MAGA": "MGLU3"})
S.index = pd.to_datetime(S.index) - pd.Timedelta(days=1)          # saldo inicial do mês = posição no fim do mês anterior
# reapresentações em duplicidade (saldo dobrado por um mês, sem evento societário que o justifique)
S.loc["2023-07-31", "AMBP3"] = S.loc["2023-06-30", "AMBP3"]; S.loc["2023-10-31", "AMBP3"] = 69081830 + 42264150 * 0  # antes da OPA de nov/23
for d in ["2025-11-30", "2025-12-31", "2026-01-31"]: S.loc[d, "MGLU3"] = S.loc[d, "MGLU3"] / 2
P = pd.read_csv(os.path.join(D, "precos_mglu_ambp_diario.csv"), index_col=0, parse_dates=True)
q = pd.period_range("2019Q1", "2026Q3", freq="Q")
fim = {p: P[P.index <= p.end_time].index.max() for p in q}
R = pd.DataFrame(index=[f"{p.quarter}Q{str(p.year)[2:]}" for p in q])
for t, split in (("MGLU3", {"3Q19": 8, "4Q20": 4, "2Q24": 0.1}), ("AMBP3", {"3Q25": 10})):
    sh = [S[t][S.index <= p.end_time].dropna().iloc[-1] if (S[t][S.index <= p.end_time].dropna().size) else np.nan for p in q]
    px = [P.loc[fim[p], t] for p in q]
    R[f"{t}_acoes_mi"] = np.array(sh) / 1e6; R[f"{t}_preco"] = px
    R[f"{t}_valor_bi"] = R[f"{t}_acoes_mi"] * R[f"{t}_preco"] / 1e3
    f = pd.Series({k: split.get(k, 1.0) for k in R.index})
    R[f"{t}_mtm_bi"] = R[f"{t}_acoes_mi"].shift(1) * f * R[f"{t}_preco"] / 1e3 - R[f"{t}_valor_bi"].shift(1)
M = pd.read_csv(os.path.join(D, "_mod_auc_tri.csv"), index_col=0)
R = R.join(M[["auc_ret", "auc_corp", "nnm_ret", "oneoff", "nnm_corp", "ma", "ma_ret", "ma_corp"]])
R.to_csv(os.path.join(D, "xp_auc_custodias_controladores_tri.csv"))
pd.set_option("display.width", 250)
print(R[["MGLU3_acoes_mi", "MGLU3_preco", "MGLU3_valor_bi", "MGLU3_mtm_bi", "oneoff", "ma_ret", "auc_ret", "AMBP3_acoes_mi", "AMBP3_preco", "AMBP3_valor_bi", "AMBP3_mtm_bi", "ma_corp", "auc_corp", "nnm_corp"]].round(2).to_string())

# ---- valorização implícita do AuC de varejo: nossa conta (ex captações extraordinárias) e ajustada sem a Magalu ----
N = pd.read_csv(os.path.join(D, "xp_auc_nowcast.csv"), index_col=0)
R = pd.read_csv(os.path.join(D, "xp_auc_custodias_controladores_tri.csv"), index_col=0)
idx = list(R.index); i0 = idx.index("3Q20")
mg_val = R.MGLU3_valor_bi.where([i >= i0 for i in range(len(idx))], 0.0)                 # bloco na custódia a partir do 3T20
mg_mtm = R.MGLU3_mtm_bi.where([i > i0 for i in range(len(idx))], 0.0); mg_mtm["3Q20"] = R.loc["3Q20", "MGLU3_valor_bi"] - 78.0  # 3T20: só o que andou depois da entrada
one = R.oneoff.fillna(0)
V = pd.DataFrame({"nossa_conta_pct": N["AuC varejo"], "bottom_up_pct": N["bottom-up"]}).reindex(R.index)
V["valorizacao_ex_one_bi"] = R.ma_ret - one
V["magalu_mtm_bi"] = mg_mtm; V["magalu_bloco_bi"] = mg_val; V["magalu_pct_auc"] = mg_val / R.auc_ret * 100
V["ajustada_pct"] = (V.valorizacao_ex_one_bi - mg_mtm) / (R.auc_ret.shift(1) - mg_val.shift(1).fillna(0)) * 100
V["ajustada_pct"] = V.ajustada_pct.where(V.magalu_bloco_bi.shift(1).fillna(0) + V.magalu_mtm_bi != 0, V.nossa_conta_pct)
V["gap_nossa"] = V.nossa_conta_pct - V.bottom_up_pct; V["gap_ajustada"] = V.ajustada_pct - V.bottom_up_pct
V.loc["1Q19":"2Q26"].to_csv(os.path.join(D, "xp_auc_valorizacao_ex_magalu.csv"))
print(V.loc["1Q19":"2Q26"].round(2).to_string())

# ---- grupo Ometto (entrada extraordinária de R$ 26 bi no 1T21, reorganização da Cosan de 08/03/21) ----
# blocos limpos do VLMO: CSAN3 do controlador = 140,5 mi (562,7 mi após o desdobramento 1:4 de mai/21; constante até o follow-on de nov/25,
# que é dinheiro novo e fica fora); RAIL3 da Cosan S.A. = 633,5 mi até a venda via TRS em dez/25 (448,8 mi depois). ADS ficam em NY: fora.
import io as _io, zipfile
px = {}
for a in range(2021, 2027):
    z = zipfile.ZipFile(os.path.join(HERE, "fontes", "setor", "b3", "cotahist_raw", f"COTAHIST_A{a}.ZIP"))
    for ln in _io.TextIOWrapper(z.open(z.namelist()[0]), encoding="latin1"):
        if ln[:2] == "01" and ln[24:27] == "010" and ln[12:24].strip() in ("CSAN3", "RAIL3"):
            px[(pd.Timestamp(ln[2:10]), ln[12:24].strip())] = int(ln[108:121]) / 100
PX = pd.Series(px).unstack().sort_index()
PX.loc[PX.index < "2021-05-10", "CSAN3"] /= 4                                       # preço ajustado ao desdobramento
PX.to_csv(os.path.join(D, "precos_csan3_rail3_diario.csv"))
ENT = pd.Timestamp("2021-03-08")
qs = [q for q in V.index if q >= "1Q21" or True]
O = pd.DataFrame(index=V.index, columns=["csan_acoes_mi", "rail_acoes_mi", "csan_preco", "rail_preco"], dtype=float)
for q in V.index:
    per = pd.Period(f"20{q[2:]}Q{q[0]}", "Q")
    if per < pd.Period("2021Q1", "Q"): continue
    d = PX.index[PX.index <= per.end_time].max()
    O.loc[q] = [562.7, 448.8 if per >= pd.Period("2025Q4", "Q") else 633.5, PX.loc[d, "CSAN3"], PX.loc[d, "RAIL3"]]
O["ometto_bloco_bi"] = (O.csan_acoes_mi * O.csan_preco + O.rail_acoes_mi * O.rail_preco) / 1e3
pv = O[["csan_preco", "rail_preco"]].shift(1); pv.loc["1Q21"] = [PX.loc[ENT, "CSAN3"], PX.loc[ENT, "RAIL3"]]
ra = O.rail_acoes_mi.shift(1).fillna(633.5)
O["ometto_mtm_bi"] = (562.7 * (O.csan_preco - pv.csan_preco) + ra * (O.rail_preco - pv.rail_preco)) / 1e3
O["ometto_entrada_bi"] = 0.0; O.loc["1Q21", "ometto_entrada_bi"] = (562.7 * PX.loc[ENT, "CSAN3"] + 633.5 * PX.loc[ENT, "RAIL3"]) / 1e3
O = O.fillna({"ometto_bloco_bi": 0.0, "ometto_mtm_bi": 0.0})
V = V.drop(columns=[c for c in V.columns if c.startswith("ometto") or c.startswith("ajust_mo") or c == "gap_ajust_mo"]).join(O[["ometto_bloco_bi", "ometto_mtm_bi", "ometto_entrada_bi"]])
V["ometto_pct_auc"] = V.ometto_bloco_bi / R.auc_ret * 100
V["ajustada_mo_pct"] = (V.valorizacao_ex_one_bi - V.magalu_mtm_bi - V.ometto_mtm_bi) / (R.auc_ret.shift(1) - V.magalu_bloco_bi.shift(1).fillna(0) - V.ometto_bloco_bi.shift(1).fillna(0)) * 100
V["ajustada_mo_pct"] = V.ajustada_mo_pct.fillna(V.ajustada_pct)
V["gap_ajust_mo"] = V.ajustada_mo_pct - V.bottom_up_pct
V.loc["1Q19":"2Q26"].to_csv(os.path.join(D, "xp_auc_valorizacao_ex_magalu.csv"))
print(V.loc["4Q20":"2Q26", ["nossa_conta_pct", "ajustada_pct", "ajustada_mo_pct", "bottom_up_pct", "magalu_mtm_bi", "ometto_mtm_bi", "ometto_bloco_bi", "ometto_pct_auc"]].round(2).to_string())
