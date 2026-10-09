# -*- coding: utf-8 -*-
"""Índice "pessoa física": constituintes do Ibovespa ponderados pelo nº de acionistas PF de cada companhia (CVM, FRE item 15),
rebalanceado anualmente com o FRE de referência do ano anterior; mais equal-weight dos mesmos nomes.

Entradas: fontes/setor/cvm/fre/fre_cia_aberta_{ano}.zip (dados abertos CVM; o zip do ano Y traz Data_Referencia dez/Y),
          ../monitor-investimentos/data/ibov_carteira/*.json e ibov_comp.json (carteiras teóricas), cotahist/*.csv (preços),
          data/_ibov_precos_ajustados.csv (yfinance, auto_adjust), ../cvm-insider-monitor/state/cd_cvm_map.json e data/_ticker_cnpj_extra.json.
Saídas: data/cvm_fre_acionistas_pf.csv (painel), data/ibov_pf_count_diario.csv (índices base 100 em 02/01/2020), data/ibov_pf_count_pesos.csv.
Teto de 8% por companhia (CAP), excesso redistribuído proporcionalmente. Regras de limpeza: contagem PF > 5x a mediana da própria cia (e > 200 mil) ou > 3 mi → substituída pela mediana (ex.: Sendas 2024);
retorno diário ajustado que diverge > 20 pp do COTAHIST → fica o menor em módulo (corrige glitches do yfinance sem estragar splits);
sem COTAHIST para comparar e |r| > 40% → 0."""
import os, json, glob, zipfile, pandas as pd, numpy as np
CAP = 0.08  # teto por companhia
HERE = os.path.dirname(os.path.abspath(__file__)); MON = os.path.join(HERE, "..", "monitor-investimentos", "data"); DATA = os.path.join(HERE, "data")

def painel_fre():
    rows = []
    for z in sorted(glob.glob(os.path.join(HERE, "fontes", "setor", "cvm", "fre", "fre_cia_aberta_*.zip"))):
        y = int(z[-8:-4]); zf = zipfile.ZipFile(z); n = [x for x in zf.namelist() if f"distribuicao_capital_{y}" in x][0]
        df = pd.read_csv(zf.open(n), sep=";", encoding="latin-1", low_memory=False).sort_values("Versao").groupby("CNPJ_Companhia").last().reset_index()
        for _, r in df.iterrows():
            rows.append(dict(ano_fre=y, ref=str(r.Data_Referencia)[:10], cnpj=r.CNPJ_Companhia, nome=r.Nome_Companhia, pf=pd.to_numeric(r.Quantidade_Acionistas_PF, errors="coerce"),
                             pj=r.Quantidade_Acionistas_PJ, inst=r.Quantidade_Acionistas_Investidores_Institucionais, ff_pct=r.Percentual_Total_Acoes_Circulacao))
    F = pd.DataFrame(rows); med = F.groupby("cnpj").pf.median(); F["pf_bruto"] = F.pf
    sus = (F.pf > 3e6) | ((F.pf > 5 * F.cnpj.map(med)) & (F.pf > 2e5)); F.loc[sus, "pf"] = F.loc[sus, "cnpj"].map(med)
    F.to_csv(os.path.join(DATA, "cvm_fre_acionistas_pf.csv"), index=False); print("FRE painel:", F.shape, "| corrigidos:", int(sus.sum()), F.loc[sus, "nome"].str[:25].tolist()[:6])
    return F

def carteiras():
    S = {}
    for f in sorted(glob.glob(os.path.join(MON, "ibov_carteira", "*.json"))):
        j = json.load(open(f, encoding="utf-8")); S[pd.Timestamp(j["data"])] = j["q"]
    c = json.load(open(os.path.join(MON, "ibov_comp.json"), encoding="utf-8")); S[pd.Timestamp(c["data"])] = {x["cod"]: x["q"] for x in c["itens"]}
    return S

def mapa_cnpj(tickers):
    m = json.load(open(os.path.join(HERE, "..", "cvm-insider-monitor", "state", "cd_cvm_map.json"), encoding="utf-8")); t2c = {t: v["cnpj"] for t, v in m.items()}
    extra = json.load(open(os.path.join(DATA, "_ticker_cnpj_extra.json"), encoding="utf-8"))
    def cn(t):
        if t in t2c: return t2c[t]
        if t in extra: return extra[t]["cnpj"]
        for k, v in t2c.items():
            if k[:4] == t[:4]: return v
    return {t: cn(t) for t in tickers}

