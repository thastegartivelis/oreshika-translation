#!/usr/bin/env python3
"""Inspect and sanity-check text in MLT/MLB files without rebuilding the ISO.

This is a format checker, not a reimplementation of the game's renderer. It
checks the MLT tables, UTF-16LE strings, bracket balance, printf-style
placeholders, and changes to inline bracket controls.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import re
import struct
import sys
from dataclasses import dataclass
from pathlib import Path


class MLTError(ValueError):
    pass


@dataclass
class Entry:
    section: int
    index: int
    offset: int
    text: str


@dataclass
class Issue:
    severity: str
    location: str
    message: str


def u32(data: bytes, offset: int, what: str) -> int:
    if offset < 0 or offset + 4 > len(data):
        raise MLTError(f"{what} at 0x{offset:x} is outside the file")
    return struct.unpack_from("<I", data, offset)[0]


def read_mlt(path: Path) -> list[Entry]:
    data = path.read_bytes()
    if data.startswith(b"\x1f\x8b"):
        try:
            data = gzip.decompress(data)
        except OSError as exc:
            raise MLTError(f"invalid gzip-wrapped MLB: {exc}") from exc
    if len(data) < 4 or data[:3] != b"MLT":
        raise MLTError("missing MLT magic/header")
    section_count = data[3]
    if 4 + section_count * 4 > len(data):
        raise MLTError("section pointer table extends past end of file")

    entries: list[Entry] = []
    for section in range(section_count):
        table = u32(data, 4 + section * 4, f"section {section} table pointer")
        count = u32(data, table, f"section {section} string count")
        table_end = table + 4 + count * 4
        if table_end > len(data):
            raise MLTError(f"section {section} string pointer table extends past end of file")
        offsets = [u32(data, table + 4 + i * 4, f"section {section} string {i} pointer")
                   for i in range(count)]
        for index, offset in enumerate(offsets):
            if offset >= len(data):
                raise MLTError(f"section {section} string {index} offset 0x{offset:x} is out of range")
            if offset % 2:
                raise MLTError(f"section {section} string {index} offset 0x{offset:x} is not UTF-16 aligned")
            # Terminators are UTF-16 code units. Do not scan odd byte positions:
            # a zero high byte in ordinary Japanese text is not a terminator.
            end = offset
            while end + 1 < len(data) and data[end:end + 2] not in (b"\0\0", b"\xff\xff"):
                end += 2
            if end + 1 >= len(data):
                raise MLTError(f"section {section} string {index} has no UTF-16 terminator")
            raw = data[offset:end]
            try:
                text = raw.decode("utf-16-le", errors="strict")
            except UnicodeDecodeError as exc:
                raise MLTError(f"section {section} string {index} has invalid UTF-16LE: {exc}") from exc
            entries.append(Entry(section, index, offset, text))
    return entries


# printf conversions commonly found in game strings, including positional and
# length modifiers. %% is a literal percent and is deliberately not captured.
PRINTF_RE = re.compile(
    r"%(?:\d+:s|(?:\d+:)?@)|%(?:\d+\$)?[-+#0 ']*(?:\d+|\*)?(?:\.(?:\d+|\*))?"
    r"(?:hh|h|ll|l|z|t|j|L)?[diuoxXfFeEgGaAcsp]"
)
CONTROL_RE = re.compile(r"\[[^\]]*\]")


def check_text(text: str, location: str, issues: list[Issue]) -> None:
    # Bracket commands observed in this title use a single opening bracket and
    # closing bracket. Their semantics and command vocabulary are incomplete.
    cursor = 0
    while True:
        left = text.find("[", cursor)
        right_before = text.find("]", cursor)
        if right_before != -1 and (left == -1 or right_before < left):
            issues.append(Issue("ERROR", location, f"unmatched ']' at character {right_before}"))
            cursor = right_before + 1
            continue
        if left == -1:
            break
        right = text.find("]", left + 1)
        if right == -1:
            issues.append(Issue("ERROR", location, f"unclosed '[' at character {left}"))
            break
        if right == left + 1:
            issues.append(Issue("WARN", location, f"empty bracket command at character {left}"))
        nested = text.find("[", left + 1, right)
        if nested != -1:
            issues.append(Issue("WARN", location, f"nested '[' inside bracket command at character {nested}"))
        cursor = right + 1


def placeholders(text: str) -> list[str]:
    return PRINTF_RE.findall(text)


def controls(text: str) -> list[str]:
    return CONTROL_RE.findall(text)


def placeholders_match(original: str, translated: str) -> bool:
    before, after = placeholders(original), placeholders(translated)
    # The game's indexed forms (for example %1:s and %2:s) may be reordered
    # safely. Ordinary printf forms consume arguments in sequence, so preserve
    # their order when comparing them.
    indexed = re.compile(r"%\d+:s\Z")
    if all(indexed.fullmatch(token) for token in before + after):
        return sorted(before) == sorted(after)
    return before == after


def compare_text(original: str, translated: str, location: str, issues: list[Issue]) -> None:
    if not placeholders_match(original, translated):
        issues.append(Issue("ERROR", location,
                            f"printf placeholders differ: {placeholders(original)!r} -> {placeholders(translated)!r}"))
    if controls(original) != controls(translated):
        issues.append(Issue("WARN", location,
                            f"bracket controls differ: {controls(original)!r} -> {controls(translated)!r}"))


def load_csv(path: Path, mlb_name: str) -> dict[tuple[int, int], tuple[str, str]]:
    result: dict[tuple[int, int], tuple[str, str]] = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"filename", "section", "string", "text", "translation"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("CSV must have filename, section, string, text, and translation columns")
        for line, row in enumerate(reader, 2):
            if Path(row["filename"]).name.casefold() != mlb_name.casefold():
                continue
            try:
                key = (int(row["section"]), int(row["string"]))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"CSV line {line}: invalid section/string index") from exc
            if key in result:
                raise ValueError(f"CSV line {line}: duplicate position {key}")
            result[key] = (row.get("text") or "", row.get("translation") or "")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mlb", type=Path, help="raw or decompressed MLT/MLB file")
    parser.add_argument("--csv", type=Path, help="translation CSV with section/string/text/translation columns")
    parser.add_argument("--preview", action="store_true", help="print a readable text preview, retaining inline controls")
    args = parser.parse_args()

    try:
        entries = read_mlt(args.mlb)
        translations = load_csv(args.csv, args.mlb.name) if args.csv else {}
    except (OSError, MLTError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    issues: list[Issue] = []
    matched = 0
    for entry in entries:
        loc = f"{args.mlb}: section {entry.section}, string {entry.index} (0x{entry.offset:x})"
        check_text(entry.text, loc, issues)
        replacement = translations.get((entry.section, entry.index))
        if replacement:
            expected, translated = replacement
            if expected and expected != entry.text:
                issues.append(Issue("ERROR", loc, f"CSV source text mismatch: CSV has {expected!r}, MLB has {entry.text!r}"))
                continue
            if translated:
                matched += 1
                check_text(translated, loc + " [translation]", issues)
                compare_text(entry.text, translated, loc, issues)
                shown = translated
            else:
                shown = entry.text
        else:
            shown = entry.text
        if args.preview:
            print(f"[{entry.section}:{entry.index:03d}] {shown}")

    errors = sum(issue.severity == "ERROR" for issue in issues)
    warns = sum(issue.severity == "WARN" for issue in issues)
    print(f"Checked {len(entries)} strings in {args.mlb}; {matched} non-empty CSV translations matched.")
    for issue in issues:
        print(f"{issue.severity}: {issue.location}: {issue.message}")
    print(f"Result: {errors} error(s), {warns} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
