"""Base cleaner interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class CleanItem:
    path: str
    size: int = 0
    description: str = ""
    selected: bool = True


@dataclass
class CleanResult:
    freed_bytes: int = 0
    removed_count: int = 0
    errors: list[str] = field(default_factory=list)
    success: bool = True


class Cleaner(ABC):
    """Abstract base for a cleaner category."""

    name: str = "Cleaner"
    description: str = ""

    @abstractmethod
    def scan(self, progress_cb: Optional[Callable[[float, str], None]] = None) -> list[CleanItem]:
        """Scan for cleanable items. Returns list of CleanItem."""

    @abstractmethod
    def clean(self, items: list[CleanItem],
             progress_cb: Optional[Callable[[float, str], None]] = None) -> CleanResult:
        """Clean the given items."""
