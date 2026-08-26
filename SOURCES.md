# Sources and attribution

## Keiyoushi

- Index: <https://github.com/keiyoushi/extensions>
- Source code and licenses: <https://github.com/keiyoushi/extensions-source>
- Website: <https://keiyoushi.github.io>
- This repository consumes the published `repo/index.json` and does not modify the upstream APK/JAR files.

## E-Hentai

- Source code: <https://github.com/HyperionHXH/E-extensions>
- Package: `eu.kanade.tachiyomi.extension.en.ehentai`
- The local APK/JAR are built from the source repository above. Account cookies and login values are never stored here.

## Super Hentais

- Maintained source code: <https://github.com/HyperionHXH/E-extensions/tree/main/src/pt/superhentais>
- Historical implementation: <https://github.com/kevin01523/tachiyomi-extensions/tree/c6278d246/src/pt/supermangas>
- Package: `eu.kanade.tachiyomi.extension.pt.superhentais`
- The source keeps the historical source ID and was migrated to the current KeiSource API. The APK, JAR and icon are built locally from the maintained source.

## Additional repositories

- Removed adult sources: <https://github.com/mojuru/cursed-manga-repo>
- Chinese CopyManga and related sources: <https://github.com/LittleSurvival/copymanga-copy20>
- Kavita: <https://github.com/Kareadita/tach-extension>
- Suwayomi connector: <https://github.com/Suwayomi/tachiyomi-extension>
- Archived Tachiyomi metadata, used only when no maintained replacement exists: <https://github.com/tachiyomiorg/extensions>

The generated `repo/build-report.json` records how many entries were fetched and retained from each repository. Zosetsu is currently excluded because its published index returns HTTP 404. The old Yuzono manga index is excluded because it only contains migration placeholders.

## Reviewed repository aliases and exclusions

- **TheNano** is the owner/branding used by LittleSurvival. Its `copymanga-copy20` repository is included above.
- **cofedream** publishes the same `eu.kanade.tachiyomi.extension.zh.copymanga` package at version `1.4.18`. It is excluded because the included TheNano/LittleSurvival build is version `1.4.83`; publishing both would create a package/signature conflict rather than an additional source.
- **LIVID (18+)** is `livid96/Aniyomi-Adult-Extensions`. Those APKs implement Aniyomi video providers, not Mihon manga sources, so they cannot be loaded by Mihon and are intentionally excluded.
- **Keiyoushi** is the primary configured repository and is included in full before cross-repository deduplication.

## Scope

Only entries present in configured, attributable indexes are published. A source can disappear when its upstream maintainer removes it or when validation fails. The repository does not redistribute unknown binaries merely to increase its count.
