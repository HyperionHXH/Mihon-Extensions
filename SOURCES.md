# Sources and attribution

## Keiyoushi

- Index: <https://github.com/keiyoushi/extensions>
- Source code and licenses: <https://github.com/keiyoushi/extensions-source>
- Website: <https://keiyoushi.github.io>
- This repository consumes the published `repo/index.json` and does not modify the upstream APK/JAR files.

## E-Hentai

- Source code: <https://github.com/HyperionHXH/E-extensions>
- Package: `eu.kanade.tachiyomi.extension.en.ehentai`
- Komikku single-source repository: <https://raw.githubusercontent.com/HyperionHXH/Mihon-Extensions/main/repo/komikku/ehentai/repo.json> (certificate `d70301d3...d02c54`)
- The local APK/JAR are built from the source repository above. Account cookies and login values are never stored here.

## Super Hentais

- Maintained source code: <https://github.com/HyperionHXH/E-extensions/tree/main/src/pt/superhentais>
- Historical implementation: <https://github.com/kevin01523/tachiyomi-extensions/tree/c6278d246/src/pt/supermangas>
- Package: `eu.kanade.tachiyomi.extension.pt.superhentais`
- The source keeps the historical source ID and was migrated to the current KeiSource API. The APK, JAR and icon are built locally from the maintained source.

## Archived PixEz

- Source code: <https://github.com/HyperionHXH/PixEz-extensions>
- Package: `eu.kanade.tachiyomi.extension.all.pixez`
- The project is archived because the implementation was not reliable enough for the active aggregate. The source and signed historical APK/JAR remain available in the GitHub repository, but PixEz is intentionally excluded from the current Mihon-Extensions index.

## Additional repositories

- Removed adult sources: <https://github.com/mojuru/cursed-manga-repo>
- Chinese CopyManga and related sources: <https://github.com/LittleSurvival/copymanga-copy20>
- Komikku single-source repository: <https://raw.githubusercontent.com/HyperionHXH/Mihon-Extensions/main/repo/komikku/copymanga/repo.json> (certificate `896d1ca3...005e79`)
- Kavita: <https://github.com/Kareadita/tach-extension>
- Suwayomi connector: <https://github.com/Suwayomi/tachiyomi-extension>
- Archived Tachiyomi metadata, used only when no maintained replacement exists: <https://github.com/tachiyomiorg/extensions>

The generated `repo/build-report.json` records how many entries were fetched and retained from each repository. Zosetsu is currently excluded because its published index returns HTTP 404. The old Yuzono manga index is excluded because it only contains migration placeholders.

## Reviewed repository aliases and exclusions

- **TheNano** is the owner/branding used by LittleSurvival. Its `copymanga-copy20` repository is included above.
- **cofedream** publishes the same `eu.kanade.tachiyomi.extension.zh.copymanga` package at version `1.4.18`. It is excluded because the included TheNano/LittleSurvival build is version `1.4.83`; publishing both would create a package/signature conflict rather than an additional source.
- **LIVID (18+)** is `livid96/Aniyomi-Adult-Extensions`. Those APKs implement Aniyomi video providers, not Mihon manga sources, so they cannot be loaded by Mihon and are intentionally excluded.
- **Keiyoushi** is the primary configured repository and is included in full before cross-repository deduplication.

## Triomi JavaScript rules

- Authored rule inputs: `triomi/rules/*.json`; the authoritative per-file license, upstream HTTPS source URL, and attribution are recorded in `triomi/catalog.json`.
- Published attribution: `repo/triomi/attribution.json`, generated from that manifest alongside byte-for-byte rule copies and their SHA-256 catalog pins.
- A manifest row is required for every published rule. The generator does not infer a license from an APK, source ID, website, or another project's license.
- Optional `apkPackages` mappings explicitly associate a hand-maintained rule with an existing Android package. `repo/triomi/compatibility.json` reports these associations and the remaining packages requiring manual ports; it is not a certificate of feature parity or live-site functionality.
- The Android aggregate and archived APK/JAR files remain separate. Only the explicitly authored Triomi subset is compatible with the JavaScript runtime; no universal conversion of the Android catalog is claimed.
- Static validation does not execute upstream binaries or JavaScript. Review the original license and preserve required notices when creating or updating a port; execute real runtime and site tests separately before release.
- Historical general Chinese-source assessment: `triomi/chinese-port-audit.json` records the earlier review of 21 upstream-SAFE Chinese packages, twelve then-installable ports, nine then-observed blockers, and the additional DM5/Manhuaren image-header transport limitation. CopyManga now has a separately authored public-web implementation; that historical blocker is not the current publication decision.
- A working browse-only source may omit `search` entirely. The generator still requires `discover`, `detail` and `content`, emits only actual exports, and rejects claimed-but-unimplemented capabilities. No empty search stub is used to satisfy publication.
- All 128 source behavior contracts passed desktop QuickJS and actual production iOS WebKit in Triomi commit `0227cf6`, accepted macOS run `40890601599` (136 total integration tests; 56-state visual tour passed). Deterministic HTTP fixtures remain separate from anonymous public-site probes. Eleven new rules passed the production Windows JsSource/Dart HTTPS/image-decoding chain; Webmota's independent Python reader succeeded but Windows Dart TLS failed. None of this asserts physical-device, paid-account or every upstream iOS-network acceptance.
- CopyManga (`copymanga.json`) is independently authored under GPL-3.0-or-later against <https://www.copy4000.com/>, with independent AES-128-CBC/PKCS7 data decoding; no APK implementation is copied or executed. Its Android package association is `eu.kanade.tachiyomi.extension.zh.copymanga`. Anonymous Chromium requests without Cookie/Authorization returned 305+185 chapters, decoded by the current rule. Dart/native HTTP still received an empty directory even with ordinary-header replay or HTTP/2; login is not a prerequisite for that public directory, while the precise transport/routing cause remains unproven. Production current-network reading and physical iOS acceptance are not claimed. The earlier 128-contract iOS result above does not include this new rule.


## Scope

Only entries present in configured, attributable indexes are published. A source can disappear when its upstream maintainer removes it or when validation fails. The repository does not redistribute unknown binaries merely to increase its count.
