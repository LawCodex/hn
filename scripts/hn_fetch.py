#!/usr/bin/env python3
"""Honduras: Biblioteca Virtual of the Tribunal Superior de Cuentas (TSC,
https://www.tsc.gob.hn/biblioteca/) — a public legal library of laws, codes, decrees and
regulations, each item linking the PDF of the norm (mostly the La Gaceta publication).
(The Congreso Nacional site, congresonacional.hn, was unreachable.)

Usage: hn_fetch.py [list|download|convert|all]
"""
import json
import os
import re
import sys
import time
import unicodedata
from datetime import date
from urllib.parse import urljoin

import requests
import yaml
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hn_pdfmd as P  # noqa: E402

RAW = os.environ.get("RAW", "/Users/magicaltux/projects/lawcodex/_raw/hn")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "LawCodex/1.0 (+https://github.com/LawCodex)"
BASE = "https://www.tsc.gob.hn/biblioteca/"
TODAY = date.today().isoformat()
s = requests.Session()
s.headers["User-Agent"] = UA
_last = [0.0]


def get(url, binary=False):
    for k in range(5):
        w = 1.0 - (time.time() - _last[0])
        if w > 0:
            time.sleep(w)
        _last[0] = time.time()
        try:
            r = s.get(url, timeout=(30, 600))
            if r.status_code == 200:
                return r.content if binary else r.content.decode("utf-8", "replace")
            if r.status_code == 404:
                return None
            print("HTTP", r.status_code, url, file=sys.stderr, flush=True)
        except requests.RequestException as e:
            print("ERR", url, e, file=sys.stderr, flush=True)
        time.sleep(10 * (k + 1))
    return None


def slug(t, n=90):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:n].rstrip("-")


def build_list():
    items = {}
    start = 0
    while True:
        html = get(f"{BASE}index.php?start={start}")
        if not html:
            break
        found = re.findall(r'href="(/biblioteca/index\.php/([a-z0-9-]+)/(\d+)-[^"#?]+)"', html)
        new = 0
        for href, cat, aid in found:
            if aid not in items:
                items[aid] = {"id": int(aid), "cat": cat, "url": urljoin(BASE, href)}
                new += 1
        if not new:
            break
        start += 10
    for it in items.values():
        cache = os.path.join(RAW, "pages", f"{it['id']}.html")
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        if os.path.exists(cache):
            html = open(cache, encoding="utf-8").read()
        else:
            html = get(it["url"]) or ""
            open(cache, "w", encoding="utf-8").write(html)
        soup = BeautifulSoup(html, "lxml")
        h = soup.select_one("div.item-page h1, div.item-page h2, div.page-header h2, h2[itemprop=headline]") or soup.find("h1")
        if h is None and soup.title:
            h = soup.title
        it["title"] = re.sub(r"\s+", " ", h.get_text(" ", strip=True)) if h else ""
        art = soup.select_one("div.item-page") or soup
        pdfs = [urljoin(it["url"], a["href"]) for a in art.find_all("a", href=True) if a["href"].lower().endswith(".pdf")]
        it["pdfs"] = list(dict.fromkeys(pdfs))
        txt = art.get_text("\n", strip=True)
        it["page_text"] = txt[:3000]
    rows = sorted(items.values(), key=lambda x: x["id"])
    json.dump(rows, open(os.path.join(RAW, "list.json"), "w"), ensure_ascii=False, indent=0)
    from collections import Counter
    print("items", len(rows), Counter(r["cat"] for r in rows), "with pdf", sum(1 for r in rows if r["pdfs"]))


def pdf_path(u):
    return os.path.join(RAW, "pdf", re.sub(r"[^\w.-]", "_", u.split("/web/", 1)[-1])[-150:])


def download():
    os.makedirs(os.path.join(RAW, "pdf"), exist_ok=True)
    for r in json.load(open(os.path.join(RAW, "list.json"))):
        if r["cat"] in SKIP_CATS:
            continue
        for u in r["pdfs"][:3]:
            p = pdf_path(u)
            for k in range(3):
                if os.path.exists(p) and P.pdf_ok(p):
                    break
                c = get(u, binary=True)
                if c:
                    open(p, "wb").write(c)
                else:
                    break
            print("ok" if P.pdf_ok(p) else "BAD", u, flush=True)


