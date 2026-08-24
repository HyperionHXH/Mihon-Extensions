#!/usr/bin/env python3
"""Build one Mihon index from maintained modern and legacy repositories."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit


USER_AGENT = "HyperionHXH-Mihon-Extensions/1.0"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_json(url: str) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.load(response)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_url(url: str) -> str:
    if not url:
        return ""
    parts = urlsplit(url.strip())
    host = (parts.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    port = f":{parts.port}" if parts.port else ""
    path = parts.path.rstrip("/")
    return urlunsplit((parts.scheme.lower() or "https", host + port, path, "", ""))


def local_extension(info: dict[str, Any], custom: dict[str, Any], base_url: str) -> dict[str, Any]:
    sources = [
        {
            "id": str(source["id"]),
            "name": source["name"],
            "language": source["lang"],
            "homeUrl": source["baseUrl"],
            **({"mirrorUrls": source["mirrorUrls"]} if source.get("mirrorUrls") else {}),
        }
        for source in info["sources"]
    ]
    return {
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
        "sources": sources,
        "_repository": custom["repository"],
        "_priority": 1000,
    }


def legacy_to_modern(entry: dict[str, Any], repository: dict[str, Any]) -> dict[str, Any]:
    package_name = entry["pkg"]
    version_name = entry["version"]
    sources = entry.get("sources") or [{
        "id": "0",
        "name": entry["name"],
        "lang": entry["lang"],
        "baseUrl": "",
    }]
    name = entry["name"]
    for prefix in ("Tachiyomi: ", "Mihonyomi Extension: "):
        if name.startswith(prefix):
            name = name[len(prefix):]
    return {
        "name": name,
        "packageName": package_name,
        "resources": {
            "apkUrl": f"{repository['assetBaseUrl'].rstrip('/')}/apk/{entry['apk']}",
            "iconUrl": f"{repository['iconBaseUrl'].rstrip('/')}/{package_name}.png",
        },
        "extensionLib": version_name.rsplit(".", 1)[0],
        "versionCode": str(entry["code"]),
        "versionName": version_name,
        "contentWarning": "CONTENT_WARNING_NSFW" if int(entry.get("nsfw", 0)) else "CONTENT_WARNING_SAFE",
        "sources": [
            {
                "id": str(source["id"]),
                "name": source["name"],
                "language": source["lang"],
                "homeUrl": source.get("baseUrl", ""),
            }
            for source in sources
        ],
        "_repository": repository["name"],
        "_priority": int(repository["priority"]),
    }


def load_repository(repository: dict[str, Any]) -> tuple[list[dict[str, Any]], str | None]:
    document = fetch_json(repository["indexUrl"])
    if repository["format"] == "modern":
        expected = repository.get("expectedSigningKey")
        actual = str(document.get("signingKey", "")).replace(":", "").lower()
        if expected and actual != expected.lower():
            raise ValueError(f"{repository['name']} signing key changed: {actual}")
        extensions = document.get("extensionList", {}).get("extensions", [])
        if not extensions:
            raise ValueError(f"{repository['name']} has no extensions")
        result = []
        for extension in extensions:
            item = dict(extension)
            item["_repository"] = repository["name"]
            item["_priority"] = int(repository["priority"])
            result.append(item)
        return result, actual
    if not isinstance(document, list) or not document:
        raise ValueError(f"{repository['name']} legacy index is empty or invalid")
    return [legacy_to_modern(entry, repository) for entry in document], None


def public_extension(extension: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in extension.items() if not key.startswith("_")}


def deduplicate(candidates: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    ordered = sorted(
        candidates,
        key=lambda item: (-int(item["_priority"]), item["name"].lower(), item["packageName"]),
    )
    packages: dict[str, dict[str, Any]] = {}
    source_ids: dict[str, dict[str, Any]] = {}
    source_urls: dict[str, dict[str, Any]] = {}
    included: list[dict[str, Any]] = []
    excluded: list[dict[str, str]] = []
    for extension in ordered:
        package_name = extension["packageName"]
        if package_name in packages:
            kept = packages[package_name]
            excluded.append({
                "packageName": package_name,
                "repository": extension["_repository"],
                "reason": f"duplicate package; kept {kept['_repository']} {kept['versionName']}",
            })
            continue
        ids = {str(source["id"]) for source in extension["sources"] if str(source["id"]) != "0"}
        collision = next((source_ids[source_id] for source_id in ids if source_id in source_ids), None)
        if collision:
            excluded.append({
                "packageName": package_name,
                "repository": extension["_repository"],
                "reason": f"duplicate source id; kept {collision['_repository']} {collision['packageName']}",
            })
            continue
        urls = {normalized_url(source.get("homeUrl", "")) for source in extension["sources"]}
        urls.discard("")
        if urls and all(url in source_urls for url in urls) and all(
            source_urls[url]["_repository"] != extension["_repository"] for url in urls
        ):
            kept = source_urls[next(iter(urls))]
            excluded.append({
                "packageName": package_name,
                "repository": extension["_repository"],
                "reason": f"duplicate site; kept {kept['_repository']} {kept['packageName']}",
            })
            continue
        packages[package_name] = extension
        for source_id in ids:
            source_ids[source_id] = extension
        for url in urls:
            source_urls[url] = extension
        included.append(extension)
    return included, excluded


def legacy_entry(extension: dict[str, Any]) -> dict[str, Any]:
    source = extension["sources"][0]
    return {
        "name": extension["name"],
        "pkg": extension["packageName"],
        "apk": extension["resources"]["apkUrl"].rsplit("/", 1)[-1],
        "lang": source["language"],
        "code": int(extension["versionCode"]),
        "version": extension["versionName"],
        "nsfw": 1 if extension["contentWarning"] != "CONTENT_WARNING_SAFE" else 0,
        "sources": [
            {
                "name": item["name"],
                "lang": item["language"],
                "id": item["id"],
                "baseUrl": item.get("homeUrl", ""),
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
    custom = config["custom"]
    output = args.output
    base_url = (args.base_url or custom["repositoryBaseUrl"]).rstrip("/")

    candidates = []
    for extension in custom["extensions"]:
        source_info_path = Path(extension["sourceInfo"])
        if not source_info_path.is_absolute():
            source_info_path = Path(__file__).resolve().parents[1] / source_info_path
        candidates.append(local_extension(read_json(source_info_path), extension, base_url))
    repository_report: list[dict[str, Any]] = []
    signing_key = ""
    for repository in config["repositories"]:
        extensions, key = load_repository(repository)
        candidates.extend(extensions)
        repository_report.append({
            "name": repository["name"],
            "indexUrl": repository["indexUrl"],
            "fetched": len(extensions),
        })
        if repository["name"] == "Keiyoushi":
            signing_key = key or repository["expectedSigningKey"]
    if not signing_key:
        raise ValueError("Keiyoushi signing key is unavailable")

    included, duplicate_report = deduplicate(candidates)
    merged = sorted((public_extension(item) for item in included), key=lambda item: (item["name"].lower(), item["packageName"]))
    included_counts: dict[str, int] = {}
    for item in included:
        included_counts[item["_repository"]] = included_counts.get(item["_repository"], 0) + 1
    for item in repository_report:
        item["included"] = included_counts.get(item["name"], 0)

    output.mkdir(parents=True, exist_ok=True)
    modern = {
        "name": "Hyperion Mihon Extensions",
        "badgeLabel": "HYP",
        "signingKey": signing_key,
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
            "signingKeyFingerprint": signing_key,
        },
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    checksums: dict[str, str] = {}
    project_root = Path(__file__).resolve().parents[1]
    for extension in custom["extensions"]:
        for relative in (extension["apk"], extension["jar"], extension["icon"]):
            path = project_root / "repo" / relative
            if path.is_file():
                checksums[relative] = sha256(path)
    (output / "checksums.json").write_text(json.dumps(checksums, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = {
        "fetched": len(candidates),
        "included": len(merged),
        "repositories": repository_report,
        "customIncluded": {
            extension["repository"]: included_counts.get(extension["repository"], 0)
            for extension in custom["extensions"]
        },
        "duplicatesExcluded": duplicate_report,
        "repositoriesExcluded": config.get("excludedRepositories", []),
    }
    (output / "build-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"built {len(merged)} extensions from {len(config['repositories'])} repositories; excluded {len(duplicate_report)} duplicates")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
