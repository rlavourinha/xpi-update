# -*- coding: utf-8 -*-
"""Coletor diário do Boletim Diário do Mercado (BDI) da B3 — API pública, sem autenticação, janela de ~21 pregões.

POST https://arquivos.b3.com.br/bdi/table/{Tabela}/{d}/{d}/{página}/{tamanho}  (corpo {})  -> {"table": {"columns", "values", "texts"}}
Catálogo: GET /bdi/table/classifications (salvo em fontes/setor/b3/bdi/_classifications.json).

Tabelas coletadas (uma linha por pregão em data/b3_bdi_diario.csv):
  DailyAverageStocks        negócios/dia e volume em ações (linha "Dia")
  StocksOperationSummary    negócios por mercado: à vista (lote padrão, fracionário, demais), opções, termo
  DerivativesOperation2     negócios e contratos por contrato: WIN, WDO, IND, DOL, DI1, DAP, BIT e total
  DailyAverageDerivatives2  contratos/dia com e sem minis (linha "Dia")
  BTBTrade                  aluguel de ações negócio a negócio com o participante: fatia XP (XP+Rico+Clear), BTG (+Necton), Itaú, Ágora
  SharesInvesVolum          participação dos investidores (acumulado do mês até a data de referência): pessoa física compras/vendas/%
Mensal (data/b3_bdi_pf_mensal.csv): SharesInvesVolumMonthly, participação por segmento (à vista, opções, termo...).

Uso: python dados_b3_bdi_diario.py            # coleta os pregões da janela ainda não coletados
     python dados_b3_bdi_diario.py --desde 2026-09-01 --ate 2026-10-07
Idempotente: não duplica dias; JSONs brutos em fontes/setor/b3/bdi/raw/ (fora do git). Rodar todo dia útil (a janela anda)."""
import os, sys, json, time, re, csv, datetime as dt, urllib.request, collections
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data"); RAW = os.path.join(HERE, "fontes", "setor", "b3", "bdi", "raw")
os.makedirs(RAW, exist_ok=True); os.makedirs(DATA, exist_ok=True)
CSV = os.path.join(DATA, "b3_bdi_diario.csv"); CSVM = os.path.join(DATA, "b3_bdi_pf_mensal.csv"); BTCJ = os.path.join(DATA, "b3_bdi_btc_participantes.json")
URL = "https://arquivos.b3.com.br/bdi/table/{t}/{d}/{d}/{pg}/{n}"
HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128 Safari/537.36", "Accept": "application/json", "Content-Type": "application/json"}
PAUSA = 0.35
GRUPOS = {"xp": r"\bXP\b|RICO|CLEAR", "btg": r"BTG|NECTON", "itau": r"\bITAU\b", "agora": r"\bAGORA\b|BRADESCO", "inter": r"\bINTER\b", "genial": r"GENIAL", "toro": r"\bTORO\b", "safra": r"SAFRA", "santander": r"SANTANDER", "bb": r"BANCO DO BRASIL"}

def post(t, d, pg=1, n=1000, tent=3):
    for i in range(tent):
        try:
            req = urllib.request.Request(URL.format(t=t, d=d, pg=pg, n=n), data=b"{}", headers=HDR)
            with urllib.request.urlopen(req, timeout=90) as r: j = json.load(r)
            time.sleep(PAUSA); return (j.get("table") or {})
        except Exception as e:
            if i == tent - 1: print(f"  {t} {d} p{pg}: {e}", file=sys.stderr); return {}
            time.sleep(3 * (i + 1))

def raw(t, d, tab):
    try: json.dump(tab, open(os.path.join(RAW, f"{t}_{d}.json"), "w", encoding="utf-8"), ensure_ascii=False)
    except Exception: pass

def num(x):
    try: return float(x)
    except Exception: return None

