# -*- coding: utf-8 -*-
"""Pipeline de IPOs: companhias com registro CVM categoria A ativo (pode emitir ações) cujas ações NÃO são negociadas na B3.
Critério de "listada": algum código de negociação de ação/unit/certificado do FCA (2023-2026) negociado no COTAHIST de 2026 — o FCA
sozinho erra (empresas preenchem 'Data_Fim_Negociacao' com a data de início ou deixam 'Mercado' vazio).
Fontes: CVM dados abertos (cad_cia_aberta.csv; fca_cia_aberta_AAAA.zip, valor mobiliário), B3 COTAHIST 2026.
Saída: data/cvm_pipeline_ipo.csv."""
import os, io, ssl, zipfile, urllib.request, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, "fontes", "setor", "cvm", "pipeline")
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
def zipfca(a):
    p = os.path.join(D, f"fca_cia_aberta_{a}.zip")
    if not os.path.exists(p):
        open(p, "wb").write(urllib.request.urlopen(urllib.request.Request(f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/fca_cia_aberta_{a}.zip", headers={"User-Agent": "Mozilla/5.0"}), timeout=300, context=ctx).read())
    return zipfile.ZipFile(p)
c = pd.read_csv(os.path.join(D, "cad_cia_aberta.csv"), sep=";", encoding="latin1", dtype=str)
A = c[(c.SIT == "ATIVO") & (c.CATEG_REG == "Categoria A")].drop_duplicates("CNPJ_CIA").copy()
V = pd.concat([pd.read_csv(zipfca(a).open(f"fca_cia_aberta_valor_mobiliario_{a}.csv"), sep=";", encoding="latin1", dtype=str) for a in range(2023, 2027)])
acoes = V[V.Valor_Mobiliario.str.contains("Ações|Units|Certificado", case=False, na=False) & V.Codigo_Negociacao.notna()]
z = zipfile.ZipFile(os.path.join(HERE, "fontes", "setor", "b3", "cotahist_raw", "COTAHIST_A2026.ZIP"))
neg = {ln[12:24].strip() for ln in io.TextIOWrapper(z.open(z.namelist()[0]), encoding="latin1") if ln[:2] == "01" and ln[24:27] in ("010", "020")}
acoes = acoes.assign(neg=acoes.Codigo_Negociacao.str.strip().str.upper().isin(neg))
listadas = set(acoes[acoes.neg].CNPJ_Companhia)
cod = acoes.groupby("CNPJ_Companhia").Codigo_Negociacao.agg(lambda s: ",".join(sorted(set(s.str.strip()))))
A["listada_b3"] = A.CNPJ_CIA.isin(listadas); A["codigos_fca"] = A.CNPJ_CIA.map(cod)
A["DT_REG"] = pd.to_datetime(A.DT_REG, errors="coerce"); A["DT_INI_CATEG"] = pd.to_datetime(A.DT_INI_CATEG, errors="coerce")
P = A[~A.listada_b3].sort_values("DT_REG", ascending=False)
P[["CNPJ_CIA", "DENOM_SOCIAL", "DT_REG", "DT_INI_CATEG", "SETOR_ATIV", "SIT_EMISSOR", "CONTROLE_ACIONARIO", "codigos_fca", "UF"]].to_csv(os.path.join(HERE, "data", "cvm_pipeline_ipo.csv"), index=False, encoding="utf-8")
print("Categoria A ativas:", len(A), "| ações negociadas em 2026:", int(A.listada_b3.sum()), "| sem ações negociadas:", len(P))
print("registro desde 2019:", int((P.DT_REG >= "2019-01-01").sum()), "| operacionais, fora de recuperação:", int(((P.DT_REG >= "2019-01-01") & (P.SIT_EMISSOR == "FASE OPERACIONAL")).sum()))
print(P.DT_REG.dt.year.value_counts().sort_index().to_dict())
