# -*- coding: utf-8 -*-
"""ADTV do mercado à vista da B3, mensal desde 2000, com os componentes para projetar: valor de mercado médio, giro anualizado
(ADTV × pregões no ano ÷ valor de mercado), abertura por produto (ações, ETF, BDR, fundos listados), participação por investidor,
co-location, Selic e Ibovespa.
Fontes: B3 RI, planilha "Dados operacionais" (fontes/setor/b3/ri/B3_dados_operacionais_trimestrais.xlsx, aba Renda Variável &
Empréstimo, mensal até o último mês publicado); meses seguintes pelo COTAHIST (soma do VOLTOT do mercado à vista, lote padrão e
fracionário, ÷ pregões do mês), calibrado pela razão RI/COTAHIST dos 12 meses anteriores; Selic (BCB SGS 4189, meta anualizada
mensal) e Ibovespa (série do screening, monitor-investimentos/data/macro.json).
Saída: data/b3_adtv_mensal.csv."""
import os, io, json, zipfile, urllib.request
import pandas as pd, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, "data")
V = pd.read_excel(os.path.join(HERE, "fontes", "setor", "b3", "ri", "B3_dados_operacionais_trimestrais.xlsx"), sheet_name="Renda Variável & Empréstimo", header=None)
def linha(i, cab=9):
    datas = pd.to_datetime(V.iloc[cab, 1:], errors="coerce")
    s = pd.Series(pd.to_numeric(V.iloc[i, 1:], errors="coerce").values, index=datas)
    return s[s.index.notna()].groupby(level=0).last()
RI = pd.DataFrame({"adtv_avista": linha(10), "adtv_acoes": linha(18, 17), "adtv_etf": linha(19, 17), "adtv_bdr": linha(20, 17),
                   "adtv_fundos": linha(21, 17), "mcap_bi": linha(67, 66), "n_empresas": linha(68, 66), "pf_part": linha(57, 56),
                   "inst_part": linha(58, 56), "estr_part": linha(59, 56), "emp_part": linha(60, 56), "ifin_part": linha(61, 56), "coloc_part": linha(74, 72)})
RI.index = RI.index.to_period("M")
RI.loc[:, ["adtv_acoes", "adtv_etf", "adtv_bdr", "adtv_fundos"]] = RI[["adtv_acoes", "adtv_etf", "adtv_bdr", "adtv_fundos"]].replace(0, np.nan)
# ---- COTAHIST: volume do mercado à vista por mês e pregões
rows = []
for a in range(2019, 2027):
    z = zipfile.ZipFile(os.path.join(HERE, "fontes", "setor", "b3", "cotahist_raw", f"COTAHIST_A{a}.ZIP"))
    for ln in io.TextIOWrapper(z.open(z.namelist()[0]), encoding="latin1"):
        if ln[:2] == "01" and ln[24:27] in ("010", "020"):
            rows.append((ln[2:10], int(ln[170:188]) / 100))
