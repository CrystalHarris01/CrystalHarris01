"""Adapters for legitimate book sources.

Each function takes a free-text query and returns a list[Result]. All sources
are public APIs that index legally available copies:

  * Gutendex      -> Project Gutenberg (public-domain texts, free to read)
  * Open Library  -> Internet Archive lending + readable scans (borrow/free)
  * Archive.org   -> Internet Archive "texts" collection (free where public)

None of these endpoints bypass a paywall; they surface copies that are
already free or lawfully borrowable.
"""

from __future__ import annotations

from .http import get_json
from .models import Access, Result

MAX_PER_SOURCE = 5


def search_gutenberg(query: str) -> list[Result]:
    """Project Gutenberg via the Gutendex API (gutendex.com)."""
    data = get_json("https://gutendex.com/books", {"search": query})
    if not data or "results" not in data:
        return []
    out: list[Result] = []
    for book in data["results"][:MAX_PER_SOURCE]:
        authors = [a.get("name", "") for a in book.get("authors", [])]
        fmts = book.get("formats", {})
        # Prefer a human-readable HTML/epub link if present.
        url = (
            fmts.get("text/html")
            or fmts.get("application/epub+zip")
            or f"https://www.gutenberg.org/ebooks/{book.get('id', '')}"
        )
        out.append(Result(
            source="Project Gutenberg",
            title=book.get("title", "Unknown title"),
            authors=[a for a in authors if a],
            access=Access.FREE,
            url=url,
            formats=[m.split("/")[-1].split("+")[0] for m in fmts],
            note="Public domain — free to read or download.",
        ))
    return out


def search_open_library(query: str) -> list[Result]:
    """Open Library search; flags borrowable/readable Internet Archive copies."""
    data = get_json("https://openlibrary.org/search.json", {
        "q": query,
        "limit": MAX_PER_SOURCE,
        "fields": "title,author_name,ia,ebook_access,key",
    })
    if not data or "docs" not in data:
        return []
    access_map = {
        "public": Access.FREE,
        "borrowable": Access.BORROW,
        "printdisabled": Access.BORROW,
        "no_ebook": Access.UNKNOWN,
    }
    notes = {
        Access.FREE: "Public domain on the Internet Archive — read free.",
        Access.BORROW: "Borrowable from the Internet Archive / Open Library.",
        Access.UNKNOWN: "Catalog record; check libraries for availability.",
    }
    out: list[Result] = []
    for doc in data["docs"][:MAX_PER_SOURCE]:
        ebook_access = doc.get("ebook_access", "no_ebook")
        access = access_map.get(ebook_access, Access.UNKNOWN)
        key = doc.get("key", "")
        url = f"https://openlibrary.org{key}" if key else "https://openlibrary.org"
        out.append(Result(
            source="Open Library",
            title=doc.get("title", "Unknown title"),
            authors=doc.get("author_name", []),
            access=access,
            url=url,
            note=notes.get(access, ""),
        ))
    return out


def search_archive_texts(query: str) -> list[Result]:
    """Internet Archive 'texts' collection (archive.org advancedsearch API)."""
    data = get_json("https://archive.org/advancedsearch.php", {
        "q": f'({query}) AND mediatype:texts',
        "fl[]": "identifier,title,creator",
        "rows": MAX_PER_SOURCE,
        "output": "json",
    })
    try:
        docs = data["response"]["docs"]  # type: ignore[index]
    except (TypeError, KeyError):
        return []
    out: list[Result] = []
    for doc in docs[:MAX_PER_SOURCE]:
        ident = doc.get("identifier", "")
        creator = doc.get("creator", [])
        if isinstance(creator, str):
            creator = [creator]
        out.append(Result(
            source="Internet Archive",
            title=doc.get("title", "Unknown title"),
            authors=creator,
            access=Access.UNKNOWN,
            url=f"https://archive.org/details/{ident}" if ident else "https://archive.org",
            note="Internet Archive item — some are free, some are lending only.",
        ))
    return out


def search_libby(query: str) -> list[Result]:
    """Optional Libby/OverDrive lookup; no-op unless a consortium key is set.

    Imported lazily so the core sources stay free of any optional config.
    """
    from .library import search_overdrive
    return search_overdrive(query)


ALL_SOURCES = (
    search_gutenberg,
    search_open_library,
    search_archive_texts,
    search_libby,
)
