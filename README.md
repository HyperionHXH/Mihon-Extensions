# Hyperion Mihon Extensions

独立的 Mihon / Suwayomi 扩展索引。它聚合经过上游发布的 Keiyoushi 扩展，并额外维护可用的 E-Hentai / ExHentai 扩展。上游 APK 保留原下载地址和签名，不在本仓库重新打包。

## 添加到 Mihon / Suwayomi

在扩展仓库设置中添加：

```text
https://raw.githubusercontent.com/HyperionHXH/Mihon-Extensions/main/repo/index.json
```

旧版本可尝试：

```text
https://raw.githubusercontent.com/HyperionHXH/Mihon-Extensions/main/repo/index.min.json
```

如果应用显示扩展未受信任，请在应用内确认扩展签名。Keiyoushi 扩展使用其官方仓库签名；E-Hentai 是本项目自维护的 APK，签名与 Keiyoushi 不同。不要同时从旧的 E-extensions 仓库安装同一个 E-Hentai 包，否则 Android 会因签名不同而拒绝更新；删除旧仓库中的版本后再从这里安装。

## 内容和更新策略

- 当前索引包含 Keiyoushi 官方索引中的全部扩展，并按包名去重。
- 上游 APK/JAR 不复制、不改签，下载仍来自上游 Release。
- E-Hentai APK/JAR 和图标放在 `repo/`，方便离线保存和直接验证。
- GitHub Actions 每周刷新上游索引，并检查包名、版本号、源信息、重复项和资源 URL。
- 不收录无法确认许可证或来源的第三方二进制；“完整”指当前可验证的上游目录，而不是未经审核的网络抓包集合。

## 本地构建和校验

需要 Python 3.11+，不需要第三方依赖：

```powershell
python tools/build_index.py
python tools/validate_index.py
```

构建脚本会拒绝上游签名指纹变化，避免把错误或被替换的索引静默发布。更新 E-Hentai APK/JAR 时，同时更新 `config/ehentai-source-info.json` 和 `config/sources.json` 中的文件名，再运行上述命令。

## 许可和归属

本仓库只维护索引、校验脚本和 E-Hentai 源的分发入口。各上游扩展的代码、图标、APK/JAR 和许可证归其原作者及对应项目所有，详见 [SOURCES.md](SOURCES.md)。
