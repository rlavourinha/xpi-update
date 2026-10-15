# -*- coding: utf-8 -*-
"""Operações de M&A envolvendo companhias brasileiras com documentos na SEC (EDGAR full-text search, 2001+).
Busca 1: formulários de M&A de filers com sede no Brasil (locationCodes=D5).
Busca 2: mesmos formulários, sem filtro de sede, com o texto "Brazil" e "financial advisor" (pega Cayman com operação no Brasil e compradores estrangeiros).
Saídas: fontes/sec_ma/_efts_hits.csv (um registro por documento) e data/sec_ma_brasil_universo.csv (um registro por filer × formulário-base × ano)."""
import os, json, time, urllib.request, urllib.parse, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "fontes", "sec_ma"); os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "Rafael Lavourinha rafael2102@gmail.com"}
FORMS = "F-4,SC 13E3,SC 14D9,SC TO-T,SC TO-I,DEFM14A,PREM14A,DEFM14C,S-4"
def efts(params, frm=0):
    u = "https://efts.sec.gov/LATEST/search-index?" + urllib.parse.urlencode({**params, "from": frm})
    for t in range(4):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=90))
        except Exception as e: time.sleep(3 * (t + 1)); err = e
    raise err
def coleta(params, rotulo):
    rows, frm = [], 0
    while True:
        j = efts(params, frm); hits = j["hits"]["hits"]
        for h in hits:
            s = h["_source"]; acc, doc = h["_id"].split(":", 1)
            rows.append(dict(busca=rotulo, accession=acc, doc=doc, form=s.get("form"), data=s.get("file_date"), filer=(s.get("display_names") or [""])[0],
                             ciks="|".join(s.get("ciks") or []), sede="|".join(sorted(set(s.get("biz_locations") or [])))[:120], inc="|".join(s.get("inc_states") or [])))
        frm += len(hits); tot = j["hits"]["total"]["value"]
        if not hits or frm >= tot or frm >= 10000: break
        time.sleep(0.3)
    print(rotulo, "documentos:", len(rows), "de", tot, flush=True); return rows
def main():
    R = coleta({"q": '"financial advisor"', "forms": FORMS, "locationCodes": "D5"}, "sede Brasil")
    R += coleta({"q": '"Brazil" "financial advisor" "fee"', "forms": FORMS}, "texto Brazil")
    H = pd.DataFrame(R).drop_duplicates(["accession", "doc"]); H.to_csv(os.path.join(OUT, "_efts_hits.csv"), index=False)
    H["form_base"] = H.form.str.replace("/A", "", regex=False); H["ano"] = H.data.str[:4]
    U = H.groupby(["filer", "form_base", "ano"]).agg(docs=("doc", "size"), buscas=("busca", lambda s: "|".join(sorted(set(s)))), sede=("sede", "first"),
                                                     primeira=("data", "min"), accession=("accession", "first")).reset_index().sort_values(["ano", "filer"])
    U.to_csv(os.path.join(HERE, "data", "sec_ma_brasil_universo.csv"), index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400)
    print(U[["ano", "form_base", "filer", "docs", "buscas", "sede"]].to_string(index=False))
if __name__ == "__main__": main()
