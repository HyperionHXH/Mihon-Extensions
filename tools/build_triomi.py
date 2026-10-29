#!/usr/bin/env python3
"""Validate and publish authored Triomi JavaScript rules, entirely offline.

Static checks are deliberately not a JavaScript parser or a website smoke test.
No APK/JAR is loaded, converted, downloaded, or executed by this tool.
"""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


CATALOG_NAME = "Hyperion Triomi Sources"
CATALOG_URL = "https://raw.githubusercontent.com/HyperionHXH/Mihon-Extensions/main/repo/triomi/index.json"
PUBLIC_BASE = CATALOG_URL.rsplit("/", 1)[0]
MAX_RULE_BYTES = 2 * 1024 * 1024
MAX_SCRIPT_BYTES = 1024 * 1024
MAX_CATALOG_BYTES = 2 * 1024 * 1024
MAX_RULES = 1000
FUNCTIONS = ("discover", "search", "detail", "content")
REQUIRED_FUNCTIONS = ("discover", "detail", "content")
SEMVER = re.compile(
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
    r"(?:-(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)
# Mask comments and literal strings before looking for named function definitions.
JS_LITERALS = re.compile(r"//[^\r\n]*|/\*[\s\S]*?\*/|'(?:\\.|[^'\\\r\n])*'|\"(?:\\.|[^\"\\\r\n])*\"|`(?:\\.|[^`\\])*`")


def discovery_marker() -> dict[str, str]:
    return {"indexUrl": CATALOG_URL, "name": CATALOG_NAME}


def json_bytes(document: Any) -> bytes:
    return (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_constant(value: str) -> None:
    raise ValueError(f"invalid JSON numeric constant: {value}")


def load_json(path: Path, maximum: int) -> tuple[Any, bytes]:
    if path.is_symlink():
        raise ValueError(f"symlinks are not allowed: {path}")
    if path.stat().st_size > maximum:
        raise ValueError(f"file exceeds {maximum} byte limit: {path}")
    data = path.read_bytes()
    return json.loads(data.decode("utf-8"), object_pairs_hook=unique_object, parse_constant=reject_constant), data


def text(value: Any, label: str, maximum: int = 200) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > maximum:
        raise ValueError(f"{label} must be a nonempty trimmed string of at most {maximum} characters")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{label} contains control characters")
    return value


def https_url(value: Any, label: str) -> str:
    value = text(value, label, 2048)
    parts = urlsplit(value)
    if parts.scheme != "https" or not parts.hostname or parts.username is not None or parts.password is not None:
        raise ValueError(f"{label} must be an absolute HTTPS URL without credentials")
    if parts.fragment or any(character.isspace() for character in value) or "\\" in value:
        raise ValueError(f"{label} contains an invalid URL component")
    try:
        port = parts.port
    except ValueError as error:
        raise ValueError(f"{label} contains an invalid port") from error
    if port is not None and port == 0:
        raise ValueError(f"{label} contains an invalid port")
    hostname = parts.hostname.lower()
    if hostname == "localhost" or hostname.endswith((".localhost", ".local")):
        raise ValueError(f"{label} must use a public host")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        if not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", hostname) or ".." in hostname:
            raise ValueError(f"{label} contains an invalid hostname")
    else:
        if not address.is_global:
            raise ValueError(f"{label} must use a public host")
    return value


def defined_functions(script: str) -> set[str]:
    code = JS_LITERALS.sub(lambda match: " " * len(match.group()), script)
    found = set()
    for name in FUNCTIONS:
        declaration = rf"\bfunction\s+{name}\s*\("
        assignment = rf"\b(?:const|let|var)\s+{name}\s*=\s*(?:async\s+)?(?:function\s*\(|\([^)]*\)\s*=>|[A-Za-z_$][\w$]*\s*=>)"
        if re.search(declaration, code) or re.search(assignment, code):
            found.add(name)
    return found


def validate_rule(rule: Any, filename: str) -> dict[str, Any]:
    if not isinstance(rule, dict):
        raise ValueError(f"{filename}: rule must be an object")
    source_id = text(rule.get("id"), f"{filename}: id", 128)
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]*", source_id):
        raise ValueError(f"{filename}: id contains unsupported characters")
    for key in ("name", "lang", "version"):
        text(rule.get(key), f"{filename}: {key}")
    if not re.fullmatch(r"[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*", rule["lang"]):
        raise ValueError(f"{filename}: lang must be a language tag")
    if not SEMVER.fullmatch(rule["version"]):
        raise ValueError(f"{filename}: version must be SemVer (for example 1.0.0)")
    if rule.get("type") != "manga" or rule.get("engine") != "js":
        raise ValueError(f"{filename}: only manga rules using the js engine are supported")
    https_url(rule.get("baseUrl"), f"{filename}: baseUrl")
    if type(rule.get("requireLogin")) is not bool:
        raise ValueError(f"{filename}: requireLogin must be a boolean")
    script = rule.get("script")
    if not isinstance(script, str) or not script.strip() or len(script.encode("utf-8")) > MAX_SCRIPT_BYTES:
        raise ValueError(f"{filename}: script is empty or exceeds {MAX_SCRIPT_BYTES} bytes")
    functions = defined_functions(script)
    missing = set(REQUIRED_FUNCTIONS) - functions
    if missing:
        raise ValueError(f"{filename}: missing JavaScript function definitions: {', '.join(sorted(missing))}")
    feeds = rule.get("feeds")
    if not isinstance(feeds, list) or not feeds or len(feeds) > 100:
        raise ValueError(f"{filename}: feeds must contain 1 to 100 entries")
    feed_ids: set[str] = set()
    for feed in feeds:
        if not isinstance(feed, dict):
            raise ValueError(f"{filename}: feed must be an object")
        feed_id = text(feed.get("id"), f"{filename}: feed id", 128)
        if feed_id in feed_ids:
            raise ValueError(f"{filename}: duplicate feed id {feed_id}")
        feed_ids.add(feed_id)
        text(feed.get("name"), f"{filename}: feed name")
        url = text(feed.get("url"), f"{filename}: feed url", 2048)
        if not (url.startswith("/") and not url.startswith("//") and "\\" not in url and not any(c.isspace() for c in url)):
            https_url(url, f"{filename}: feed url")
    capabilities = rule.get("capabilities")
    if capabilities is not None:
        if not isinstance(capabilities, list) or any(not isinstance(value, str) for value in capabilities):
            raise ValueError(f"{filename}: capabilities must be a list of function names")
        if len(capabilities) != len(set(capabilities)) or set(capabilities) != functions:
            raise ValueError(f"{filename}: capabilities must match the required function definitions exactly")
    if "nsfw" in rule and type(rule["nsfw"]) is not bool:
        raise ValueError(f"{filename}: nsfw must be a boolean")
    return rule


def compatibility_report(android: dict[str, Any], entries: list[dict[str, Any]], rows: list[dict[str, Any]]) -> dict[str, Any]:
    packages = android.get("extensionList", {}).get("extensions")
    if not isinstance(packages, list):
        raise ValueError("repo/index.json must contain extensionList.extensions")
    mapping: dict[str, list[str]] = {}
    for entry, row in zip(entries, rows):
        apk_packages = row.get("apkPackages", [])
        if not isinstance(apk_packages, list) or any(not isinstance(value, str) for value in apk_packages):
            raise ValueError(f"{row['file']}: apkPackages must be a list of unique package names")
        if len(apk_packages) != len(set(apk_packages)):
            raise ValueError(f"{row['file']}: apkPackages must not contain duplicates")
        for package in apk_packages:
            text(package, f"{row['file']}: apkPackages entry")
            if not re.fullmatch(r"[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+", package):
                raise ValueError(f"{row['file']}: invalid APK package name {package}")
            mapping.setdefault(package, []).append(entry["id"])
    known = {package["packageName"] for package in packages}
    if set(mapping) - known:
        raise ValueError(f"apkPackages references packages absent from repo/index.json: {', '.join(sorted(set(mapping) - known))}")
    results = []
    for package in sorted(packages, key=lambda item: item["packageName"]):
        rule_ids = sorted(mapping.get(package["packageName"], []))
        results.append({
            "packageName": package["packageName"],
            "name": package["name"],
            "status": "ported" if rule_ids else "manual_port_required",
            "ruleIds": rule_ids,
        })
    ported = sum(item["status"] == "ported" for item in results)
    return {
        "schemaVersion": 1,
        "notice": "Explicit authored-rule mappings only; ported does not imply feature parity, live-site verification, or APK conversion.",
        "counts": {"androidPackages": len(results), "ported": ported, "manualPortRequired": len(results) - ported, "trackedRules": len(entries)},
        "extensions": results,
    }


def expected_outputs(root: Path) -> dict[str, bytes]:
    manifest, _ = load_json(root / "triomi/catalog.json", MAX_CATALOG_BYTES)
    if not isinstance(manifest, dict) or type(manifest.get("schemaVersion")) is not int or manifest["schemaVersion"] != 1:
        raise ValueError("triomi/catalog.json requires schemaVersion 1")
    rows = manifest.get("sources")
    if not isinstance(rows, list) or len(rows) > MAX_RULES:
        raise ValueError(f"manifest sources must be a list of at most {MAX_RULES} entries")
    rule_directory = root / "triomi/rules"
    if rule_directory.is_symlink():
        raise ValueError("triomi/rules may not be a symlink")
    present = {path.name for path in rule_directory.glob("*.json")}
    listed: set[str] = set()
    ids: set[str] = set()
    entries = []
    outputs: dict[str, bytes] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("manifest source must be an object")
        filename = text(row.get("file"), "manifest file", 160)
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*\.json", filename):
            raise ValueError(f"invalid rule filename: {filename}")
        if filename in listed:
            raise ValueError(f"duplicate manifest filename: {filename}")
        listed.add(filename)
        text(row.get("license"), f"{filename}: license", 300)
        https_url(row.get("upstreamUrl"), f"{filename}: upstreamUrl")
        text(row.get("attribution"), f"{filename}: attribution", 2000)
        rule, data = load_json(rule_directory / filename, MAX_RULE_BYTES)
        validate_rule(rule, filename)
        if rule["id"] in ids:
            raise ValueError(f"duplicate source id: {rule['id']}")
        ids.add(rule["id"])
        outputs[f"rules/{filename}"] = data
        entry = {key: rule[key] for key in ("id", "name", "type", "lang", "version")}
        entry.update({"url": f"{PUBLIC_BASE}/rules/{filename}", "hash": hashlib.sha256(data).hexdigest()})
        entry["capabilities"] = [name for name in FUNCTIONS if name in defined_functions(rule["script"])]
        entry["license"] = row["license"]
        if "nsfw" in rule:
            entry["nsfw"] = rule["nsfw"]
        entries.append(entry)
    if listed != present:
        raise ValueError(f"manifest must list every rule exactly once; unlisted={sorted(present - listed)}, missing={sorted(listed - present)}")
    catalog = {"schemaVersion": 1, "name": CATALOG_NAME, "sources": sorted(entries, key=lambda item: item["id"])}
    outputs["index.json"] = json_bytes(catalog)
    if len(outputs["index.json"]) > MAX_CATALOG_BYTES:
        raise ValueError("generated catalog exceeds size limit")
    # Preserve per-rule license/provenance beside the distributed rules.
    outputs["attribution.json"] = json_bytes({"schemaVersion": 1, "sources": sorted(rows, key=lambda row: row["file"])})
    android, _ = load_json(root / "repo/index.json", 64 * 1024 * 1024)
    for name in ("index.json", "repo.json"):
        document = android if name == "index.json" else load_json(root / "repo" / name, MAX_CATALOG_BYTES)[0]
        if not isinstance(document, dict) or document.get("triomi") != discovery_marker():
            raise ValueError(f"repo/{name} must advertise the canonical triomi marker")
    outputs["compatibility.json"] = json_bytes(compatibility_report(android, entries, rows))
    return outputs


def build(root: Path, check: bool = False) -> None:
    outputs = expected_outputs(root)
    target = root / "repo/triomi"
    if target.is_symlink():
        raise ValueError("repo/triomi may not be a symlink")
    existing = {path.relative_to(target).as_posix(): path for path in target.rglob("*") if path.is_file() or path.is_symlink()}
    if any(path.is_symlink() for path in target.rglob("*")):
        raise ValueError("generated output may not contain symlinks")
    stale = sorted(set(existing) - set(outputs))
    changed = sorted(name for name, data in outputs.items() if name not in existing or existing[name].read_bytes() != data)
    if check:
        if stale or changed:
            raise ValueError(f"stale Triomi publication; run python tools/build_triomi.py; changed/missing={changed}, extra={stale}")
        return
    for name in stale:
        existing[name].unlink()
    for name, data in outputs.items():
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if name in changed:
            path.write_bytes(data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check", action="store_true", help="reject missing, stale, extra, or tampered generated files; do not write")
    args = parser.parse_args()
    build(args.root, check=args.check)
    print("Triomi publication is current" if args.check else "Built Triomi publication offline")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
