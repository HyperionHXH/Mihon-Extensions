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

### Komikku 的归属显示

主聚合索引包含 E-Hentai、拷贝漫画和自维护 Komiic，Mihon/Suwayomi 可从主入口安装和检查更新。Komikku 的扩展管理器按“包名 + 仓库声明的签名指纹”匹配已安装 APK，每个仓库只能声明一个指纹；主聚合入口声明 Keiyoushi 签名，因此独立签名扩展可能显示“无归属”或无法识别更新。E-Hentai 和自维护 Komiic 使用正式发布证书。

Komikku 使用下列同仓库入口匹配相应 APK 的签名；它们与主索引共用下载文件：

```text
https://raw.githubusercontent.com/HyperionHXH/Mihon-Extensions/main/repo/komikku/ehentai/repo.json
https://raw.githubusercontent.com/HyperionHXH/Mihon-Extensions/main/repo/komikku/copymanga/repo.json
```

Komiic（Komikku 签名匹配入口）：

```text
https://raw.githubusercontent.com/HyperionHXH/Mihon-Extensions/main/repo/komikku/komiic/repo.json
```

这些入口由索引刷新工作流自动生成，只包含对应包名，并声明对应 APK 的签名证书；不会重复占用 APK 存储。切换仓库入口不会改变 APK 签名。同签名的自维护版本可更新；上游 Komiic `1.6.10` 的 `versionCode` 为 `106010`，自维护 `1.6.13` 为 `13`，两者签名也不同，不能直接覆盖安装。需要迁移时应先备份并确认数据影响，不能通过改索引签名解决 Android 的签名检查。

Komiic 已由 Hyperion E-extensions 单独维护为 `1.6.13`，正式包保存在本聚合仓库，通过主索引和上面的 Komiic 入口分发。安装后填写官网邮箱和密码，完整填写后会自动验证，也可使用“验证登录状态”选项。设置页显示官网确认的登录状态、检查时间、图片已用额度和下载错误；不会仅凭旧 Cookie 报告登录成功。账号的每日额度、赞助等级和可见章节仍由 Komiic 服务器决定。密码只保存在客户端本地私有设置中，不会上传到 GitHub。

本机 Suwayomi 已验证游客状态、额度查询及 3 页和 10 页章节下载；真实账号登录和手机 Komikku 界面尚未验证。

## 内容和更新策略

- 当前索引汇集 Keiyoushi、Fucked by FAKKU、copymanga-copy20、Kavita、Suwayomi 和 Tachiyomi 历史索引。
- 按包名、源 ID 和跨仓库站点地址去重；同一上游仓库明确并存的不同实现会保留。
- 当前构建共包含 1,481 个扩展，具体来源数量和排除原因见 `repo/build-report.json`（该数字会随上游刷新变化）。
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
- 本次验证索引包含 1,477 个扩展；逐项数量、版本、签名和下载地址见 `repo/build-report.json` 与 `repo/url-report.json`。
- 归档资源数量和体积会随上游变化，不在 README 中硬编码；当前分片及校验结果以 `repo/archive-report.json` 为准。
- CopyManga 和 Komiic 的正式 APK/JAR 已纳入本仓库主索引，并提供 Komikku 签名匹配入口；Komiic 登录后可按账号权限读取可用章节和图片额度。
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
