"""Baixa todos os exhibits 99.x dos 6-K e o 20-F da XP Inc. (CIK 1787425) na SEC EDGAR.
Salva em xp/fontes/sec/<data>_<form>_<arquivo>. Rode de novo: só baixa o que falta."""
import json, os, time, urllib.request, sys
UA = {"User-Agent": "Rafael Lavourinha rafael2102@gmail.com"}
CIK = "1787425"; OUT = os.path.dirname(os.path.abspath(__file__)) + "/fontes/sec"
def get(url, binary=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r: return r.read()
sub = json.loads(get(f"https://data.sec.gov/submissions/CIK{int(CIK):010d}.json"))
rec = sub["filings"]["recent"]
rows = list(zip(rec["form"], rec["filingDate"], rec["accessionNumber"], rec["primaryDocument"]))
for f in sub["filings"].get("files", []):
    d = json.loads(get("https://data.sec.gov/submissions/" + f["name"]))
    rows += list(zip(d["form"], d["filingDate"], d["accessionNumber"], d["primaryDocument"]))
print(len(rows), "filings no total")
json.dump(rows, open(OUT + "/_filings.json", "w"), indent=1)
n = 0
for form, date, acc, prim in rows:
    if form not in ("6-K", "20-F", "20-F/A", "F-1", "F-1/A", "424B4"): continue
    folder = acc.replace("-", "")
    base = f"https://www.sec.gov/Archives/edgar/data/{CIK}/{folder}/"
    try: idx = json.loads(get(base + "index.json"))
    except Exception as e: print("ERRO idx", acc, e); continue
    time.sleep(0.12)
    for it in idx["directory"]["item"]:
        name = it["name"]
        if not (name.endswith(".htm") or name.endswith(".pdf") or name.endswith(".xlsx")): continue
        if name.startswith("000"): continue
        dest = f"{OUT}/{date}_{form.replace('/','')}_{name}"
        if os.path.exists(dest) and os.path.getsize(dest) > 0: continue
        try:
            open(dest, "wb").write(get(base + name)); n += 1
            print(date, form, name, os.path.getsize(dest))
        except Exception as e: print("ERRO", acc, name, e)
        time.sleep(0.12)
print("baixados:", n)
