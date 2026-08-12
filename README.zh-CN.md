# Xray Decky — Steam Deck 的 VPN 与代理客户端

[English](README.md) · [Русский](README.ru.md) · **中文** · [فارسی](README.fa.md) · [Español](README.es.md)

在你的 Steam Deck 上运行 VPN——包括在游戏模式（Gaming Mode）下。Xray Decky 是一款
[Decky Loader](https://wiki.deckbrew.xyz/) 插件：一个功能完整的代理客户端
（VLESS/VMess/Trojan/Shadowsocks/Hysteria2/TUIC），其 TUN 模式会将**全部**系统
流量通过加密隧道转发——实现系统级、VPN 式的全覆盖，游戏也无法绕过。内置多
服务器订阅、Steam 风格的 Web 管理面板、断线阻断（kill switch）和实时流量统计。

## 功能特性

- **广泛的协议与传输方式支持** — 支持导入 **VLESS**（REALITY / XTLS-Vision）、
  **VMess**、**Trojan** 和 **Shadowsocks**（含 2022 加密方式），传输方式覆盖
  RAW/TCP、WebSocket、gRPC、HTTPUpgrade、XHTTP 和 mKCP，并提供完整的 TLS /
  REALITY / uTLS 指纹参数。**Hysteria2** 和 **TUIC** 运行在 sing-box 内核上，
  按需下载。
- **多服务器配置与订阅** — 保存多个服务器；导入订阅链接（base64 或纯文本链接
  列表）并原地刷新。手动添加的服务器在刷新后会被保留，若服务商返回了流量
  配额/到期信息（`Subscription-Userinfo`）也会一并显示。
- **延迟测试** — 对所有服务器进行 TCPing 测速，在 QAM 选择器和 Web 面板中均以
  颜色标注每个服务器的测速结果。
- **实时流量统计** — 在 QAM 中显示下载/上传速度及本次会话的流量总计，Web 面板
  还提供实时速度图表。
- **Web 管理面板** — 可在手机/电脑上使用的 Steam 风格管理界面（通过 QAM 中的
  二维码配对）：实时状态 + 速度图表、服务器列表、订阅信息、导入功能、TUN /
  断线阻断（kill switch）开关，以及内核更新检测。以每次安装随机生成的令牌保护，并对
  认证失败请求进行限流。
- **快速访问菜单（Quick Access Menu）** — 连接开关、服务器选择、实时状态/
  速度、TUN + 断线阻断（kill switch），以及管理面板二维码。
- **英语 / 俄语** — QAM 和 Web 面板均已本地化（根据 Steam / 浏览器语言自动
  检测）。
- **连接开关** — 在快速访问菜单中一键开启/关闭代理。
- **TUN 模式** — 通过虚拟网络接口实现系统级、VPN 式的流量路由，**推荐在
  游戏模式（Gaming Mode）下使用**。
- **断线阻断（Kill Switch）** — 在代理断开时阻断流量（可选启用）。
- **高可靠性** — xray-core 崩溃会被立即检测并按退避策略自动重启；系统休眠/
  唤醒后会重新应用 TUN 路由；若只读文件系统清除了内置的核心程序，固定核心
  会自动修复。

**网络恢复：** 如果 Deck 因插件异常退出而失去网络连接，可在桌面模式
（Desktop Mode）终端中运行 `sudo bash recover.sh`（随插件目录一同分发，也可
在 [defaults/recover.sh](defaults/recover.sh) 中找到）——该脚本会移除 kill
switch 防火墙链、残留的 TUN 路由以及系统代理设置。

## 安装

**前置条件：** 已安装 [Decky Loader](https://wiki.deckbrew.xyz/) 的 Steam Deck。

- **插件商店（推荐）：** Decky Loader → Plugin Store → 搜索 “Xray Decky” → Install。
- **桌面模式（一键安装）：** 下载 [Install-Xray-Decky.desktop](https://raw.githubusercontent.com/VadimOnix/xray-decky/master/scripts/Install-Xray-Decky.desktop)，将其设置为可执行（Properties → Permissions），双击运行。详见 [scripts/README.md](scripts/README.md)。
- **手动安装：** 下载 [最新版本](https://github.com/VadimOnix/xray-decky/releases/latest) 的 zip 压缩包 → Decky Loader → Settings → Developer → Install Plugin from URL → 粘贴 zip 的下载链接。

**TUN 模式（推荐）：** 在游戏模式下，Steam 不会遵循系统的 SOCKS 代理设置——
游戏和大多数系统服务都会忽略它。TUN 模式会创建一个虚拟网络接口，将**全部**
系统流量通过代理转发，是在游戏模式下代理流量的唯一可靠方式。只需在插件
设置中启用 TUN，无需额外配置。

若不启用 TUN，插件会回退到 SOCKS 代理模式，该模式在桌面模式下可用，但在
游戏模式下可能无法覆盖游戏和系统服务。

**使用说明、故障排查等：** 参见 [GitHub Pages 文档](https://vadimonix.github.io/xray-decky/)。

## 开发

### 前置条件

- Node.js v16.14+
- pnpm v9（必须）
- Python 3.x
- xray-core 可执行文件

### 环境搭建

```bash
pnpm install
pnpm run build
# Backend: pip install -r requirements-dev.txt
# xray-core: place in bin/xray-core
```

测试与代码检查（无需真机）：`pnpm test`、`pnpm run lint`、
`pytest tests/`、`ruff check py_modules/ tests/ main.py conftest.py`。
详见 [Tests and linters](CONTRIBUTING.md#tests-and-linters)。

### 项目结构

```
├── src/                      # Frontend TypeScript/React
├── py_modules/backend/src/   # Backend Python, xray-core/sing-box managers
├── defaults/static/          # Embedded web admin panel (ships to plugin root)
├── defaults/recover.sh       # Network recovery script (ships to plugin root)
├── tests/                    # Python test suite (pytest)
├── tests/frontend/           # Frontend test suite (vitest: src/ + admin panel)
├── bin/                      # Local dev core binaries (xray-core, sing-box)
├── site/                     # GitHub Pages site (Astro, 5 locales)
├── main.py                   # Backend entry point
├── plugin.json
└── package.json
```

更多内容参见 [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) 与 [docs/RELEASING.md](docs/RELEASING.md)。

## 许可证

MIT — 详见 LICENSE 文件。

## 相关资源

- [Decky Loader](https://wiki.deckbrew.xyz/)
- [xray-core](https://xtls.github.io/)
- [插件规格说明](./specs/001-xray-vless-decky/spec.md)
