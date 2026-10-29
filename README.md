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

## Triomi iOS：兼容规则子集

Triomi 的 JavaScript 漫画规则使用单独的目录，不执行 Android APK/JAR。可添加同一个主仓库 URL，应用通过现代索引中的显式 `triomi.indexUrl` 发现兼容目录；也可直接添加：

```text
https://raw.githubusercontent.com/HyperionHXH/Mihon-Extensions/main/repo/triomi/index.json
```

`repo/index.json` 和 `repo/repo.json` 的 `triomi` 字段只是附加发现信息；原 Android/Windows 扩展条目、签名与 APK/JAR 下载地址保留，旧版列表 `repo/index.min.json` 不增加该字段。

**Android扩展数量不等于iOS规则数量。** 这里只发布已人工编写、单独维护且列入 `triomi/catalog.json` 的 Triomi 规则，不提供通用 APK 转 JavaScript 转换器。`repo/triomi/compatibility.json` 按 Android 包名列出 `ported` / `manual_port_required`：只有清单显式填写 `apkPackages` 的规则才建立对应关系；`ported` 也不证明完整功能对等或站点当前可用。未映射的原生 Triomi 规则仍可出现在兼容目录中。

当前显式移植5项，不是把全部APK换成JSON：

| 兼容规则 | 行为范围与本轮证据 |
| --- | --- |
| MangaDex | 中文作品/章节、图片及低流量；Windows生产JS实网发现20部、搜索、211章/88页中的首图实际解码通过 |
| Komiic | 游客/已保存网站会话的公开GraphQL与图片额度；公开接口和单张JPEG取回通过，Windows Dart TLS握手失败另列为当前网络限制；没有移植APK邮箱密码登录/续期 |
| xkcd | 官方API最近列表、编号/URL搜索、单图条漫；生产JS实网20部及第1期图片解码通过，标题搜索不提供假结果 |
| 漫画柜 | 公开HTML目录与受限数据解码，不执行网页脚本；公开reader和一张WebP取回通过，当前主机部分DNS/TLS/搜索请求受限 |
| WEBTOON繁中 | 完整公开网页解析与离线真实JS契约通过；实网viewer未完成，当前站点返回停机页/TLS错误，不宣称可读已验收 |

拷贝漫画公开章节API返回210并要求官方App解除限制，网页样本也没有可读章节；本次没有发布半成品JSON。原Android APK继续提供，不为追求“全库兼容”绕过站点访问权限。兼容报告中`ported`仅表示有明确规则实现和包映射，不表示账号、全部语言或实站网络全功能对等。规则必须持续随站点变化维护。

### 规则清单和离线发布

维护者在 `triomi/rules/*.json` 编辑真实规则，并在 `triomi/catalog.json` 登记每个文件一次：

```json
{
  "schemaVersion": 1,
  "sources": [
    {
      "file": "example.json",
      "license": "MIT",
      "upstreamUrl": "https://example.org/source",
      "attribution": "Original author and port maintainer",
      "apkPackages": ["org.example.extension"]
    }
  ]
}
```

示例只说明字段，不是可安装规则；`apkPackages` 可省略，但填写时必须指向当前 Android 索引中实际存在的包。许可证和上游 URL 必须来自对应源的实际授权与出处，不能由脚本推断。

规则根对象要求 `id`、`name`、`type: "manga"`、`engine: "js"`、`lang`、SemVer `version`、HTTPS `baseUrl`、布尔 `requireLogin`、非空 `feeds` 和 `script`。脚本必须定义 `discover`、`search`、`detail`、`content`；可选 `capabilities` 是这四个函数名组成的数组，必须与定义一致。可选 `nsfw` 必须为布尔值。规则和脚本分别限制为 2 MiB 和 1 MiB。

```powershell
python tools/build_triomi.py
python tools/build_triomi.py --check
python -m unittest discover -s tools -p "test_build_triomi.py"
```

脚本完全离线：逐字节复制已登记规则到 `repo/triomi/rules/`，生成带 SHA-256 固定校验值和绝对 HTTPS 地址的 `repo/triomi/index.json`，同步分发 `attribution.json` 和兼容性报告。输出按 ID/文件名/包名排序，无时间戳；`--check` 不写文件，拒绝缺失、过期、多余文件以及哈希或内容漂移。编辑规则后应将重新生成的输出一并提交。

这些检查仅覆盖结构、基本元数据、大小、HTTPS 地址、函数声明和能力一致性；**不会执行 JavaScript，也不证明脚本语义、登录流程、网络访问或漫画站点可用**。真实 JavaScript/应用测试须另行完成。专用 Triomi 工作流在推送和 PR 上检查已提交输出，手动触发时只构建/发布 Triomi，不下载全部上游归档。每周索引刷新和归档刷新同样保留、重新生成并发布 Triomi 目录；只替换生成的 `repo/triomi/`，不会覆盖作者维护的 `triomi/` 输入。


## 内容和更新策略

- 当前索引汇集 Keiyoushi、Fucked by FAKKU、copymanga-copy20、Kavita、Suwayomi 和 Tachiyomi 历史索引。
- 按包名、源 ID 和跨仓库站点地址去重；同一上游仓库明确并存的不同实现会保留。
- 当前扩展数量以 `repo/build-report.json` 为准，不把兼容规则数量等同于APK数量。
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
- 主索引已通过校验；当前数量、版本、签名和下载地址见 `repo/build-report.json` 与 `repo/url-report.json`。
- 归档资源数量和体积会随上游变化，不在 README 中硬编码；当前分片及校验结果以 `repo/archive-report.json` 为准。
- CopyManga 和 Komiic 的正式 APK/JAR 已纳入本仓库主索引，并提供 Komikku 签名匹配入口；Komiic 登录后可按账号权限读取可用章节和图片额度。
- Super Hentais `1.6.1` 已迁移到当前 KeiSource API；热门、最新、搜索、完整筛选、详情、长篇章节、封面和正文图片均已在 Suwayomi 中通过烟测。
- PixEz 已归档，不再列入当前合集；需要旧版时可从其 GitHub Release 手动获取。
- 详细的合并结果、URL 检查和 Suwayomi 烟测见 `repo/build-report.json`、`repo/url-report.json` 和 `repo/smoke-test-report.json`。
- 2026-10-07 的 Komiic 登录状态栏、主仓库归属和 E-Hentai 下载回归结果见 [专项验证记录](repo/komiic-ehentai-verification.json)。真实 Komiic 账号登录和手机 Komikku 界面尚未验证。

## 本地构建和校验

需要 Python 3.11+，不需要第三方依赖：

```powershell
python tools/build_index.py
python tools/validate_index.py
python tools/validate_index.py --check-urls --url-report repo/url-report.json
```

构建脚本会拒绝上游签名指纹变化，避免把错误或被替换的索引静默发布。更新自维护扩展时，同时更新对应的 `config/*-source-info.json` 和 `config/sources.json` 中的文件名，再运行上述命令。

## 许可和归属

本仓库维护索引、校验脚本、独立 Triomi JavaScript 规则及 E-Hentai 源的分发入口。各上游扩展的代码、图标、APK/JAR 和许可证归其原作者及对应项目所有；Triomi 规则的逐文件许可与出处保存在 `triomi/catalog.json`，随发布复制为 `repo/triomi/attribution.json`，详见 [SOURCES.md](SOURCES.md)。
