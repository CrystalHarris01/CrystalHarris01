"""Minimal web UI for bookfinder — standard library http.server only.

Run:  python -m bookfinder.web   (then open http://localhost:8000)

Reuses cli.aggregate() so the web and CLI paths return identical results.
This serves a search page and a small JSON API; it does not bypass any
paywall or DRM — it only surfaces lawful free/borrowable copies.
"""

from __future__ import annotations

import html
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .cli import _ACCESS_LABEL, aggregate
from .models import Access

_BADGE = {
    Access.FREE: "#1a7f37",
    Access.BORROW: "#9a6700",
    Access.PREVIEW: "#0969da",
    Access.UNKNOWN: "#57606a",
}

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>bookfinder — find books legally</title>
<style>
 :root {{ font-family: system-ui, sans-serif; }}
 body {{ max-width: 760px; margin: 2rem auto; padding: 0 1rem; color:#1f2328; }}
 h1 {{ margin-bottom: .25rem; }}
 .sub {{ color:#57606a; margin-top:0; }}
 form {{ display:flex; gap:.5rem; margin:1.5rem 0; }}
 input[type=text] {{ flex:1; padding:.6rem .8rem; font-size:1rem;
   border:1px solid #d0d7de; border-radius:6px; }}
 button {{ padding:.6rem 1rem; font-size:1rem; border:0; border-radius:6px;
   background:#1f6feb; color:#fff; cursor:pointer; }}
 label.free {{ font-size:.85rem; color:#57606a; }}
 .card {{ border:1px solid #d0d7de; border-radius:8px; padding:1rem;
   margin:.75rem 0; }}
 .badge {{ display:inline-block; padding:.1rem .5rem; border-radius:999px;
   color:#fff; font-size:.75rem; font-weight:600; }}
 .card a {{ color:#0969da; text-decoration:none; word-break:break-all; }}
 .meta {{ color:#57606a; font-size:.9rem; margin:.3rem 0; }}
 .note {{ color:#57606a; font-size:.85rem; }}
 footer {{ margin-top:2rem; color:#57606a; font-size:.85rem; }}
</style></head><body>
<h1>bookfinder</h1>
<p class="sub">Find lawful, free, or borrowable copies of a book.</p>
<form method="get" action="/search">
  <input type="text" name="q" placeholder="title and/or author" value="{q}"
    autofocus required>
  <button type="submit">Search</button>
</form>
<label class="free"><input type="checkbox" name="free" form="ff" {free_checked}
  onchange="location.href='/search?q={q_url}'+(this.checked?'&free=1':'')">
  free to read now only</label>
{results}
<footer>Sources: Project Gutenberg · Open Library · Internet Archive.
 This tool surfaces copies that are already free or lawfully lendable — it
 does not remove paywalls or DRM. In-copyright titles point you to a library
 hold or purchase.</footer>
</body></html>"""


def _render_results(query: str, free_only: bool) -> str:
    if not query:
        return ""
    results = aggregate(query)
    if free_only:
        results = [r for r in results if r.access is Access.FREE]
    if not results:
        return ('<div class="card">No legal free/borrowable copies found. '
                'Try your library app (Libby/OverDrive) or a bookstore.</div>')
    cards = []
    for r in results:
        cards.append(
            '<div class="card">'
            f'<span class="badge" style="background:{_BADGE[r.access]}">'
            f'{_ACCESS_LABEL[r.access]}</span> '
            f'<strong>{html.escape(r.title)}</strong>'
            f'<div class="meta">by {html.escape(r.author_str)} · '
            f'{html.escape(r.source)}</div>'
            f'<a href="{html.escape(r.url)}" target="_blank" rel="noopener">'
            f'{html.escape(r.url)}</a>'
            + (f'<div class="note">{html.escape(r.note)}</div>' if r.note else '')
            + '</div>'
        )
    return "".join(cards)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # quieter console
        pass

    def _send(self, body: str, content_type="text/html; charset=utf-8", code=200):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        query = (params.get("q", [""])[0]).strip()
        free_only = params.get("free", ["0"])[0] in ("1", "true", "on")

        if parsed.path == "/api/search":
            results = aggregate(query)
            if free_only:
                results = [r for r in results if r.access is Access.FREE]
            payload = [{
                "source": r.source, "title": r.title, "authors": r.authors,
                "access": r.access.value, "url": r.url, "note": r.note,
            } for r in results]
            self._send(json.dumps(payload, indent=2), "application/json")
            return

        if parsed.path in ("/", "/search"):
            page = PAGE.format(
                q=html.escape(query, quote=True),
                q_url=html.escape(query, quote=True),
                free_checked="checked" if free_only else "",
                results=_render_results(query, free_only),
            )
            self._send(page)
            return

        self._send("<h1>404</h1>", code=404)


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"bookfinder web UI on http://{host}:{port}  (Ctrl-C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping…")
        server.shutdown()


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(prog="bookfinder.web")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    args = p.parse_args()
    serve(args.host, args.port)
