# -*- coding: utf-8 -*-
"""Lê os relatórios de acompanhamento diário do CAP do RLP (B3) baixados por dados_b3_rlp.py e monta a série por corretora:
% do fluxo de varejo da corretora executado contra a própria oferta RLP ("taxa de internalização"), por dia e ativo.
Formatos: PDF (minis ago/19-2023), xlsx (ações 2022+, minis 2024-out/25; uma aba por ativo, corretoras na linha 2), CSV long (nov/25+).
Saídas: data/b3_rlp_diario_long.csv (data, corretora, mercado, ativo, pct) e data/b3_rlp_mensal_xp.csv (resumo XP por mês e ativo)."""
import os, re, glob, csv, datetime as dt, unicodedata, openpyxl, pdfplumber, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, "fontes", "setor", "b3", "rlp", "raw"); DATA = os.path.join(HERE, "data")
def norm(s): return re.sub(r"\s+", " ", unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper()).strip()
def grupo(n):
    n = norm(n)
    for k, p in [("XP", r"\bXP\b|GRUPO XP"), ("BTG", r"BTG"), ("TORO", r"TORO"), ("GENIAL", r"GENIAL"), ("CM CAPITAL", r"CM CAPITAL"), ("NOVA FUTURA", r"NOVA FUTURA"), ("TERRA", r"TERRA"), ("MODAL", r"MODAL"), ("ITAU", r"ITAU"), ("GUIDE", r"GUIDE"), ("ICAP", r"ICAP"), ("MIRAE", r"MIRAE"), ("VITREO", r"VITREO"), ("COMMCOR", r"COMMCOR"), ("SAFRA", r"SAFRA"), ("AGORA", r"AGORA|BRADESCO"), ("INTER", r"\bINTER\b"), ("CLEAR", r"CLEAR"), ("RICO", r"RICO")]:
        if re.search(p, n): return k
    return n[:30]
def pnum(v):
    if isinstance(v, (int, float)): return float(v) * (100 if abs(v) <= 1.5 else 1)
    if isinstance(v, str):
        s = v.strip().replace("%", "").replace(",", ".")
        try: return float(s)
        except: return None
    return None
out = []
def add(d, corr, mkt, ativo, pct, fonte):
    if pct is None or d is None: return
    out.append(dict(data=d.strftime("%Y-%m-%d"), corretora=grupo(corr), mercado=mkt, ativo=ativo, pct=round(pct, 3), fonte=fonte))
def xlsx(f, mkt):
    wb = openpyxl.load_workbook(f, read_only=True, data_only=True)
    for ws in wb.worksheets:
        G = [list(r) for r in ws.iter_rows(values_only=True, max_col=60)]
        if len(G) < 3: continue
        hi = next((i for i, r in enumerate(G[:6]) if sum(isinstance(v, str) and len(v) > 3 for v in r[1:]) >= 2 and not any(hasattr(v, "year") for v in r)), None)
        if hi is None: continue
        ativo = next((str(v).strip() for v in G[0][1:] if isinstance(v, str) and v.strip()), ws.title.strip())
        hdr = G[hi]
        for r in G[hi + 1:]:
            d = r[0]
            if isinstance(d, str):
                try: d = dt.datetime.strptime(d.strip()[:10], "%d/%m/%Y")
                except: d = None
            if not hasattr(d, "year"): continue
            for j in range(1, len(hdr)):
                if isinstance(hdr[j], str) and hdr[j].strip(): add(d, hdr[j], mkt, ativo, pnum(r[j]) if j < len(r) else None, os.path.basename(f))
