"""Lê a planilha oficial do RI (Historical Financials XQYY.xlsx) e grava data/historical_financials.json
Estrutura: {aba: {serie: {periodo: valor}}}; períodos trimestrais ("1Q18") e anuais ("2018").
Linhas duplicadas na mesma aba (ex.: 'Securities' em FVTPL/FVOCI/custo amortizado) ganham sufixo do bloco pai."""
import json, re, sys, glob, os, openpyxl
HERE = os.path.dirname(os.path.abspath(__file__))
def _ord(p):
    m = re.search(r"([1-4])Q(\d{2})", p); return (int(m.group(2)), int(m.group(1))) if m else (0, 0)
arq = max(glob.glob(HERE + "/fontes/ri/Historical Financials *.xlsx"), key=_ord)
wb = openpyxl.load_workbook(arq, data_only=True)
out = {"_fonte": os.path.basename(arq)}
def lab(v): return re.sub(r"\s+", " ", str(v)).strip()
for ws in wb.worksheets:
    if ws.title[0] not in "123456": continue
    rows = list(ws.iter_rows(values_only=True))
    # linha de cabeçalho = a que tem mais rótulos de período
    def per(v):
        if isinstance(v, (int, float)) and 2000 < v < 2100 and float(v).is_integer(): return str(int(v))
        if isinstance(v, str) and re.fullmatch(r"[1-4]Q\d{2}", v.strip()): return v.strip()
        return None
    hdr_i = max(range(len(rows)), key=lambda i: sum(per(v) is not None for v in rows[i]))
    hdr = rows[hdr_i]
    cols = {j: per(v) for j, v in enumerate(hdr) if per(v) is not None}
    series, parent, seen = {}, None, {}
    for r in rows[hdr_i + 1:]:
        if r is None: continue
        labcol = next((j for j, v in enumerate(r[:3]) if isinstance(v, str) and v.strip()), None)
        if labcol is None: continue
        name = lab(r[labcol])
        if re.match(r"^\d+ ?[-–]", name): continue  # notas de rodapé
        vals = {cols[j]: (round(r[j], 4) if isinstance(r[j], (int, float)) else None) for j in cols if j < len(r)}
        if all(v is None for v in vals.values()):
            parent = name; continue
        key = name
        if key in series: key = f"{name} ({parent})"
        if key in series: key = f"{name} ({parent}) #{seen.get(name,2)}"; seen[name] = seen.get(name,2)+1
        series[key] = {k: v for k, v in vals.items() if v is not None}
    out[ws.title] = series
    qs = sorted([c for c in cols.values() if "Q" in c], key=lambda c: (c[2:], c[0]))
    print(f"{ws.title}: {len(series)} séries, {len(cols)} períodos ({qs[0]}..{qs[-1]})")
json.dump(out, open(HERE + "/data/historical_financials.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("ok ->", HERE + "/data/historical_financials.json")
