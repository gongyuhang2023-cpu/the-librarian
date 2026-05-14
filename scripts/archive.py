#!/usr/bin/env python3
"""
Archive processed files to Wiki raw directory with correct structure.

Takes MinerU output (md + images) from _processing/ and original PDF from inbox/,
places them into the correct directory structure under PhD/raw/.

Usage:
    python scripts/archive.py \
        --paper-name "Smith2024_phage_therapy" \
        --notebooks "PC047 粘液螺旋菌" "生信分析方法" \
        --processed-md "library/_processing/Smith2024_phage.md" \
        [--processed-images "library/_processing/Smith2024_phage_images/"] \
        [--original-pdf "inbox/Smith2024_phage.pdf"] \
        [--raw-root "C:/Users/Yuhang/Library/PhD/raw"]

Output: JSON to stdout with archive results.

Strategy: copy first, verify, then report success. Does NOT delete originals.
"""

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

DEFAULT_RAW_ROOT = Path("C:/Users/Yuhang/Library/PhD/raw")


def rewrite_image_paths(content: str, old_prefix: str) -> str:
    """Replace old image directory prefix with 'images/' in markdown image links."""
    pattern = re.escape(old_prefix)
    return re.sub(
        rf"(\!\[[^\]]*\]\(){pattern}",
        r"\1images/",
        content,
    )


def insert_pdf_link(content: str, paper_name: str, notebook_name: str) -> str:
    """Insert PDF cross-link at the top of markdown content."""
    link = f"> 📄 原始 PDF: [{paper_name}.pdf](../../pdfs/{notebook_name}/{paper_name}.pdf)\n\n"
    return link + content


def archive_one_notebook(
    paper_name: str,
    notebook_name: str,
    md_content: str,
    processed_images: Path | None,
    original_pdf: Path | None,
    raw_root: Path,
    is_primary: bool,
) -> dict:
    """Archive files to one notebook directory. Returns result dict."""
    sources_dir = raw_root / "sources" / notebook_name / paper_name
    result = {
        "notebook": notebook_name,
        "sources_dir": str(sources_dir),
        "content_md": False,
        "images": False,
        "pdf": False,
        "image_count": 0,
    }

    # Create directories
    sources_dir.mkdir(parents=True, exist_ok=True)

    # Write content.md
    content_path = sources_dir / "content.md"
    content_path.write_text(md_content, encoding="utf-8")
    result["content_md"] = content_path.exists()

    # Copy images
    if processed_images and processed_images.exists():
        dest_images = sources_dir / "images"
        if dest_images.exists():
            shutil.rmtree(str(dest_images))
        shutil.copytree(str(processed_images), str(dest_images))
        result["images"] = dest_images.exists()
        result["image_count"] = len(list(dest_images.iterdir()))

    # Copy/move PDF
    if original_pdf and original_pdf.exists():
        pdfs_dir = raw_root / "pdfs" / notebook_name
        pdfs_dir.mkdir(parents=True, exist_ok=True)
        pdf_dest = pdfs_dir / f"{paper_name}{original_pdf.suffix}"

        if is_primary:
            shutil.copy2(str(original_pdf), str(pdf_dest))
        else:
            shutil.copy2(str(original_pdf), str(pdf_dest))

        result["pdf"] = pdf_dest.exists()
        result["pdf_path"] = str(pdf_dest)

    return result


def main():
    parser = argparse.ArgumentParser(description="Archive processed files to Wiki raw")
    parser.add_argument("--paper-name", required=True, help="Paper name (e.g. Smith2024_phage_therapy)")
    parser.add_argument("--notebooks", required=True, nargs="+", help="Target notebook name(s) from library_index.json")
    parser.add_argument("--processed-md", required=True, help="Path to processed .md file in _processing/")
    parser.add_argument("--processed-images", help="Path to processed images directory (optional)")
    parser.add_argument("--original-pdf", help="Path to original PDF in inbox/ (optional, skip for non-PDF sources)")
    parser.add_argument("--raw-root", default=str(DEFAULT_RAW_ROOT), help="Wiki raw root directory")
    args = parser.parse_args()

    processed_md = Path(args.processed_md)
    raw_root = Path(args.raw_root)
    processed_images = Path(args.processed_images) if args.processed_images else None
    original_pdf = Path(args.original_pdf) if args.original_pdf else None

    # Validate inputs
    errors = []
    if not processed_md.exists():
        errors.append(f"Processed md not found: {processed_md}")
    if processed_images and not processed_images.exists():
        errors.append(f"Processed images dir not found: {processed_images}")
    if original_pdf and not original_pdf.exists():
        errors.append(f"Original PDF not found: {original_pdf}")
    if not raw_root.exists():
        errors.append(f"Raw root not found: {raw_root}")

    if errors:
        print(json.dumps({"status": "error", "errors": errors}, ensure_ascii=False, indent=2))
        sys.exit(1)

    # Read and transform md content
    md_content = processed_md.read_text(encoding="utf-8")

    # Rewrite image paths (xxx_images/ → images/)
    if processed_images:
        old_prefix = processed_images.name + "/"
        md_content = rewrite_image_paths(md_content, old_prefix)

    # Insert PDF link (using first notebook for relative path)
    if original_pdf:
        md_content = insert_pdf_link(md_content, args.paper_name, args.notebooks[0])

    # Archive to each notebook
    results = []
    for i, notebook_name in enumerate(args.notebooks):
        r = archive_one_notebook(
            paper_name=args.paper_name,
            notebook_name=notebook_name,
            md_content=md_content,
            processed_images=processed_images,
            original_pdf=original_pdf,
            raw_root=raw_root,
            is_primary=(i == 0),
        )
        results.append(r)

    # Build output
    output = {
        "status": "ok",
        "paper_name": args.paper_name,
        "notebooks": results,
        "content_paths": [f"PhD/raw/sources/{nb}/{args.paper_name}/" for nb in args.notebooks],
    }
    if original_pdf:
        output["pdf_path"] = f"PhD/raw/pdfs/{args.notebooks[0]}/{args.paper_name}{original_pdf.suffix}"

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