def pdf(f):
    with pdfplumber.open(f) as P:
        curtas = [w["text"] for pg in P.pages for w in pg.extract_words() if re.match(r"^\d{1,2}/\d{1,2}/\d{2}$", w["text"])]
        fmt_curta = "%d/%m/%y" if any(int(c.split("/")[0]) > 12 for c in curtas) else "%m/%d/%y"
        for pg in P.pages:
            W = pg.extract_words(keep_blank_chars=False, use_text_flow=False)
            mk = [w for w in W if w["text"] in ("WIN", "WDO")]
            gx = [w for w in W if w["text"].upper() == "GRUPO"]
            if not mk or not gx: continue
            # cada tabela: um 'GRUPO' (XP é a 1ª coluna) + o rótulo WIN/WDO acima dele mais próximo (lado a lado: o mais próximo em x)
            tabs = []
            for g in gx:
                acima = [m for m in mk if m["top"] < g["top"] + 2]
                if not acima: continue
                tmax = max(m["top"] for m in acima); cand = [m for m in acima if abs(m["top"] - tmax) < 5]
                if len(cand) > 1:  # lado a lado: ordem de x
                    gs = sorted([h for h in gx if abs(h["top"] - g["top"]) < 5], key=lambda h: h["x0"]); cs = sorted(cand, key=lambda m: m["x0"])
                    lab = cs[min(gs.index(g), len(cs) - 1)]
                else: lab = cand[0]
                tabs.append(dict(mkt=lab["text"], xc=(g["x0"] + g["x1"]) / 2, top=g["top"]))
            linhas = {}
            for w in W:
                if not tabs or w["top"] <= min(t["top"] for t in tabs) or w["x0"] > 120: continue
                if re.match(r"^\d{2}/\d{2}/\d{4}$", w["text"]): linhas[round(w["top"], 1)] = (dt.datetime.strptime(w["text"], "%d/%m/%Y"), [])
                elif re.match(r"^\d{1,2}/\d{1,2}/\d{2}$", w["text"]): linhas[round(w["top"], 1)] = (dt.datetime.strptime(w["text"], fmt_curta), [])
            for w in W:
                if re.match(r"^-?\d+([,.]\d+)?%$", w["text"]) and linhas:
                    k = min(linhas, key=lambda t: abs(t - w["top"]))
                    if abs(k - w["top"]) < 4: linhas[k][1].append(((w["x0"] + w["x1"]) / 2, pnum(w["text"])))
            for top, (d, vals) in linhas.items():
                if not vals: continue
                ts = [t for t in tabs if t["top"] < top]
                if not ts: continue
                tm = max(t["top"] for t in ts)
                for t in [t for t in ts if abs(t["top"] - tm) < 5]:
                    x, v = min(vals, key=lambda q: abs(q[0] - t["xc"]))
                    if abs(x - t["xc"]) < 30: add(d, "GRUPO XP", "DRV", t["mkt"], v, os.path.basename(f))
def csvf(f):
    for r in csv.DictReader(open(f, encoding="utf-8-sig")):
        try: d = dt.datetime.strptime(r["Date"][:10], "%Y-%m-%d")
        except: continue
        add(d, r["Broker Name"], r["Market"], r["Ticker"].strip(), pnum(r["% RLP"]), os.path.basename(f))
def main():
    fs = sorted(glob.glob(os.path.join(RAW, "*")))
    for f in fs:
        b = os.path.basename(f); nb = norm(b)
        if "RELRLP" in nb or "CAP_VALUES" in nb: continue
        try:
            if b.lower().endswith(".csv"): csvf(f)
            elif b.lower().endswith(".pdf"): pdf(f)
            elif b.lower().endswith(".xlsx"): xlsx(f, "DRV" if re.search(r"MINIS|FUTUROS", nb) else "EQT")
        except Exception as e: print("ERRO", b, e)
    L = pd.DataFrame(out).drop_duplicates(["data", "corretora", "mercado", "ativo"], keep="last")
    L["mercado"] = L.apply(lambda r: "DRV" if r.ativo in ("WIN", "WDO") else r.mercado, axis=1)
    L.sort_values(["data", "mercado", "ativo", "corretora"]).to_csv(os.path.join(DATA, "b3_rlp_diario_long.csv"), index=False)
    L["mes"] = L.data.str[:7]; X = L[L.corretora == "XP"]
    M = X.groupby(["mes", "mercado", "ativo"]).pct.mean().unstack(["mercado", "ativo"])
    eq = X[X.mercado == "EQT"].groupby("mes").agg(acoes_n=("ativo", "nunique"), acoes_pct_medio=("pct", "mean"))
    R = pd.DataFrame({"win_pct": M.get(("DRV", "WIN")), "wdo_pct": M.get(("DRV", "WDO"))}).join(eq, how="outer")
    R["corretoras_win"] = L[(L.ativo == "WIN")].groupby("mes").corretora.nunique(); R["corretoras_acoes"] = L[(L.mercado == "EQT")].groupby("mes").corretora.nunique()
    R.round(2).to_csv(os.path.join(DATA, "b3_rlp_mensal_xp.csv")); print(L.groupby("mercado").data.agg(["min", "max", "count"])); print(R.round(1).to_string())
if __name__ == "__main__": main()
