import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock


def load_module(name: str):
    path = Path(__file__).with_name(name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


archive = load_module("archive_extensions")
build_index = load_module("build_index")


class ArchiveExtensionsTest(unittest.TestCase):
    def test_selection_includes_nsfw_and_explicit_packages(self):
        index = {
            "extensionList": {
                "extensions": [
                    {"packageName": "safe", "contentWarning": "CONTENT_WARNING_SAFE"},
                    {"packageName": "adult", "contentWarning": "CONTENT_WARNING_NSFW"},
                    {"packageName": "common", "contentWarning": "CONTENT_WARNING_SAFE"},
                ],
            },
        }
        config = {"contentWarnings": ["CONTENT_WARNING_NSFW"], "packages": ["common"]}
        selected = archive.selected_extensions(index, config)
        self.assertEqual([item["packageName"] for item in selected], ["adult", "common"])

    def test_selection_can_archive_every_extension(self):
        index = {
            "extensionList": {
                "extensions": [
                    {"packageName": "safe", "contentWarning": "CONTENT_WARNING_SAFE"},
                    {"packageName": "adult", "contentWarning": "CONTENT_WARNING_NSFW"},
                ],
            },
        }
        selected = archive.selected_extensions(index, {"archiveAll": True})
        self.assertEqual([item["packageName"] for item in selected], ["safe", "adult"])

    def test_shard_is_stable(self):
        first = archive.shard_for("eu.kanade.example", 4)
        self.assertEqual(first, archive.shard_for("eu.kanade.example", 4))
        self.assertIn(first, range(4))

    def test_certificate_parser_accepts_colons(self):
        digest = "D7:03:01:D3:31:61:D1:83:34:5F:A7:CD:4D:65:1C:D0:FF:89:2E:A9:BE:28:0E:7A:4D:F4:F3:C5:32:D0:2C:54"
        self.assertEqual(
            archive.parse_certificate_digest(f"Signer #1 certificate SHA-256 digest: {digest}"),
            digest.replace(":", "").lower(),
        )

    def test_badging_parser(self):
        output = "package: name='eu.kanade.example' versionCode='7' versionName='1.6.7'"
        self.assertEqual(
            archive.parse_badging(output),
            ("eu.kanade.example", "7", "1.6.7"),
        )

    def test_archive_rewrites_matching_version(self):
        upstream = self.extension("1.6.2", "2", "https://upstream/current.apk")
        manifest = self.manifest(self.extension("1.6.2", "2", "https://mirror/current.apk"))
        result, report, duplicates = build_index.apply_archive_manifest([upstream], manifest)
        self.assertEqual(result[0]["resources"]["apkUrl"], "https://mirror/current.apk")
        self.assertEqual(report["mirrored"], 1)
        self.assertEqual(duplicates, [])

    def test_archive_does_not_replace_newer_upstream_version(self):
        upstream = self.extension("1.6.3", "3", "https://upstream/new.apk")
        manifest = self.manifest(self.extension("1.6.2", "2", "https://mirror/old.apk"))
        result, report, _ = build_index.apply_archive_manifest([upstream], manifest)
        self.assertEqual(result[0]["resources"]["apkUrl"], "https://upstream/new.apk")
        self.assertEqual(report["mirrored"], 0)

    def test_archive_restores_removed_extension(self):
        archived = self.extension("1.6.2", "2", "https://mirror/current.apk")
        result, report, _ = build_index.apply_archive_manifest([], self.manifest(archived))
        self.assertEqual(result[0]["packageName"], "eu.kanade.example")
        self.assertEqual(report["recovered"], 1)

    def test_same_version_repair_preserves_existing_jar_when_download_fails(self):
        extension = self.extension("1.6.2", "2", "https://upstream/current.apk")
        extension["resources"]["jarUrl"] = "https://upstream/current.jar"
        extension["resources"].pop("iconUrl")
        existing_jar = {
            "assetName": "existing.jar",
            "url": "https://mirror/existing.jar",
            "upstreamUrl": "https://upstream/existing.jar",
            "sha256": "1" * 64,
            "size": 123,
        }
        existing = {
            "versions": [{
                "versionCode": "2",
                "versionName": "1.6.2",
                "jar": existing_jar,
            }],
        }

        def download(url, destination, _timeout):
            if url.endswith(".jar"):
                raise OSError("temporary failure")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(b"apk")

        with tempfile.TemporaryDirectory() as temp_dir, \
                mock.patch.object(archive, "download", side_effect=download), \
                mock.patch.object(archive, "verify_apk", return_value="a" * 64):
            package, _, failures = archive.archive_extension(
                extension,
                existing,
                Path(temp_dir),
                "owner/repo",
                self.archive_config(),
                "apksigner",
                "aapt",
            )

        self.assertEqual(package["versions"][0]["jar"], existing_jar)
        self.assertEqual(len(failures), 1)

    def test_archive_retains_only_current_and_previous_versions(self):
        extension = self.extension("1.6.3", "3", "https://upstream/new.apk")
        extension["resources"].pop("iconUrl")
        existing = {
            "versions": [
                {"versionCode": "2", "versionName": "1.6.2"},
                {"versionCode": "1", "versionName": "1.6.1"},
            ],
        }

        def download(_url, destination, _timeout):
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(b"apk")

        with tempfile.TemporaryDirectory() as temp_dir, \
                mock.patch.object(archive, "download", side_effect=download), \
                mock.patch.object(archive, "verify_apk", return_value="a" * 64):
            package, _, failures = archive.archive_extension(
                extension,
                existing,
                Path(temp_dir),
                "owner/repo",
                self.archive_config(),
                "apksigner",
                "aapt",
            )

        self.assertEqual(
            [version["versionCode"] for version in package["versions"]],
            ["3", "2"],
        )
        self.assertEqual(failures, [])

    def test_existing_package_keeps_its_original_shard(self):
        extension = self.extension("1.6.3", "3", "https://upstream/new.apk")
        extension["resources"].pop("iconUrl")
        existing = {"shard": 1, "versions": []}

        def download(_url, destination, _timeout):
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(b"apk")

        config = self.archive_config()
        config["releaseShardCount"] = 8
        with tempfile.TemporaryDirectory() as temp_dir, \
                mock.patch.object(archive, "download", side_effect=download), \
                mock.patch.object(archive, "verify_apk", return_value="a" * 64):
            package, _, failures = archive.archive_extension(
                extension,
                existing,
                Path(temp_dir),
                "owner/repo",
                config,
                "apksigner",
                "aapt",
            )

        self.assertEqual(package["shard"], 1)
        self.assertEqual(failures, [])

    def test_extract_apk_icon_selects_highest_density_raster(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            apk = root / "extension.apk"
            with zipfile.ZipFile(apk, "w") as output:
                output.writestr("res/low.png", b"low")
                output.writestr("res/high.png", b"high")
            badging = "\n".join([
                "application-icon-160:'res/low.png'",
                "application-icon-640:'res/high.png'",
            ])
            with mock.patch.object(archive, "command_output", return_value=badging):
                path, name, resource = archive.extract_apk_icon(
                    apk,
                    root / "output",
                    "eu.kanade.example",
                    "aapt",
                )

            self.assertEqual(path.read_bytes(), b"high")
            self.assertEqual(name, "eu.kanade.example--icon.png")
            self.assertEqual(resource, "res/high.png")

    @staticmethod
    def extension(version_name, version_code, apk_url):
        return {
            "name": "Example",
            "packageName": "eu.kanade.example",
            "resources": {"apkUrl": apk_url, "iconUrl": "https://example/icon.png"},
            "extensionLib": "1.6",
            "versionCode": version_code,
            "versionName": version_name,
            "contentWarning": "CONTENT_WARNING_NSFW",
            "sources": [{"id": "123", "name": "Example", "language": "en", "homeUrl": "https://example.com"}],
            "_repository": "Test",
            "_priority": 100,
        }

    @staticmethod
    def manifest(extension):
        return {
            "packages": {
                extension["packageName"]: {
                    "versions": [
                        {
                            "versionName": extension["versionName"],
                            "versionCode": extension["versionCode"],
                            "extension": extension,
                        },
                    ],
                },
            },
        }

    @staticmethod
    def archive_config():
        return {
            "releaseShardCount": 4,
            "releaseTagPrefix": "extension-archive",
            "requestTimeoutSeconds": 30,
            "retentionPerPackage": 2,
        }


if __name__ == "__main__":
    unittest.main()
