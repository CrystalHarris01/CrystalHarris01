"""Offline tests — no network required. Run: python -m pytest book-finder/tests

These stub the source functions so the sorting/formatting logic is verified
deterministically without hitting live APIs.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bookfinder import cli, sources  # noqa: E402
from bookfinder.models import Access, Result  # noqa: E402


def test_sort_orders_free_before_borrow_before_unknown(monkeypatch):
    fake = [
        Result(source="C", title="c", access=Access.UNKNOWN),
        Result(source="A", title="a", access=Access.BORROW),
        Result(source="B", title="b", access=Access.FREE),
    ]
    monkeypatch.setattr(sources, "ALL_SOURCES", (lambda q: fake,))
    monkeypatch.setattr(cli, "ALL_SOURCES", (lambda q: fake,))

    out = cli.aggregate("anything")
    assert [r.access for r in out] == [Access.FREE, Access.BORROW, Access.UNKNOWN]


def test_free_only_filter(monkeypatch, capsys):
    fake = [
        Result(source="X", title="free one", access=Access.FREE,
               url="http://example/free"),
        Result(source="Y", title="borrow one", access=Access.BORROW,
               url="http://example/borrow"),
    ]
    monkeypatch.setattr(cli, "ALL_SOURCES", (lambda q: fake,))

    rc = cli.main(["--free-only", "test"])
    captured = capsys.readouterr().out
    assert rc == 0
    assert "free one" in captured
    assert "borrow one" not in captured


def test_no_results_returns_nonzero(monkeypatch):
    monkeypatch.setattr(cli, "ALL_SOURCES", (lambda q: [],))
    assert cli.main(["nothing here"]) == 1


def test_author_str_handles_empty():
    assert Result(source="s", title="t").author_str == "Unknown author"
