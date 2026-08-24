#!/usr/bin/env python3
"""Build the Mihon repository index from an upstream index plus local sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "HyperionHXH-Mihon-Extensions/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.load(response)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_entries(info: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": str(source["id"]),
            "name": source["name"],
            "language": source["lang"],
            "homeUrl": source["baseUrl"],
            **({"mirrorUrls": source["mirrorUrls"]} if source.get("mirrorUrls") else {}),
        }
        for source in info["sources"]
    ]


def legacy_entry(extension: dict[str, Any]) -> dict[str, Any]:
    resources = extension["resources"]
    source = extension["sources"][0]
    return {
        "name": extension["name"],
        "pkg": extension["packageName"],
        "apk": resources["apkUrl"].rsplit("/", 1)[-1],
        "lang": source["language"],
        "code": int(extension["versionCode"]),
        "version": extension["versionName"],
        "nsfw": 1 if extension["contentWarning"] != "CONTENT_WARNING_SAFE" else 0,
        "sources": [
            {
                "name": item["name"],
                "lang": item["language"],
                "id": item["id"],
                "baseUrl": item["homeUrl"],
            }
            for item in extension["sources"]
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config/sources.json"))
    parser.add_argument("--output", type=Path, default=Path("repo"))
    parser.add_argument("--base-url", help="Override the public repo directory URL")
    args = parser.parse_args()

    config = read_json(args.config)
    upstream = config["upstream"]
    custom = config["custom"]
    output = args.output
    source_info_path = Path(custom["sourceInfo"])
    if not source_info_path.is_absolute():
        source_info_path = Path(__file__).resolve().parents[1] / source_info_path
    info = read_json(source_info_path)
    upstream_index = fetch_json(upstream["indexUrl"])
    extensions = list(upstream_index.get("extensionList", {}).get("extensions", []))
    if not extensions:
        raise ValueError("upstream index has no extensions")
    expected_key = upstream["expectedSigningKey"].lower()
    actual_key = str(upstream_index.get("signingKey", "")).replace(":", "").lower()
    if actual_key != expected_key:
        raise ValueError(f"upstream signing key changed: {actual_key}")

    base_url = (args.base_url or custom["repositoryBaseUrl"]).rstrip("/")
    local_sources = source_entries(info)
    local_extension = {
        "name": info["name"],
        "packageName": info["packageName"],
        "resources": {
            "apkUrl": f"{base_url}/{custom['apk']}",
            "iconUrl": f"{base_url}/{custom['icon']}",
            "jarUrl": f"{base_url}/{custom['jar']}",
        },
        "extensionLib": info["extensionLib"],
        "versionCode": str(info["versionCode"]),
        "versionName": info["versionName"],
        "contentWarning": "CONTENT_WARNING_NSFW" if info["contentWarning"] == 3 else "CONTENT_WARNING_MIXED",
        "sources": local_sources,
    }

    by_package: dict[str, dict[str, Any]] = {}
    for extension in extensions + [local_extension]:
        package_name = extension["packageName"]
        previous = by_package.get(package_name)
        if previous and previous["versionCode"] != extension["versionCode"]:
            raise ValueError(f"duplicate package with conflicting versions: {package_name}")
        by_package[package_name] = extension
    merged = sorted(by_package.values(), key=lambda item: (item["name"].lower(), item["packageName"]))

    output.mkdir(parents=True, exist_ok=True)
    modern = {
        "name": "Hyperion Mihon Extensions",
        "badgeLabel": "HYP",
        "signingKey": expected_key,
        "contact": {
            "website": "https://github.com/HyperionHXH/Mihon-Extensions",
            "discord": None,
        },
        "extensionList": {"extensions": merged},
    }
    (output / "index.json").write_text(json.dumps(modern, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "index.min.json").write_text(json.dumps([legacy_entry(item) for item in merged], ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    (output / "repo.json").write_text(json.dumps({
        "index_v2": f"{base_url}/index.json",
        "meta": {
            "name": modern["name"],
            "shortName": modern["badgeLabel"],
            "website": modern["contact"]["website"],
            "signingKeyFingerprint": expected_key,
        },
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    checksums: dict[str, str] = {}
    for relative in (custom["apk"], custom["jar"], custom["icon"]):
        path = output / Path(relative).name if "/" not in relative else Path(__file__).resolve().parents[1] / "repo" / relative
        if path.is_file():
            checksums[relative] = sha256(path)
    (output / "checksums.json").write_text(json.dumps(checksums, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"built {len(merged)} extensions ({len(extensions)} upstream + 1 local)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
