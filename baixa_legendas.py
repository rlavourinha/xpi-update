"""Baixa legendas automáticas (YouTube) das gravações dos calls listadas em fontes/ri/_calls.json e converte em texto limpo.
Saída: fontes/webcast/<ano>_<tri>_call.txt. Só YouTube por enquanto (Vimeo/Zoom: ver _calls.json)."""
import json, os, re, subprocess, sys, glob
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = HERE + "/fontes/webcast"
calls = json.load(open(HERE + "/fontes/ri/_calls.json"))
def vtt_to_text(path):
    lines, last = [], None
    for ln in open(path, encoding="utf-8", errors="ignore"):
        ln = ln.strip()
        if not ln or "-->" in ln or ln.startswith(("WEBVTT", "Kind:", "Language:")) or re.fullmatch(r"\d+", ln): continue
        ln = re.sub(r"<[^>]+>", "", ln)
        if ln != last: lines.append(ln); last = ln
    # legendas auto do YouTube repetem a linha anterior em cada cue: remove duplicatas consecutivas já feitas; junta
    return " ".join(lines)
for per, url in sorted(calls.items()):
    if "youtube.com" not in url and "youtu.be" not in url: continue
    dest = f"{OUT}/{per}_call.txt"
    if os.path.exists(dest): continue
    base = f"{OUT}/{per}"
    r = subprocess.run([sys.executable, "-m", "yt_dlp", "--skip-download", "--write-auto-sub", "--write-sub",
                        "--sub-lang", "en-orig,en,pt-orig,pt", "--sub-format", "vtt", "-o", base, url],
                       capture_output=True, text=True)
    vtts = glob.glob(base + "*.vtt")
    if not vtts: print(per, "SEM LEGENDA", r.stderr[-300:]); continue
    pref = sorted(vtts, key=lambda p: (".en-orig" not in p, ".pt-orig" not in p, ".en." not in p))[0]
    txt = vtt_to_text(pref)
    open(dest, "w", encoding="utf-8").write(f"# {per} earnings call — legendas automáticas {os.path.basename(pref)} — {url}\n\n" + txt)
    print(per, os.path.basename(pref), len(txt.split()), "palavras", flush=True)
