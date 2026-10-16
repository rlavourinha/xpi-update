# -*- coding: utf-8 -*-
"""Fechamento diário de MGLU3 e AMBP3 (B3, COTAHIST anual, mercado à vista). Saída: data/precos_mglu_ambp_diario.csv."""
import os, zipfile, io, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, "fontes", "setor", "b3", "cotahist_raw")
rows = []
for a in range(2019, 2027):
    z = zipfile.ZipFile(os.path.join(RAW, f"COTAHIST_A{a}.ZIP"))
    for ln in io.TextIOWrapper(z.open(z.namelist()[0]), encoding="latin1"):
        if ln[:2] == "01" and ln[24:27] == "010" and ln[12:24].strip() in ("MGLU3", "AMBP3"):
            rows.append(dict(data=pd.Timestamp(ln[2:10]), ticker=ln[12:24].strip(), fech=int(ln[108:121]) / 100, fatcot=int(ln[210:217])))
P = pd.DataFrame(rows).pivot(index="data", columns="ticker", values="fech").sort_index()
P.to_csv(os.path.join(HERE, "data", "precos_mglu_ambp_diario.csv")); print(P.resample("QE").last().to_string())