def coleta_dia(d):
    """Retorna dict com a linha do dia ou None se a B3 não tiver o pregão."""
    row = {"data": d}
    t = post("DailyAverageStocks", d, n=20); vals = t.get("values") or []
    if not vals: return None
    raw("DailyAverageStocks", d, t)
    for v in vals:
        if str(v[0]).strip() == "Dia": row["acoes_negocios"] = num(v[1]); row["acoes_vol_mi"] = num(v[2])
        if str(v[0]).strip() == "Mês": row["acoes_negocios_media_mes"] = num(v[1])
    t = post("StocksOperationSummary", d, n=100); raw("StocksOperationSummary", d, t)
    for v in t.get("values") or []:
        k = str(v[0]).strip().upper(); n_ = num(v[1]); vol = num(v[4])
        if k == "TOTAL A VISTA": row["avista_negocios"] = n_; row["avista_vol_mil"] = vol
        elif k == "LOTE PADRAO": row["lote_negocios"] = n_
        elif k == "FRACIONARIO": row["frac_negocios"] = n_
        elif k == "TOTAL DE OPCOES": row["opcoes_negocios"] = n_; row["opcoes_vol_mil"] = vol
        elif k == "TERMO": row["termo_negocios"] = n_
    t = post("DerivativesOperation2", d, n=300); raw("DerivativesOperation2", d, t)
    tot_n = tot_c = 0.0; por = collections.defaultdict(lambda: [0.0, 0.0])
    for v in t.get("values") or []:
        nome = str(v[0]).strip(); tipo = str(v[4]).strip().upper(); n_ = num(v[5]) or 0; c = num(v[6]) or 0
        if not nome or ":" not in nome: continue  # linhas de total/categoria vêm sem código
        cod = nome.split(":")[0].strip().upper()
        tot_n += n_; tot_c += c
        if cod in ("WIN", "WDO", "IND", "DOL", "DI1", "DAP", "BIT", "ISP", "WSP"):
            if "FUTURO" in tipo: por[cod][0] += n_; por[cod][1] += c
    row["deriv_negocios"] = tot_n; row["deriv_contratos"] = tot_c
    for cod in ("WIN", "WDO", "IND", "DOL", "DI1", "DAP", "BIT"): row[f"{cod.lower()}_negocios"] = por[cod][0]; row[f"{cod.lower()}_contratos"] = por[cod][1]
    t = post("DailyAverageDerivatives2", d, n=20); raw("DailyAverageDerivatives2", d, t)
    for v in t.get("values") or []:
        if str(v[0]).strip() == "Dia": row["deriv_contratos_com_minis"] = num(v[1]); row["deriv_contratos_sem_minis"] = num(v[2])
    # aluguel: todas as páginas, agrega por participante (tomador/doador) e por grupo
    tom = collections.Counter(); doa = collections.Counter(); qt_tom = collections.Counter(); pg = 1; n_btc = 0
    while pg <= 400:
        t = post("BTBTrade", d, pg=pg, n=1000); vals = t.get("values") or []
        if not vals: break
        for v in vals:
            n_btc += 1; q = num(v[1]) or 0; tom[str(v[10]).strip()] += 1; doa[str(v[8]).strip()] += 1; qt_tom[str(v[10]).strip()] += q
        if len(vals) < 1000: break
        pg += 1
    row["btc_negocios"] = n_btc; row["btc_paginas"] = pg
    def grupo(cnt, g):
        return sum(n for k, n in cnt.items() if re.search(GRUPOS[g], k.upper()))
    for g in ("xp", "btg", "itau", "agora", "inter"):
        row[f"btc_{g}_tomador"] = grupo(tom, g); row[f"btc_{g}_doador"] = grupo(doa, g)
    row["btc_xp_tomador_qtd"] = sum(q for k, q in qt_tom.items() if re.search(GRUPOS["xp"], k.upper()))
    try:
        J = json.load(open(BTCJ, encoding="utf-8")) if os.path.exists(BTCJ) else {}
        J[d] = {"tomador": dict(tom.most_common()), "doador": dict(doa.most_common())}
        json.dump(J, open(BTCJ, "w", encoding="utf-8"), ensure_ascii=False)
    except Exception as e: print("  btc json:", e, file=sys.stderr)
    t = post("SharesInvesVolum", d, n=100); raw("SharesInvesVolum", d, t)
    ref = ""
    for x in t.get("texts") or []:
        m = re.search(r"at[ée] o dia (\d{2})/(\d{2})/(\d{4})", x.get("textPt", ""))
        if m: ref = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    row["pf_ref"] = ref
    for v in t.get("values") or []:
        k = str(v[0]).strip().lower()
        if "individua" in k or "física" in k or "fisica" in k:
            row["pf_compras_mil"] = num(v[1]); row["pf_compras_pct"] = num(v[2]); row["pf_vendas_mil"] = num(v[3]); row["pf_vendas_pct"] = num(v[4])
    return row

