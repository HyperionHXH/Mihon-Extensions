#!/usr/bin/env python3
"""Validate a generated index without downloading every extension APK."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


PACKAGE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*(?:\.[a-zA-Z][a-zA-Z0-9_]*)+$")
USER_AGENT = "HyperionHXH-Mihon-Extensions/1.0"


def check_url(item: tuple[str, str]) -> tuple[str, str, str]:
    package_name, url = item
    last_error = ""
    for attempt in range(2):
        request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                if response.status < 400:
                    return package_name, url, "ok"
                last_error = f"HTTP {response.status}"
        except Exception as error:  # noqa: BLE001 - every network failure belongs in the report
            last_error = str(error)
        if attempt == 0:
            time.sleep(0.5)
    return package_name, url, last_error


def validate_komikku_repositories(root: Path) -> list[str]:
    errors: list[str] = []
    if not root.is_dir():
        return errors
    for index_path in sorted(root.glob("*/index.json")):
        repo_path = index_path.with_name("repo.json")
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
            repo = json.loads(repo_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"invalid Komikku repository {index_path.parent}: {error}")
            continue
        extensions = index.get("extensionList", {}).get("extensions", [])
        signing_key = str(index.get("signingKey", "")).replace(":", "").lower()
        meta_key = str(repo.get("meta", {}).get("signingKeyFingerprint", "")).replace(":", "").lower()
        if len(extensions) != 1:
            errors.append(f"Komikku repository must contain one extension: {index_path.parent}")
        if not re.fullmatch(r"[0-9a-f]{64}", signing_key):
            errors.append(f"invalid Komikku signing key: {index_path}")
        if signing_key != meta_key:
            errors.append(f"Komikku signing key mismatch: {index_path.parent}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("index", type=Path, nargs="?", default=Path("repo/index.json"))
    parser.add_argument("--check-urls", action="store_true")
    parser.add_argument("--workers", type=int, default=24)
    parser.add_argument("--url-report", type=Path)
    args = parser.parse_args()
    document = json.loads(args.index.read_text(encoding="utf-8"))
    extensions = document["extensionList"]["extensions"]
    packages: set[str] = set()
    errors: list[str] = []
    for extension in extensions:
        package_name = extension.get("packageName", "")
        if package_name in packages:
            errors.append(f"duplicate package: {package_name}")
        packages.add(package_name)
        if not PACKAGE.fullmatch(package_name):
            errors.append(f"invalid package: {package_name}")
        for key in ("apkUrl", "iconUrl"):
            url = extension.get("resources", {}).get(key, "")
            if urlparse(url).scheme not in {"http", "https"}:
                errors.append(f"invalid {key} for {package_name}: {url}")
        if not extension.get("sources"):
            errors.append(f"no sources: {package_name}")
        if int(extension.get("versionCode", 0)) < 1:
            errors.append(f"invalid versionCode: {package_name}")
    errors.extend(validate_komikku_repositories(args.index.parent / "komikku"))
    if args.check_urls:
        work = [(extension["packageName"], extension["resources"]["apkUrl"]) for extension in extensions]
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
            results = list(executor.map(check_url, work))
        failures = [
            {"packageName": package_name, "url": url, "error": status}
            for package_name, url, status in results
            if status != "ok"
        ]
        if args.url_report:
            args.url_report.parent.mkdir(parents=True, exist_ok=True)
            args.url_report.write_text(json.dumps({
                "checked": len(results),
                "reachable": len(results) - len(failures),
                "failed": failures,
            }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        errors.extend(f"unreachable {item['packageName']}: {item['error']} {item['url']}" for item in failures)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"valid: {len(extensions)} extensions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
