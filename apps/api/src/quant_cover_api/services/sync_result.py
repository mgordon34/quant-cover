from dataclasses import dataclass


@dataclass
class SyncResult:
    created: int = 0
    updated: int = 0
    skipped: int = 0