def garbled(text):
    """Share of tokens that look like OCR noise; clean text layers score ~0.03-0.06."""
    toks = re.findall(r"\S+", text)
    bad = sum(1 for t in toks if re.search(r"[a-záéíóúñ][A-ZÁÉÍÓÚÑ]|[A-Za-zÁÉÍÓÚÑáéíóúñ]\d|\d[A-Za-zÁÉÍÓÚáéíóú]{2,}|[~_·|\\{}<>@^`]|"
                                       r"[a-zA-Z][.,;:'][a-zA-Z]{2,}", t) and not re.fullmatch(r"\d+[ºª°]|\d+-\d+|[A-Z]\d+", t))
    return bad / max(1, len(toks))


FOLDER = {"codigos": "codigos", "leyes": "leyes", "reglamentos": "reglamentos", "varios": "decretos-y-otros",
          "tratados": "tratados", "normas": "normas", "acuerdos-de-creacion": "acuerdos-de-creacion"}
# TSC internal documents (manuals, plans, guidelines) are not legislation: skipped
SKIP_CATS = {"manuales", "planes", "marcos-rectores"}


def convert():
    st = {"ok": 0, "scanned": 0, "nopdf": 0}
    skipped = []
    used = set()
    for r in json.load(open(os.path.join(RAW, "list.json"))):
        if r["cat"] in SKIP_CATS:
            continue
        pdfs = [u for u in r["pdfs"] if P.pdf_ok(pdf_path(u))]
        if not pdfs:
            st["nopdf"] += 1
            skipped.append((r["id"], r["title"], r["url"], "sin PDF"))
            continue
        pages = []
        for u in pdfs[:3]:
            pages += P.extract_pages(pdf_path(u))
        empty = sum(1 for t in pages if len(t.strip()) < 150)
        if empty <= 0.5 * len(pages) and garbled("\n".join(pages)) > 0.10:
            st["garbled"] = st.get("garbled", 0) + 1
            skipped.append((r["id"], r["title"], r["url"], "texto OCR ilegible"))
            continue
        if empty > 0.5 * len(pages):
            st["scanned"] += 1
            skipped.append((r["id"], r["title"], r["url"], "PDF escaneado (sin capa de texto)"))
            continue
        title = r["title"] or r["url"].rsplit("/", 1)[-1]
        is_const = re.match(r"constituci[óo]n de la rep[úu]blica", title.lower()) is not None
        folder = "constitucion" if is_const else FOLDER.get(r["cat"], r["cat"])
        fn = os.path.join(folder, f"{slug(title)}-{r['id']}.md")
        md = P.lines_to_md(P.clean_pages(pages))
        typ = {"codigos": "code", "leyes": "act", "reglamentos": "regulation", "tratados": "treaty",
               "acuerdos-de-creacion": "decree", "normas": "regulation"}.get(r["cat"], "decree")
        if is_const:
            typ = "constitution"
        m = re.search(r"Decreto\s*(?:No\.?|N[°º]\.?|Número)?\s*(\d+-\d{4})", title + " " + r.get("page_text", ""), re.I)
        front = {"title": title, "identifier": f"Decreto {m.group(1)}" if m else None, "type": typ, "jurisdiction": "hn",
                 "language": "es", "status": "unknown", "source": r["url"], "source_pdf": pdfs[0], "retrieved": TODAY}
        fm = yaml.safe_dump(front, allow_unicode=True, sort_keys=False, width=1000).strip()
        path = os.path.join(REPO, fn)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w", encoding="utf-8").write("\n".join(["---", fm, "---", "", f"# {title}", "",
            "> Texto del PDF publicado en la Biblioteca Virtual del Tribunal Superior de Cuentas.", "", md, ""]))
        st["ok"] += 1
    json.dump(skipped, open(os.path.join(RAW, "skipped.json"), "w"), ensure_ascii=False, indent=0)
    print(st)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd in ("list", "all"):
        build_list()
    if cmd in ("download", "all"):
        download()
    if cmd in ("convert", "all"):
        convert()
