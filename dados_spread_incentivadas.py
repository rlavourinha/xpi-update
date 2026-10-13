# -*- coding: utf-8 -*-
"""Spread das debêntures incentivadas (Lei 12.431) com gross-up × spread das debêntures DI, diário — o gráfico da Régia Capital
publicado no Valor (13/10/2026: "Após recorde, spread de papel incentivado supera o do comum"), refeito com dados públicos.

Fontes (todas públicas, papel a papel):
  1. IDEX-Infra Geral (IDEX Analytics, ex-JGP): composição diária com peso, duration (anos) e MID spread (bps sobre a NTN-B de
     referência). Histórico 04/01/2021→25/03/2026 = captura de 27/03/2026 do Wayback do arquivo público no S3
     (fontes/setor/idex/idex_infra_geral_datafile_wb20260327.xlsx); 09/09→hoje = arquivo atual (janela móvel de ~1 mês).
  2. IDEX-CDI Geral: composição diária com peso e spread de compra (fração a.a.). Histórico ago/2017→30/04/2026 = arquivo do site
     (idex_cdi_geral_datafile.xlsx); 09/09→hoje = arquivo atual no S3. Ex-distressed (spread > 10% fora), como a IDEX publica.
  3. IDA-IPCA Infraestrutura e IDA-DI (ANBIMA, os índices que a Régia usa): carteira teórica diária com taxa indicativa e duration
     (d.u.), janela pública de ~1 mês (fontes/setor/anbima/ida/). Serve para validar o método e para o trecho recente.
  Curvas: ETTJ ANBIMA (fotos diárias do monitor) quando há; antes disso, curva do Tesouro do monitor (pré 1-10a, real 2-30a),
  que difere da ETTJ em < 0,1 p.p. (efeito ~2 bp no gross-up).

Gross-up (método da Régia, IR de 15%): taxa nominal do papel isento = (1 + taxa real)(1 + inflação implícita no prazo) − 1;
taxa tributável equivalente = nominal ÷ 0,85; spread com gross-up = equivalente − taxa pré do Tesouro no mesmo prazo.
Taxa real do papel: ANBIMA = taxa indicativa; IDEX = NTN-B real no prazo + MID spread. Média ponderada pelo peso no índice.

Saída: data/spread_incentivadas_diario.csv (data, fonte, infra_spread, infra_gu, infra_dur, di_spread, dif).
Uso: python dados_spread_incentivadas.py  (rodar depois de baixar os arquivos; idempotente)."""
import os, sys, csv, json, glob, datetime as dt
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
IDEX = os.path.join(HERE, "fontes", "setor", "idex"); IDA = os.path.join(HERE, "fontes", "setor", "anbima", "ida")
MON = os.path.join(HERE, "..", "monitor-investimentos")
sys.path.insert(0, MON)
IR = 0.15
OUT = os.path.join(DATA, "spread_incentivadas_diario.csv")

# ---------------------------------------------------------------- curvas (real e pré por prazo em anos)
C = json.load(open(os.path.join(MON, "data", "curva_tesouro.json"), encoding="utf-8"))
TP, TR = C["prazos_pre"], C["prazos_real"]
CURVA = {}
for rp, rr in zip(C["pre"], C["real"]):
    pts_p = [(t, v) for t, v in zip(TP, rp[1:]) if v is not None]
    pts_r = [(t, v) for t, v in zip(TR, rr[1:]) if v is not None]
    if pts_p and pts_r:
        CURVA[rp[0]] = (pts_r, pts_p)
try:
    from fontes import anbima
    for d, f in anbima.fotos().items():
        v = [x for x in f["vertices"] if x[1] is not None and x[2] is not None]
        if v:
            CURVA[d] = ([(x[0] / 252, x[1]) for x in v], [(x[0] / 252, x[2]) for x in v])   # ETTJ ANBIMA tem prioridade
except Exception as e:
    print("  ETTJ ANBIMA indisponível:", e, file=sys.stderr)
DATAS_CURVA = sorted(CURVA)

def _interp(pts, x):
    if x <= pts[0][0]: return pts[0][1]
    if x >= pts[-1][0]: return pts[-1][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)

def curva(d: str):
    """(real(D), pré(D)) do dia d ou do último dia anterior disponível (até 7 dias)."""
    import bisect
    i = bisect.bisect_right(DATAS_CURVA, d) - 1
    if i < 0 or (dt.date.fromisoformat(d) - dt.date.fromisoformat(DATAS_CURVA[i])).days > 7:
        return None
    pr, pp = CURVA[DATAS_CURVA[i]]
    return (lambda D: _interp(pr, D)), (lambda D: _interp(pp, D))

