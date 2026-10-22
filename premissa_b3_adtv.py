# -*- coding: utf-8 -*-
"""Premissa de ADTV do mercado à vista da B3, 4T26 a 2032, por decomposição: ADTV = valor de mercado × giro anual ÷ 252.

Por que assim: desde 2023 o giro (ADTV × 252 ÷ valor de mercado médio) oscila em torno de 1,40 (1T23-3T26: média 1,40, dp 0,17), com
o HFT estável em ~45% do volume; o que muda o ADTV é o tamanho do mercado. A Selic explicava o giro na amostra longa (2010-26, controlando
o co-location: +0,045 de giro por 1 p.p. a menos), mas desde 2022 o efeito some (t = 1,3, sinal trocado). Por isso o cenário-base não
usa a Selic, e o otimista usa a elasticidade longa com a Selic do Focus.

Premissas (editáveis abaixo):
  Ibovespa: fim de 3T26 e 4T26 do XPMod (MOD, linha "IBOV": 186.340 e 208.581); depois cresce G_IBOV ao ano (média do ano = fim do ano
            anterior × (1+g)^0,5).
  Valor de mercado = Ibovespa × razão valor de mercado/Ibovespa dos 6 meses até ago/26 (B3 RI).
  Giro: pessimista 1,25 (média − 1 dp), base 1,40 (média 1T23-3T26), otimista = base + 0,045 × (14 − Selic do Focus), limitado a 1,70.
  4T26: outubro observado (BDI/COTAHIST até 20/10), resto de outubro com o 2º turno (25/10) a GIRO_2T_ELEICAO, nov-dez no giro do cenário.
  Participação da pessoa física no à vista e derivativos de ações: PF_PART (média jan-ago/26) → ADTV PF.
Saída: data/b3_adtv_premissa.csv."""
import os, json
import pandas as pd, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, "data")
IBOV_FIM = {"2026Q3": 186340.0, "2026Q4": 208581.0}      # XPMod, MOD linha "IBOV"
G_IBOV = 0.08                                            # crescimento nominal do Ibovespa a partir de 2027 (lucro nominal, sem rerating)
GIRO = {"pessimista": 1.25, "base": 1.40}
ELAST_SELIC, GIRO_TETO = 0.045, 1.70
GIRO_2T_ELEICAO = 2.0                                     # pregões restantes de outubro (2º turno em 25/10)
PREG = {"2026Q4": 62, 2026: 247, 2027: 249, 2028: 248, 2029: 250, 2030: 250, 2031: 250, 2032: 250}   # XPMod linha "Dias Úteis"
R = pd.read_csv(os.path.join(D, "b3_adtv_mensal.csv"), index_col=0)
RAZAO = float((R.mcap_bi / R.ibov).loc["2026-03":"2026-08"].mean())          # R$ bi de valor de mercado por ponto do Ibovespa
PF_PART = float(R.pf_part.loc["2026-01":"2026-08"].mean())
m = json.load(open(os.path.join(HERE, "..", "monitor-investimentos", "data", "macro.json"), encoding="utf-8"))
top5 = {l["DataReferencia"]: l["Mediana"] for l in m["focus_top5"]["linhas"] if l["Indicador"] == "Selic"}
focus = {int(a): v[-1][1] for a, v in m["focus"]["Selic"].items() if int(a) >= 2026}
SELIC_FIM = {a: focus.get(a, float(top5.get(str(a), np.nan))) for a in range(2026, 2033)}
SELIC_FIM = {a: (v if pd.notna(v) else SELIC_FIM.get(a - 1)) for a, v in SELIC_FIM.items()}
for a in range(2027, 2033):
    if pd.isna(SELIC_FIM[a]): SELIC_FIM[a] = SELIC_FIM[a - 1]
selic_med = {a: (SELIC_FIM[a - 1] + SELIC_FIM[a]) / 2 if a > 2026 else 14.3 for a in range(2026, 2033)}

def giro(cen, ano):
    if cen in GIRO: return GIRO[cen]
    return min(GIRO_TETO, GIRO["base"] + ELAST_SELIC * max(0.0, 14.0 - selic_med[ano]))

# ---- 4T26: outubro observado + resto
out = R.loc["2026-10"]; n_obs = int(out.pregoes); giro_obs = float(out.giro_anual)
ibov_4t = (float(out.ibov) * 1 + IBOV_FIM["2026Q4"] * 2) / 3            # out observado, nov-dez no fim de ano do modelo
linhas = []
for cen in ("pessimista", "base", "otimista"):
    g4 = (n_obs * giro_obs + (22 - n_obs) * GIRO_2T_ELEICAO + 40 * giro(cen, 2026)) / PREG["2026Q4"]
    mc4 = ibov_4t * RAZAO
    linhas.append({"periodo": "4T26", "cenario": cen, "ibov_medio": ibov_4t, "mcap_bi": mc4, "giro": g4, "selic_media": 14.0,
                   "adtv_bi": mc4 * g4 / 252, "pf_part": PF_PART})
    # ano de 2026 = jan-set observado (média ponderada por pregões) + 4T26
    obs = R.loc["2026-01":"2026-09"]
    adtv26 = ((obs.adtv_avista * obs.pregoes).sum() / 1e9 + mc4 * g4 / 252 * PREG["2026Q4"]) / (obs.pregoes.sum() + PREG["2026Q4"])
    linhas.append({"periodo": "2026", "cenario": cen, "ibov_medio": float(R.ibov.loc["2026-01":"2026-10"].mean()), "mcap_bi": np.nan,
                   "giro": np.nan, "selic_media": selic_med[2026], "adtv_bi": adtv26, "pf_part": PF_PART})
    fim = IBOV_FIM["2026Q4"]
    for a in range(2027, 2033):
        ib = fim * (1 + G_IBOV) ** 0.5; fim *= (1 + G_IBOV)
        gi = giro(cen, a); mc = ib * RAZAO
        linhas.append({"periodo": str(a), "cenario": cen, "ibov_medio": ib, "mcap_bi": mc, "giro": gi, "selic_media": selic_med[a],
                       "adtv_bi": mc * gi / 252, "pf_part": PF_PART})
P = pd.DataFrame(linhas); P["adtv_pf_bi"] = P.adtv_bi * P.pf_part
P.round(4).to_csv(os.path.join(D, "b3_adtv_premissa.csv"), index=False)
# histórico anual para comparação
R["ano"] = R.index.str[:4]
H = R.loc["2018-01":"2025-12"].groupby("ano").apply(lambda g: pd.Series({"adtv_bi": (g.adtv_avista * g.pregoes).sum() / g.pregoes.sum() / 1e9,
                                                                         "giro": (g.giro_anual * g.pregoes).sum() / g.pregoes.sum(), "pf": g.pf_part.mean()}))
print("razão valor de mercado/Ibov:", round(RAZAO * 1000, 2), "R$ bi por mil pontos | PF:", round(PF_PART, 3), "| Selic fim de ano (Focus):", SELIC_FIM)
print("outubro observado:", n_obs, "pregões, giro", round(giro_obs, 2), ", ADTV", round(float(out.adtv_avista) / 1e9, 1))
print(H.round(2).T.to_string())
print(P.pivot(index="periodo", columns="cenario", values="adtv_bi").loc[["4T26", "2026"] + [str(a) for a in range(2027, 2033)], ["pessimista", "base", "otimista"]].round(1).to_string())
print(P[P.cenario == "otimista"].set_index("periodo")[["selic_media", "giro"]].round(2).T.to_string())
