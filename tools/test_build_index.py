import unittest

import build_index


class DeduplicateTests(unittest.TestCase):
    def extension(self, package: str, repository: str, priority: int, allow_duplicate: bool = False):
        return {
            "name": package,
            "packageName": package,
            "versionName": "1.0.0",
            "sources": [{"id": package, "homeUrl": "https://www.pixiv.net"}],
            "_repository": repository,
            "_priority": priority,
            "_allowDuplicateSite": allow_duplicate,
        }

    def test_explicit_site_coexistence_preserves_both_packages(self):
        pixez = self.extension("pixez", "custom", 1000, allow_duplicate=True)
        pixiv = self.extension("pixiv", "upstream", 100)

        included, excluded = build_index.deduplicate([pixez, pixiv])

        self.assertEqual({item["packageName"] for item in included}, {"pixez", "pixiv"})
        self.assertEqual(excluded, [])


if __name__ == "__main__":
    unittest.main()
