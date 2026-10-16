# -*- coding: utf-8 -*-
"""Posição mensal do grupo controlador de Magazine Luiza e Ambipar (CVM, VLMO consolidado) e movimentações com intermediário.
Fonte: ../cvm-insider-monitor/data/vlmo_AAAA.zip (dados abertos CVM). Saída: data/vlmo_controladores_mglu_ambp.csv e _mov.csv."""
import os, zipfile, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(HERE, "..", "cvm-insider-monitor", "data")
ALVO = r"MAGAZINE LUIZA|AMBIPAR"
out = []
for a in range(2018, 2027):
    z = zipfile.ZipFile(os.path.join(SRC, f"vlmo_{a}.zip"))
    n = [x for x in z.namelist() if "_con_" in x][0]
    df = pd.read_csv(z.open(n), sep=";", encoding="latin1", dtype=str)
    df = df[df.Nome_Companhia.str.contains(ALVO, case=False, na=False)]
    out.append(df)
X = pd.concat(out)
X["Versao"] = X.Versao.astype(int); X["Quantidade"] = pd.to_numeric(X.Quantidade, errors="coerce")
X = X[X.Versao == X.groupby(["CNPJ_Companhia", "Data_Referencia"]).Versao.transform("max")]
X.to_csv(os.path.join(HERE, "data", "vlmo_mglu_ambp_bruto.csv"), index=False)
print(X.Nome_Companhia.unique(), X.Tipo_Cargo.unique(), X.Tipo_Movimentacao.unique()[:40], X.Tipo_Ativo.unique())
