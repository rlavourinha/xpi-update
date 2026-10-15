# -*- coding: utf-8 -*-
"""Universo de operações de M&A de companhias brasileiras na SEC, pelo histórico de formulários de cada registrante
(submissions API do EDGAR), não pela busca de texto (que perde documentos).
Registrantes: todos com endereço comercial no Brasil (EDGAR State=D5, fontes/sec_ma/_ciks_d5.json) + brasileiras com sede no exterior (lista abaixo, resolvida pelo company_tickers e por busca de nome).
Formulários de M&A: F-4, S-4, SC 13E3, SC 14D9, SC TO-T, SC TO-I, DEFM14A, PREM14A, DEFM14C, SC 13E4, CB (e emendas).
Saída: data/sec_ma_brasil_filings.csv (um registro por formulário) e data/sec_ma_brasil_operacoes.csv (um por registrante × formulário-base × ano)."""
import os, json, time, urllib.request, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "fontes", "sec_ma"); DATA = os.path.join(HERE, "data")
UA = {"User-Agent": "Rafael Lavourinha rafael2102@gmail.com"}
MA = ("F-4", "S-4", "SC 13E3", "SC 14D9", "SC TO-T", "SC TO-I", "DEFM14A", "PREM14A", "DEFM14C", "SC 13E4", "CB")
EXTRA = ["XP Inc", "StoneCo", "PagSeguro", "PagBank", "Afya", "VTEX", "Nu Holdings", "Inter & Co", "Patria Investments", "Zenvia", "Semantix", "Netshoes", "Cosan Ltd", "Cosan S.A.",
         "Vinci Partners", "Vinci Compass", "Nuvini", "Arco Platform", "Vasta Platform", "Vitru", "Lavoro", "Ambipar", "Moove", "Sendas", "JBS N.V.", "Natura &Co", "Braskem", "Itau Unibanco",
         "BRF S.A.", "Suzano", "Gol Linhas", "Azul S.A.", "Embraer", "Gerdau", "Ultrapar", "Telefonica Brasil", "TIM S.A.", "Oi S.A.", "Petroleo Brasileiro", "Vale S.A.", "Centrais Eletricas Brasileiras",
         "Companhia Brasileira de Distribuicao", "Banco Bradesco", "Banco Santander (Brasil)", "Sabesp", "Companhia Energetica de Minas Gerais", "CPFL", "Copel", "Eletrobras", "Arcos Dorados"]
def get(u):
    for t in range(4):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60))
        except Exception as e: time.sleep(2 * (t + 1)); err = e
    raise err
def main():
    ciks = set(json.load(open(os.path.join(OUT, "_ciks_d5.json"))))
    tk = get("https://www.sec.gov/files/company_tickers.json")
    for v in tk.values():
        if any(n.lower() in v["title"].lower() for n in EXTRA): ciks.add(str(v["cik_str"]).zfill(10))
    ciks = sorted(c.zfill(10) for c in ciks); print("registrantes:", len(ciks), flush=True)
    rows = []
    for i, c in enumerate(ciks):
        try: j = get(f"https://data.sec.gov/submissions/CIK{c}.json")
        except Exception as e: print("falhou", c, e); continue
        nome = j.get("name"); sede = (j.get("addresses", {}).get("business", {}) or {}).get("stateOrCountryDescription")
        blocos = [j["filings"]["recent"]] + [get("https://data.sec.gov/submissions/" + f["name"]) for f in j["filings"].get("files", [])]
        for b in blocos:
            for fo, d, a, p in zip(b["form"], b["filingDate"], b["accessionNumber"], b["primaryDocument"]):
                if fo.replace("/A", "") in MA:
                    rows.append(dict(cik=c, filer=nome, sede=sede, sic=j.get("sicDescription"), form=fo, data=d, accession=a, doc=p))
        time.sleep(0.12)
        if i % 100 == 0: print(i, len(rows), flush=True)
    F = pd.DataFrame(rows).sort_values("data"); F.to_csv(os.path.join(DATA, "sec_ma_brasil_filings.csv"), index=False)
    F["form_base"] = F.form.str.replace("/A", "", regex=False); F["ano"] = F.data.str[:4]
    O = F.groupby(["cik", "filer", "form_base", "ano"]).agg(docs=("accession", "size"), primeira=("data", "min"), accession=("accession", "first"), doc=("doc", "first"), sede=("sede", "first")).reset_index().sort_values("primeira")
    O.to_csv(os.path.join(DATA, "sec_ma_brasil_operacoes.csv"), index=False)
    pd.set_option("display.width", 220); pd.set_option("display.max_rows", 500)
    print(len(O), "operações (registrante × formulário × ano)"); print(O[["primeira", "form_base", "filer", "docs", "sede"]].to_string(index=False))
if __name__ == "__main__": main()
