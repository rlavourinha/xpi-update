"""Cota e PL diários dos fundos geridos pela XP Investimentos CCTVM (tesouraria), a partir dos informes diários da CVM.
Lê a lista em data/xp_tesouraria_fundos.csv, baixa os zips mensais (2019+; HIST p/ 2019-2020), filtra e grava data/xp_tesouraria_diario.csv.
Também baixa o CDI diário (BCB SGS 12) para data/cdi_diario.csv."""
import os, io, zipfile, urllib.request, datetime as dt, pandas as pd, json
HERE=os.path.dirname(os.path.abspath(__file__)); TMP=HERE+"/fontes/setor/cvm/_tmp"; os.makedirs(TMP,exist_ok=True)
B="https://dados.cvm.gov.br/dados/FI/DOC/INF_DIARIO/DADOS"
cnpjs=set(pd.read_csv(HERE+"/data/xp_tesouraria_fundos.csv").CNPJ_FUNDO)
def per():
    for y in (2019,2020): yield f"HIST/inf_diario_fi_{y}.zip"
    h=dt.date.today()
    for y in range(2021,h.year+1):
        for m in range(1,13):
            if (y,m)>(h.year,h.month): break
            yield f"inf_diario_fi_{y}{m:02d}.zip"
out=[]
for p in per():
    d=f"{TMP}/{os.path.basename(p)}"
    try:
        if not os.path.exists(d): urllib.request.urlretrieve(f"{B}/{p}",d)
        with zipfile.ZipFile(d) as z:
            for n in z.namelist():
                if not n.lower().endswith(".csv"): continue
                df=pd.read_csv(z.open(n),sep=";",encoding="latin-1",low_memory=False); df.columns=[c.replace("_CLASSE","") for c in df.columns]
                out.append(df[df.CNPJ_FUNDO.isin(cnpjs)])
        os.remove(d); print(p,sum(len(x) for x in out),flush=True)
    except Exception as e: print("ERRO",p,e,flush=True)
res=pd.concat(out).sort_values(["CNPJ_FUNDO","DT_COMPTC"]); res.to_csv(HERE+"/data/xp_tesouraria_diario.csv",index=False)
print("gravado",len(res),flush=True)
cdi=json.load(urllib.request.urlopen("https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=json&dataInicial=01/01/2018"))
pd.DataFrame(cdi).to_csv(HERE+"/data/cdi_diario.csv",index=False); print("cdi ok",len(cdi))
