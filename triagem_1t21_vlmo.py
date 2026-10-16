# -*- coding: utf-8 -*-
"""Triagem do evento extraordinário de R$ 26 bi no 1T21: grupos controladores (CVM VLMO) que operam via XP e cujo bloco
valia R$ 10-60 bi em 31/03/21. Preço: COTAHIST 2021 (ação mais líquida do emissor, casada pelo nome). Saída: data/triagem_1t21_controladores.csv."""
import os, re, zipfile, io, unicodedata, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(HERE, "..", "cvm-insider-monitor", "data")
def norm(s): return re.sub(r"[^A-Z0-9 ]", "", unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper())
fr = []
for a in (2020, 2021, 2022):
    z = zipfile.ZipFile(os.path.join(SRC, f"vlmo_{a}.zip")); n = [x for x in z.namelist() if "_con_" in x][0]
    df = pd.read_csv(z.open(n), sep=";", encoding="latin1", dtype=str); df["Versao"] = df.Versao.astype(int)
    df = df[df.Versao == df.groupby(["CNPJ_Companhia", "Data_Referencia"]).Versao.transform("max")]
    fr.append(df[df.Tipo_Cargo == "Controlador ou Vinculado"])
V = pd.concat(fr); V["Quantidade"] = pd.to_numeric(V.Quantidade, errors="coerce")
mov = V[(V.Tipo_Movimentacao != "Saldo Inicial") & V.Intermediario.notna()]
mov = mov.assign(xp=mov.Intermediario.str.upper().str.contains(r"\bXP\b|XP INV|XPINV|XP CORR|RICO|CLEAR", regex=True))
I = mov.groupby("CNPJ_Companhia").agg(n_mov=("xp", "size"), n_xp=("xp", "sum"))
S = V[(V.Tipo_Movimentacao == "Saldo Inicial") & V.Tipo_Ativo.str.startswith("A")]
def saldo(d): return S[S.Data_Referencia == d].groupby(["CNPJ_Companhia", "Nome_Companhia", "Caracteristica_Valor_Mobiliario"]).Quantidade.sum()
B = pd.concat({"jan21": saldo("2021-01-01"), "abr21": saldo("2021-04-01")}, axis=1).reset_index()
# preços de 31/03/21 e 31/12/20 (lote padrão, mercado à vista)
px = {}
for a, d in ((2020, "20201230"), (2021, "20210331")):
    z = zipfile.ZipFile(os.path.join(HERE, "fontes", "setor", "b3", "cotahist_raw", f"COTAHIST_A{a}.ZIP"))
    for ln in io.TextIOWrapper(z.open(z.namelist()[0]), encoding="latin1"):
        if ln[:2] == "01" and ln[2:10] == d and ln[24:27] == "010" and ln[39:41] in ("ON", "PN", "UN"):
            px.setdefault((norm(ln[27:39]).strip(), ln[39:41]), {})[d] = (int(ln[108:121]) / 100, ln[12:24].strip(), int(ln[170:188]) / 100)
P = pd.DataFrame([dict(nomres=k[0], esp=k[1], p20=v.get("20201230", (None,))[0], p21=v.get("20210331", (None,))[0], tick=list(v.values())[0][1]) for k, v in px.items()])
B["esp"] = B.Caracteristica_Valor_Mobiliario.str[:2].str.upper().replace({"UN": "UN"})
B["nm"] = B.Nome_Companhia.map(norm)
def acha(r):
    c = P[(P.esp == r.esp) & P.nomres.apply(lambda x: len(x) >= 4 and (r.nm.startswith(x.split(" ")[0]) and x.split(" ")[0] in r.nm))]
    return c.iloc[0] if len(c) else None
rows = []
for _, r in B.iterrows():
    m = acha(r)
    if m is None or pd.isna(m.p21): continue
    rows.append(dict(cnpj=r.CNPJ_Companhia, companhia=r.Nome_Companhia, esp=r.esp, ticker=m.tick, acoes_jan21_mi=r.jan21 / 1e6, acoes_abr21_mi=r.abr21 / 1e6,
                     preco_31mar21=m.p21, valor_bi=(r.abr21 if pd.notna(r.abr21) else r.jan21) * m.p21 / 1e9))
T = pd.DataFrame(rows).groupby(["cnpj", "companhia"]).agg(tickers=("ticker", ",".join), acoes_abr21_mi=("acoes_abr21_mi", "sum"), acoes_jan21_mi=("acoes_jan21_mi", "sum"), valor_bi=("valor_bi", "sum")).reset_index()
T = T.merge(I, left_on="cnpj", right_index=True, how="left").fillna({"n_mov": 0, "n_xp": 0})
T["pct_xp"] = T.n_xp / T.n_mov.where(T.n_mov > 0)
T = T.sort_values("valor_bi", ascending=False); T.to_csv(os.path.join(HERE, "data", "triagem_1t21_controladores.csv"), index=False)
pd.set_option("display.width", 250)
print(T[(T.valor_bi > 8) & (T.valor_bi < 80)].round(2).to_string(index=False))
print("\ncom operações via XP:"); print(T[T.n_xp > 0].head(40).round(2).to_string(index=False))
