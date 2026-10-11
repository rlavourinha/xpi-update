# -*- coding: utf-8 -*-
"""Nowcast dos DATs de varejo da XP a partir dos negócios/dia do mercado (COTAHIST via monitor, desde 2019).
Regressão trimestral DATs ~ a + b x negócios/dia do mercado (1T20-2T26) e projeção para os trimestres sem resultado.
Entradas: data/historical_financials.json (Retail DATs), ../monitor-investimentos/data/b3_volume_diario.csv. Saída: data/xp_dats_nowcast.csv."""
import os, json, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
j = json.load(open(os.path.join(DATA, "historical_financials.json"), encoding="utf-8"))["2. KPIs"]["Retail DATs (in million)"]
dats = pd.Series({k: float(v) for k, v in j.items() if len(k) == 4 and k[1] == "Q"}); dats.index = [pd.Period(f"20{k[2:]}Q{k[0]}") for k in dats.index]
v = pd.read_csv(os.path.join(HERE, "..", "monitor-investimentos", "data", "b3_volume_diario.csv"), parse_dates=["data"]).set_index("data")
q = v.negocios.resample("QE").mean() / 1e6; q.index = q.index.to_period("Q"); n = v.negocios.resample("QE").count(); n.index = q.index
df = pd.DataFrame({"dats": dats, "mercado_mi": q, "pregoes": n}).dropna(subset=["mercado_mi"])
fit = df.dropna(); b, a = np.polyfit(fit.mercado_mi, fit.dats, 1); df["nowcast"] = a + b * df.mercado_mi; r = np.corrcoef(fit.mercado_mi, fit.dats)[0, 1]
df["erro"] = df.dats - df.nowcast; df.round(3).to_csv(os.path.join(DATA, "xp_dats_nowcast.csv"))
print(f"DATs = {a:.3f} + {b:.4f} x negócios/dia do mercado (mi) | r = {r:.2f} | erro-padrão {fit.eval('dats - (@a + @b*mercado_mi)').std():.2f} mi | n = {len(fit)}")
print(df.tail(8).round(2).to_string())

# ---- diário: DAT estimado por pregão = a + b x negócios do dia (mi), e pelo share da XP no último trimestre fechado ----
ult = fit.index[-1]; share = fit.dats[ult] / fit.mercado_mi[ult]
dd = pd.DataFrame({"negocios_mercado_mi": v.negocios / 1e6}); dd["dat_regressao"] = a + b * dd.negocios_mercado_mi; dd["dat_share"] = share * dd.negocios_mercado_mi
dd["tri"] = dd.index.to_period("Q").astype(str); dd["media_tri_regressao"] = dd.groupby("tri").dat_regressao.transform("mean")
dd.round(3).to_csv(os.path.join(DATA, "xp_dats_nowcast_diario.csv"))
print(f"\nshare XP no {ult}: {share:.3f} negócio de varejo XP por negócio do mercado | diário (últimos 30 pregões):")
print(dd.tail(30).drop(columns="tri").round(2).to_string())
