#!/usr/bin/env python3
"""Download only allow-listed MedicoBuddy source files and record checksums."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


USER_AGENT = "MedicoBuddyEvidenceIndexer/1.0 (source provenance downloader)"
ALLOWED_POLICIES = {"download_allowed", "download_allowed_restricted"}


def discover_medlineplus_zip(page_url: str) -> str:
    request = urllib.request.Request(page_url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        html = response.read().decode("utf-8", errors="replace")
    matches = re.findall(
        r'href=["\']([^"\']*mplus_topics_compressed_\d{4}-\d{2}-\d{2}\.zip)["\']',
        html,
        flags=re.IGNORECASE,
    )
    if not matches:
        raise RuntimeError("Current MedlinePlus compressed XML link was not found")
    return urllib.parse.urljoin(page_url, matches[0])


def safe_name(source_id: str, url: str, content_type: str | None) -> str:
    name = Path(urllib.parse.urlparse(url).path).name
    if not name or "." not in name:
        extension = ".pdf" if content_type and "pdf" in content_type else ".bin"
        name = f"{source_id}{extension}"
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)


def download(source_id: str, url: str, destination: Path) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    digest = hashlib.sha256()
    with urllib.request.urlopen(request, timeout=90) as response:
        content_type = response.headers.get("Content-Type")
        filename = safe_name(source_id, response.geturl(), content_type)
        target = destination / filename
        with target.open("wb") as output:
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                output.write(block)
                digest.update(block)
    return {
        "status": "downloaded",
        "source_id": source_id,
        "url": url,
        "file": str(target),
        "bytes": target.stat().st_size,
        "sha256": digest.hexdigest(),
        "content_type": content_type,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).with_name("source_manifest.csv"),
    )
    parser.add_argument("--output", type=Path, default=Path("downloaded"))
    parser.add_argument(
        "--include-restricted-traditional",
        action="store_true",
        help="Download traditional documents that require strict output filtering.",
    )
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []

    with args.manifest.open(newline="", encoding="utf-8") as manifest_file:
        for row in csv.DictReader(manifest_file):
            policy = row["ingestion_policy"]
            if policy not in ALLOWED_POLICIES:
                results.append(
                    {
                        "status": "not_downloaded",
                        "source_id": row["source_id"],
                        "reason": f"policy={policy}; use API/MCP or official link",
                    }
                )
                continue
            if (
                policy == "download_allowed_restricted"
                and not args.include_restricted_traditional
            ):
                results.append(
                    {
                        "status": "not_downloaded",
                        "source_id": row["source_id"],
                        "reason": "restricted traditional source; pass explicit flag",
                    }
                )
                continue

            try:
                url = row["download_url"]
                if url == "AUTO_DISCOVER_MEDLINEPLUS":
                    url = discover_medlineplus_zip(row["primary_url"])
                results.append(download(row["source_id"], url, args.output))
            except Exception as exc:  # report per-source without hiding failures
                results.append(
                    {
                        "status": "failed",
                        "source_id": row["source_id"],
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manifest": str(args.manifest),
        "results": results,
    }
    report_path = args.output / "download_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    failed = sum(item["status"] == "failed" for item in results)
    downloaded = sum(item["status"] == "downloaded" for item in results)
    print(f"Downloaded {downloaded}; failed {failed}; report: {report_path}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