def retornos(tickers):
    px = pd.read_csv(os.path.join(DATA, "_ibov_precos_ajustados.csv"), index_col=0, parse_dates=True)
    cot = pd.concat([pd.read_csv(f, parse_dates=["data"]) for f in glob.glob(os.path.join(MON, "cotahist", "*.csv"))]).pivot(index="data", columns="ticker", values="fechamento")
    idx = px.index[px["^BVSP"].notna()]; cot = cot.reindex(idx).ffill(limit=5); px = px.reindex(idx).ffill(limit=5)
    ra = px.pct_change(); rc = cot.pct_change(); R = pd.DataFrame(index=idx); nfix = 0
    for t in tickers:
        if t in ra.columns:
            a = ra[t].copy()
            if t in rc.columns:
                b = rc[t]; div = ((a - b).abs() > 0.20) & b.notna(); fix = div & (b.abs() < a.abs()); a[fix] = b[fix]; nfix += int(fix.sum())
                solo = (a.abs() > 0.40) & b.isna(); a[solo] = 0.0; nfix += int(solo.sum())
            else:
                solo = a.abs() > 0.40; a[solo] = 0.0; nfix += int(solo.sum())
            R[t] = a
        elif t in rc.columns: R[t] = rc[t]
    print("retornos corrigidos:", nfix); return R

def main():
    F = painel_fre(); S = carteiras(); tick_all = sorted({t for q in S.values() for t in q}); mapa = mapa_cnpj(tick_all); R = retornos(tick_all)
    days = R.index[R.index >= "2020-01-02"]; val = valq = 100.0; out = []; pesos = []; prev = None
    for i in range(1, len(days)):
        d = days[i]; y = d.year
        if y != prev:
            fre = F[F.ano_fre == y - 1]; q = S[[x for x in sorted(S) if x <= d][-1]]; w = {}
            for t in q:
                cn = mapa.get(t)
                if not cn or t not in R.columns: continue
                r = fre[fre.cnpj == cn]
                if len(r) and pd.notna(r.pf.iloc[0]): w[t] = float(r.pf.iloc[0])
            byc = {}
            for t in w: byc.setdefault(mapa[t], []).append(t)
            W = {}
            for cn, ts in byc.items():
                qs = sum(q[t] for t in ts)
                for t in ts: W[t] = w[t] * q[t] / qs
            tot = sum(W.values()); W = {t: v / tot for t, v in W.items()}; prev = y
            # teto de CAP por companhia (bases pulverizadas herdadas: Vivo, TIM, Oi), redistribuindo o excesso
            for _ in range(10):
                porc = {}
                for t, v in W.items(): porc[mapa[t]] = porc.get(mapa[t], 0) + v
                exc = {c: v - CAP for c, v in porc.items() if v > CAP}
                if not exc: break
                sobra = sum(exc.values()); livres = {t: v for t, v in W.items() if mapa[t] not in exc}; tl = sum(livres.values())
                for t in list(W):
                    c = mapa[t]
                    if c in exc: W[t] = W[t] * CAP / porc[c]
                    else: W[t] = W[t] + sobra * W[t] / tl
            pesos += [dict(ano=y, ticker=t, peso=v, acionistas_pf=w[t]) for t, v in W.items()]
            print(y, "nomes", len(W), "/", len(q), "| top:", [(t, round(v * 100, 1)) for t, v in sorted(W.items(), key=lambda x: -x[1])[:5]])
        row = R.loc[d]; r = {t: row[t] for t in W if pd.notna(row[t])}
        if r: val *= 1 + sum(W[t] * r[t] for t in r) / sum(W[t] for t in r); valq *= 1 + sum(r.values()) / len(r)
        out.append(dict(data=d, pf_count=val, equal=valq))
    I = pd.DataFrame(out).set_index("data")
    base = pd.read_csv(os.path.join(DATA, "ibov_ex_petr_vale_diario.csv"), index_col=0, parse_dates=True)[["ibov", "ex_petr_vale"]]
    base = base / base.loc[I.index[0]].values * 100; I = I.join(base, how="left"); I.index.name = "data"
    I.round(3).to_csv(os.path.join(DATA, "ibov_pf_count_diario.csv")); pd.DataFrame(pesos).round(5).to_csv(os.path.join(DATA, "ibov_pf_count_pesos.csv"), index=False)
    ye = I.resample("YE").last(); Y = (ye / ye.shift() - 1) * 100; Y.iloc[0] = (ye.iloc[0] / 100 - 1) * 100; Y.index = Y.index.year
    print("\nretorno anual, %:"); print(Y.round(1).to_string()); print("acumulado:", I.iloc[-1].round(1).to_dict())

if __name__ == "__main__": main()
