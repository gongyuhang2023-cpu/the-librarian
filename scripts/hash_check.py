"""File deduplication checker using SHA-256 hashes."""

import argparse
import hashlib
import json
import sys
from pathlib import Path


def compute_hash(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def load_registry(registry_path: Path) -> list[dict]:
    if not registry_path.exists():
        return []
    with open(registry_path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_files(file_paths: list[str], registry_path: str | None) -> dict:
    registry = load_registry(Path(registry_path)) if registry_path else []
    hash_index = {entry["hash"]: entry for entry in registry}

    results = []
    for fp in file_paths:
        p = Path(fp)
        if not p.exists():
            results.append({"path": str(p), "error": "file not found"})
            continue

        file_hash = compute_hash(p)
        existing = hash_index.get(file_hash)
        results.append({
            "path": str(p),
            "hash": file_hash,
            "duplicate": existing is not None,
            "existing_entry": existing,
        })

    return {"files": results}


def main():
    parser = argparse.ArgumentParser(description="Check files for duplicates via SHA-256")
    parser.add_argument("-p", nargs="+", required=True, help="File paths to check")
    parser.add_argument("-r", default=None, help="Path to registry/files.json for dedup comparison")
    args = parser.parse_args()

    result = check_files(args.p, args.r)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
