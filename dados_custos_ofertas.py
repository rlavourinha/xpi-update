# -*- coding: utf-8 -*-
"""Comissionamento das ofertas de ações (o "pool" dos bancos) a partir dos prospectos na CVM (IPE, 2014+).
Entrada: fontes/setor/cvm/ipe/_ofertas_prospectos.csv (oferta × link do prospecto). Baixa cada documento (rad.cvm.gov.br, PDF ou ZIP)
em fontes/setor/cvm/prospectos/, extrai o texto (pdftotext -layout) e lê a tabela "Custos de Distribuição": comissões de coordenação,
colocação, garantia firme, incentivo/sucesso, total de comissões e total de custos, em % do valor da oferta.
Saída: data/cvm_ofertas_custos.csv. Pausa de 2 s entre downloads."""
import os, re, ssl, time, zipfile, io, subprocess, urllib.request, unicodedata, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); PD = os.path.join(HERE, "fontes", "setor", "cvm", "prospectos"); os.makedirs(PD, exist_ok=True)
CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE
def baixa(url, nome):
    p = os.path.join(PD, nome)
    if os.path.exists(p) and os.path.getsize(p) > 20000: return p
    for t in range(4):
        try:
            b = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), context=CTX, timeout=300).read()
            if b[:2] == b"PK":
                z = zipfile.ZipFile(io.BytesIO(b)); pdfs = [n for n in z.namelist() if n.lower().endswith(".pdf")]
                if pdfs: b = z.read(max(pdfs, key=lambda n: z.getinfo(n).file_size))
            open(p, "wb").write(b); time.sleep(2); return p
        except Exception as e:
            time.sleep(5 * (t + 1)); err = e
    print("  falhou", nome, str(err)[:80], flush=True); return None
def texto(p):
    t = p[:-4] + "_raw.txt"
    if not os.path.exists(t):
        subprocess.run(["pdftotext", "-raw", p, t], capture_output=True, timeout=300)
    return open(t, encoding="latin1", errors="ignore").read() if os.path.exists(t) else ""
def norm(s): return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
NUM = re.compile(r"\d{1,3}(?:\.\d{3})*,\d{1,6}%?|\d+,\d{1,6}%?")
LAB = [("coordenacao", r"^comiss[a-z]* de (coordena|estrutura)"), ("garantia", r"^comiss[a-z]* de garantia"), ("colocacao", r"^comiss[a-z]* de coloca"),
       ("incentivo", r"^(remunera|comiss|taxa)[a-z]* (de |discricion)[a-z ]*(incentivo|sucesso)?|^remunera[a-z]* discricion|^comiss[a-z]* de sucesso|^comiss[a-z]* das institui"),
       ("total_comissoes", r"^total de comiss[a-z]*\s*[\.\(\d]|^total de comiss[a-z]*$|^total das comiss"),
       ("total_custos", r"^total de (comiss[a-z]*,? (tributos|impostos|e despesas)|custos|despesas e comiss)|^custo total")]
def valores(linha):
    v = NUM.findall(linha)
    if not v: return None, None
    rs = max((float(x.replace(".", "").replace(",", ".")) for x in v if "%" not in x), default=None)
    ps = [x for x in v if x.endswith("%")]
    if ps: pct = float(ps[0][:-1].replace(",", "."))
    else:
        cand = [float(x.replace(",", ".")) for x in v if "." not in x]
        pct = cand[-1] if cand else None
    return rs, pct
def custos(txt):
    L = [norm(l).strip() for l in txt.split("\n")]
    tabelas, atual = [], {}
    for i, l in enumerate(L):
        for k, pat in LAB:
            if re.search(pat, l):
                rs, pct = valores(re.sub(r"\(\d\)", "", l))
                for j in (1, 2):
                    if pct is None and i + j < len(L): rs, pct = valores(re.sub(r"\(\d\)", "", L[i + j]))
                if pct is None or pct > 20: break
                comps = [c for c in ("coordenacao", "colocacao", "garantia", "incentivo") if c in atual]
                if k == "total_custos":
                    if len(comps) >= 2:  # tabela sem linha "Total de Comissões": total = soma dos componentes
                        atual.update(total_comissoes=round(sum(atual[c] for c in comps), 4), rs=atual.get("_rs", 0), total_somado=True, total_custos=pct)
                        tabelas.append(atual); atual = {}
                    elif tabelas and "total_custos" not in tabelas[-1]: tabelas[-1]["total_custos"] = pct
                elif k == "total_comissoes":
                    atual.update(total_comissoes=pct, rs=rs or atual.get("_rs", 0)); tabelas.append(atual); atual = {}
                elif k not in atual: atual[k] = pct; atual["_rs"] = atual.get("_rs", 0) + (rs or 0)
                break
    ok = [t for t in tabelas if 0.3 <= t.get("total_comissoes", 0) <= 12 and len([k for k in ("coordenacao", "colocacao", "garantia", "incentivo") if k in t]) >= 2]
    if not ok: return {}
    t = max(ok, key=lambda d: d["rs"])
    soma = sum(t.get(k, 0) for k in ("coordenacao", "colocacao", "garantia", "incentivo"))
    t["confere_soma"] = abs(soma - t["total_comissoes"]) <= 0.06
    return t
def main():
    M = pd.read_csv(os.path.join(HERE, "fontes", "setor", "cvm", "ipe", "_ofertas_prospectos.csv"))
    M = M[M.doc.notna()].copy(); rows = []
    for i, r in M.iterrows():
        nome = re.sub(r"[^A-Za-z0-9]+", "_", f"{r.ano}_{str(r.Nome_Emissor)[:40]}") + ".pdf"
        p = baixa(r.doc, nome)
        if not p: continue
        c = custos(texto(p)); rows.append({**{k: r[k] for k in ["data", "ano", "Nome_Emissor", "valor", "ipo", "lider", "rito", "doc_tipo"]}, **c, "arquivo": nome})
        print(r.ano, str(r.Nome_Emissor)[:35].ljust(35), "IPO" if r.ipo else "FO ", c.get("total_comissoes"), c.get("coordenacao"), c.get("colocacao"), c.get("garantia"), c.get("incentivo"), c.get("total_custos"), c.get("confere_soma"), flush=True)
    C = pd.DataFrame(rows); C.to_csv(os.path.join(HERE, "data", "cvm_ofertas_custos.csv"), index=False)
    print("ok", len(C), "com total de comissões:", C.total_comissoes.notna().sum())
if __name__ == "__main__": main()
