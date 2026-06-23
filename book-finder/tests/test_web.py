"""Offline tests for the web layer and the optional Libby adapter."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bookfinder import library, web  # noqa: E402
from bookfinder.models import Access, Result  # noqa: E402


def test_render_results_escapes_and_badges(monkeypatch):
    fake = [Result(source="Project Gutenberg", title="<script>x</script>",
                   authors=["A. Author"], access=Access.FREE,
                   url="https://example/book", note="free")]
    monkeypatch.setattr(web, "aggregate", lambda q: fake)

    out = web._render_results("anything", free_only=False)
    assert "&lt;script&gt;" in out          # title is HTML-escaped
    assert "<script>x</script>" not in out  # no raw injection
    assert "FREE" in out


def test_render_results_free_only_filters(monkeypatch):
    fake = [
        Result(source="s", title="freebie", access=Access.FREE, url="u1"),
        Result(source="s", title="lendme", access=Access.BORROW, url="u2"),
    ]
    monkeypatch.setattr(web, "aggregate", lambda q: fake)

    out = web._render_results("q", free_only=True)
    assert "freebie" in out and "lendme" not in out


def test_libby_noop_without_key(monkeypatch):
    monkeypatch.delenv("BOOKFINDER_OVERDRIVE_LIBRARY", raising=False)
    assert library.search_overdrive("anything") == []


def test_libby_parses_items(monkeypatch):
    payload = {"items": [{
        "title": "Borrowable Book", "id": "abc123",
        "creators": [{"name": "Jane Doe", "role": "Author"},
                     {"name": "Narrator Person", "role": "Narrator"}],
    }]}
    monkeypatch.setattr(library, "get_json", lambda url, params=None: payload)

    results = library.search_overdrive("x", library="lapl")
    assert len(results) == 1
    r = results[0]
    assert r.access is Access.BORROW
    assert r.authors == ["Jane Doe"]        # only Author role kept
    assert "lapl" in r.source
