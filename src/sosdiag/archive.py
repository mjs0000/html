from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import tarfile
from typing import Iterable


@dataclass(frozen=True)
class SosEntry:
    path: str
    data: bytes

    def text(self, encoding: str = "utf-8") -> str:
        return self.data.decode(encoding, errors="replace")


class SosArchive:
    """Read sosreport directories and tar archives without extracting them."""

    def __init__(self, source: str | Path):
        self.source = Path(source)
        if not self.source.exists():
            raise FileNotFoundError(self.source)

    def paths(self) -> list[str]:
        return [entry.path for entry in self.iter_entries()]

    def iter_entries(self) -> Iterable[SosEntry]:
        if self.source.is_dir():
            yield from self._iter_directory()
            return
        if not tarfile.is_tarfile(self.source):
            raise ValueError(f"Unsupported sosreport source: {self.source}")
        yield from self._iter_tar()

    def read_bytes(self, path: str) -> bytes | None:
        wanted = self._normalize(path)
        for entry in self.iter_entries():
            if entry.path == wanted:
                return entry.data
        return None

    def read_text(self, path: str, encoding: str = "utf-8") -> str | None:
        data = self.read_bytes(path)
        if data is None:
            return None
        return data.decode(encoding, errors="replace")

    def first_text(self, candidates: Iterable[str]) -> tuple[str, str] | None:
        for candidate in candidates:
            text = self.read_text(candidate)
            if text is not None:
                return self._normalize(candidate), text
        return None

    def glob_text(self, pattern: str) -> list[tuple[str, str]]:
        normalized_pattern = self._normalize(pattern)
        results: list[tuple[str, str]] = []
        for entry in self.iter_entries():
            if PurePosixPath(entry.path).match(normalized_pattern):
                results.append((entry.path, entry.text()))
        return results

    def _iter_directory(self) -> Iterable[SosEntry]:
        root = self._directory_root()
        for item in sorted(root.rglob("*")):
            if not item.is_file():
                continue
            rel = item.relative_to(root).as_posix()
            yield SosEntry(rel, item.read_bytes())

    def _directory_root(self) -> Path:
        children = [p for p in self.source.iterdir() if p.name not in {".", ".."}]
        dirs = [p for p in children if p.is_dir()]
        files = [p for p in children if p.is_file()]
        if len(dirs) == 1 and not files and dirs[0].name.startswith("sosreport-"):
            return dirs[0]
        return self.source

    def _iter_tar(self) -> Iterable[SosEntry]:
        with tarfile.open(self.source, mode="r:*") as tf:
            members = [m for m in tf.getmembers() if m.isfile()]
            prefix = self._common_sos_prefix(m.name for m in members)
            for member in members:
                extracted = tf.extractfile(member)
                if extracted is None:
                    continue
                path = self._strip_prefix(member.name, prefix)
                if not path:
                    continue
                yield SosEntry(path, extracted.read())

    @staticmethod
    def _common_sos_prefix(paths: Iterable[str]) -> str | None:
        first_parts = []
        for path in paths:
            parts = PurePosixPath(path).parts
            if parts:
                first_parts.append(parts[0])
        if first_parts and len(set(first_parts)) == 1 and first_parts[0].startswith("sosreport-"):
            return first_parts[0]
        return None

    @classmethod
    def _strip_prefix(cls, path: str, prefix: str | None) -> str:
        normalized = cls._normalize(path)
        if prefix and normalized.startswith(prefix + "/"):
            return normalized[len(prefix) + 1 :]
        return normalized

    @staticmethod
    def _normalize(path: str) -> str:
        value = str(PurePosixPath(path)).lstrip("/")
        if value in {"", "."}:
            return ""
        if value == ".." or value.startswith("../"):
            raise ValueError(f"Unsafe archive path: {path}")
        return value
