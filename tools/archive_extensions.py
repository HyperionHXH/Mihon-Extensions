#!/usr/bin/env python3
"""Download, verify, and retain mirrored extension release assets."""

from __future__ import annotations

import argparse
import concurrent.futures
import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


USER_AGENT = "HyperionHXH-Mihon-Archive/1.0"
PACKAGE_LINE = re.compile(
    r"package: name='([^']+)' versionCode='([^']+)' versionName='([^']+)'",
)
CERT_DIGEST = re.compile(r"SHA-256 digest:\s*([0-9A-Fa-f:]+)")
SAFE_ASSET = re.compile(r"[^A-Za-z0-9._-]+")
ICON_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".svg"}
APK_ICON_LINE = re.compile(r"application-icon-(\d+):'([^']+)'")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sanitize(value: str) -> str:
    return SAFE_ASSET.sub("_", value).strip("._-")


def shard_for(package_name: str, count: int) -> int:
    digest = hashlib.sha256(package_name.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") % count


def asset_name(extension: dict[str, Any], kind: str, suffix: str) -> str:
    package_name = sanitize(extension["packageName"])
    version_name = sanitize(str(extension["versionName"]))
    version_code = sanitize(str(extension["versionCode"]))
    return f"{package_name}--v{version_name}--c{version_code}.{kind}{suffix}"


def icon_asset_name(package_name: str, url: str) -> str:
    suffix = Path(urlsplit(url).path).suffix.lower()
    if suffix not in ICON_SUFFIXES:
        suffix = ".png"
    return f"{sanitize(package_name)}--icon{suffix}"


def release_url(repository: str, tag: str, name: str) -> str:
    return f"https://github.com/{repository}/releases/download/{tag}/{name}"


def download(url: str, destination: Path, timeout: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None
    for attempt in range(3):
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                if response.status >= 400:
                    raise OSError(f"HTTP {response.status}")
                with destination.open("wb") as output:
                    shutil.copyfileobj(response, output, length=1024 * 1024)
            if destination.stat().st_size == 0:
                raise OSError("empty response")
            return
        except Exception as error:  # noqa: BLE001 - all transport failures are retried
            last_error = error
            destination.unlink(missing_ok=True)
            if attempt < 2:
                time.sleep(attempt + 1)
    raise OSError(f"download failed: {last_error}")


def command_output(arguments: list[str]) -> str:
    result = subprocess.run(arguments, check=False, capture_output=True, text=True)
    output = (result.stdout + "\n" + result.stderr).strip()
    if result.returncode != 0:
        raise ValueError(output or f"command exited with {result.returncode}")
    return output


def parse_certificate_digest(output: str) -> str:
    match = CERT_DIGEST.search(output)
    if not match:
        raise ValueError("APK signer certificate digest is unavailable")
    digest = match.group(1).replace(":", "").lower()
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ValueError("APK signer certificate digest is invalid")
    return digest


def parse_badging(output: str) -> tuple[str, str, str]:
    match = PACKAGE_LINE.search(output)
    if not match:
        raise ValueError("APK package metadata is unavailable")
    return match.group(1), match.group(2), match.group(3)


def verify_apk(
    path: Path,
    extension: dict[str, Any],
    apksigner: str,
    aapt: str,
    expected_certificate: str | None,
) -> str:
    signer_output = command_output([apksigner, "verify", "--print-certs", str(path)])
    certificate = parse_certificate_digest(signer_output)
    if expected_certificate and certificate != expected_certificate:
        raise ValueError(
            f"signing certificate changed from {expected_certificate} to {certificate}",
        )

    package_name, version_code, version_name = parse_badging(
        command_output([aapt, "dump", "badging", str(path)]),
    )
    expected = (
        extension["packageName"],
        str(extension["versionCode"]),
        str(extension["versionName"]),
    )
    actual = (package_name, version_code, version_name)
    if actual != expected:
        raise ValueError(f"APK metadata mismatch: expected {expected}, got {actual}")
    return certificate


def extract_apk_icon(
    apk_path: Path,
    destination_dir: Path,
    package_name: str,
    aapt: str,
) -> tuple[Path, str, str]:
    candidates = [
        (int(density), resource)
        for density, resource in APK_ICON_LINE.findall(
            command_output([aapt, "dump", "badging", str(apk_path)]),
        )
    ]
    if not candidates:
        raise ValueError("APK has no raster launcher icon")
    _, resource = max(candidates)
    suffix = Path(resource).suffix.lower()
    if suffix not in ICON_SUFFIXES - {".svg"}:
        raise ValueError(f"unsupported APK icon format: {suffix or 'none'}")
    with zipfile.ZipFile(apk_path) as archive:
        content = archive.read(resource)
    if not content or len(content) > 5 * 1024 * 1024:
        raise ValueError("APK launcher icon has an invalid size")
    name = f"{sanitize(package_name)}--icon{suffix}"
    path = destination_dir / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path, name, resource


def asset_record(path: Path, upstream_url: str, mirror_url: str, name: str) -> dict[str, Any]:
    return {
        "assetName": name,
        "url": mirror_url,
        "upstreamUrl": upstream_url,
        "sha256": sha256_file(path),
        "size": path.stat().st_size,
    }


def previous_certificate(package: dict[str, Any] | None) -> str | None:
    if not package:
        return None
    for version in package.get("versions", []):
        certificate = version.get("apk", {}).get("signingCertificateSha256")
        if certificate:
            return str(certificate)
    return None


def same_version(extension: dict[str, Any], version: dict[str, Any]) -> bool:
    return (
        str(extension["versionCode"]) == str(version.get("versionCode"))
        and str(extension["versionName"]) == str(version.get("versionName"))
    )


def needs_archive(extension: dict[str, Any], package: dict[str, Any] | None) -> bool:
    if not package or not package.get("versions"):
        return True
    current = package["versions"][0]
    if not same_version(extension, current):
        return True
    resources = extension.get("resources", {})
    if resources.get("jarUrl") and not current.get("jar"):
        return True
    if resources.get("iconUrl") and not package.get("icon"):
        return True
    return False


def archive_extension(
    extension: dict[str, Any],
    existing: dict[str, Any] | None,
    output: Path,
    repository: str,
    config: dict[str, Any],
    apksigner: str,
    aapt: str,
) -> tuple[dict[str, Any] | None, list[Path], list[str]]:
    package_name = extension["packageName"]
    shard = (
        int(existing["shard"])
        if existing and "shard" in existing
        else shard_for(package_name, int(config["releaseShardCount"]))
    )
    tag = f"{config['releaseTagPrefix']}-{shard}"
    asset_dir = output / "assets" / f"shard-{shard}"
    resources = extension.get("resources", {})
    failures: list[str] = []
    uploads: list[Path] = []

    apk_url = resources.get("apkUrl")
    if not apk_url:
        return None, uploads, ["missing APK URL"]
    apk_name = asset_name(extension, "apk", "")
    apk_path = asset_dir / apk_name
    try:
        download(apk_url, apk_path, int(config["requestTimeoutSeconds"]))
        certificate = verify_apk(
            apk_path,
            extension,
            apksigner,
            aapt,
            previous_certificate(existing),
        )
    except (OSError, ValueError) as error:
        apk_path.unlink(missing_ok=True)
        return None, uploads, [f"APK: {error}"]

    apk = asset_record(apk_path, apk_url, release_url(repository, tag, apk_name), apk_name)
    apk["signingCertificateSha256"] = certificate
    uploads.append(apk_path)

    matching_version = None
    if existing:
        matching_version = next(
            (version for version in existing.get("versions", []) if same_version(extension, version)),
            None,
        )
    jar = copy.deepcopy(matching_version.get("jar")) if matching_version and matching_version.get("jar") else None
    jar_url = resources.get("jarUrl")
    if jar_url:
        jar_name = asset_name(extension, "jar", "")
        jar_path = asset_dir / jar_name
        try:
            download(jar_url, jar_path, int(config["requestTimeoutSeconds"]))
            jar = asset_record(jar_path, jar_url, release_url(repository, tag, jar_name), jar_name)
            uploads.append(jar_path)
        except OSError as error:
            jar_path.unlink(missing_ok=True)
            failures.append(f"JAR: {error}")

    icon = copy.deepcopy(existing.get("icon")) if existing and existing.get("icon") else None
    icon_url = resources.get("iconUrl")
    if icon_url:
        icon_name = icon_asset_name(package_name, icon_url)
        icon_path = asset_dir / icon_name
        try:
            download(icon_url, icon_path, int(config["requestTimeoutSeconds"]))
            icon = asset_record(icon_path, icon_url, release_url(repository, tag, icon_name), icon_name)
            uploads.append(icon_path)
        except OSError as error:
            icon_path.unlink(missing_ok=True)
            try:
                icon_path, icon_name, resource = extract_apk_icon(
                    apk_path,
                    asset_dir,
                    package_name,
                    aapt,
                )
                icon = asset_record(
                    icon_path,
                    f"{apk_url}#{resource}",
                    release_url(repository, tag, icon_name),
                    icon_name,
                )
                uploads.append(icon_path)
            except (OSError, ValueError, KeyError, zipfile.BadZipFile) as fallback_error:
                failures.append(f"icon: {error}; APK fallback: {fallback_error}")

    snapshot = copy.deepcopy(extension)
    snapshot["resources"]["apkUrl"] = apk["url"]
    if jar:
        snapshot["resources"]["jarUrl"] = jar["url"]
    if icon:
        snapshot["resources"]["iconUrl"] = icon["url"]

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    version = {
        "versionCode": str(extension["versionCode"]),
        "versionName": str(extension["versionName"]),
        "archivedAt": now,
        "apk": apk,
        **({"jar": jar} if jar else {}),
        "extension": snapshot,
    }
    versions = [] if not existing else copy.deepcopy(existing.get("versions", []))
    versions = [item for item in versions if not same_version(extension, item)]
    versions.insert(0, version)
    versions = versions[: int(config["retentionPerPackage"])]
    package = {
        "shard": shard,
        "upstreamPresent": True,
        "selected": True,
        **({"icon": icon} if icon else {}),
        "versions": versions,
    }
    return package, uploads, failures


def selected_extensions(index: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    extensions = index["extensionList"]["extensions"]
    if config.get("archiveAll", False):
        return extensions
    warnings = set(config.get("contentWarnings", []))
    packages = set(config.get("packages", []))
    return [
        extension
        for extension in extensions
        if extension.get("contentWarning") in warnings or extension["packageName"] in packages
    ]


def desired_assets(manifest: dict[str, Any]) -> dict[int, set[str]]:
    result = {shard: set() for shard in range(int(manifest["releaseShardCount"]))}
    for package in manifest["packages"].values():
        names = result[int(package["shard"])]
        if package.get("icon"):
            names.add(package["icon"]["assetName"])
        for version in package.get("versions", []):
            names.add(version["apk"]["assetName"])
            if version.get("jar"):
                names.add(version["jar"]["assetName"])
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path("config/archive.json"))
    parser.add_argument("--existing", type=Path, default=Path("repo/archive-manifest.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--apksigner", required=True)
    parser.add_argument("--aapt", required=True)
    args = parser.parse_args()

    config = read_json(args.config)
    index = read_json(args.index)
    existing = read_json(args.existing) if args.existing.is_file() else {"packages": {}}
    args.output.mkdir(parents=True, exist_ok=True)
    selected = selected_extensions(index, config)
    all_packages = {item["packageName"] for item in index["extensionList"]["extensions"]}
    existing_packages = existing.get("packages", {})
    packages: dict[str, Any] = {}
    failures: list[dict[str, str]] = []
    upload_paths: list[Path] = []
    archived = 0
    reused = 0

    def task(extension: dict[str, Any]) -> tuple[str, dict[str, Any] | None, list[Path], list[str], bool]:
        package_name = extension["packageName"]
        current = existing_packages.get(package_name)
        if not needs_archive(extension, current):
            package = copy.deepcopy(current)
            package["upstreamPresent"] = True
            package["selected"] = True
            return package_name, package, [], [], False
        package, uploads, errors = archive_extension(
            extension,
            current,
            args.output,
            args.repository,
            config,
            args.apksigner,
            args.aapt,
        )
        return package_name, package, uploads, errors, True

    with concurrent.futures.ThreadPoolExecutor(max_workers=int(config["maxWorkers"])) as executor:
        futures = [executor.submit(task, extension) for extension in selected]
        for future in concurrent.futures.as_completed(futures):
            package_name, package, uploads, errors, attempted = future.result()
            if package is None:
                old_package = existing_packages.get(package_name)
                if old_package:
                    package = copy.deepcopy(old_package)
                failures.extend({"packageName": package_name, "error": error} for error in errors)
            else:
                failures.extend({"packageName": package_name, "error": error} for error in errors)
                upload_paths.extend(uploads)
                archived += int(attempted)
                reused += int(not attempted)
            if package:
                packages[package_name] = package

    if config.get("retainRemovedPackages", True):
        for package_name, package in existing_packages.items():
            if package_name in packages:
                continue
            retained = copy.deepcopy(package)
            retained["upstreamPresent"] = package_name in all_packages
            retained["selected"] = False
            packages[package_name] = retained

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    manifest = {
        "schemaVersion": int(config["schemaVersion"]),
        "generatedAt": now if archived or packages != existing_packages else existing.get("generatedAt"),
        "releaseTagPrefix": config["releaseTagPrefix"],
        "releaseShardCount": int(config["releaseShardCount"]),
        "retentionPerPackage": int(config["retentionPerPackage"]),
        "packages": dict(sorted(packages.items())),
    }
    write_json(args.output / "archive-manifest.json", manifest)
    write_json(
        args.output / "archive-report.json",
        {
            "generatedAt": now,
            "selected": len(selected),
            "archivedOrRepaired": archived,
            "reused": reused,
            "retainedPackages": len(packages),
            "uploadedAssets": len(upload_paths),
            "uploadedBytes": sum(path.stat().st_size for path in upload_paths),
            "failures": sorted(failures, key=lambda item: (item["packageName"], item["error"])),
        },
    )
    for shard, names in desired_assets(manifest).items():
        desired = args.output / "desired-assets" / f"shard-{shard}.txt"
        desired.parent.mkdir(parents=True, exist_ok=True)
        desired.write_text("".join(f"{name}\n" for name in sorted(names)), encoding="utf-8")
    print(
        f"selected {len(selected)} extensions; archived/repaired {archived}; "
        f"reused {reused}; failures {len(failures)}",
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
