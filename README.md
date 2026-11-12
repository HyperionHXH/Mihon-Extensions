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

### 下载地址维护

上游会轮换 GitHub Release，旧索引中的 APK/JAR 链接可能已返回 404，而同包或更新版本仍在维护。定时刷新从每周改为每日，沿用原来的完整目录生成器（`python tools/build_index.py`），从 `config/sources.json` 已配置且签名指纹匹配的现代索引读取明确的 APK/JAR 下载地址，并保留现有自维护、归档与来源去重策略。不猜测 tag，不提供硬编码备用链接，不改变客户端信任。目录生成及全量 URL 检查全部成功后才发布完整索引；失败时不发布部分结果。插件目录元数据更新不等于自动安装或升级设备上的插件，实际安装仍由客户端和用户控制。

APK 下载失败、APK 静态签名不通过、兼容宿主无法加载，以及内容网站不可用是不同阶段；刷新索引只修复失效下载地址，不保证所有插件或内容网站可用。客户端仍须验证 APK 原签名，桌面原生 JAR 仍须单独确认来源与内容指纹。日志及仓库不得记录账号或凭据。

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

标签搜索修复（Copy1.1.1、WNACG1.0.2、MangaDex1.0.6）：Copy主题标签使用源站slug并保留显示名别名，WNACG详情标签进入真实tag端点，MangaDex标签筛选不附空title条件并保留服务端AND/分页/中文语言约束。Triomi iOS198修订1同时修复宿主标签ID映射与动漫播放源丢标签。已有安装请在原兼容仓库刷新后明确点“更新”；不会在启动时覆盖已安装/自定义/停用规则或重新启用已移除来源。更新可能按既有代码指纹策略撤销旧来源会话，账号仍只在应用内管理。离线生产JS/路由与安装器升级测试不代表所有实网站点或本人账号可用。

后续实网修复：WNACG **1.0.3** 将分类菜单与详情标签分为不同名称空间，重复的“漢化 / 日語 / English”分类不再截获同名详情标签；分类ID保持不变。JMComic **1.0.3** 按真实API的`type: slug`与`type: search`区分分类和搜索入口，中文搜索入口不再触发“分类标识无效”，多标签使用源站AND查询。两者均为规则更新，无需变更原生宿主或应用版本，仍需明确更新已安装规则。JM上游个别搜索记录（例如`中文`第二页的74549）标题为空，详情接口也缺名；保留可见数据错误，不编造标题或静默丢弃作品。

E-Hentai **1.2.0**：改由 Triomi iOS 0.15.5+199 起的原生宿主实现（`requiresHost: ehentai.native.v1`），对齐 Android E-Hentai 1.6.36：单章节完整图库、ExHentai 与三 Cookie、收藏夹/关注流和 21 项筛选。规则内脚本仅为旧版客户端的“需要更新应用”提示；旧版 Triomi 更新此规则后 E-Hentai 将不可用，请先升级应用再更新规则。

**Android扩展数量不等于iOS规则数量。** 这里只发布已人工编写、单独维护且列入 `triomi/catalog.json` 的 Triomi 规则，不提供通用 APK 转 JavaScript 转换器。`repo/triomi/compatibility.json` 按 Android 包名列出 `ported` / `manual_port_required`：只有清单显式填写 `apkPackages` 的规则才建立对应关系；`ported` 也不证明完整功能对等或站点当前可用。未映射的原生 Triomi 规则仍可出现在兼容目录中。

