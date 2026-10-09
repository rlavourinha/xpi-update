# -*- coding: utf-8 -*-
"""Coleta diária das taxas indicativas de debêntures da ANBIMA (arquivo público, só os últimos ~5 dias úteis) e
agrega um spread de crédito privado por dia.

Arquivo: https://www.anbima.com.br/informacoes/merc-sec-debentures/arqs/dbAAMMDD.txt  (latin-1, campos separados por @)
Campos: Código, Nome, Repac./Venc., Índice/Correção (ex.: "DI + 1,6%", "DI x 110%", "IPCA + 6,5%"), Taxa de Compra, Taxa de Venda,
        Taxa Indicativa, Desvio Padrão, Intervalo Indicativo Mín/Máx, PU, % PU Par, Duration (dias úteis), % Reune, Referência NTN-B.
Para papéis DI+ a taxa indicativa JÁ É o spread sobre o DI (em % a.a.). Para IPCA+ o spread = taxa indicativa − NTN-B de mesma
duration, interpolada na ETTJ real da ANBIMA guardada pelo monitor (../monitor-investimentos/data/curva_tesouro.json).

Saídas: data/anbima_debentures_spread_diario.csv (1 linha/dia: mediana e média simples do spread DI+ por faixa de duration,
spread IPCA+ sobre NTN-B, nº de papéis) e brutos em fontes/setor/anbima/debentures/dbAAMMDD.txt.
Uso: python dados_anbima_debentures_diario.py  (idempotente; rodar todo dia útil — a janela pública é curta)."""
import os, sys, csv, re, json, datetime as dt, urllib.request, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, "fontes", "setor", "anbima", "debentures"); DATA = os.path.join(HERE, "data")
os.makedirs(RAW, exist_ok=True); CSV = os.path.join(DATA, "anbima_debentures_spread_diario.csv")
URL = "https://www.anbima.com.br/informacoes/merc-sec-debentures/arqs/db{d}.txt"
HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128 Safari/537.36"}
CURVA = os.path.join(HERE, "..", "monitor-investimentos", "data", "curva_tesouro.json")

def num(s):
    s = str(s).strip().replace(".", "").replace(",", ".")
    try: return float(s)
    except Exception: return None

def baixa(d):
    p = os.path.join(RAW, f"db{d.strftime('%y%m%d')}.txt")
    if os.path.exists(p) and os.path.getsize(p) > 1000: return p
    try:
        req = urllib.request.Request(URL.format(d=d.strftime("%y%m%d")), headers=HDR)
        with urllib.request.urlopen(req, timeout=60) as r: b = r.read()
        if len(b) < 5000 or b"ANBIMA" not in b[:300]: return None
        open(p, "wb").write(b); return p
    except Exception: return None

def curva_real():
    """{data: [(prazo_anos, taxa)]} da ETTJ real (IPCA) da ANBIMA via monitor; None se não houver."""
    try:
        c = json.load(open(CURVA, encoding="utf-8")); prazos = c["prazos_real"]; out = {}
        for row in c["real"]: out[row[0]] = list(zip(prazos, row[1:]))
        return out
    except Exception: return None

def ntnb_na_duration(cv, data, anos):
    pts = cv.get(data) if cv else None
    if not pts:  # último dia disponível antes
        ks = sorted(k for k in (cv or {}) if k <= data); pts = cv[ks[-1]] if ks else None
    if not pts: return None
    pts = [(p, t) for p, t in pts if t is not None]
    if anos <= pts[0][0]: return pts[0][1]
    for (p0, t0), (p1, t1) in zip(pts, pts[1:]):
        if p0 <= anos <= p1: return t0 + (t1 - t0) * (anos - p0) / (p1 - p0)
    return pts[-1][1]

def agrega(p, data_iso, cv):
    di, ipca, ipca_sp = [], [], []
    for line in open(p, encoding="latin-1"):
        f = line.rstrip("\n").split("@")
        if len(f) < 13 or not re.match(r"^[A-Z0-9]{5,6}$", f[0].strip()): continue
        idx = f[3].strip().upper(); tx = num(f[6]); dur = num(f[12])
        if tx is None or dur is None or dur <= 0: continue
        anos = dur / 252
        if idx.startswith("DI +") or idx.startswith("DI+"):
            di.append((tx, anos))
        elif idx.startswith("IPCA"):
            ipca.append((tx, anos)); b = ntnb_na_duration(cv, data_iso, anos)
            if b is not None: ipca_sp.append((tx - b, anos))
    def stats(v, lo=0, hi=99):
        x = [t for t, a in v if lo <= a < hi]
        return (round(st.median(x), 3), round(sum(x) / len(x), 3), len(x)) if x else (None, None, 0)
    r = {"data": data_iso}
    for nome, lo, hi in [("di", 0, 99), ("di_ate2a", 0, 2), ("di_2a4a", 2, 4), ("di_acima4a", 4, 99)]:
        r[f"{nome}_mediana"], r[f"{nome}_media"], r[f"{nome}_n"] = stats(di, lo, hi)
    r["ipca_taxa_mediana"], r["ipca_taxa_media"], r["ipca_n"] = stats(ipca)
    r["ipca_spread_ntnb_mediana"], r["ipca_spread_ntnb_media"], r["ipca_spread_n"] = stats(ipca_sp)
    r["duration_di_mediana_anos"] = round(st.median([a for _, a in di]), 2) if di else None
    return r

def main():
    have = []
    if os.path.exists(CSV):
        with open(CSV, encoding="utf-8") as f: have = list(csv.DictReader(f))
    feitos = {r["data"] for r in have}; cv = curva_real(); novos = []
    hoje = dt.date.today(); d = hoje - dt.timedelta(days=12)
    while d <= hoje:
        s = d.isoformat()
        if d.weekday() < 5 and s not in feitos:
            p = baixa(d)
            if p:
                r = agrega(p, s, cv); novos.append(r); print(f"{s}: DI+ mediana {r['di_mediana']} ({r['di_n']} papéis) | IPCA+ sobre NTN-B {r['ipca_spread_ntnb_mediana']} ({r['ipca_spread_n']})", flush=True)
        d += dt.timedelta(days=1)
    # reprocessa brutos antigos que ainda não estejam no CSV (ex.: baixados à mão)
    for fn in sorted(os.listdir(RAW)):
        m = re.match(r"db(\d{6})\.txt$", fn)
        if not m: continue
        s = dt.datetime.strptime(m.group(1), "%y%m%d").date().isoformat()
        if s not in feitos and s not in {r["data"] for r in novos}:
            r = agrega(os.path.join(RAW, fn), s, cv); novos.append(r); print(f"{s} (bruto): DI+ mediana {r['di_mediana']}", flush=True)
    if novos:
        allr = sorted(have + novos, key=lambda r: r["data"]); keys = list(novos[0].keys())
        with open(CSV, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); [w.writerow(r) for r in allr]
    print(f"+{len(novos)} dias, total {len(have) + len(novos)} em {CSV}")

if __name__ == "__main__": main()
