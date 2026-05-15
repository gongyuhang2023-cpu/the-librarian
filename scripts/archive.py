#!/usr/bin/env python3
"""
Archive processed files to Wiki with dual-output structure.

Two output layers:
  sources_dir/<notebook>/paper-name.md        — flat md-only (for LLM consumption)
  backup_dir/<notebook>/<paper-name>/         — full package (PDF + md + images/)

Paths are read from paths.yaml (project root). Does NOT delete originals.

Usage:
    python scripts/archive.py \
        --paper-name "Smith2024_phage_therapy" \
        --notebooks "PC047 粘液螺旋菌" "生信分析方法" \
        --processed-md "library/_processing/Smith2024_phage.md" \
        [--processed-images "library/_processing/Smith2024_phage_images/"] \
        [--original-pdf "inbox/Smith2024_phage.pdf"] \
        [--config "paths.yaml"]
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

import yaml


def load_config(config_path: Path | None = None) -> dict:
    if config_path is None:
        config_path = Path(__file__).parent.parent / "paths.yaml"
    if not config_path.exists():
        print(f"[Error] Config not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def strip_images(content: str) -> str:
    """Remove markdown image references for LLM-consumption copy."""
    return re.sub(r"!\[[^\]]*\]\([^)]+\)\n?", "", content)


def rewrite_image_paths(content: str, old_prefix: str) -> str:
    """Rewrite image directory prefix to 'images/' for backup copy."""
    pattern = re.escape(old_prefix)
    return re.sub(
        rf"(\!\[[^\]]*\]\(){pattern}",
        lambda m: m.group(1) + "images/",
        content,
    )


def archive_to_sources(
    paper_name: str,
    notebook_name: str,
    md_content: str,
    sources_dir: Path,
) -> dict:
    """Write flat md file to sources layer (LLM consumption)."""
    nb_dir = sources_dir / notebook_name
    nb_dir.mkdir(parents=True, exist_ok=True)

    clean_md = strip_images(md_content)
    md_path = nb_dir / f"{paper_name}.md"
    md_path.write_text(clean_md, encoding="utf-8")

    return {
        "notebook": notebook_name,
        "source_path": str(md_path),
        "source_ok": md_path.exists(),
    }


def archive_to_backup(
    paper_name: str,
    notebook_name: str,
    md_content: str,
    processed_images: Path | None,
    original_pdf: Path | None,
    backup_dir: Path,
) -> dict:
    """Write full package to backup layer."""
    paper_dir = backup_dir / notebook_name / paper_name
    paper_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "notebook": notebook_name,
        "backup_dir": str(paper_dir),
        "md": False,
        "images": False,
        "pdf": False,
        "image_count": 0,
    }

    md_path = paper_dir / f"{paper_name}.md"
    md_path.write_text(md_content, encoding="utf-8")
    result["md"] = md_path.exists()

    if processed_images and processed_images.exists():
        dest_images = paper_dir / "images"
        if dest_images.exists():
            shutil.rmtree(str(dest_images))
        shutil.copytree(str(processed_images), str(dest_images))
        result["images"] = dest_images.exists()
        result["image_count"] = len(list(dest_images.iterdir()))

    if original_pdf and original_pdf.exists():
        pdf_dest = paper_dir / f"{paper_name}{original_pdf.suffix}"
        shutil.copy2(str(original_pdf), str(pdf_dest))
        result["pdf"] = pdf_dest.exists()

    return result


def main():
    parser = argparse.ArgumentParser(description="Archive processed files (dual-output)")
    parser.add_argument("--paper-name", required=True)
    parser.add_argument("--notebooks", required=True, nargs="+")
    parser.add_argument("--processed-md", required=True)
    parser.add_argument("--processed-images")
    parser.add_argument("--original-pdf")
    parser.add_argument("--config", help="Path to paths.yaml (default: project root)")
    args = parser.parse_args()

    config_path = Path(args.config) if args.config else None
    cfg = load_config(config_path)

    sources_dir = Path(cfg["sources_dir"])
    backup_dir = Path(cfg["backup_dir"])
    reg_prefix = cfg.get("registry_prefix", {})

    processed_md = Path(args.processed_md)
    processed_images = Path(args.processed_images) if args.processed_images else None
    original_pdf = Path(args.original_pdf) if args.original_pdf else None

    errors = []
    if not processed_md.exists():
        errors.append(f"Processed md not found: {processed_md}")
    if processed_images and not processed_images.exists():
        errors.append(f"Processed images dir not found: {processed_images}")
    if original_pdf and not original_pdf.exists():
        errors.append(f"Original PDF not found: {original_pdf}")

    if errors:
        print(json.dumps({"status": "error", "errors": errors}, ensure_ascii=False, indent=2))
        sys.exit(1)

    md_content = processed_md.read_text(encoding="utf-8")

    if processed_images:
        old_prefix = processed_images.name + "/"
        backup_md = rewrite_image_paths(md_content, old_prefix)
    else:
        backup_md = md_content

    source_results = []
    backup_results = []

    for notebook_name in args.notebooks:
        sr = archive_to_sources(args.paper_name, notebook_name, md_content, sources_dir)
        source_results.append(sr)

        br = archive_to_backup(
            args.paper_name, notebook_name, backup_md,
            processed_images, original_pdf, backup_dir,
        )
        backup_results.append(br)

    src_prefix = reg_prefix.get("sources", "raw/sources")
    bak_prefix = reg_prefix.get("backup", "00-raw")

    output = {
        "status": "ok",
        "paper_name": args.paper_name,
        "sources": source_results,
        "backups": backup_results,
        "source_paths": [
            f"{src_prefix}/{nb}/{args.paper_name}.md"
            for nb in args.notebooks
        ],
        "backup_paths": [
            f"{bak_prefix}/{nb}/{args.paper_name}/"
            for nb in args.notebooks
        ],
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
