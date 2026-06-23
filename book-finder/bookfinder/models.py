"""Shared data structures for search results."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Access(str, Enum):
    """How a copy can be accessed, in decreasing order of convenience."""

    FREE = "free"            # public domain / openly licensed, read or download now
    BORROW = "borrow"        # library lending copy, may have a waitlist
    PREVIEW = "preview"      # limited preview only
    UNKNOWN = "unknown"


@dataclass
class Result:
    """A single place a book can be read legally."""

    source: str                      # e.g. "Project Gutenberg"
    title: str
    authors: list[str] = field(default_factory=list)
    access: Access = Access.UNKNOWN
    url: str = ""                    # user-facing page to read/borrow
    formats: list[str] = field(default_factory=list)
    note: str = ""

    @property
    def author_str(self) -> str:
        return ", ".join(self.authors) if self.authors else "Unknown author"
