# -*- coding: utf-8 -*-
"""Remuneração de assessores financeiros em operações de M&A de companhias brasileiras com documentos na SEC.
Entrada: data/sec_ma_brasil_filings.csv (dados_sec_ma_filers.py). Para cada registrante × formulário-base × ano, baixa o documento
principal da versão mais recente (a emenda final costuma ter a descrição completa das taxas), guarda o texto em fontes/sec_ma/docs/,
descarta trocas de títulos de dívida (sem "financial advisor"/"fairness") e extrai as frases sobre a remuneração dos assessores.
Saída: data/sec_ma_brasil_fees_frases.csv (uma linha por frase) e data/sec_ma_brasil_deals.csv (uma por operação, com marcadores)."""
import os, re, time, html, urllib.request, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); DOCS = os.path.join(HERE, "fontes", "sec_ma", "docs"); os.makedirs(DOCS, exist_ok=True); DATA = os.path.join(HERE, "data")
UA = {"User-Agent": "Rafael Lavourinha rafael2102@gmail.com"}
def baixa(cik, acc, doc):
    p = os.path.join(DOCS, f"{acc}.txt")
    if os.path.exists(p): return open(p, encoding="utf-8").read()
    u = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-', '')}/{doc}"
    for t in range(4):
        try:
            b = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=180).read().decode("utf-8", "ignore"); break
        except Exception as e: time.sleep(3 * (t + 1)); b = None; err = e
    if b is None: print("falhou", u, err, flush=True); return ""
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", b); t = re.sub(r"(?s)<[^>]+>", " ", t); t = html.unescape(t); t = re.sub(r"\s+", " ", t)
    open(p, "w", encoding="utf-8").write(t); time.sleep(0.15); return t
MOEDA = r"(?:US\$|U\.S\.\$|\$|R\$|BRL|USD)\s?[\d][\d.,]*\s?(?:million|billion|thousand|milh\w+|mil)?"
def frases(t):
    out = []
    for s in re.split(r"(?<=[.;])\s+(?=[A-Z(])", t):
        if len(s) > 1500: continue
        if re.search(r"(?i)\bfees?\b|compensation|remunera", s) and re.search(MOEDA, s) and re.search(r"(?i)financial advis|fairness|engage|opinion|advis[oe]r|investment bank|dealer.manager|placement agent|valuation", s):
            out.append(s.strip())
    return out
def main():
    F = pd.read_csv(os.path.join(DATA, "sec_ma_brasil_filings.csv")); F["form_base"] = F.form.str.replace("/A", "", regex=False); F["ano"] = F.data.str[:4]
    G = F.sort_values("data").groupby(["cik", "form_base", "ano"]).tail(1)  # versão mais recente de cada operação
    deals, fr = [], []
    for _, r in G.iterrows():
        t = baixa(r.cik, r.accession, r.doc)
        fa = len(re.findall(r"(?i)financial advis", t)); fo = len(re.findall(r"(?i)fairness opinion|opinion of", t))
        ma = bool(re.search(r"(?i)merger|tender offer|acquisition of|business combination|incorporação|share exchange|exchange of shares|offer to purchase", t))
        debt = bool(re.search(r"(?i)registration rights agreement", t) and re.search(r"(?i)exchange notes|old notes|outstanding notes", t))
        fs = frases(t) if fa else []
        deals.append(dict(cik=r.cik, filer=r.filer, form=r.form, form_base=r.form_base, data=r.data, accession=r.accession, doc=r.doc, n_financial_advisor=fa, n_fairness=fo,
                          parece_ma=ma and not debt, troca_divida=debt, n_frases_fee=len(fs), tamanho=len(t)))
        for s in fs: fr.append(dict(cik=r.cik, filer=r.filer, form=r.form, data=r.data, accession=r.accession, frase=s[:1500]))
        print(r.data, r.form.ljust(10), str(r.filer)[:45].ljust(45), "FA", fa, "| frases", len(fs), "| M&A" if (ma and not debt) else ("| dívida" if debt else ""), flush=True)
    pd.DataFrame(deals).to_csv(os.path.join(DATA, "sec_ma_brasil_deals.csv"), index=False)
    pd.DataFrame(fr).to_csv(os.path.join(DATA, "sec_ma_brasil_fees_frases.csv"), index=False)
    D = pd.DataFrame(deals); print("operações:", len(D), "| com assessor financeiro:", (D.n_financial_advisor > 0).sum(), "| com frase de fee:", (D.n_frases_fee > 0).sum())
if __name__ == "__main__": main()
