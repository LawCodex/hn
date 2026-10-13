# LawCodex — Honduras (hn)

Honduran legislation as Markdown, from the **Biblioteca Virtual of the Tribunal Superior de
Cuentas (TSC)** (https://www.tsc.gob.hn/biblioteca/), a public legal library maintained by
Honduras' supreme audit institution: the **Constitución de la República (1982)**, **codes**,
**laws**, **decrees and other legislative acts**, **regulations** and treaties, each item with
the PDF of the norm (mostly its publication in *La Gaceta*).

Part of [LawCodex](https://github.com/LawCodex): one public repository per jurisdiction.

Retrieved: **2026-10-13**. Language: Spanish (`es`).

Status: **partial** — see "What is NOT covered".

## What is covered

| Category (library section) | Directory | Files |
|---|---|---|
| Constitución de la República | `constitucion/` | 1 |
| Códigos | `codigos/` | 15 |
| Leyes | `leyes/` | 208 |
| Varios (decrees, legislative and executive acts) | `decretos-y-otros/` | 379 |
| Reglamentos | `reglamentos/` | 330 |
| Acuerdos de creación | `acuerdos-de-creacion/` | 101 |
| Normas | `normas/` | 29 |
| Tratados | `tratados/` | 2 |

Files are named `<title-slug>-<library id>.md`. The text is the PDF's text layer converted to
Markdown (headings for TÍTULO/CAPÍTULO/SECCIÓN, one heading per article). Many PDFs are the
consolidated or published versions collected by the TSC; the date of the version is not
always stated — check `source_pdf`. `status` is `unknown`.

Of the 1,482 library items in these sections, 1,065 were converted; 387 have scanned PDFs
(no text layer; no OCR applied), 14 only a garbled OCR layer, and 16 no downloadable PDF.

## What is NOT covered

- The library is a selection (≈1,500 items) oriented to public administration and audit; it is
  not the complete legislation of Honduras. The Congreso Nacional's site
  (congresonacional.hn) was unreachable and the official gazette *La Gaceta* (ENAG) offers no
  free per-law catalogue.
- Items whose PDF is a scanned image (no OCR) or could not be downloaded.
- TSC internal documents of the library (manuals, plans, "marcos rectores").

## Source

Tribunal Superior de Cuentas — Biblioteca Virtual: listing `index.php?start=N`, item pages
`index.php/<section>/<id>-<slug>`, PDFs under `https://www.tsc.gob.hn/web/leyes/`. Each file's
`source` is the item page and `source_pdf` the PDF.

## Copyright

Honduras' Ley del Derecho de Autor y de los Derechos Conexos (Decreto 4-99-E) excludes official
texts of a legislative, administrative or judicial nature from protection.

## Regenerate

```
python3 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt
RAW=/path/to/scratch .venv/bin/python scripts/hn_fetch.py all
```
