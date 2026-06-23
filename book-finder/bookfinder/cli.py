"""Command-line interface: search a title across all legal sources."""

from __future__ import annotations

import argparse
import concurrent.futures
import sys

from .models import Access, Result
from .sources import ALL_SOURCES

# Sort so the most useful access types float to the top.
_ACCESS_RANK = {Access.FREE: 0, Access.BORROW: 1, Access.PREVIEW: 2, Access.UNKNOWN: 3}

_ACCESS_LABEL = {
    Access.FREE: "FREE",
    Access.BORROW: "BORROW",
    Access.PREVIEW: "PREVIEW",
    Access.UNKNOWN: "CHECK",
}


def aggregate(query: str) -> list[Result]:
    """Query every source concurrently and return a flat, sorted result list."""
    results: list[Result] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(ALL_SOURCES)) as pool:
        for found in pool.map(lambda fn: fn(query), ALL_SOURCES):
            results.extend(found)
    results.sort(key=lambda r: (_ACCESS_RANK[r.access], r.source))
    return results


def format_result(r: Result) -> str:
    label = _ACCESS_LABEL[r.access]
    lines = [
        f"  [{label}] {r.title}",
        f"          by {r.author_str}  ·  {r.source}",
        f"          {r.url}",
    ]
    if r.note:
        lines.append(f"          {r.note}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bookfinder",
        description="Find lawful free or borrowable copies of a book.",
    )
    parser.add_argument("query", nargs="+", help="title and/or author to search for")
    parser.add_argument(
        "--free-only", action="store_true",
        help="show only copies that are free to read right now",
    )
    args = parser.parse_args(argv)
    query = " ".join(args.query)

    print(f'Searching legal sources for: "{query}"\n')
    results = aggregate(query)

    if args.free_only:
        results = [r for r in results if r.access is Access.FREE]

    if not results:
        print("No legal free/borrowable copies found.")
        print("Tip: try your local library's app (Libby/OverDrive) or a bookstore.")
        return 1

    for r in results:
        print(format_result(r))
        print()

    print(f"{len(results)} result(s). Borrowing may involve a library waitlist.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