def gross_up(taxa_real, D, real, pre):
    """Spread com gross-up (p.p.) de um papel isento com taxa real `taxa_real` (% a.a.) e duration D (anos)."""
    r, p = real(D) / 100, pre(D) / 100
    pi = (1 + p) / (1 + r) - 1
    nominal = (1 + taxa_real / 100) * (1 + pi) - 1
    return (nominal / (1 - IR) - p) * 100

# ---------------------------------------------------------------- coleta diária das janelas móveis (IDEX S3 e ANBIMA IDA ~1 mês)
S3 = "https://jgp-credito-public-s3.s3.us-east-1.amazonaws.com/idex/"
SNAP = os.path.join(IDEX, "s3")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128 Safari/537.36"}

def baixa():
    """Guarda uma cópia datada dos arquivos atuais da IDEX (a janela pública anda ~1 mês) e as carteiras diárias do IDA dos
    últimos ~30 dias úteis ainda não guardadas. Idempotente."""
    import urllib.request, urllib.parse
    os.makedirs(SNAP, exist_ok=True); os.makedirs(IDA, exist_ok=True)
    hoje = dt.date.today().strftime("%Y%m%d")
    for nome, local in (("idex_infra_geral_datafile.xlsx", "idex_infra_geral_datafile"), ("idex_cdi_geral_datafile.xlsx", "idex_cdi_geral_datafile_s3")):
        p = os.path.join(SNAP, f"{local}_{hoje}.xlsx")
        if os.path.exists(p): continue
        try:
            b = urllib.request.urlopen(urllib.request.Request(S3 + nome, headers=UA), timeout=300).read()
            open(p, "wb").write(b); print("  IDEX", nome, len(b))
        except Exception as e:
            print("  IDEX", nome, "falhou:", str(e)[:80], file=sys.stderr)
    H = {**UA, "Content-Type": "application/x-www-form-urlencoded", "Referer": "https://www.anbima.com.br/informacoes/ida/default.asp"}
    d, novos = dt.date.today() - dt.timedelta(days=45), 0
    while d <= dt.date.today():
        if d.weekday() < 5:
            for ind in ("IPCA_INFRAESTRUTURA", "DI"):
                p = os.path.join(IDA, f"ida_{ind}_{d:%Y%m%d}.csv")
                if os.path.exists(p) and os.path.getsize(p) > 2000: continue
                body = urllib.parse.urlencode({"tipo": "cd", "indice": ind, "escolha": "2", "Idioma": "PT", "saida": "csv",
                                               "DataIniD": d.strftime("%d/%m/%Y"), "DataIniM": d.strftime("%m/%Y")}).encode()
                try:
                    t = urllib.request.urlopen(urllib.request.Request("https://www.anbima.com.br/informacoes/ida/IDA_down.asp", data=body, headers=H), timeout=90).read().decode("latin-1")
                    if "Taxa Indicativa" in t:
                        open(p, "w", encoding="utf-8").write(t); novos += 1
                except Exception as e:
                    print("  IDA", ind, d, "falhou:", str(e)[:60], file=sys.stderr)
        d += dt.timedelta(days=1)
    print("  IDA: carteiras novas", novos)

def _arquivos(base_hist, nome_atual):
    """Arquivos do mais antigo ao mais novo: histórico (Wayback/site), cópias datadas do S3 e o arquivo atual. Em datas repetidas
    vale o arquivo mais novo (lido por último)."""
    arqs = [os.path.join(IDEX, a) for a in base_hist] + [os.path.join(IDEX, nome_atual)]
    arqs += sorted(glob.glob(os.path.join(SNAP, nome_atual.replace(".xlsx", "_2*.xlsx"))))
    return [a for a in arqs if os.path.exists(a)]

# ---------------------------------------------------------------- IDEX-Infra (histórico + janela atual)
def idex_infra():
    out = {}
    for p in _arquivos(["idex_infra_geral_datafile_wb20260327.xlsx"], "idex_infra_geral_datafile.xlsx"):
        df = pd.read_excel(p, usecols=["Data", "Peso no índice (%)", "Duration", "MID spread (Bps/NTNB)"])
        df["Data"] = pd.to_datetime(df["Data"]).dt.date.astype(str)
        for d, g in df.groupby("Data"):
            c = curva(d)
            g = g.dropna()
            w = g["Peso no índice (%)"]
            if c is None or w.sum() <= 0: continue
            real, pre = c
            s = g["MID spread (Bps/NTNB)"] / 100
            gu = [gross_up(real(D) + si, D, real, pre) for D, si in zip(g["Duration"], s)]
            out[d] = {"infra_spread": float((s * w).sum() / w.sum()), "infra_gu": float(sum(x * wi for x, wi in zip(gu, w)) / w.sum()),
                      "infra_dur": float((g["Duration"] * w).sum() / w.sum())}
    return out

