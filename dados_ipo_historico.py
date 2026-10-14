# -*- coding: utf-8 -*-
"""Série de ofertas de ações no Brasil desde 1995 (IPO e follow-on) a partir dos dados abertos da CVM:
oferta_distribuicao.csv (ICVM 400/476, 1988-2023) + oferta_resolucao_160.csv (RCVM 160, 2023+), em fontes/setor/cvm/ofertas/raw/.
Uma oferta = emissor × data de registro (componentes primário e secundário e classes ON/PN somados). IPO = Oferta_Inicial 'S'.
Também: alocação por tipo de investidor (quantidade × preço) e coordenador líder. Valores reais corrigidos pelo IPCA até ago/26.
Saídas: data/cvm_ofertas_acoes.csv (uma linha por oferta), data/cvm_ipo_anual.csv."""
import os, json, re, pandas as pd, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, "fontes", "setor", "cvm", "ofertas", "raw"); DATA = os.path.join(HERE, "data")
INV = {"pf": "Pessoa_Fisica", "clube": "Clube_Investimento", "fundos": "Fundos_Investimento", "previdencia": "Entidade_Previdencia_Privada", "seguradora": "Companhia_Seguradora",
       "estrangeiro": "Investidor_Estrangeiro", "inst_consorcio": "Instit_Intermed_Partic_Consorcio_Distrib", "if_emissora": "Instit_Financ_Emissora_Partic_Consorcio",
       "demais_if": "Demais_Instit_Financ", "pj_ligada": "Demais_Pessoa_Juridica_Emissora_Partic_Consorcio", "demais_pj": "Demais_Pessoa_Juridica", "outros": "Outros"}
def num(s): return pd.to_numeric(s, errors="coerce")
def carrega():
    D = pd.read_csv(os.path.join(RAW, "oferta_distribuicao.csv"), sep=";", encoding="latin1", low_memory=False)
    D = D[D.Tipo_Ativo.str.contains(r"A[ÇC][ÕÔO]ES (ORDIN|PREF)|CERTIFICADO DE DEP[ÓO]SITO DE A", case=False, na=False, regex=True)].copy()
    D["data"] = pd.to_datetime(D.Data_Registro_Oferta, errors="coerce").fillna(pd.to_datetime(D.Data_Encerramento_Oferta, errors="coerce")).fillna(pd.to_datetime(D.Data_Abertura_Processo, errors="coerce"))
    D["valor"] = num(D.Valor_Total); D["preco"] = num(D.Preco_Unitario); D["ipo"] = D.Oferta_Inicial.eq("S")
    D["primaria"] = np.where(D.Tipo_Oferta.eq("Secundária"), 0.0, np.where(D.Tipo_Oferta.eq("Primária"), D.valor, np.nan))
    for k, c in INV.items(): D["inv_" + k] = num(D.get("Qtd_" + c)) * D.preco
    D["lider"] = D.Nome_Lider; D["rito"] = D.Rito_Oferta; D["bdr"] = D.Tipo_Ativo.str.contains("DEP", na=False)
    D["fonte"] = "CVM oferta_distribuicao"
    R = pd.read_csv(os.path.join(RAW, "oferta_resolucao_160.csv"), sep=";", encoding="latin1", low_memory=False)
    R = R[R.Valor_Mobiliario.str.contains(r"^A[çc][õo]es|Certificados de Dep", case=False, na=False, regex=True) & R.Status_Requerimento.isin(["Oferta Encerrada", "Registro Concedido"])].copy()
    R["data"] = pd.to_datetime(R.Data_Registro, errors="coerce"); R["valor"] = num(R.Valor_Total_Registrado); R["ipo"] = R.Oferta_inicial.eq("S")
    R["primaria"] = np.where(R.Tipo_Oferta.astype(str).str.contains("Secund", na=False), 0.0, np.where(R.Tipo_Oferta.astype(str).str.contains("Prim", na=False), R.valor, np.nan))
    R["preco"] = R.valor / num(R.Qtde_Total_Registrada)
    m160 = {"pf": "Pessoa_Natural", "clube": "Clube_Investimento", "fundos": "Fundos_Investimento", "previdencia": "Entidade_Previdencia_Privada", "seguradora": "Companhia_Seguradora",
            "estrangeiro": "Investidor_Estrangeiro", "inst_consorcio": "Instit_Intermed_Partic_Consorcio_Distrib", "if_emissora": "Instit_Financ_Emissora_Partic_Consorcio",
            "demais_if": "Demais_Instit_Financ", "pj_ligada": "Demais_Pessoa_Juridica_Emissora_Partic_Consorcio", "demais_pj": "Demais_Pessoa_Juridica"}
    for k, c in m160.items(): R["inv_" + k] = num(R.get("Qtde_VM_" + c)) * R.preco
    R["lider"] = R.Nome_Lider; R["rito"] = "RCVM 160 " + R.Rito_Requerimento.astype(str); R["bdr"] = R.Valor_Mobiliario.str.contains("Dep", na=False); R["fonte"] = "CVM oferta_resolucao_160"
    cols = ["data", "Nome_Emissor", "CNPJ_Emissor", "valor", "primaria", "ipo", "lider", "rito", "bdr", "fonte"] + ["inv_" + k for k in INV]
    X = pd.concat([D.reindex(columns=cols), R.reindex(columns=cols)], ignore_index=True)
    X = X[X.data.notna() & X.valor.gt(0)]
    X = X[~((X.fonte == "CVM oferta_distribuicao") & (X.data >= "2023-01-01") & X.rito.astype(str).str.contains("160"))]  # evita dupla contagem
    return X
