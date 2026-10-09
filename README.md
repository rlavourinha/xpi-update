# XP Inc. (XP / XPBR31) — Update

Update de XP Inc., iniciado em 08/10/2026, período de referência **2T26** (próximo resultado: 3T26, meados de novembro).
Mesmo padrão do update da Cyrela (`../cyrela/`): fontes primárias, raciocínio próprio, dashboard/deck
HTML autocontido (SVG inline, sem CDN de JS) e modelo em Excel no estilo JGP (FCFE/Ke).

Ponto de partida histórico: cobertura antiga do usuário na Genoa (2017–2020) em
`OneDrive\Arquivo\Genoa\3. Financial\8. XP\` — modelo `XPIMod.xlsx` (ago/2020), F-1 do IPO, deck "XP Investimentos" (set/2019),
dados ANBIMA de distribuição. Serve de "então × agora": o modelo de 2020 projetava receita bruta de R$ 33,9 bi em 2025; o real foi R$ 19,4 bi.

## Estrutura

```
fontes/sec/   todos os 6-K (exhibits 99.x), 20-F, F-1/424B da SEC EDGAR (CIK 1787425) — baixa_sec.py
fontes/ri/    kit do RI via api.mziq.com: 2019_4T..2026_2T × {rel=release, apr=apresentação, dfs=DFs consolidadas},
              bxp = DFs do Banco XP (2T25, 4T25), Historical Financials 2Q26.xlsx (planilha oficial de séries),
              apresentação institucional 2026; _manifest.py guarda os IDs do MZ e rebaixa o que faltar
