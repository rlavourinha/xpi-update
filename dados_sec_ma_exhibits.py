# -*- coding: utf-8 -*-
"""Complementa dados_sec_ma_fees.py: para operações de M&A cujo documento principal não descreve a remuneração dos assessores,
baixa os anexos (EX-99 etc.) do arquivamento ORIGINAL e da última emenda (oferta de compra, laudos, fairness opinions, 14D-9)
e reaplica a extração de frases. Também amplia o padrão de frase (fee/compensation/paid/remuneration + valor + assessor).
Saída: data/sec_ma_brasil_fees_frases_exhibits.csv."""
import os, re, json, time, html, urllib.request, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); DOCS = os.path.join(HERE, "fontes", "sec_ma", "docs"); DATA = os.path.join(HERE, "data")
UA = {"User-Agent": "Rafael Lavourinha rafael2102@gmail.com"}
def get(u, binario=False):
    for t in range(4):
        try:
            b = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=180).read(); time.sleep(0.15)
            return b if binario else b.decode("utf-8", "ignore")
        except Exception as e: time.sleep(3 * (t + 1)); err = e
    print("falhou", u, err, flush=True); return None
def texto(b):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", b); t = re.sub(r"(?s)<[^>]+>", " ", t); return re.sub(r"\s+", " ", html.unescape(t))
MOEDA = r"(?:US\$|U\.S\.\$|\$|R\$|BRL|USD)\s?[\d][\d.,]*\s?(?:million|billion|thousand|milh\w+|mil)?"
BANCO = r"(?i)financial advis|fairness|opinion|advis[oe]r|investment bank|valuation|appraiser|avaliador|laudo|BTG|Ita[uú] BBA|Bradesco|Santander|Morgan|Goldman|J\.?P\.? ?Morgan|Citi|Merrill|BofA|UBS|Credit Suisse|Rothschild|Lazard|Evercore|XP Investimentos|Banco XP|Safra|Bank of America|Deutsche|Barclays|HSBC|Apsis|Planconsult|PwC|KPMG|Ernst|Deloitte|Moelis|Jefferies|Houlihan|Perella|Centerview"
def frases(t):
    out = []
    for s in re.split(r"(?<=[.;])\s+(?=[A-Z(])", t):
        if 40 < len(s) < 1500 and re.search(r"(?i)\bfees?\b|compensation|remunera|honor[aá]rio|paid|pay", s) and re.search(MOEDA, s) and re.search(BANCO, s) \
           and not re.search(r"(?i)filing fee|fee rate advisory|transaction valuation|deferred tax|ICMS|activation fee", s):
            out.append(s.strip())
    return out
def main():
    D = pd.read_csv(os.path.join(DATA, "sec_ma_brasil_deals.csv")); F = pd.read_csv(os.path.join(DATA, "sec_ma_brasil_filings.csv"))
    F["form_base"] = F.form.str.replace("/A", "", regex=False); F["ano"] = F.data.str[:4]
    alvo = D[D.parece_ma & (D.n_frases_fee == 0)]
    alvo = alvo.drop_duplicates("accession")  # mesma operação arquivada por várias subsidiárias (NET) conta uma vez
    rows = []
    for _, r in alvo.iterrows():
        g = F[(F.cik == r.cik) & (F.form_base == r.form_base) & (F.ano == str(r.data)[:4])].sort_values("data")
        accs = list(dict.fromkeys([g.accession.iloc[0], g.accession.iloc[-1]]))
        for acc in accs:
            idx = get(f"https://www.sec.gov/Archives/edgar/data/{int(r.cik)}/{acc.replace('-', '')}/index.json")
            if not idx: continue
            itens = [i["name"] for i in json.loads(idx)["directory"]["item"] if i["name"].lower().endswith((".htm", ".html", ".txt")) and "index" not in i["name"].lower()]
            for nm in itens[:25]:
                p = os.path.join(DOCS, f"{acc}__{nm}.txt")
                if os.path.exists(p): t = open(p, encoding="utf-8").read()
                else:
                    b = get(f"https://www.sec.gov/Archives/edgar/data/{int(r.cik)}/{acc.replace('-', '')}/{nm}")
                    if not b: continue
                    t = texto(b); open(p, "w", encoding="utf-8").write(t)
                for s in frases(t): rows.append(dict(cik=r.cik, filer=r.filer, form=r.form_base, data=r.data, accession=acc, arquivo=nm, frase=s[:1500]))
        print(r.data, r.form_base.ljust(8), str(r.filer)[:40].ljust(40), "frases:", sum(1 for x in rows if x["cik"] == r.cik and x["data"] == r.data), flush=True)
    X = pd.DataFrame(rows).drop_duplicates(["cik", "frase"]); X.to_csv(os.path.join(DATA, "sec_ma_brasil_fees_frases_exhibits.csv"), index=False)
    print("frases:", len(X), "operações com frase:", X.groupby(["cik", "data"]).ngroups)
if __name__ == "__main__": main()