def main():
    X = carrega(); X["emissor"] = X.Nome_Emissor.str.upper().str.replace(r"[^A-Z0-9 ]", "", regex=True).str.strip()
    X["mes"] = X.data.dt.to_period("M")
    agg = {"CNPJ_Emissor": "first", "valor": "sum", "primaria": lambda s: s.sum(min_count=1), "ipo": "max", "lider": "first", "rito": "first", "bdr": "max", "fonte": "first", "data": "min", "Nome_Emissor": "first"}
    agg.update({"inv_" + k: lambda s: s.sum(min_count=1) for k in INV})
    O = X.groupby(["emissor", "mes"]).agg(agg).reset_index().sort_values("data")
    # IPO por esforços restritos (ICVM 476): a CVM não marca Oferta_Inicial. Critério: primeira oferta de ações do CNPJ na base
    # e registro de companhia aberta (cad_cia_aberta.DT_REG) entre 400 dias antes e 30 dias depois da oferta.
    cad = pd.read_csv(os.path.join(RAW, "cad_cia_aberta.csv"), sep=";", encoding="latin1", low_memory=False)
    cad["cnpj"] = cad.CNPJ_CIA.astype(str).str.replace(r"\D", "", regex=True); reg = cad.assign(dt=pd.to_datetime(cad.DT_REG, errors="coerce")).groupby("cnpj").dt.min()
    O["cnpj"] = O.CNPJ_Emissor.astype(str).str.replace(r"\D", "", regex=True).str.replace(r"^0+$", "", regex=True)
    O["primeira"] = ~O.duplicated("cnpj") | O.cnpj.eq("") | O.cnpj.eq("nan")
    O["dt_reg"] = O.cnpj.map(reg); dd = (O.data - O.dt_reg).dt.days
    O["ipo_476"] = (~O.ipo) & O.rito.astype(str).str.contains("476") & O.primeira & dd.between(-30, 400)
    O["ipo"] = O.ipo | O.ipo_476
    O = O.drop(columns=["cnpj", "dt_reg", "primeira"])
    ipca = pd.DataFrame(json.load(open(os.path.join(DATA, "_ipca_mensal_1995.json"), encoding="utf-8")))  # BCB SGS 433
    ipca["mes"] = pd.to_datetime(ipca.data, dayfirst=True).dt.to_period("M"); ipca["idx"] = (1 + ipca.valor.astype(float) / 100).cumprod()
    idx = ipca.set_index("mes").idx; base = idx.iloc[-1]
    O["fator_real"] = base / O.data.dt.to_period("M").map(idx).fillna(base)
    O["valor_real"] = O.valor * O.fator_real
    O["ano"] = O.data.dt.year
    O.drop(columns=["emissor", "mes"]).to_csv(os.path.join(DATA, "cvm_ofertas_acoes.csv"), index=False)
    inv = ["inv_" + k for k in INV]
    def resumo(g):
        tot_inv = g[inv].sum(min_count=1).sum()
        return pd.Series({"n": len(g), "valor_bi": g.valor.sum() / 1e9, "valor_real_bi": g.valor_real.sum() / 1e9, "mediana_mi": g.valor.median() / 1e6,
                          "pct_estrangeiro": g.inv_estrangeiro.sum() / tot_inv if tot_inv else np.nan,
                          "pct_pf": (g.inv_pf.sum() + g.inv_clube.sum()) / tot_inv if tot_inv else np.nan,
                          "pct_fundos": g.inv_fundos.sum() / tot_inv if tot_inv else np.nan})
    I = O[O.ipo & ~O.bdr].groupby("ano").apply(resumo); F = O[~O.ipo & ~O.bdr].groupby("ano").apply(resumo)
    B = O[O.ipo & O.bdr].groupby("ano").agg(ipo_bdr_n=("valor", "size"), ipo_bdr_valor_bi=("valor", lambda s: s.sum() / 1e9))
    I476 = O[O.ipo_476 & ~O.bdr].groupby("ano").size().rename("ipo_n_476")
    A = I.add_prefix("ipo_").join(I476, how="outer").join(B, how="outer").join(F.add_prefix("fo_"), how="outer").loc[1995:]
    A.round(3).to_csv(os.path.join(DATA, "cvm_ipo_anual.csv"))
    pd.set_option("display.width", 250); print(A[[c for c in A.columns if "pct" not in c]].round(1).to_string())
    for ini, fim in ((2004, 2008), (2020, 2021)):
        g = O[O.ipo & ~O.bdr & O.ano.between(ini, fim)]
        print(f"\nLideres dos IPOs {ini}-{fim} ({len(g)} IPOs):", g.lider.map(banco).value_counts().head(10).to_dict())


BANCOS = [("Itau BBA", r"ITA[UÚ]"), ("BTG Pactual", r"BTG|PACTUAL"), ("UBS", r"\bUBS\b"), ("Credit Suisse", r"CREDIT SUISSE|CSFB"), ("Bradesco BBI", r"BRADESCO"),
          ("Santander", r"SANTANDER|\bREAL\b|ABN"), ("Morgan Stanley", r"MORGAN STANLEY"), ("JP Morgan", r"J\.?\s?P\.? ?MORGAN"), ("Goldman Sachs", r"GOLDMAN"),
          ("Merrill/BofA", r"MERRILL|BOFA|BANK OF AMERICA"), ("Citi", r"CITI"), ("XP", r"\bXP\b"), ("BB", r"BANCO DO BRASIL|\bBB\b"), ("Safra", r"SAFRA"), ("HSBC", r"HSBC"), ("Votorantim", r"VOTORANTIM")]
def banco(x):
    x = str(x).upper()
    for n, pat in BANCOS:
        if re.search(pat, x): return n
    return "sem dado" if x in ("NAN", "") else x.title()[:30]
if __name__ == "__main__": main()