data/         historical_financials.json — séries limpas da planilha do RI (dados_hist_fin.py)
_xpimod_dump.txt, _deck_antigo_2019.txt — dumps do material antigo da Genoa (referência, não fonte)
```

## Fontes e como acessar

- **SEC EDGAR** é a fonte primária parseável: `data.sec.gov/submissions/CIK0001787425.json` (header User-Agent obrigatório)
  → `index.json` de cada filing → exhibits `*_ex9901.htm` (release) e `*_ex9902.htm`. 20-F anual (xp-20251231.htm).
- **Site de RI** (investors.xpinc.com, MZ Group) devolve 403 para curl/WebFetch nas páginas, mas o CDN
  `api.mziq.com/mzfilemanager/v2/d/d1820734-.../<id>?origin=2` aceita curl com UA de navegador. Os IDs saem do HTML
  da página (pane do navegador + JS `querySelectorAll('main table a[href]')`), ano a ano no combobox.
- **Planilha oficial** ("Planilha" no menu Informações Financeiras): Historical Financials XQYY.xlsx — abas Highlights
  (new 1Q21+ / discontinued 1Q18–4Q25), KPIs 1Q18+, Managerial P&L (new/discontinued), Accounting IS 1Q18+, Balance Sheet 1Q20+, Capital.
  Taxonomia mudou no 1T26: "Institucional" migrou para Banco de Atacado e a linha "Outras receitas" foi extinta
  (absorvida na margem financeira das linhas de negócio) → usar aba "new" para comparar.
- Estrutura acionária (18/08/2026): XP Control LLC 19,04% do capital / 70,31% dos votos (classe B = 10 votos);
  free float 80,38%; 508,5 mi ações totais (573 mi em 2021). Itaúsa não aparece mais como acionista relevante.
- Gravações dos calls estão no RI só em áudio (não baixadas). Transcrições: verificar 6-K.

## Convenções (as mesmas da casa)

- HTML autocontido, SVG inline, `.replace(sentinela)` em templates, chip de versão no cabeçalho, selo "novo" por versão.
- Gráficos: série mais longa disponível; sem barras empilhadas densas; real + MM12 quando volátil.
- Slides: imagem > texto; caixa verde de uma frase; agente de formatação roda sem pedir.
- Números sempre com fonte primária (release/planilha/DF/20-F); estimativa marcada como estimativa.

## Roteiro proposto (em discussão)

1. **O negócio** — o que uma plataforma de investimentos faz, de onde vem o take rate, por que virou banco (float, crédito, cartão).
2. **A indústria** — distribuição de investimentos no Brasil (ANBIMA, B3, Susep, BCB): bancos × plataformas, assessores (CVM 178/179), take rate da indústria.
3. **A companhia** — KPIs, receita por linha, custos/IFA, balanço e capital (Basileia, RWA), mix caminhando para o balanço.
4. **Resultados e qualidade do lucro** — gerencial × contábil, MtM de renda fixa, come-cotas, recompras × lucro.
5. **Soma das partes e valuation** — modelo XPMod (FCFE/Ke), sensibilidade, comparação com consenso só no fim.

## Dados setoriais — o que a XP cita e o que temos de público

**O que o F-1 (2019) e o 20-F (2025) citam.** As fontes "oficiais" de mercado da companhia são poucas:
- F-1: relatório encomendado à **Oliver Wyman** (set/2019; consentimento no Exhibit 23.3) — TAM de R$ 7,9 tri (2018), bancos com 93% do AuC de varejo, independentes 7% → **previsão de 25% em 2024**; poupança 20% dos ativos; 5 mil → 9 mil assessores (2015–19); mercado adjacente de R$ 487 bi de receita (seguros, cartões, crédito); previdência R$ 1,8 tri crescendo 15% a.a. Gráficos com "Source: ANBIMA, Valor, Infomoney survey May/2017, Financial Times, Platforum. Oliver Wyman analysis".
- 20-F 2025: sem consultoria; "internal research and public data from **Anbima**" → ativos de PF na XP ≈ 12% de um mercado de R$ 8,6 tri; concentração dos 5 bancos via **BCB e Fenaprevi** (63% dos depósitos de R$ 6,5 tri; 85% dos R$ 1,5 tri de previdência aberta; 69% do crédito PF; 58% do crédito PJ); poupança 11,2% do volume investido por PF (Anbima dez/25); macro de FGV/IBGE/IPEA/BCB/Bloomberg. Lista genérica de fontes: BCB, IBGE, IPEA, CNseg, ANS, Fenaprevi, Abrapp, B3, ANBIMA, Nielsen, FGV/IBRE.
- Em nenhum dos dois há série pública de take rate, de market share por distribuidor ou de assessores por plataforma: isso é construção nossa.

**Opções públicas, por pergunta (status testado em 08/10/26):**

| Pergunta | Fonte | Acesso |
|---|---|---|
| Tamanho e mix do mercado de investimentos PF (varejo, alta renda, private; por produto; poupança) | ANBIMA — Estatísticas de Varejo / Private / Gestão de Patrimônio (mensal/semestral), `data.anbima.com.br` | portal SPA (JS); baixar pelo navegador; o usuário já usou essas planilhas em 2017–20 (Genoa) |
| Indústria de fundos (PL, captação líquida por classe, taxas) | ANBIMA Consolidado Histórico de Fundos; **CVM dados abertos** `FI/CAD`, `FI/DOC/CDA`, `FI/DOC/INF_DIARIO` | CVM: CSV direto (ok); ANBIMA: html ok |
| Nº de investidores PF na B3, custódia, perfil (idade, gênero, UF) | B3 — Histórico/Perfil Pessoas Físicas (mensal desde 2002) | página JS; planilha via navegador |
| Assessores de investimento: quantidade, vínculo por corretora (XP vs BTG etc.) | **CVM dados abertos `AGENTE_AUTON/`** (cadastro de assessores com instituição vinculada) + `INTERMED/` | CSV direto (ok) — permite contar assessores por plataforma ao longo do tempo |
| Previdência aberta: reservas, captação, share XPV&P vs bancos | **Susep SES** (base mensal por entidade/produto PGBL-VGBL) + Fenaprevi | SES ok (ASP.NET); Fenaprevi relatórios PDF |
| Banco XP: balanço, carteira, Basileia, comparáveis (BTG, Inter, Nubank) | **BCB IF.data** (trimestral, por conglomerado prudencial) + API Olinda | portal ok; endpoint Olinda a ajustar |
| Poupança, crédito PF/PJ, depósitos, Selic | **BCB SGS API** (`api.bcb.gov.br/dados/serie/bcdata.sgs.<id>`) | ok (testado) |
| Volumes negociados, DATs, market share de corretoras em bolsa | B3 boletins / ranking de corretoras (mensal) | página JS |
| Ofertas (ECM/DCM) e coordenadores — share de XP em emissões | ANBIMA Boletins de Mercado de Capitais; CVM `OFERTA/` | CVM CSV ok |
| Comparáveis listados (BTG, Itaú, Nubank, Inter, B3) | CVM `CIA_ABERTA/` (ITR/DFP/FRE) e releases | CSV ok |

**Primeira prioridade (hipóteses escolhidas):** (1) plataforma cresce → ANBIMA varejo + B3 PF + CVM assessores; (2) qualidade do lucro → só a companhia (DFs); (3) competição/take rate → CVM assessores por instituição, IF.data (BTG/Inter/Nubank), ANBIMA fundos (taxas), CVM 179.

## Monitor de atividade na B3 (DATs, minis, aluguel)

- `dados_b3_bdi_diario.py` — coleta diária do Boletim Diário do Mercado (API pública `arquivos.b3.com.br/bdi/table`, janela de ~21 pregões): negócios em ações por mercado, negócios e contratos por derivativo (WIN, WDO, IND, DOL, DI1, DAP, BIT), contratos/dia com e sem minis, aluguel de ações negócio a negócio agregado por participante (fatia XP = XP+Rico+Clear, BTG+Necton, Itaú, Ágora, Inter) e participação da pessoa física. Saída: `data/b3_bdi_diario.csv` (1 linha/pregão), `data/b3_bdi_btc_participantes.json`, `data/b3_bdi_pf_mensal.csv`. **Rodar todo dia útil** (a janela anda; o script é idempotente). Brutos em `fontes/setor/b3/bdi/raw/`.
- `data/b3_ri_operacional_mensal.csv` — série mensal longa do RI da B3 (planilha "dados operacionais", `fontes/setor/b3/ri/`): ADV de derivativos por produto e RPC desde 2005 (minis convertidos em contratos padrão dentro de índices/câmbio), ADTV de ações por mercado desde 2000, participação PF/institucional/estrangeiro desde 1999, aluguel de ações (volume, nº de operações, estoque) desde 2000.
- `monitor-investimentos/data/b3_volume_diario.csv` — negócios/dia em ações pelo COTAHIST desde 2019 (nowcast dos DATs: corr 0,69 em variação t/t).