C = pd.DataFrame(rows, columns=["d", "vol"]); C["d"] = pd.to_datetime(C.d)
dia = C.groupby("d").vol.sum()
# pregões depois do último COTAHIST: BDI diário (data/b3_bdi_diario.csv, à vista em R$ mil) × razão COTAHIST/BDI dos dias comuns
B = pd.read_csv(os.path.join(D, "b3_bdi_diario.csv"), parse_dates=["data"]).set_index("data").avista_vol_mil * 1e3
comum = dia.index.intersection(B.index)
K_BDI = float((dia[comum] / B[comum]).mean()) if len(comum) else np.nan
extra = B[B.index > dia.index.max()] * K_BDI
dia = pd.concat([dia, extra])
M = pd.DataFrame({"vol": dia.groupby(dia.index.to_period("M")).sum(), "pregoes": dia.groupby(dia.index.to_period("M")).size()})
M["adtv_cotahist"] = M.vol / M.pregoes
R = RI.join(M[["adtv_cotahist", "pregoes"]], how="outer")
ult_ri = RI.adtv_avista.dropna().index.max()
k = (R.adtv_avista / R.adtv_cotahist).loc[ult_ri - 11:ult_ri]
R["fonte_adtv"] = np.where(R.adtv_avista.notna(), "B3 RI", None)
fut = R.adtv_avista.isna() & R.adtv_cotahist.notna()          # meses depois do RI e buracos do RI (nov/24)
R.loc[fut, "adtv_avista"] = R.loc[fut, "adtv_cotahist"] * k.mean(); R.loc[fut & R.adtv_avista.notna(), "fonte_adtv"] = "COTAHIST/BDI calibrado"
# ---- participação por investidor dos meses depois do RI: BDI SharesInvesVolum (acumulado do mês até o último pregão coletado;
# (compras + vendas) de cada tipo ÷ (compras + vendas) totais). Set/26 bate com o RI em ~0,2 p.p. por tipo. "Outros" = empresas.
import glob, re
TIPO_BDI = {"Investidores Individuais": "pf_part", "Institucionais": "inst_part", "Investidor Estrangeiro": "estr_part", "Outros": "emp_part"}
ult_part = RI.pf_part.dropna().index.max()
R["fonte_part"] = np.where(R.pf_part.notna(), "B3 RI", None); R["part_ate"] = None
ult_dia = {}
for f in sorted(glob.glob(os.path.join(HERE, "fontes", "setor", "b3", "bdi", "raw", "SharesInvesVolum_*.json"))):
    d = pd.Timestamp(re.search(r"(\d{4}-\d{2}-\d{2})", f).group(1)); ult_dia[d.to_period("M")] = (d, f)
for mes, (d, f) in ult_dia.items():
    if mes <= ult_part or mes not in R.index:
        continue
    vals = json.load(open(f, encoding="utf-8")).get("values") or []
    tot = sum(v[1] + v[3] for v in vals)
    if not tot:
        continue
    for v in vals:
        col = "ifin_part" if v[0].startswith("Institui") else TIPO_BDI.get(v[0])
        if col: R.loc[mes, col] = (v[1] + v[3]) / tot
    R.loc[mes, "fonte_part"] = "BDI acumulado do mês"; R.loc[mes, "part_ate"] = d.date().isoformat()
# ---- Selic meta (SGS 4189, taxa anualizada do mês) e Ibovespa
try:
    s = json.loads(urllib.request.urlopen(urllib.request.Request("https://api.bcb.gov.br/dados/serie/bcdata.sgs.4189/dados?formato=json&dataInicial=01/01/2000", headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}), timeout=60).read())
    sel = pd.Series({pd.Timestamp(x["data"][6:] + "-" + x["data"][3:5] + "-" + x["data"][:2]): float(x["valor"]) for x in s})
    R["selic"] = sel.groupby(sel.index.to_period("M")).mean()
except Exception as e:
    print("Selic falhou:", e)
ib = pd.Series({pd.Timestamp(d): v for d, v in json.load(open(os.path.join(HERE, "..", "monitor-investimentos", "data", "macro.json"), encoding="utf-8"))["hist"]["Ibovespa"]}).sort_index()
R["ibov"] = ib.groupby(ib.index.to_period("M")).mean()
# ---- valor de mercado dos meses sem RI: último valor × variação do Ibovespa médio (razão valor de mercado/Ibov dos 6 meses anteriores)
razao = (R.mcap_bi / R.ibov).loc[ult_ri - 5:ult_ri].mean()
R["mcap_estimado"] = R.mcap_bi.isna() & R.ibov.notna() & (R.index > ult_ri)
R.loc[R.mcap_estimado, "mcap_bi"] = R.loc[R.mcap_estimado, "ibov"] * razao
# ---- giro anualizado (252 pregões) sobre o valor de mercado médio do mês
R["giro_anual"] = R.adtv_avista * 252 / (R.mcap_bi * 1e9)
R = R.loc["2000-01":]
R.index = R.index.astype(str); R.index.name = "mes"
R.round(6).to_csv(os.path.join(D, "b3_adtv_mensal.csv"))
print("último RI:", ult_ri, "| calibração RI/COTAHIST 12m:", round(k.mean(), 3), "dp", round(k.std(), 3), "| COTAHIST/BDI:", round(K_BDI, 3), len(comum), "dias; BDI até", B.index.max().date())
print(R[["adtv_avista", "fonte_adtv", "pregoes", "mcap_bi", "giro_anual", "pf_part", "estr_part", "selic", "ibov"]].tail(6).round(3).to_string())
