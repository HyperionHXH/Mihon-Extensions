#!/usr/bin/env python3
"""Validate a generated index without downloading every extension APK."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


PACKAGE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*(?:\.[a-zA-Z][a-zA-Z0-9_]*)+$")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("index", type=Path, nargs="?", default=Path("repo/index.json"))
    parser.add_argument("--check-urls", action="store_true")
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
    if args.check_urls:
        for extension in extensions:
            url = extension["resources"]["apkUrl"]
            request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "HyperionHXH-Mihon-Extensions/1.0"})
            try:
                with urllib.request.urlopen(request, timeout=20) as response:
                    if response.status >= 400:
                        errors.append(f"{response.status} {url}")
            except Exception as error:  # noqa: BLE001 - report all broken upstream URLs
                errors.append(f"unreachable {url}: {error}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"valid: {len(extensions)} extensions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
