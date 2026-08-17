import type { Dict } from './types';
import { localeHref } from '../lib/urls';

/**
 * Cross-links baked into this locale's copy at module-eval time (build
 * time). localeHref() derives the prefix from the locale literal, so a
 * translated dict only has to swap 'en' for its own locale — the actual
 * path prefix always comes from the localePrefixes single source of truth.
 */
const guideHref = localeHref('zh', 'vpn-on-steam-deck.html');
const landingFaqHref = `${localeHref('zh', '')}#faq`;

export const zh = {
  seo: {
    title: 'Xray Decky — Steam Deck 的 VPN 与代理客户端',
    description:
      '免费开源的 Steam Deck VPN 与代理客户端（Decky Loader 插件）。支持 VLESS、VMess、Trojan、Shadowsocks、SOCKS5、Hysteria2、TUIC——面向游戏模式的 TUN 模式、订阅、断线阻断（kill switch）、Web 管理面板。',
  },

  nav: {
    ariaLabel: '主导航',
    features: '功能特性',
    panel: '管理面板',
    install: '安装',
    guide: '指南',
    changelog: '更新日志',
    help: '帮助',
    donate: '捐赠',
    github: 'GitHub ↗',
  },

  hero: {
    badgeStable: '稳定版 V2',
    badgeContext: 'Steam Deck · Decky Loader · 开源',
    titleHtml: '真正的代理客户端。<br>就在你的 <span class="grad">Steam&nbsp;Deck</span> 上。',
    purpose:
      'VLESS · VMess · Trojan · Shadowsocks · SOCKS5 · Hysteria2 · TUIC——支持 REALITY 与现代传输方式。带托管服务器列表的订阅、TUN 模式、断线阻断（kill switch）、实时流量统计——以及可在手机上打开的完整 Web 管理面板。',
    ctaInstall: '安装插件',
    ctaGithub: '在 GitHub 上查看',
    statsAriaLabel: '项目数据',
    stats: [
      { countup: 6, label: '支持的协议数' },
      { countup: 199, label: '后端测试数' },
      { value: 'EN·RU', label: '两种界面语言' },
      { value: 'MIT', label: '许可证' },
    ],
    demoAriaLabel: '动态演示：Steam Deck 上的插件与手机上的 Web 管理面板',
    demo: {
      deckStatus: '未连接',
      enableConnection: '启用连接',
      phonePill: '离线',
      phoneStatus: '未连接',
      phoneSub: '代理处于空闲状态',
    },
    demoCaption: 'Deck 上的快速访问菜单 · 手机上的管理面板——一键连接',
  },

  protocols: {
    ariaLabel: '支持的协议',
    chips: ['VLESS + REALITY', 'VMess', 'Trojan', 'Shadowsocks', 'SOCKS5', 'Hysteria2', 'TUIC'],
    note: 'Hysteria2 / TUIC 运行在 sing-box 内核上，按需下载',
  },

  featuresTitle: '代理客户端该有的一切功能',
  features: [
    {
      title: '一键粘贴导入',
      html: '粘贴任意 <code>vless://</code>、<code>vmess://</code>、<code>trojan://</code>、<code>ss://</code>、<code>hysteria2://</code> 或 <code>tuic://</code> 链接、订阅 URL、其 base64 内容——或整段 sing-box JSON 配置。',
    },
    {
      title: '订阅与服务器列表',
      html: '支持流量配额与到期时间的多服务器订阅、可编辑名称、手动与<b>按计划自动刷新</b>。手动添加的服务器在刷新后始终保留。',
    },
    {
      title: '延迟测试',
      html: '并发 ping 所有服务器，结果直接显示在列表中，一键切换——正在使用的连接会自动通过新服务器重新连接。',
    },
    {
      title: '实时流量统计',
      html: '来自 xray 统计 API 的真实上传/下载速度与本次会话总量——显示在快速访问卡片中，也在管理面板中以实时图表呈现。',
    },
    {
      title: 'TUN 模式',
      html: '将<b>全部</b>系统流量通过代理转发——在游戏模式（Gaming Mode）下唯一可靠的方式，因为 Steam 会忽略 SOCKS 设置。支持休眠/唤醒后继续生效。',
    },
    {
      title: '会自我清理的断线阻断',
      html: '在代理断开时阻断流量——并在之后可靠地移除其防火墙规则。以防万一，插件还附带一个恢复脚本。',
    },
    {
      title: 'Web 管理面板',
      html: '在 Deck 上扫描二维码，即可在手机上管理一切：服务器、导入/导出、选项、更新。有令牌保护、请求限流，并可切换局域网访问开关。',
    },
    {
      title: '天生高可靠',
      html: '进程监视器会在数秒内重启崩溃的内核，休眠后自动修复路由，版本号被固定——并且一切都由 199 个后端测试覆盖。',
    },
  ],

  panel: {
    titleHtml: '快速访问菜单用来玩游戏。<br>管理面板用来管理一切。',
    introHtml:
      'QAM 保持精简：连接、选服务器、看速度。其余的一切都交给插件自身通过 HTTPS 提供的 <b>Steam 风格 Web 管理面板</b>：',
    list: [
      '带实时状态和两分钟速度图表的仪表盘',
      '按延迟排序的服务器列表，附协议与内核标签',
      '订阅栏：刷新、重命名、自动刷新计划、流量配额与到期时间',
      '导入任意内容 · 将任意服务器导出为分享链接或订阅',
      '插件及其内核的更新检测——不含任何遥测',
      '英语与俄语，随时切换',
    ],
    securityHtml:
      '<b>安全模型：</b>每次安装独立令牌（通过二维码配对）、恒定时间比较、认证失败限流，列表视图中从不显示凭据——还可用 QAM 开关将整个面板限制为仅 Deck 可访问。',
  },

  install: {
    title: '安装',
    prereqTitle: '前置条件',
    prereqHtml: [
      '已安装 <a href="https://wiki.deckbrew.xyz/" target="_blank" rel="noopener">Decky Loader</a> 的 Steam Deck',
      '<span class="badge-stable">STABLE</span> v2 系列已在真实硬件上测试并被每日使用——如果仍然遇到问题，欢迎<a href="https://github.com/VadimOnix/xray-decky/issues" target="_blank" rel="noopener">反馈</a>',
    ],
    methods: [
      {
        title: '方式一 · 桌面模式',
        stepsHtml: [
          '切换到桌面模式（Desktop Mode）',
          '下载 <a href="https://raw.githubusercontent.com/VadimOnix/xray-decky/master/scripts/Install-Xray-Decky.desktop" target="_blank" rel="noopener">Install‑Xray‑Decky.desktop</a>',
          'Properties → Permissions → “Is executable”',
          '双击运行安装程序',
        ],
      },
      {
        title: '方式二 · Konsole 安装脚本',
        stepsHtml: [
          '切换到桌面模式并打开 Konsole',
          '运行 <code>curl -sSL https://raw.githubusercontent.com/VadimOnix/xray-decky/master/scripts/install-xray-decky.sh | bash</code>',
          '脚本会检查 Decky Loader、下载最新版本并完成安装',
        ],
      },
      {
        title: '方式三 · 压缩包（zip）',
        stepsHtml: [
          '下载 <a href="https://github.com/VadimOnix/xray-decky/releases/latest" target="_blank" rel="noopener">最新版本</a>的 zip 压缩包',
          'Decky → Settings → Developer → Install Plugin from URL',
          '粘贴 zip 的下载链接',
        ],
      },
    ],
    noteHtml:
      'Xray Decky <b>未上架 Decky Plugin Store</b>——请使用上面的安装脚本或发布版 zip 压缩包安装。',
    tunTitle: '为什么需要 TUN 模式？',
    tunHtml:
      '在游戏模式下，Steam 会忽略系统的 SOCKS 设置——游戏和系统服务都会绕过代理。<b>TUN 会创建一个转发全部流量的虚拟网络接口</b>，这正是你真正需要的模式。只需打开开关，路由和清理都由插件自动处理。',
  },

  usageTitle: '三步从零开始使用代理',
  usage: [
    {
      number: '1',
      title: '导入',
      body: '在 QAM 中粘贴分享链接或订阅 URL——或扫描二维码后在手机上粘贴。订阅中的每个服务器都会被保存。',
    },
    {
      number: '2',
      title: '连接',
      body: '一键开关。实时状态与速度直接显示在快速访问卡片中。随时切换其他服务器——重新连接会自动完成。',
    },
    {
      number: '3',
      title: '实现全系统覆盖',
      body: '启用 TUN 模式以覆盖游戏模式，如需严格防止泄漏可加上断线阻断（kill switch），其余交给 Web 面板管理。',
    },
  ],

  faqTitle: '故障排查',
  faq: [
    {
      q: '无法连接',
      html: '<ul><li>确认分享链接或订阅 URL 有效——无效链接会在破坏可用配置之前被拒绝</li><li>检查 Steam Deck 的网络连接</li><li>对列表中的服务器测速，尝试最快的一个</li></ul>',
    },
    {
      q: 'TUN 模式不生效',
      html: '<ul><li>确认插件拥有所需权限（参见仓库中的 INSTALLATION.md）</li><li>系统更新后重新切换 TUN——SteamOS 更新可能会清除权限</li></ul>',
    },
    {
      q: '断线阻断（kill switch）正在阻止流量',
      html: '<ul><li>重新连接代理——断线阻断会自动解除</li><li>或在插件/管理面板中点击 <b>Unblock traffic</b></li><li>最坏情况下：插件自带的 <code>defaults/recover.sh</code> 可无条件恢复网络</li></ul>',
    },
    {
      q: '无法从手机打开管理面板',
      html: '<ul><li>检查 QAM 选项中的 <b>Allow LAN access</b> 开关——在仅 Deck 模式下，面板会被有意设为其他设备不可访问</li><li>两台设备必须在同一网络下；需接受自签名证书的安全警告</li><li>二维码中内嵌了本次安装专属的令牌——请通过扫描配对，不要手动输入 URL</li></ul>',
    },
    {
      q: '缺少 xray-core 可执行文件',
      html: '<ul><li>插件会在下次启动时自动重新下载其固定版本的内核</li><li>处于离线环境？可从 <a href="https://github.com/XTLS/Xray-core/releases" target="_blank" rel="noopener">Xray-core releases</a> 下载后放入 <code>backend/out/</code></li></ul>',
    },
    {
      q: 'Steam Deck 支持 VPN 吗？',
      html: '<p>开箱并不支持——SteamOS 未内置 VPN 客户端，游戏模式也会忽略系统代理设置。Xray Decky 以 Decky Loader 插件的形式补上这一环：其 TUN 模式会隧道化全部系统流量，因此在游戏模式下同样可用。</p>',
    },
    {
      q: '如何在游戏模式下使用 VPN？',
      html: `<p>安装插件、导入服务器链接、启用 TUN 模式并连接——全部操作都在快速访问菜单中完成，无需切换到桌面模式。查看详细教程：<a href="${guideHref}">如何在 Steam Deck 上设置 VPN</a>。</p>`,
    },
    {
      q: 'Xray Decky 是真正的 VPN 还是代理？',
      html: '<p>严格来说它是代理客户端（xray-core / sing-box）——但启用 TUN 模式后，它的效果与 VPN 无异：虚拟接口会将系统的每一个数据包都转发进加密隧道。不启用 TUN 时，它在桌面模式下表现为 SOCKS 代理。</p>',
    },
  ],

  donate: {
    title: '支持本项目',
    intro:
      'Xray Decky 免费且开源，由作者利用业余时间开发。如果它帮你顺利玩上了游戏，可以通过加密货币捐赠支持项目继续维护。下列地址均属于本项目作者。',
    assetHeader: '币种',
    networkHeader: '网络',
    addressHeader: '地址',
    copy: '复制',
    copied: '已复制',
  },

  footer: {
    links: ['GitHub', '更新日志', '发行版', '反馈问题', '路线图', 'Decky Loader', 'Xray-core'],
    copy: 'Xray Decky · MIT 许可证 · 为 Steam Deck 打造',
  },

  guide: {
    seo: {
      title: 'Steam Deck 上设置 VPN（游戏模式）教程 | Xray Decky',
      description:
        '手把手教程：用 Decky Loader 和 Xray Decky 在 Steam Deck 上安装 VPN——通过 TUN 模式在游戏模式下同样生效，无需切换到桌面模式。',
    },
    h1: '如何在 Steam Deck 上设置 VPN（含游戏模式）',
    intro:
      'SteamOS 没有内置 VPN 客户端，而在游戏模式下，游戏会完全忽略系统代理设置。本教程将带你配置 Xray Decky——一款面向 Decky Loader 的免费开源 VPN 与代理插件——让全部流量都在系统级别被隧道化，全程无需离开游戏模式。',
    whyTun: {
      title: '为什么需要 TUN，而不只是代理',
      body: '在游戏模式下，Steam 会忽略 SOCKS 代理设置。TUN 模式会创建一个虚拟网络接口，捕获全部系统流量——游戏、更新、语音聊天——并将其通过你的加密服务器连接转发出去。这正是它表现得像 VPN，而不是被游戏直接忽略的 SOCKS 代理的原因。',
    },
    prereqTitle: '你需要准备',
    prereqHtml: [
      'Steam Deck（任意型号）',
      '已安装 <a href="https://wiki.deckbrew.xyz/" target="_blank" rel="noopener">Decky Loader</a>',
      '一个服务器分享链接或订阅——<code>vless://</code>、<code>vmess://</code>、<code>trojan://</code>、<code>ss://</code>、<code>hysteria2://</code>、<code>tuic://</code> 或订阅 URL',
    ],
    stepsTitle: '五步搭建可用的 VPN',
    stepsHtml: [
      '<b>安装 Decky Loader</b>——按照 <a href="https://wiki.deckbrew.xyz/" target="_blank" rel="noopener">deckbrew.xyz wiki</a> 操作；如果已经安装可跳过此步。',
      '<b>安装 Xray Decky</b>——在桌面模式下运行安装脚本（<code>curl -sSL https://raw.githubusercontent.com/VadimOnix/xray-decky/master/scripts/install-xray-decky.sh | bash</code>），或通过 Decky → Settings → Developer → Install Plugin from URL 安装发布版 zip 压缩包。本插件未上架 Decky Plugin Store。',
      '<b>导入服务器</b>——在 Quick Access 中打开插件卡片，粘贴分享链接或订阅 URL；也可以扫描二维码后在手机上粘贴。',
      '<b>启用 TUN 模式</b>——在插件选项中打开一个开关即可；路由和清理均自动完成。如需严格防止泄漏，可选择启用断线阻断（kill switch）。',
      '<b>连接并验证</b>——打开连接开关，在卡片中查看实时速度；在 Deck 浏览器中打开任意有地区限制的商店页面或 IP 查询网站，确认出口 IP 已更改。',
    ],
    troubleshootingTitle: '遇到问题？',
    troubleshootingHtml: `查看主页上的<a href="${landingFaqHref}">故障排查 FAQ</a>——涵盖连接失败、TUN 模式、断线阻断（kill switch）以及管理面板的访问问题。最坏情况下，插件自带的 <code>defaults/recover.sh</code> 可无条件恢复网络。`,
  },
} satisfies Dict;
