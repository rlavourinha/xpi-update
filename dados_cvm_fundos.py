"""Indústria de fundos pela CVM (INF_DIARIO + cad_fi): agrega por mês o PL/cotistas de fim de mês e a captação/resgate
acumulados, por CLASSE e por GESTOR/ADMIN. Baixa cada zip (HIST anual 2005-2020, mensal 2021+), processa e apaga.
Saídas em data/: cvm_fundos_mensal_classe.csv, cvm_fundos_mensal_gestor.csv, cvm_fundos_mensal_admin.csv, cvm_fundos_mensal_total.csv"""
import io, os, sys, zipfile, urllib.request, datetime as dt
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); TMP = HERE + "/fontes/setor/cvm/_tmp"; os.makedirs(TMP, exist_ok=True)
B = "https://dados.cvm.gov.br/dados/FI/DOC/INF_DIARIO/DADOS"
cad = pd.read_csv(HERE + "/fontes/setor/cvm/cad_fi.csv", sep=";", encoding="latin-1", low_memory=False,
                  usecols=["CNPJ_FUNDO", "TP_FUNDO", "CLASSE", "ADMIN", "GESTOR", "DENOM_SOCIAL", "SIT", "FUNDO_COTAS", "FUNDO_EXCLUSIVO", "PUBLICO_ALVO"])
cad = cad.drop_duplicates("CNPJ_FUNDO", keep="last").set_index("CNPJ_FUNDO")
print("cad_fi:", len(cad), "fundos", flush=True)
def periodos():
    for y in range(2005, 2021): yield f"HIST/inf_diario_fi_{y}.zip"
    hoje = dt.date.today()
    for y in range(2021, hoje.year + 1):
        for m in range(1, 13):
            if (y, m) > (hoje.year, hoje.month): break
            yield f"inf_diario_fi_{y}{m:02d}.zip"
def processa(zpath):
    out = []
    with zipfile.ZipFile(zpath) as z:
        for n in z.namelist():
            if not n.lower().endswith(".csv"): continue
            df = pd.read_csv(z.open(n), sep=";", encoding="latin-1", low_memory=False)
            df.columns = [c.replace("_CLASSE", "") for c in df.columns]
            keep = [c for c in ["CNPJ_FUNDO", "DT_COMPTC", "VL_PATRIM_LIQ", "CAPTC_DIA", "RESG_DIA", "NR_COTST"] if c in df.columns]
            df = df[keep].copy(); df["DT_COMPTC"] = pd.to_datetime(df["DT_COMPTC"]); df["mes"] = df["DT_COMPTC"].dt.to_period("M")
            df = df.sort_values(["CNPJ_FUNDO", "DT_COMPTC"])
            g = df.groupby(["CNPJ_FUNDO", "mes"], sort=False)
            fim = g[["VL_PATRIM_LIQ", "NR_COTST"]].last(); flx = g[["CAPTC_DIA", "RESG_DIA"]].sum()
            out.append(fim.join(flx).reset_index())
    return pd.concat(out) if out else None
acc = []
for p in periodos():
    dest = f"{TMP}/{os.path.basename(p)}"
    try:
        if not os.path.exists(dest): urllib.request.urlretrieve(f"{B}/{p}", dest)
        m = processa(dest); os.remove(dest)
        if m is None: continue
        m = m.join(cad[["CLASSE", "GESTOR", "ADMIN", "TP_FUNDO"]], on="CNPJ_FUNDO")
        acc.append(m); print(p, len(m), "fundo-meses", flush=True)
    except Exception as e: print("ERRO", p, e, flush=True)
df = pd.concat(acc); df["mes"] = df["mes"].astype(str)
df.drop(columns=["CLASSE","GESTOR","ADMIN","TP_FUNDO"]).to_csv(HERE + "/data/_cvm_fundos_painel.csv.gz", index=False, compression="gzip")
print("painel salvo", len(df), flush=True)
agg = {"VL_PATRIM_LIQ": "sum", "NR_COTST": "sum", "CAPTC_DIA": "sum", "RESG_DIA": "sum", "CNPJ_FUNDO": "count"}
ren = {"VL_PATRIM_LIQ": "pl", "NR_COTST": "cotistas", "CAPTC_DIA": "captacao", "RESG_DIA": "resgate", "CNPJ_FUNDO": "n_fundos"}
df.groupby("mes").agg(agg).rename(columns=ren).to_csv(HERE + "/data/cvm_fundos_mensal_total.csv")
df.groupby(["mes", "CLASSE"]).agg(agg).rename(columns=ren).to_csv(HERE + "/data/cvm_fundos_mensal_classe.csv")
df.groupby(["mes", "TP_FUNDO"]).agg(agg).rename(columns=ren).to_csv(HERE + "/data/cvm_fundos_mensal_tipo.csv")
for col, nome in [("GESTOR", "gestor"), ("ADMIN", "admin")]:
    g = df.groupby(["mes", col]).agg(agg).rename(columns=ren).reset_index()
    ult = g[g.mes == g.mes.max()].nlargest(80, "pl")[col]
    g[g[col].isin(ult)].to_csv(HERE + f"/data/cvm_fundos_mensal_{nome}.csv", index=False)
print("FIM", flush=True)
