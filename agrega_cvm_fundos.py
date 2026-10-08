"""Junta o painel fundo-mês (data/_cvm_fundos_painel.csv.gz, de dados_cvm_fundos.py) aos cadastros da CVM e agrega.
Cadastros: registro_fundo_classe.zip (regime CVM 175: classe → fundo, Classificacao, Classificacao_Anbima, gestor, admin),
cad_fi.csv (regime antigo: CLASSE, GESTOR, ADMIN, FUNDO_COTAS), cad_fi_hist.zip (classe/fic por período).
Saídas em data/: cvm_fundos_mensal_{total,classe,gestor,admin,fic}.csv"""
import os, re, zipfile, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); CVM = HERE + "/fontes/setor/cvm"
dig = lambda s: s.astype(str).str.replace(r"\D", "", regex=True).str.zfill(14)
def mapa():
    z = zipfile.ZipFile(CVM + "/registro_fundo_classe.zip")
    rf = pd.read_csv(z.open("registro_fundo.csv"), sep=";", encoding="latin-1", low_memory=False)
    rc = pd.read_csv(z.open("registro_classe.csv"), sep=";", encoding="latin-1", low_memory=False)
    rf["k"] = dig(rf.CNPJ_Fundo); rc["k"] = dig(rc.CNPJ_Classe)
    rc = rc.merge(rf[["ID_Registro_Fundo", "Administrador", "Gestor", "Tipo_Fundo"]], on="ID_Registro_Fundo", how="left")
    novo = pd.DataFrame({"k": rc.k, "classe": rc.Classificacao, "classe_anbima": rc.Classificacao_Anbima, "tipo": rc.Tipo_Classe,
                         "gestor": rc.Gestor, "admin": rc.Administrador, "fic": rc.Classe_Cotas.eq("S"),
                         "exclusivo": rc.Exclusivo, "publico": rc.Publico_Alvo}).drop_duplicates("k")
    fund = pd.DataFrame({"k": rf.k, "classe": None, "classe_anbima": None, "tipo": rf.Tipo_Fundo, "gestor": rf.Gestor, "admin": rf.Administrador, "fic": None, "exclusivo": None, "publico": None}).drop_duplicates("k")
    cad = pd.read_csv(CVM + "/cad_fi.csv", sep=";", encoding="latin-1", low_memory=False)
    cad["k"] = dig(cad.CNPJ_FUNDO)
    velho = pd.DataFrame({"k": cad.k, "classe": cad.CLASSE, "classe_anbima": cad.CLASSE_ANBIMA, "tipo": cad.TP_FUNDO, "gestor": cad.GESTOR, "admin": cad.ADMIN,
                          "fic": cad.FUNDO_COTAS.eq("S"), "exclusivo": cad.FUNDO_EXCLUSIVO, "publico": cad.PUBLICO_ALVO}).drop_duplicates("k", keep="last")
    m = pd.concat([novo, velho, fund]).groupby("k").first()  # prioridade: registro de classe (175) > cad_fi > registro de fundo
    # classes do regime antigo (cad_fi) usam rótulos 'Fundo de Renda Fixa' etc.; novas usam 'Renda Fixa' etc. — normaliza
    m["classe_n"] = m.classe.astype(str).str.replace(r"^Fundo (de )?", "", regex=True).str.replace("FIC ", "").str.strip()
    m["classe_n"] = m.classe_n.replace({"nan": "Sem classe", "None": "Sem classe", "Curto Prazo": "Renda Fixa", "Referenciado": "Renda Fixa", "Dívida Externa": "Renda Fixa"})
    return m
if __name__ == "__main__":
    m = mapa(); print("mapa:", len(m), "cnpjs;", m.classe_n.value_counts().head(12).to_dict())
    p = pd.read_csv(HERE + "/data/_cvm_fundos_painel.csv.gz"); p["k"] = dig(p.CNPJ_FUNDO)
    p = p.join(m, on="k"); print("match classe:", p.classe_n.notna().mean().round(3), "| gestor:", p.gestor.notna().mean().round(3))
    agg = {"VL_PATRIM_LIQ": "sum", "NR_COTST": "sum", "CAPTC_DIA": "sum", "RESG_DIA": "sum", "CNPJ_FUNDO": "count"}
    ren = {"VL_PATRIM_LIQ": "pl", "NR_COTST": "cotistas", "CAPTC_DIA": "captacao", "RESG_DIA": "resgate", "CNPJ_FUNDO": "n_fundos"}
    p["fic"] = p.fic.fillna(False).astype(bool)
    p.groupby("mes").agg(agg).rename(columns=ren).to_csv(HERE + "/data/cvm_fundos_mensal_total.csv")
    p.groupby(["mes", "fic"]).agg(agg).rename(columns=ren).to_csv(HERE + "/data/cvm_fundos_mensal_fic.csv")
    p.groupby(["mes", "classe_n"]).agg(agg).rename(columns=ren).to_csv(HERE + "/data/cvm_fundos_mensal_classe.csv")
    p[~p.fic].groupby(["mes", "classe_n"]).agg(agg).rename(columns=ren).to_csv(HERE + "/data/cvm_fundos_mensal_classe_exfic.csv")
    for col in ["gestor", "admin"]:
        g = p[~p.fic].groupby(["mes", col]).agg(agg).rename(columns=ren).reset_index()
        top = g[g.mes == g.mes.max()].nlargest(100, "pl")[col]
        g[g[col].isin(top)].to_csv(HERE + f"/data/cvm_fundos_mensal_{col}.csv", index=False)
    xpg = p[~p.fic & p.gestor.astype(str).str.contains(r"\bXP ")].groupby("mes").agg(agg).rename(columns=ren).add_prefix("gestor_")
    xpa = p[~p.fic & p.admin.astype(str).str.contains(r"\bXP ")].groupby("mes").agg(agg).rename(columns=ren).add_prefix("admin_")
    xpg.join(xpa, how="outer").to_csv(HERE + "/data/cvm_fundos_mensal_xp.csv")
    print("FIM")
