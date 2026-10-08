"""Composição da carteira (CDA) dos fundos de tesouraria da XP em meses escolhidos. Baixa cda_fi_AAAAMM.zip (~100-200 MB),
filtra os CNPJs de data/xp_tesouraria_fundos.csv em todos os blocos e grava data/xp_tesouraria_cda_<mes>.csv."""
import os, sys, zipfile, urllib.request, pandas as pd
HERE=os.path.dirname(os.path.abspath(__file__)); TMP=HERE+"/fontes/setor/cvm/_tmp"; os.makedirs(TMP,exist_ok=True)
cnpjs=set(pd.read_csv(HERE+"/data/xp_tesouraria_fundos.csv").CNPJ_FUNDO)
for mes in sys.argv[1:]:
    z=f"{TMP}/cda_fi_{mes}.zip"
    if not os.path.exists(z): urllib.request.urlretrieve(f"https://dados.cvm.gov.br/dados/FI/DOC/CDA/DADOS/cda_fi_{mes}.zip", z)
    out=[]
    with zipfile.ZipFile(z) as zf:
        for n in zf.namelist():
            if not n.endswith(".csv"): continue
            df=pd.read_csv(zf.open(n),sep=";",encoding="latin-1",low_memory=False,quoting=3,on_bad_lines="skip",dtype=str); df.columns=[c.replace("_CLASSE","") for c in df.columns]
            col="CNPJ_FUNDO" if "CNPJ_FUNDO" in df.columns else None
            if not col: continue
            sel=df[df[col].str.strip().isin(cnpjs)].copy(); sel["BLOCO"]=n
            if len(sel): out.append(sel)
    res=pd.concat(out,ignore_index=True); res.to_csv(f"{HERE}/data/xp_tesouraria_cda_{mes}.csv",index=False); print(mes,len(res),"linhas",flush=True)
    os.remove(z)
print("FIM")
