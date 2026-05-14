#!/usr/bin/env python3
"""
Extract metadata from processed markdown for file profiling.

Strategy:
  1. Scan for structured signals: title, abstract, conclusion, DOI, authors
  2. If abstract found → output extracted sections (compact)
  3. If no abstract  → output full text (let Claude analyze)

Usage:
    python scripts/profile.py -p "library/_processing/paper.md"

Output: JSON to stdout.
"""

import argparse
import json
import re
import sys
from pathlib import Path


# Strip markdown image syntax, keep alt text
IMG_PATTERN = re.compile(r"!\[[^\]]*\]\([^)]+\)")
DOI_PATTERN = re.compile(r"10\.\d{4,9}/[^\s,;\"'}\]]+")
# Common abstract heading patterns (case-insensitive)
ABSTRACT_HEADINGS = re.compile(
    r"^#{1,3}\s*(abstract|摘\s*要|summary)\s*$", re.IGNORECASE | re.MULTILINE
)
CONCLUSION_HEADINGS = re.compile(
    r"^#{1,3}\s*(conclusions?|concluding\s+remarks?|结\s*论|总\s*结)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


def strip_images(text: str) -> str:
    return IMG_PATTERN.sub("", text)


def find_title(text: str) -> str | None:
    """First H1 heading, or first H2 if no H1."""
    for match in HEADING_PATTERN.finditer(text):
        level = len(match.group(1))
        title = match.group(2).strip()
        if level == 1 and len(title) > 3:
            return title
    # Fallback: first H2
    for match in HEADING_PATTERN.finditer(text):
        level = len(match.group(1))
        title = match.group(2).strip()
        if level == 2 and len(title) > 3:
            return title
    return None


def extract_section(text: str, heading_re: re.Pattern) -> str | None:
    """Extract text between a heading and the next heading of same or higher level."""
    match = heading_re.search(text)
    if not match:
        return None

    start = match.end()
    # Find the heading level
    line_start = text.rfind("\n", 0, match.start()) + 1
    heading_line = text[line_start : match.end()]
    level = 0
    for ch in heading_line:
        if ch == "#":
            level += 1
        else:
            break

    # Find next heading of same or higher level
    rest = text[start:]
    next_heading = re.search(rf"^#{{1,{level}}}\s+", rest, re.MULTILINE)
    if next_heading:
        section = rest[: next_heading.start()]
    else:
        section = rest[:3000]  # cap at 3000 chars if no next heading

    return section.strip()


def find_doi(text: str) -> str | None:
    match = DOI_PATTERN.search(text)
    if match:
        doi = match.group(0).rstrip(".")
        return doi
    return None


def find_authors(text: str, title_pos: int) -> str | None:
    """Heuristic: look for author-like lines near the title (within 500 chars after)."""
    region = text[title_pos : title_pos + 800]
    # Pattern: lines with multiple comma-separated names, possibly with superscripts/numbers
    for line in region.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Skip very short or very long lines
        if len(line) < 10 or len(line) > 500:
            continue
        # Author lines typically have commas and capital letters
        comma_count = line.count(",")
        if comma_count >= 2:
            # Check it's not a sentence (no period-heavy text)
            if line.count(".") <= comma_count:
                return line[:300]
    return None


def profile(md_path: Path) -> dict:
    text = md_path.read_text(encoding="utf-8")
    clean = strip_images(text)
    # Collapse multiple blank lines
    clean = re.sub(r"\n{3,}", "\n\n", clean)

    result: dict = {
        "file": str(md_path),
        "char_count": len(clean),
        "has_abstract": False,
    }

    # Title
    title = find_title(clean)
    if title:
        result["title"] = title

    # DOI
    doi = find_doi(clean)
    if doi:
        result["doi"] = doi

    # Authors (heuristic)
    if title:
        title_pos = clean.find(title)
        if title_pos >= 0:
            authors = find_authors(clean, title_pos + len(title))
            if authors:
                result["authors_hint"] = authors

    # Abstract
    abstract = extract_section(clean, ABSTRACT_HEADINGS)
    if abstract and len(abstract) > 50:
        result["has_abstract"] = True
        result["abstract"] = abstract[:2000]

        # Conclusion
        conclusion = extract_section(clean, CONCLUSION_HEADINGS)
        if conclusion and len(conclusion) > 50:
            result["conclusion"] = conclusion[:2000]

        # In structured mode, also include first 20 lines for context
        first_lines = "\n".join(clean.split("\n")[:20])
        result["header"] = first_lines

    else:
        # No abstract found → include full text (without images)
        result["full_text"] = clean

    return result


def main():
    parser = argparse.ArgumentParser(description="Extract metadata from markdown")
    parser.add_argument("-p", "--path", required=True, help="Path to .md file")
    args = parser.parse_args()

    md_path = Path(args.path)
    if not md_path.exists():
        print(json.dumps({"error": f"File not found: {md_path}"}, ensure_ascii=False))
        sys.exit(1)

    result = profile(md_path)
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