当前目录共22项（原18项加WNACG、E-Hentai、JMComic和哔咔），不是把全部APK换成JSON。Copy1.1.0使用实际Android1.4.85 App API协议，Komiic官方镜像、漫画柜镜像选路和WEBTOON公开目录API保留；Triomi源码0c27925的[最终iOS验收41600804216](https://github.com/HyperionHXH/triomi/actions/runs/41600804216)记录不扩大为新增候选已实站可读。此前12个一般中文来源保留，历史逐项评估见 [中文来源审计](triomi/chinese-port-audit.json)。

### 四个阅读源与宿主要求

2026-11-04阅读修复：WNACG1.0.1修复真实页面`document.writeln`和`[0001]`标题导致只返回一张图片；EH1.1.1支持H@H节点合法的HTTPS自定义端口（如4443/8443），不再误报超出HTTPS范围。只允许明确`.hath.network`域的有效端口，保持TLS校验、账号/内网/额度/验证边界。两条通用JS更新可在原目录刷新安装；应用随包EH原生解析器也单独修正。

四个来源都从同一兼容仓库自主安装；**能安装不代表旧宿主支持原生功能**：

- **绅士漫画 WNACG 1.0.1**：通用JS读取官方`.buzz`镜像，保留数字身份和NSFW标记，无额外原生网关。
- **E-Hentai公开图库 1.1.1**：专门适配现有通用JS宿主，脚本解析真实HTTPS图片URL，不把`/s/`网页冒充图片。每个选定图库按10页拆成章节，版本图库作为独立作品；不支持ExHentai、登录、额度/验证绕过。过期图片需刷新章节，站点变更页数需刷新目录。仅协议合成测试，不冒称修改后真实iOS/实站图片验收。
- **JMComic 1.0.1（需原生网关宿主）**：需要原生API解密和二进制图片还原。
- **哔咔 1.0.4（需 iOS181 原生网关宿主）**：修复目录总页数超过200时单页浏览/搜索被误拒绝；章节与图片全量遍历仍限制200页及20000项。需要原生签名、安全账号网关与系统安全存储。用户只在支持的客户端内登录，不把账号Secrets、签名常量、密码或token加入本仓库；授权测试账号在181生产协议下登录通过，但JS真实目录/阅读未验收。

**历史正式iOS178（源码`0c27925`）不支持JM/哔咔。** JM 1.0.1 从正式iOS179开始获得 `jmcomic.api.v1` / `jmcomic.image.v1` 宿主支持；当前哔咔 1.0.4 需要iOS181（`0.12.0+181`）或声明 `picacomic.account.v3` 的兼容后继。实际IPA发布及验收状态以[应用仓库Release](https://github.com/HyperionHXH/triomi/releases)为准。旧宿主无法只靠JSON补齐原生能力。`hostRequirements`是说明字段，旧客户端不会据此阻止安装，故条目名称也保留显式警告。

用户使用步骤是「漫画 → 浏览 → JS / API漫画来源目录 → 管理兼容仓库 → 添加上面的原网址 → 返回并刷新 → 选择来源安装」。启用排除NSFW筛选时看不到这四个条目；保留原分级，不改为安全来源伪装展示。已有仓库无需更换网址，新来源须由用户明确安装，不自动替换书库/下载。

本仓库只发布插件，不构建软件IPA。JM 1.0.1 使用 `jmcomic.api.v1` / `jmcomic.image.v1`，正式 iOS179 支持。哔咔 1.0.4 要求 **iOS181（0.12.0+181）或声明 `picacomic.account.v3` 的后继宿主**：宿主对齐两个独立参考实现登录时发送空 `Authorization` 请求头的行为，并安全分类 HTTP 400 错误。1.0.4 只改JS目录分页，不增加原生能力；179/180 仍会明确提示缺少 v3，须先更新应用。授权测试账号已在181生产登录/分类路径通过，但真实目录、详情、图片与本人阅读未验。本次未使用 GitHub Secrets。逐项依赖和限制见 [阅读源兼容性记录](triomi/reader-port-compatibility.json)。

| 兼容规则 | 行为范围与本轮证据 |
| --- | --- |
| MangaDex | 中文作品/章节、图片及低流量；Windows生产JS实网发现20部、搜索、211章/88页中的首图实际解码通过 |
| Komiic | 1.0.1游客公开GraphQL与图片额度，使用官方komiic.cc传输，作品/章节规范ID和.com网址保留。实际iOS及Windows公开章节多页解码通过，没有移植APK邮箱密码登录/续期 |
| xkcd | 官方API最近列表、编号/URL搜索、单图条漫；生产JS实网20部及第1期图片解码通过，标题搜索不提供假结果 |
| 漫画柜 | 1.0.1公开HTML目录与有界数据解码，不执行网页脚本；显式支持四个官方镜像、不自动跨站重试。最终实际iOS首/中/末图通过，本机网络可达性另列 |
| WEBTOON繁中 | 1.0.1保留公开HTML发现/搜索/阅读页，完整章节改官方mobile episodes API；最终实际iOS623章及公开正文阅读通过，本机直连停止页属于网络/出口差异而非全站停机 |
| 崩坏3官方漫画 | 官方全集与标题筛选、完整章节；生产JS/Dart HTTPS目录23部、章节和首张JPEG解码通过 |
| 泰拉记事社 / 塔卫二 | 两个官方主题、公开目录/完整章节、即时签名页URL；真实HTTPS首图解码与生产JS链路通过，过期需重载章节 |
| 快看漫画 | 公开搜索、完整目录及免费章节；实网377章/8图样本，付费10103/登录/App专享限制保留 |
| MH1234 | 搜索、分页、分组完整目录及公开reader；实网554章，样本23张WebP取回通过 |
| 瓜子漫画 | 公开桌面HTML搜索/分页/分组目录；341章目录、12图章节首中末JPEG取回通过 |
| 喵趣漫画（仅浏览） | 排行浏览、299章目录与52图公开章节；站点搜索404，所以不导出、不宣称搜索能力 |
| 爱奇艺叭嗒 | 官方公开签名API与免费5图章节；付费/authPass拒绝保留 |
| 咚漫简体中文 | 独立官方域名、搜索与完整公开章节分页；112图章节首末JPEG取回，不解锁App专属内容 |
| 包子漫画+ / Webmota | 公开网页/AMP完整分页，41579235687实际iOS阅读通过；搜索ID与详情规范ID可能不同。旧Windows TLS失败为历史网络记录，不外推当前网络 |
| GoDa / baozimh.org | 公开目录/API与有界数据解码；150图章节首末取回，不执行网页代码 |
| 再漫画 | 公开游客章节、分组顺序与签名HD图；36图样本首末取回，不绕过账号权限 |
| 杂志迷 | 中文客户端的公开整刊来源，非纯漫画目录；252页完整刊物样本首末取回 |
| 拷贝漫画 | 1.1.0实际App API协议、完整分组分页/真实页序；最终实际iOS完整490章、旧章205页/新章14页、生产搜索滚动定位主作品、翻页/下一章及原生文字吐槽/设置账号入口通过，11状态截图和录屏独立保存 |

R178的新宿主功能需要Triomi178：Copy独立线路/平台/分辨率/筛选设置、系统安全存储可选账号、文字吐槽，以及图片Referer/UA在阅读/下载/保存中的传递。匿名阅读不要求登录，无真实账号凭据不声称本人登录/收藏远端验收。兼容目录网址不变；旧1.0.0网页AES路径已删除，不以旧规则安装成功替代本轮可读。

第二轮41579235687的17个旧源实网16通过；唯一喵趣在云端收到HTTP403验证页。用户授权把此外部阻塞与已验收修复分开交付：17项仍完整执行，原失败记录保留；只有其他16项全部完成且唯一失败明确为喵趣discover的403验证页才允许发布，其余失败/缺项/超时继续阻止。不自动添加验证Cookie、代理、TLS放宽或挑战绕过。

这12条使用既有Triomi 0.12.0+176宿主能力；已添加原兼容仓库的用户，只需打开目录点刷新，再安装/更新，无需更换网址或安装扩展App。喵趣只能从浏览入口进入，不参加聚合搜索。杂志迷按刊名（如25ans）搜索，完整的带日期期刊名可能无结果。章节图片签名过期时重开/重新加载章节；不宣称具备APK图片拦截器的所有恢复能力。

本轮最终Windows生产`JsSource + QuickJS + Dart HTTPS`实网链路有11个新增来源完成发现、所声明的搜索、章节、首图真实解码；Webmota为独立Python公开阅读成功、Windows Dart TLS受限，不能混称应用实网通过。实际字节摘要/计数和边界写入中文审计。实网发现的相对重定向、普通页面含Cloudflare jsd脚本导致的误判及杂志API空结果/空格目录已修正为1.0.1；没有放宽站点域名、TLS或真实验证页拒绝策略。

实际iOS验收也已完成：Triomi源码`0227cf6`的[macOS运行40890601599](https://github.com/HyperionHXH/triomi/actions/runs/40890601599)中，新增规则128项真实WKWebView契约、整套136项集成及56状态视觉巡检通过。建议使用[独立iOS177版](https://github.com/HyperionHXH/triomi/releases/tag/v0.12.0-ios.177)修复仓库管理收键盘负边距崩溃；已有176支持相同规则协议，但没有这项宿主修复。该iOS规则协议验收不等于所有站点实网/付费账号或实体iPhone均已验证。

未发布项目也已记录：baozimh主站、Comicabc、漫画屋和MH160遇访问验证/图片错误；毒漫屋、如漫画及Mangabz遇连接或证书问题；Vomic要求账号；CCC创作集需要当前宿主没有的二进制图片解码。另查DM5和漫画人，公开阅读可达但图片必须携带章节专属Referer，当前客户端不能持久保存并传给图片/离线下载，故不发布“能列作品但图全失败”的JSON。原APK不变，不关闭TLS校验、不绕过付费/验证或绕过站点访问限制。

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
