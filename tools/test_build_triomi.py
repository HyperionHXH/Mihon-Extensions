import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build_triomi


class TriomiCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "triomi/rules").mkdir(parents=True)
        (self.root / "repo").mkdir()
        self.rule = {
            "id": "example",
            "name": "Example",
            "type": "manga",
            "engine": "js",
            "lang": "en",
            "version": "1.0.0",
            "baseUrl": "https://example.com",
            "requireLogin": False,
            "feeds": [{"id": "popular", "name": "Popular", "url": "/popular"}],
            "script": "\n".join(f"async function {name}() {{ return {{}}; }}" for name in build_triomi.FUNCTIONS),
        }
        self.manifest = {
            "schemaVersion": 1,
            "sources": [{
                "file": "example.json",
                "license": "MIT",
                "upstreamUrl": "https://example.com/source",
                "attribution": "Example author (test fixture, not a site port)",
                "apkPackages": ["org.example.ported"],
            }],
        }
        self.android = {
            "triomi": build_triomi.discovery_marker(),
            "extensionList": {"extensions": [
                {"packageName": "org.example.manual", "name": "Manual", "resources": {"apkUrl": "https://example.com/manual.apk"}},
                {"packageName": "org.example.ported", "name": "Ported", "resources": {"apkUrl": "https://example.com/ported.apk"}},
            ]},
        }
        self.save("triomi/rules/example.json", self.rule)
        self.save("triomi/catalog.json", self.manifest)
        self.save("repo/index.json", self.android)
        self.save("repo/repo.json", {"triomi": build_triomi.discovery_marker(), "index_v2": "https://example.com/index.json"})

    def save(self, path, document):
        (self.root / path).write_bytes(build_triomi.json_bytes(document))

    def load(self, path):
        return json.loads((self.root / path).read_text(encoding="utf-8"))

    def test_build_pins_exact_bytes_and_preserves_android_catalog(self):
        original_android = (self.root / "repo/index.json").read_bytes()
        build_triomi.build(self.root)
        build_triomi.build(self.root, check=True)
        entry = self.load("repo/triomi/index.json")["sources"][0]
        authored = (self.root / "triomi/rules/example.json").read_bytes()
        self.assertEqual(entry["hash"], hashlib.sha256(authored).hexdigest())
        self.assertEqual(entry["url"], build_triomi.PUBLIC_BASE + "/rules/example.json")
        self.assertEqual(entry["capabilities"], list(build_triomi.FUNCTIONS))
        self.assertEqual(entry["license"], "MIT")
        self.assertEqual((self.root / "repo/triomi/rules/example.json").read_bytes(), authored)
        self.assertEqual((self.root / "repo/index.json").read_bytes(), original_android)
        report = self.load("repo/triomi/compatibility.json")
        self.assertEqual(report["counts"], {"androidPackages": 2, "ported": 1, "manualPortRequired": 1, "trackedRules": 1})
        self.assertEqual(report["extensions"][0]["status"], "manual_port_required")
        self.assertEqual(report["extensions"][1]["ruleIds"], ["example"])
        self.assertEqual(self.load("repo/triomi/attribution.json"), self.manifest)

    def test_regular_expression_quotes_do_not_mask_following_function_exports(self):
        self.rule["script"] = (
            r"function parse(value) { return value.replace(/[\"']/g, ''); }"
            "\n" + self.rule["script"]
        )
        self.save("triomi/rules/example.json", self.rule)
        build_triomi.build(self.root)
        self.assertEqual(self.load("repo/triomi/index.json")["sources"][0]["id"], "example")

    def test_repeated_build_is_byte_deterministic(self):
        first = build_triomi.expected_outputs(self.root)
        build_triomi.build(self.root)
        build_triomi.build(self.root)
        self.assertEqual(first, build_triomi.expected_outputs(self.root))
        for name, expected in first.items():
            self.assertEqual((self.root / "repo/triomi" / name).read_bytes(), expected)

    def test_development_source_ids_cannot_be_published(self):
        for source_id in ("local-fixture", "local-fixture-js", "local-fixture-anime", "local-fixture-novel"):
            with self.subTest(source_id=source_id):
                self.rule["id"] = source_id
                self.save("triomi/rules/example.json", self.rule)
                with self.assertRaisesRegex(ValueError, "development source id"):
                    build_triomi.build(self.root)
                self.assertFalse((self.root / "repo/triomi").exists())

    def test_host_requirements_are_preserved_in_catalog(self):
        self.manifest["sources"][0]["hostRequirements"] = "Native gateway required; legacy host unsupported"
        self.save("triomi/catalog.json", self.manifest)
        build_triomi.build(self.root)
        self.assertEqual(
            self.load("repo/triomi/index.json")["sources"][0]["hostRequirements"],
            self.manifest["sources"][0]["hostRequirements"],
        )

    def test_native_contracts_are_preserved_in_catalog(self):
        self.rule["requiresHost"] = ["jmcomic.api.v1", "jmcomic.image.v1"]
        self.save("triomi/rules/example.json", self.rule)
        build_triomi.build(self.root)
        self.assertEqual(self.load("repo/triomi/index.json")["sources"][0]["requiresHost"], self.rule["requiresHost"])

    def test_invalid_native_contracts_are_rejected(self):
        for value in ("a.b", [1], ["a.b", "a.b"], ["bad feature"], ["a.b"] * 33):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "requiresHost"):
                build_triomi.validate_rule({**self.rule, "requiresHost": value}, "example.json")

    def test_invalid_host_requirements_are_rejected(self):
        for value in ("", 178, "unsafe\ncontrol", "x" * 1001):
            self.manifest["sources"][0]["hostRequirements"] = value
            self.save("triomi/catalog.json", self.manifest)
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "hostRequirements"):
                build_triomi.expected_outputs(self.root)

    def test_check_detects_tampered_rule_without_writing(self):
        build_triomi.build(self.root)
        path = self.root / "repo/triomi/rules/example.json"
        path.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "stale Triomi publication"):
            build_triomi.build(self.root, check=True)
        self.assertEqual(path.read_bytes(), b"tampered")

    def test_check_detects_invalid_catalog_hash(self):
        build_triomi.build(self.root)
        catalog = self.load("repo/triomi/index.json")
        catalog["sources"][0]["hash"] = "not-a-sha256"
        self.save("repo/triomi/index.json", catalog)
        with self.assertRaisesRegex(ValueError, "index.json"):
            build_triomi.build(self.root, check=True)

    def test_check_detects_stale_authored_version(self):
        build_triomi.build(self.root)
        self.rule["version"] = "1.0.1"
        self.save("triomi/rules/example.json", self.rule)
        with self.assertRaisesRegex(ValueError, "stale Triomi publication"):
            build_triomi.build(self.root, check=True)

    def test_check_detects_missing_and_extra_outputs(self):
        build_triomi.build(self.root)
        (self.root / "repo/triomi/attribution.json").unlink()
        (self.root / "repo/triomi/obsolete.json").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "obsolete.json"):
            build_triomi.build(self.root, check=True)
        build_triomi.build(self.root)
        self.assertFalse((self.root / "repo/triomi/obsolete.json").exists())
        build_triomi.build(self.root, check=True)

    def test_duplicate_id_is_rejected(self):
        self.save("triomi/rules/duplicate.json", self.rule)
        row = copy.deepcopy(self.manifest["sources"][0])
        row["file"] = "duplicate.json"
        self.manifest["sources"].append(row)
        self.save("triomi/catalog.json", self.manifest)
        with self.assertRaisesRegex(ValueError, "duplicate source id"):
            build_triomi.expected_outputs(self.root)

    def test_unlisted_rule_is_rejected(self):
        self.save("triomi/rules/unlisted.json", self.rule)
        with self.assertRaisesRegex(ValueError, "unlisted"):
            build_triomi.expected_outputs(self.root)

    def test_invalid_urls_are_rejected(self):
        for invalid in ("http://example.com", "//example.com", "https://user:secret@example.com", "https://example.com/#fragment", "https://localhost", "https://127.0.0.1", "https://example.com:99999"):
            with self.subTest(url=invalid):
                with self.assertRaises(ValueError):
                    build_triomi.https_url(invalid, "test url")
        self.rule["baseUrl"] = "http://example.com"
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            build_triomi.validate_rule(self.rule, "example.json")

    def test_missing_functions_and_comment_only_functions_are_rejected(self):
        for script in ("async function discover() {}", "/* " + self.rule["script"] + " */", json.dumps(self.rule["script"])):
            with self.subTest(script=script):
                rule = {**self.rule, "script": script}
                with self.assertRaisesRegex(ValueError, "missing JavaScript function"):
                    build_triomi.validate_rule(rule, "example.json")

    def test_capabilities_must_match_functions(self):
        self.rule["capabilities"] = ["search"]
        with self.assertRaisesRegex(ValueError, "capabilities"):
            build_triomi.validate_rule(self.rule, "example.json")
        self.rule["capabilities"] = list(build_triomi.FUNCTIONS)
        build_triomi.validate_rule(self.rule, "example.json")

    def test_browse_only_rule_does_not_advertise_unimplemented_search(self):
        functions = ("discover", "detail", "content")
        self.rule["script"] = "\n".join(f"async function {name}() {{ return {{}}; }}" for name in functions)
        self.rule["capabilities"] = list(functions)
        self.save("triomi/rules/example.json", self.rule)
        build_triomi.build(self.root)
        entry = self.load("repo/triomi/index.json")["sources"][0]
        self.assertEqual(entry["capabilities"], list(functions))
        self.assertNotIn("search", entry["capabilities"])

    def test_browse_only_rule_cannot_claim_search_or_omit_reading(self):
        for missing in ("discover", "detail", "content"):
            rule = {**self.rule, "script": "\n".join(
                f"async function {name}() {{ return {{}}; }}"
                for name in build_triomi.FUNCTIONS if name != missing
            )}
            with self.subTest(missing=missing), self.assertRaisesRegex(ValueError, "missing JavaScript function"):
                build_triomi.validate_rule(rule, "example.json")
        self.rule["script"] = "function discover() {} function detail() {} function content() {}"
        self.rule["capabilities"] = list(build_triomi.FUNCTIONS)
        with self.assertRaisesRegex(ValueError, "capabilities"):
            build_triomi.validate_rule(self.rule, "example.json")

    def test_invalid_semver_engine_type_and_metadata_are_rejected(self):
        for field, invalid in (("version", "01.0.0"), ("version", "1.0"), ("engine", "apk"), ("type", "novel"), ("requireLogin", "false"), ("name", "")):
            with self.subTest(field=field, invalid=invalid):
                with self.assertRaises(ValueError):
                    build_triomi.validate_rule({**self.rule, field: invalid}, "example.json")

    def test_script_and_document_size_limits_are_enforced(self):
        with patch.object(build_triomi, "MAX_SCRIPT_BYTES", 10):
            with self.assertRaisesRegex(ValueError, "script"):
                build_triomi.validate_rule(self.rule, "example.json")
        with patch.object(build_triomi, "MAX_RULE_BYTES", 10):
            with self.assertRaisesRegex(ValueError, "byte limit"):
                build_triomi.expected_outputs(self.root)

    def test_missing_provenance_and_traversal_are_rejected(self):
        for field, value in (("license", ""), ("upstreamUrl", "http://example.com"), ("attribution", ""), ("file", "../example.json")):
            with self.subTest(field=field):
                manifest = copy.deepcopy(self.manifest)
                manifest["sources"][0][field] = value
                self.save("triomi/catalog.json", manifest)
                with self.assertRaises(ValueError):
                    build_triomi.expected_outputs(self.root)

    def test_unknown_apk_mapping_is_not_inferred_or_fabricated(self):
        self.manifest["sources"][0]["apkPackages"] = ["org.missing.package"]
        self.save("triomi/catalog.json", self.manifest)
        with self.assertRaisesRegex(ValueError, "absent"):
            build_triomi.expected_outputs(self.root)

    def test_discovery_markers_must_be_canonical(self):
        self.android["triomi"]["indexUrl"] = "https://example.com/incorrect.json"
        self.save("repo/index.json", self.android)
        with self.assertRaisesRegex(ValueError, "canonical triomi marker"):
            build_triomi.expected_outputs(self.root)

    def test_duplicate_json_keys_are_rejected(self):
        (self.root / "triomi/catalog.json").write_text('{"schemaVersion": 1, "schemaVersion": 1, "sources": []}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            build_triomi.expected_outputs(self.root)

    def test_non_json_numeric_constants_are_rejected(self):
        (self.root / "triomi/catalog.json").write_text('{"schemaVersion": 1, "sources": [], "invalid": NaN}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "invalid JSON numeric constant"):
            build_triomi.expected_outputs(self.root)


class ReleasedHostReaderCatalogTests(unittest.TestCase):
    def test_four_readers_keep_nsfw_and_warn_about_native_gateways(self):
        root = Path(__file__).resolve().parents[1]
        output = build_triomi.expected_outputs(root)
        entries = {row['id']: row for row in json.loads(output['index.json'])['sources']}
        self.assertEqual(entries['wnacg']['version'], '1.0.1')
        self.assertEqual(entries['ehentai']['version'], '1.1.1')
        self.assertTrue(entries['wnacg']['nsfw'])
        self.assertTrue(entries['ehentai']['nsfw'])
        for source_id in ('jmcomic', 'picacomic'):
            entry = entries[source_id]
            self.assertEqual(entry['version'], '1.0.2' if source_id == 'picacomic' else '1.0.1')
            self.assertTrue(entry['nsfw'])
            self.assertIn('需原生网关宿主', entry['name'])
            self.assertIn('67ce2cd', entry['hostRequirements'])
            self.assertIn('unsupported', entry['hostRequirements'])
            rule = json.loads(output[f'rules/{source_id}.json'])
            self.assertEqual(rule['name'], entry['name'])
            self.assertEqual(rule['requireLogin'], source_id == 'picacomic')
            self.assertEqual(entry['requiresHost'], rule['requiresHost'])
            self.assertTrue(entry['requiresHost'])

    def test_host_blockers_are_documented_not_mislabeled_as_legacy_compatible(self):
        root = Path(__file__).resolve().parents[1]
        audit = json.loads((root / 'triomi/reader-port-compatibility.json').read_text(encoding='utf-8'))
        decisions = {row['id']: row['decision'] for row in audit['candidates']}
        self.assertEqual(decisions, {
            'wnacg': 'catalog_ready', 'ehentai': 'catalog_ready_limited',
            'jmcomic': 'published_native_host_required',
            'picacomic': 'published_native_host_required',
        })
        self.assertIn('NOT prevented', audit['enforcement'])


if __name__ == "__main__":
    unittest.main()
