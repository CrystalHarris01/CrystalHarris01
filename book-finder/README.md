# bookfinder

Find **lawful** copies of a book — free where it's public domain, borrowable
where a library lending copy exists. It aggregates public catalog APIs and
tells you where you can legally read a title.

It does **not** bypass, remove, or circumvent paywalls or DRM. It only surfaces
copies that are already free or lawfully lendable.

## Sources

| Source            | What it finds                                          |
|-------------------|--------------------------------------------------------|
| Project Gutenberg | Public-domain texts, free to read/download (Gutendex)  |
| Open Library      | Internet Archive lending + readable scans (borrow/free)|
| Internet Archive  | "texts" collection — free where public domain          |

## Usage

No dependencies — standard library only. Requires Python 3.10+.

```bash
cd book-finder
python -m bookfinder "pride and prejudice"
python -m bookfinder --free-only "the time machine wells"
```

Example output:

```
Searching legal sources for: "the time machine wells"

  [FREE] The Time Machine
          by H. G. Wells  ·  Project Gutenberg
          https://www.gutenberg.org/ebooks/35
          Public domain — free to read or download.
```

Access labels:

- **FREE** — public domain / openly licensed; read now.
- **BORROW** — library lending copy; may have a waitlist.
- **CHECK** — catalog record found; verify availability at a library.

## Web UI

A zero-dependency web front end (standard-library `http.server`) reuses the
same aggregation logic:

```bash
python -m bookfinder.web            # http://127.0.0.1:8000
python -m bookfinder.web --port 8099
```

It serves a search page plus a JSON API at `/api/search?q=...&free=1`.

## Library availability (Libby / OverDrive) — optional

OverDrive (the service behind Libby) has **no open public search API**; access
is per-library through the "Thunder" API and needs your consortium key. So this
adapter is opt-in and stays dormant until you set:

```bash
export BOOKFINDER_OVERDRIVE_LIBRARY=lapl   # your Libby library subdomain
```

With it set, borrowable results from your library appear alongside the others.
Without it, everything else works unchanged. This just asks a library you
belong to whether a title is lendable — exactly what the Libby app does.

## Where this won't help

If a book is in copyright and not offered for lending, the lawful paths are a
library hold (try Libby/OverDrive with your library card) or buying it. This
tool will point you to those rather than around them.

## Layout

```
book-finder/
  bookfinder/
    cli.py        # argparse entry point + result formatting
    web.py        # stdlib http.server web UI + JSON API
    sources.py    # one adapter per source
    library.py    # optional Libby/OverDrive adapter (needs a key)
    http.py       # stdlib JSON-over-HTTP helper
    models.py     # Result / Access dataclasses
  tests/
```
