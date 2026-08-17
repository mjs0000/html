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
        self._directory_root_cache: Path | None = None
        self._tar_prefix: str | None = None
        self._tar_member_index: dict[str, tarfile.TarInfo] | None = None

    def paths(self) -> list[str]:
        if self.source.is_dir():
            root = self._directory_root()
            return [item.relative_to(root).as_posix() for item in sorted(root.rglob("*")) if item.is_file()]
        self._ensure_tar_index()
        return sorted(self._tar_member_index or {})

    def iter_entries(self) -> Iterable[SosEntry]:
        if self.source.is_dir():
            yield from self._iter_directory()
            return
        self._ensure_tar_index()
        with tarfile.open(self.source, mode="r:*") as tf:
            for path, member in (self._tar_member_index or {}).items():
                extracted = tf.extractfile(member)
                if extracted is not None:
                    yield SosEntry(path, extracted.read())

    def read_bytes(self, path: str) -> bytes | None:
        wanted = self._normalize(path)
        if self.source.is_dir():
            target = self._directory_root() / wanted
            return target.read_bytes() if target.is_file() else None

        self._ensure_tar_index()
        member = (self._tar_member_index or {}).get(wanted)
        if member is None:
            return None
        with tarfile.open(self.source, mode="r:*") as tf:
            extracted = tf.extractfile(member)
            return extracted.read() if extracted is not None else None

    def read_text(self, path: str, encoding: str = "utf-8") -> str | None:
        data = self.read_bytes(path)
        if data is None:
            return None
        return data.decode(encoding, errors="replace")

    def first_text(self, candidates: Iterable[str]) -> tuple[str, str] | None:
        for candidate in candidates:
            normalized = self._normalize(candidate)
            text = self.read_text(normalized)
            if text is not None:
                return normalized, text
        return None

    def glob_text(self, pattern: str) -> list[tuple[str, str]]:
        normalized_pattern = self._normalize(pattern)
        results: list[tuple[str, str]] = []
        if self.source.is_dir():
            root = self._directory_root()
            for item in sorted(root.rglob("*")):
                if not item.is_file():
                    continue
                rel = item.relative_to(root).as_posix()
                if PurePosixPath(rel).match(normalized_pattern):
                    results.append((rel, item.read_text(encoding="utf-8", errors="replace")))
            return results

        self._ensure_tar_index()
        matches = [
            (path, member)
            for path, member in (self._tar_member_index or {}).items()
            if PurePosixPath(path).match(normalized_pattern)
        ]
        if not matches:
            return results
        with tarfile.open(self.source, mode="r:*") as tf:
            for path, member in matches:
                extracted = tf.extractfile(member)
                if extracted is not None:
                    results.append((path, extracted.read().decode("utf-8", errors="replace")))
        return results

    def _iter_directory(self) -> Iterable[SosEntry]:
        root = self._directory_root()
        for item in sorted(root.rglob("*")):
            if not item.is_file():
                continue
            rel = item.relative_to(root).as_posix()
            yield SosEntry(rel, item.read_bytes())

    def _directory_root(self) -> Path:
        if self._directory_root_cache is not None:
            return self._directory_root_cache
        children = [p for p in self.source.iterdir() if p.name not in {".", ".."}]
        dirs = [p for p in children if p.is_dir()]
        files = [p for p in children if p.is_file()]
        if len(dirs) == 1 and not files and dirs[0].name.startswith("sosreport-"):
            self._directory_root_cache = dirs[0]
        else:
            self._directory_root_cache = self.source
        return self._directory_root_cache

    def _ensure_tar_index(self) -> None:
        if self._tar_member_index is not None:
            return
        if not tarfile.is_tarfile(self.source):
            raise ValueError(f"Unsupported sosreport source: {self.source}")
        with tarfile.open(self.source, mode="r:*") as tf:
            members = [m for m in tf.getmembers() if m.isfile()]
        self._tar_prefix = self._common_sos_prefix(m.name for m in members)
        self._tar_member_index = {}
        for member in members:
            path = self._strip_prefix(member.name, self._tar_prefix)
            if path:
                self._tar_member_index[path] = member

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
