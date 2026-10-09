# -*- coding: utf-8 -*-
"""Escreve na aba "Claude" do XPMod.xlsx (Excel aberto, via COM) o bloco ANBIMA de alocação da PF por segmento, a partir de
data/anbima_alocacao_segmentos_serie.csv. Substitui as linhas 69+ (bloco anterior). Não salva a planilha."""
import time, datetime as dt, os, pandas as pd, win32com.client
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data"); R0 = 69
S = pd.read_csv(os.path.join(DATA, "anbima_alocacao_segmentos_serie.csv"))
C = [("cdb", "CDB/RDB"), ("lci_lca", "LCI/LCA"), ("tit_publicos", "Títulos públicos / Tesouro Direto"), ("credito_privado", "Crédito privado (CRA/CRI/LF/deb./LIG/LC/compromissadas/outros)"), ("coe", "COE"), ("acoes", "Ações"),
     ("fundos_rf", "Fundos 555 - renda fixa"), ("fundos_mm", "Fundos 555 - multimercados"), ("fundos_acoes", "Fundos 555 - ações"), ("fundos_555", "Fundos 555 (total)"),
     ("fii", "FII"), ("fidc", "FIDC"), ("fip", "FIP"), ("etf", "ETF"), ("estruturados", "Estruturados/ETF (total)"), ("poupanca", "Poupança"), ("caixa", "Caixa"), ("previdencia", "Previdência"), ("total", "TOTAL")]
SEGS = [("varejo_tradicional", "Varejo tradicional"), ("varejo_alta_renda", "Varejo alta renda"), ("private", "Private")]
NC = 2 + S.groupby("seg").size().max()

def ret(f):
    for _ in range(40):
        try: return f()
        except Exception as e:
            if "rejected" in str(e).lower() or "-2147418111" in str(e) or "Workbooks" in str(e): time.sleep(2)
            else: raise
    raise RuntimeError("Excel ocupado")

def pad(row): return row + [None] * (NC - len(row))
def fonte(f): return "anexo" if f.startswith("anexo") else "mensal" if f.startswith("estat") else "coletiva"

def main():
    wb = ret(lambda: [w for w in win32com.client.GetActiveObject("Excel.Application").Workbooks if "XPMod" in w.Name][0]); ws = wb.Sheets("Claude")
    ret(lambda: ws.Range(ws.Cells(R0, 1), ws.Cells(R0 + 400, 80)).Clear())
    rows = [pad(["ANBIMA - alocação da pessoa física por classe e segmento (R$ bi). Fontes: (a) Anexo do Boletim de Private e Varejo, dezembros de 2013 a 2025, série revisada; (m) edições das Estatísticas de Varejo/Private (2014-ago/26, recuperadas do Wayback e do site); (c) coletivas de imprensa em PDF (jun/16-jun/20, % x total por segmento). Scripts: dados_anbima_alocacao_{anual,segmentos,coletivas,serie}.py; escrito por escreve_claude_anbima.py em " + dt.date.today().strftime("%d/%m/%Y")]),
            pad(["Ressalvas: previdência só entra no varejo a partir de dez/23 (anexo) / ago/24 (mensal) - % calculados ex-previdência; poupança do varejo só a partir de 2014; o anexo de 2025 revisou dez/24 do varejo tradicional; nas coletivas, 'demais produtos' não está aberto (fica fora das classes); private 2014-15: CDB = captação bancária (inclui LF/compromissadas) e LCI/LCA = lastro imobiliário+agrícola (inclui CRI/CRA); private = clientes > R$ 5 mi (R$ 3 mi antes de 2019)."]),
            pad([None])]
    for seg, nome in SEGS:
        d = S[S.seg == seg].sort_values("data"); prev = d.previdencia.where(d.previdencia > 0); base = (d.total - prev.fillna(0)).tolist()
        rows.append(pad([nome] + [dt.datetime(int(str(x)[:4]), int(str(x)[4:]), 1) for x in d.data]))
        rows.append(pad(["fonte"] + [fonte(f) for f in d.fonte]))
        for k, lab in C:
            if k not in d.columns or (d[k].fillna(0) == 0).all(): continue
            col = prev if k == "previdencia" else d[k]
            rows.append(pad([lab] + [None if (pd.isna(v) or (v == 0 and k != "total")) else round(v / 1e3, 1) for v in col]))
        rows.append(pad([None])); rows.append(pad(["% do total ex-previdência"]))
        for k, lab in C:
            if k in ("total", "previdencia") or k not in d.columns or (d[k].fillna(0) == 0).all(): continue
            rows.append(pad([lab] + [None if (pd.isna(v) or v == 0 or b == 0) else round(100 * v / b, 1) for v, b in zip(d[k], base)]))
        rows.append(pad([None]))
    nr = len(rows); rng = ws.Range(ws.Cells(R0, 1), ws.Cells(R0 + nr - 1, NC)); ret(lambda: setattr(rng, "Value", rows))
    ws.Range(ws.Cells(R0 + 3, 2), ws.Cells(R0 + nr, NC)).NumberFormat = "#,##0.0"
    for i, row in enumerate(rows):
        r = R0 + i; a = row[0]
        if isinstance(a, str) and a.startswith(("Varejo", "Private", "ANBIMA", "% do total", "TOTAL")): ws.Cells(r, 1).Font.Bold = True
        if isinstance(row[1], dt.datetime): rg = ws.Range(ws.Cells(r, 2), ws.Cells(r, NC)); rg.NumberFormat = "mmm/yy"; rg.Font.Bold = True
        if a == "fonte": rg = ws.Range(ws.Cells(r, 1), ws.Cells(r, NC)); rg.Font.Italic = True; rg.Font.Size = 8
    ws.Columns(1).ColumnWidth = max(ws.Columns(1).ColumnWidth, 44)
    print("escrito", R0, "a", R0 + nr - 1, "| colunas", NC, "| salvo?", wb.Saved)

if __name__ == "__main__": main()