def coleta_mensal():
    """SharesInvesVolumMonthly: participação PF por segmento do mês anterior à data consultada; tenta desde 2022."""
    have = set()
    if os.path.exists(CSVM):
        with open(CSVM, encoding="utf-8") as f: have = {r["mes"] for r in csv.DictReader(f)}
    hoje = dt.date.today(); novos = []
    m = dt.date(2022, 2, 1)
    while m <= hoje:
        mes_ref = (m - dt.timedelta(days=1)).strftime("%Y-%m")
        if mes_ref not in have:
            t = post("SharesInvesVolumMonthly", m.strftime("%Y-%m-%d"), n=100); vals = t.get("values") or []
            if vals:
                raw("SharesInvesVolumMonthly", m.strftime("%Y-%m-%d"), t)
                cols = t.get("columns") or []
                segs = [c.get("friendlyNamePt") for c in cols if c.get("parentId") is None and c.get("friendlyNamePt") != "Tipos de investidores"]
                for v in vals:
                    k = str(v[0]).strip().lower()
                    if "individua" in k or "física" in k or "fisica" in k:
                        r = {"mes": mes_ref, "consulta": m.strftime("%Y-%m-%d")}
                        for i, sg in enumerate(segs):  # pares (R$, %) por segmento
                            if 2 + 2 * i < len(v):
                                key = re.sub(r"\W+", "_", str(sg)).strip("_").lower(); r[f"pf_{key}_rs"] = v[1 + 2 * i]; r[f"pf_{key}_pct"] = v[2 + 2 * i]
                        novos.append(r); have.add(mes_ref)
        m = (m.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
    if novos:
        ex = []
        if os.path.exists(CSVM):
            with open(CSVM, encoding="utf-8") as f: ex = list(csv.DictReader(f))
        allr = ex + novos; keys = sorted({k for r in allr for k in r}, key=lambda k: (k not in ("mes", "consulta"), k))
        with open(CSVM, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); [w.writerow(r) for r in sorted(allr, key=lambda r: r["mes"])]
    print(f"mensal: +{len(novos)} meses")

def salva(allr):
    keys = sorted({k for r in allr for k in r}, key=lambda k: (k != "data", k))
    with open(CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); [w.writerow(r) for r in sorted(allr, key=lambda r: r["data"])]

def main():
    args = sys.argv[1:]; hoje = dt.date.today()
    desde = dt.date.fromisoformat(args[args.index("--desde") + 1]) if "--desde" in args else hoje - dt.timedelta(days=40)
    ate = dt.date.fromisoformat(args[args.index("--ate") + 1]) if "--ate" in args else hoje - dt.timedelta(days=1)
    have = []
    if os.path.exists(CSV):
        with open(CSV, encoding="utf-8") as f: have = list(csv.DictReader(f))
    feitos = {r["data"] for r in have}
    novos = []; d = desde
    while d <= ate:
        s = d.isoformat()
        if d.weekday() < 5 and s not in feitos:
            r = coleta_dia(s)
            if r:
                novos.append(r); print(f"{s}: ações {r.get('acoes_negocios'):,.0f} neg | WIN {r.get('win_negocios'):,.0f} | BTC {r.get('btc_negocios')} (XP tom {r.get('btc_xp_tomador')})", flush=True)
                salva(have + novos)  # grava a cada pregão: uma queda no meio não perde o que já veio
            else: print(f"{s}: sem dados", flush=True)
        d += dt.timedelta(days=1)
    print(f"diário: +{len(novos)} pregões, total {len(have) + len(novos)} em {CSV}")
    if "--sem-mensal" not in args: coleta_mensal()

if __name__ == "__main__": main()
