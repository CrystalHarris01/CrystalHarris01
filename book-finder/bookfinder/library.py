"""Optional library-availability adapter (Libby / OverDrive).

OverDrive (the service behind Libby) has **no open public search API**. Access
goes through the per-library "Thunder" API, which requires:

  * a specific library/consortium key (the subdomain you see in Libby, e.g.
    ``lapl`` for Los Angeles Public Library), and
  * agreeing to OverDrive/Libby API terms for that consortium.

So this adapter is opt-in: it only runs when you supply a consortium key via
the ``BOOKFINDER_OVERDRIVE_LIBRARY`` environment variable (or the function
argument). Without it, the rest of bookfinder works unchanged.

This does not bypass anything — it asks a library you belong to whether a
title is available to borrow, exactly like the Libby app does.
"""

from __future__ import annotations

import os

from .http import get_json
from .models import Access, Result

# Public Thunder endpoint pattern. The {library} segment is the consortium key.
THUNDER_MEDIA = "https://thunder.api.overdrive.com/v2/libraries/{library}/media"


def search_overdrive(query: str, library: str | None = None) -> list[Result]:
    """Search a specific OverDrive/Libby consortium for borrowable copies.

    ``library`` defaults to the BOOKFINDER_OVERDRIVE_LIBRARY env var. Returns
    an empty list (never raises) when no key is configured or the call fails,
    so it can be added to ALL_SOURCES without breaking offline use.
    """
    library = library or os.environ.get("BOOKFINDER_OVERDRIVE_LIBRARY", "")
    if not library:
        return []

    data = get_json(THUNDER_MEDIA.format(library=library), {
        "query": query,
        "perPage": 5,
        "format": "ebook-overdrive,ebook-media-do",
    })
    items = (data or {}).get("items") if isinstance(data, dict) else None
    if not items:
        return []

    out: list[Result] = []
    for item in items[:5]:
        creators = [c.get("name", "") for c in item.get("creators", [])
                    if c.get("role") == "Author"]
        title = item.get("title", "Unknown title")
        item_id = item.get("id", "")
        out.append(Result(
            source=f"Libby/OverDrive ({library})",
            title=title,
            authors=[c for c in creators if c],
            access=Access.BORROW,
            url=f"https://libbyapp.com/search/{library}/search/query-{item_id}",
            note="Borrow with your library card via the Libby app.",
        ))
    return out
