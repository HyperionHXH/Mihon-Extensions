# Hyperion Mihon Extensions

独立的 Mihon / Suwayomi 漫画扩展聚合索引。它汇集当前仍可获取的主流仓库，并额外维护 E-Hentai / ExHentai 与经验证可用的历史来源。上游 APK 保留原下载地址和签名，不重新打包。

## 添加到 Mihon / Suwayomi

在扩展仓库设置中添加：

```text
https://raw.githubusercontent.com/HyperionHXH/Mihon-Extensions/main/repo/index.json
```

旧版本可尝试：

```text
https://raw.githubusercontent.com/HyperionHXH/Mihon-Extensions/main/repo/index.min.json
```

如果应用显示扩展未受信任，请在应用内确认扩展签名。聚合仓库包含多个原作者的签名，Mihon 只允许仓库声明一个默认签名，因此非 Keiyoushi 扩展首次安装后可能需要手动信任。不要同时从签名不同的仓库安装同一包名，否则 Android 会拒绝覆盖安装。

## 内容和更新策略

- 当前索引汇集 Keiyoushi、Fucked by FAKKU、copymanga-copy20、Kavita、Suwayomi 和 Tachiyomi 历史索引。
- 按包名、源 ID 和跨仓库站点地址去重；同一上游仓库明确并存的不同实现会保留。
- 当前构建共包含 1,388 个扩展，具体来源数量和排除原因见 `repo/build-report.json`。
- 聚合索引中的全部扩展都会复制到本仓库的分片归档 Release；归档文件不改签，并在上传前校验包名、版本和签名证书。
- 每个已归档插件保留当前版和上一版。即使上游仓库删除插件，最后归档版本仍会继续出现在本索引中。
- 自维护的 E-Hentai 和 Super Hentais 扩展的 APK/JAR 与图标放在 `repo/`，方便 Mihon 与 Suwayomi 使用同一索引。
- PixEz 已从当前索引下架并在 GitHub 上归档；其源码和历史 Release 保留在 [PixEz-extensions](https://github.com/HyperionHXH/PixEz-extensions)，不再随本合集自动安装。
- GitHub Actions 每周刷新索引和归档，并检查包名、版本号、源信息、重复项和所有 APK 下载地址。
- 所有推送和拉取请求都会扫描常见凭据格式；工作流依赖固定到审核过的提交 SHA。
- 已失效、只剩迁移占位符、来源不明或存在更新版本的仓库会排除并记录原因。

下载可达不等同于漫画网站始终可用。Cloudflare、登录权限、地区限制和站点改版都可能影响搜索、章节或图片加载；这些问题需要按具体源持续维护，不能仅靠索引检查证明。

## 归档的代价和限制

归档占用 GitHub Releases 的文件存储和 GitHub Actions 的运行时间，不占用你电脑或手机的空间，除非你实际下载安装插件。APK、可用的 JAR 和图标按包名固定分到 `extension-archive-0` 至 `extension-archive-7`，避免单个 Release 超过 1,000 个资源；Git 仓库历史本身只保存较小的索引和校验清单。

归档解决的是“上游文件被删除后无法安装”，不能自动修复漫画网站接口变更。签名证书发生变化、APK 元数据与索引不一致或下载失败时，自动化不会把该文件收入归档，错误会记录在 `repo/archive-report.json`。如果新版本失败而旧版已经归档，旧版不会被误删。

## 验证状态

- GitHub Actions 已成功完成一次完整的远程刷新和校验。
- 远程索引包含 1,388 个扩展，1,388 个 APK 下载地址全部可达。
- 归档镜像已收录全部 1,388 个插件、4,159 个 Release 资源，约 230.29 MiB；八个分片均低于 1,000 个资源限制，1,388 个镜像 APK 地址全部可达。
- CopyManga `1.4.83` 已在 Suwayomi 中从本仓库安装，热门列表、详情、章节、30 页页面列表、封面和正文图片均通过烟测。
- Super Hentais `1.6.1` 已迁移到当前 KeiSource API；热门、最新、搜索、完整筛选、详情、长篇章节、封面和正文图片均已在 Suwayomi 中通过烟测。
- PixEz 已归档，不再列入当前合集；需要旧版时可从其 GitHub Release 手动获取。
- 详细的合并结果、URL 检查和 Suwayomi 烟测见 `repo/build-report.json`、`repo/url-report.json` 和 `repo/smoke-test-report.json`。

## 本地构建和校验

需要 Python 3.11+，不需要第三方依赖：

```powershell
python tools/build_index.py
python tools/validate_index.py
python tools/validate_index.py --check-urls --url-report repo/url-report.json
```

构建脚本会拒绝上游签名指纹变化，避免把错误或被替换的索引静默发布。更新自维护扩展时，同时更新对应的 `config/*-source-info.json` 和 `config/sources.json` 中的文件名，再运行上述命令。

## 许可和归属

本仓库只维护索引、校验脚本和 E-Hentai 源的分发入口。各上游扩展的代码、图标、APK/JAR 和许可证归其原作者及对应项目所有，详见 [SOURCES.md](SOURCES.md)。