def idex_cdi():
    out = {}
    for p in _arquivos(["idex_cdi_geral_datafile.xlsx"], "idex_cdi_geral_datafile_s3.xlsx"):
        df = pd.read_excel(p, usecols=["Data", "Peso no índice (%)", "Spread de compra (%)"])
        df["Data"] = pd.to_datetime(df["Data"]).dt.date.astype(str)
        df = df[df["Data"] >= "2020-07-01"].dropna()
        df = df[df["Spread de compra (%)"] <= 0.10]                       # ex-distressed (> 10% a.a. fora), como a IDEX publica
        for d, g in df.groupby("Data"):
            w = g["Peso no índice (%)"]
            if w.sum() > 0:
                out[d] = float((g["Spread de compra (%)"] * w).sum() / w.sum() * 100)
    return out

# ---------------------------------------------------------------- ANBIMA IDA (janela pública)
def _num(s):
    s = str(s).strip().replace(".", "").replace(",", ".")
    try: return float(s)
    except ValueError: return None

def _carteira(p):
    linhas = open(p, encoding="utf-8").read().splitlines()
    i = next(k for k, l in enumerate(linhas) if l.startswith("Data;Código"))
    cab = linhas[i].split(";")
    rows = [dict(zip(cab, l.split(";"))) for l in linhas[i + 1:] if l.count(";") >= 10]
    return rows

def ida():
    out = {}
    for p in sorted(glob.glob(os.path.join(IDA, "ida_IPCA_INFRAESTRUTURA_*.csv"))):
        ymd = os.path.basename(p)[-12:-4]; d = f"{ymd[:4]}-{ymd[4:6]}-{ymd[6:]}"
        c = curva(d)
        if c is None: continue
        real, pre = c
        sw = sgu = s = w = dur = 0.0
        for r in _carteira(p):
            tx, du, pw = _num(r["Taxa Indicativa (% a.a.)"]), _num(r["Duration (d.u.)"]), _num(r["Peso (%)"])
            if tx is None or not du or not pw: continue
            D = du / 252
            s += (tx - real(D)) * pw; sgu += gross_up(tx, D, real, pre) * pw; dur += D * pw; w += pw
        rec = {"infra_spread": s / w, "infra_gu": sgu / w, "infra_dur": dur / w} if w else {}
        pd_ = os.path.join(IDA, f"ida_DI_{ymd}.csv")
        if os.path.exists(pd_):
            sd = wd = 0.0
            for r in _carteira(pd_):
                tx, du, pw = _num(r["Taxa Indicativa (% a.a.)"]), _num(r["Duration (d.u.)"]), _num(r["Peso (%)"])
                if tx is None or not pw: continue
                sp = (tx / 100 - 1) * pre((du or 252) / 252) if tx > 30 else tx     # "% do DI" -> spread aproximado sobre o DI
                sd += sp * pw; wd += pw
            if wd: rec["di_spread"] = sd / wd
        if rec: out[d] = rec
    return out

def main():
    inf, cdi, anb = idex_infra(), idex_cdi(), ida()
    linhas = []
    for d in sorted(set(inf) | set(cdi)):
        if d < "2021-01-01": continue
        r = {"data": d, "fonte": "IDEX", **inf.get(d, {})}
        if d in cdi: r["di_spread"] = cdi[d]
        if "infra_gu" in r and "di_spread" in r: r["dif"] = r["infra_gu"] - r["di_spread"]
        linhas.append(r)
    for d in sorted(anb):
        r = {"data": d, "fonte": "ANBIMA IDA", **anb[d]}
        if "infra_gu" in r and "di_spread" in r: r["dif"] = r["infra_gu"] - r["di_spread"]
        linhas.append(r)
    cols = ["data", "fonte", "infra_spread", "infra_gu", "infra_dur", "di_spread", "dif"]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for r in linhas:
            w.writerow({k: (round(r[k], 4) if isinstance(r.get(k), float) else r.get(k, "")) for k in cols})
    for fonte in ("IDEX", "ANBIMA IDA"):
        L = [r for r in linhas if r["fonte"] == fonte]
        print(f"{fonte}: {len(L)} dias, {L[0]['data']} → {L[-1]['data']}")
        for r in L[-2:]:
            print("   ", {k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()})

if __name__ == "__main__":
    if "--sem-baixar" not in sys.argv:
        baixa()
    main()
