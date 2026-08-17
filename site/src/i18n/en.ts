import type { Dict } from './types';
import { localeHref } from '../lib/urls';

/**
 * Cross-links baked into this locale's copy at module-eval time (build
 * time). localeHref() derives the prefix from the locale literal, so a
 * translated dict only has to swap 'en' for its own locale — the actual
 * path prefix always comes from the localePrefixes single source of truth.
 */
const guideHref = localeHref('en', 'vpn-on-steam-deck.html');
const landingFaqHref = `${localeHref('en', '')}#faq`;

export const en = {
  seo: {
    title: 'Xray Decky — VPN & Proxy Client for Steam Deck',
    description:
      'Free open-source VPN & proxy client for Steam Deck (Decky Loader plugin). VLESS, VMess, Trojan, Shadowsocks, SOCKS5, Hysteria2, TUIC — TUN mode for Gaming Mode, subscriptions, kill switch, web admin panel.',
  },

  nav: {
    ariaLabel: 'Main navigation',
    features: 'Features',
    panel: 'Admin panel',
    install: 'Install',
    guide: 'Guide',
    changelog: 'Changelog',
    help: 'Help',
    donate: 'Donate',
    github: 'GitHub ↗',
  },

  hero: {
    badgeStable: 'STABLE V2',
    badgeContext: 'Steam Deck · Decky Loader · Open source',
    titleHtml: 'A real proxy client.<br>On your <span class="grad">Steam&nbsp;Deck</span>.',
    purpose:
      "VLESS · VMess · Trojan · Shadowsocks · SOCKS5 · Hysteria2 · TUIC — with REALITY and modern transports. Subscriptions with a managed server list, TUN mode, kill switch, live traffic stats — and a full web admin panel you open from your phone.",
    ctaInstall: 'Install plugin',
    ctaGithub: 'View on GitHub',
    statsAriaLabel: 'Project facts',
    stats: [
      { countup: 6, label: 'protocols supported' },
      { countup: 199, label: 'backend tests' },
      { value: 'EN·RU', label: 'two languages' },
      { value: 'MIT', label: 'license' },
    ],
    demoAriaLabel:
      'Animated demo: the plugin on a Steam Deck next to the web admin panel on a phone',
    demo: {
      deckStatus: 'Disconnected',
      enableConnection: 'Enable connection',
      phonePill: 'OFFLINE',
      phoneStatus: 'Disconnected',
      phoneSub: 'Proxy is idle',
    },
    demoCaption: 'Quick Access on the Deck · admin panel on your phone — one tap to connect',
  },

  protocols: {
    ariaLabel: 'Supported protocols',
    chips: ['VLESS + REALITY', 'VMess', 'Trojan', 'Shadowsocks', 'SOCKS5', 'Hysteria2', 'TUIC'],
    note: 'Hysteria2 / TUIC run on the sing-box core, downloaded on demand',
  },

  featuresTitle: 'Everything a proxy client should do',
  features: [
    {
      title: 'One-paste import',
      html: 'Paste any <code>vless://</code>, <code>vmess://</code>, <code>trojan://</code>, <code>ss://</code>, <code>hysteria2://</code> or <code>tuic://</code> link, a subscription URL, its base64 body — or a whole sing-box JSON config.',
    },
    {
      title: 'Subscriptions & server list',
      html: 'Multi-server subscriptions with quota &amp; expiry, editable names, manual and <b>scheduled auto-refresh</b>. Manually added servers always survive a refresh.',
    },
    {
      title: 'Latency testing',
      html: 'Ping every server concurrently, see results in the list, switch with one tap — a live connection reconnects through the new server automatically.',
    },
    {
      title: 'Live traffic stats',
      html: "Real up/down speed and session totals from xray's stats API — in the Quick Access card and as a live graph in the admin panel.",
    },
    {
      title: 'TUN mode',
      html: 'Routes <b>all</b> system traffic through the proxy — the only reliable way in Gaming Mode, where Steam ignores SOCKS settings. Survives suspend/resume.',
    },
    {
      title: 'Kill switch that cleans up',
      html: 'Blocks traffic if the proxy drops — and reliably removes its firewall rules afterwards. A recovery script ships with the plugin, just in case.',
    },
    {
      title: 'Web admin panel',
      html: 'Scan a QR from the Deck and manage everything from your phone: servers, import/export, options, updates. Token-guarded, rate-limited, with a LAN on/off switch.',
    },
    {
      title: 'Resilient by design',
      html: 'Process supervisor restarts a crashed core in seconds, routes are repaired after suspend, versions are pinned — and everything is covered by 199 backend tests.',
    },
  ],

  panel: {
    titleHtml: 'The Quick Access Menu is for playing.<br>The panel is for managing.',
    introHtml:
      "The QAM stays minimal: connect, pick a server, watch the speed. For everything else there's a <b>Steam-styled web admin panel</b> served by the plugin itself over HTTPS:",
    list: [
      'Dashboard with live status and a two-minute speed graph',
      'Server list sorted by latency, with protocol and core badges',
      'Subscription bar: refresh, rename, auto-refresh schedule, quota & expiry',
      'Import anything · export every server as share links or a subscription',
      'Update checker for the plugin and its cores — telemetry-free',
      'English & Russian, switchable on the fly',
    ],
    securityHtml:
      '<b>Security model:</b> per-install token (QR-paired), constant-time comparison, failed-auth rate limiting, credentials never shown in list views — and a QAM toggle to restrict the whole thing to the Deck only.',
  },

  install: {
    title: 'Installation',
    prereqTitle: 'Prerequisites',
    prereqHtml: [
      'Steam Deck with <a href="https://wiki.deckbrew.xyz/" target="_blank" rel="noopener">Decky Loader</a> installed',
      '<span class="badge-stable">STABLE</span> the v2 line is tested on real hardware and used daily — if something still bites, please <a href="https://github.com/VadimOnix/xray-decky/issues" target="_blank" rel="noopener">report it</a>',
    ],
    methods: [
      {
        title: 'Option 1 · Desktop Mode',
        stepsHtml: [
          'Switch to Desktop Mode',
          'Download <a href="https://raw.githubusercontent.com/VadimOnix/xray-decky/master/scripts/Install-Xray-Decky.desktop" target="_blank" rel="noopener">Install‑Xray‑Decky.desktop</a>',
          'Properties → Permissions → “Is executable”',
          'Double-click to run the installer',
        ],
      },
      {
        title: 'Option 2 · Konsole script',
        stepsHtml: [
          'Switch to Desktop Mode and open Konsole',
          'Run <code>curl -sSL https://raw.githubusercontent.com/VadimOnix/xray-decky/master/scripts/install-xray-decky.sh | bash</code>',
          'The script checks Decky Loader, downloads the latest release and installs it',
        ],
      },
      {
        title: 'Option 3 · Archive (zip)',
        stepsHtml: [
          'Grab the <a href="https://github.com/VadimOnix/xray-decky/releases/latest" target="_blank" rel="noopener">latest release</a> zip',
          'Decky → Settings → Developer → Install Plugin from URL',
          'Paste the zip URL',
        ],
      },
    ],
    noteHtml:
      'Xray Decky is <b>not published in the Decky Plugin Store</b> — install it with the script or the release zip above.',
    tunTitle: 'Why TUN mode?',
    tunHtml:
      "In Gaming Mode Steam ignores system SOCKS settings — games and system services bypass the proxy. <b>TUN creates a virtual network interface that routes everything</b>, so it's the mode you actually want. Just flip the toggle; the plugin handles routes and cleanup itself.",
  },

  usageTitle: 'From zero to proxied in three steps',
  usage: [
    {
      number: '1',
      title: 'Import',
      body: 'Paste a share link or subscription URL in the QAM — or scan the QR and paste it from your phone. Every server in a subscription is stored.',
    },
    {
      number: '2',
      title: 'Connect',
      body: 'One toggle. Live status and speed right in the Quick Access card. Pick a different server any time — reconnection is automatic.',
    },
    {
      number: '3',
      title: 'Go system-wide',
      body: 'Enable TUN mode for Gaming Mode coverage, add the kill switch if you want strict leak protection, and manage the rest from the web panel.',
    },
  ],

  faqTitle: 'Troubleshooting',
  faq: [
    {
      q: 'Connection fails',
      html: '<ul><li>Verify the share link or subscription URL is valid — invalid links are rejected before they can break a working config</li><li>Check network connectivity on your Steam Deck</li><li>Ping the servers from the list and try the fastest one</li></ul>',
    },
    {
      q: 'TUN mode not working',
      html: "<ul><li>Ensure the plugin has the required privileges (see the repository's INSTALLATION.md)</li><li>Re-toggle TUN after a system update — SteamOS updates can wipe permissions</li></ul>",
    },
    {
      q: 'Kill switch is blocking traffic',
      html: '<ul><li>Reconnect the proxy — the kill switch releases automatically</li><li>Or press <b>Unblock traffic</b> in the plugin / admin panel</li><li>Worst case: <code>defaults/recover.sh</code> ships with the plugin and restores networking unconditionally</li></ul>',
    },
    {
      q: "Can't open the admin panel from my phone",
      html: "<ul><li>Check the <b>Allow LAN access</b> toggle in the QAM options — in Deck-only mode the panel is deliberately unreachable from other devices</li><li>Both devices must be on the same network; accept the self-signed certificate warning</li><li>The QR embeds a per-install token — pair by scanning, don't retype the URL</li></ul>",
    },
    {
      q: 'xray-core binary missing',
      html: '<ul><li>The plugin re-downloads its pinned core automatically on next start</li><li>Offline? Download from <a href="https://github.com/XTLS/Xray-core/releases" target="_blank" rel="noopener">Xray-core releases</a> into <code>backend/out/</code></li></ul>',
    },
    {
      q: 'Does the Steam Deck support a VPN?',
      html: '<p>Not out of the box — SteamOS ships no VPN client and Gaming Mode ignores system proxy settings. Xray Decky adds one as a Decky Loader plugin: its TUN mode tunnels all system traffic, so it works in Gaming Mode too.</p>',
    },
    {
      q: 'How do I use a VPN in Gaming Mode?',
      html: `<p>Install the plugin, import a server link, enable TUN mode and connect — all from the Quick Access menu, no desktop switching. See the step-by-step guide: <a href="${guideHref}">How to Set Up a VPN on Steam Deck</a>.</p>`,
    },
    {
      q: 'Is Xray Decky a real VPN or a proxy?',
      html: '<p>Technically a proxy client (xray-core / sing-box) — but with TUN mode it does what a VPN does: a virtual interface routes every packet from the system through the encrypted tunnel. Without TUN it behaves as a SOCKS proxy for Desktop Mode.</p>',
    },
  ],

  donate: {
    title: 'Support the project',
    intro:
      'Xray Decky is free and open source, developed in spare time. If it saved your gaming session, a crypto donation keeps it going — every address below belongs to the maintainer.',
    assetHeader: 'Asset',
    networkHeader: 'Network',
    addressHeader: 'Address',
    copy: 'Copy',
    copied: 'Copied',
  },

  footer: {
    links: ['GitHub', 'Changelog', 'Releases', 'Report an issue', 'Roadmap', 'Decky Loader', 'Xray-core'],
    copy: 'Xray Decky · MIT License · Made for Steam Deck',
  },

  guide: {
    seo: {
      title: 'How to Set Up a VPN on Steam Deck (Gaming Mode) | Xray Decky',
      description:
        'Step-by-step: install a VPN on your Steam Deck with Decky Loader and Xray Decky — working in Gaming Mode via TUN mode, no desktop switching required.',
    },
    h1: 'How to Set Up a VPN on Steam Deck (Gaming Mode Included)',
    intro:
      'SteamOS has no built-in VPN client, and in Gaming Mode games ignore system proxy settings entirely. This guide sets up Xray Decky — a free, open-source VPN & proxy plugin for Decky Loader — so all your traffic is tunneled system-wide, without ever leaving Gaming Mode.',
    whyTun: {
      title: 'Why you need TUN, not just a proxy',
      body: 'Steam ignores SOCKS proxy settings in Gaming Mode. TUN mode creates a virtual network interface that captures all system traffic — games, updates, voice chat — and routes it through your encrypted server connection. That is what makes it behave like a VPN rather than a SOCKS proxy that games simply ignore.',
    },
    prereqTitle: 'What you need',
    prereqHtml: [
      'A Steam Deck (any model)',
      '<a href="https://wiki.deckbrew.xyz/" target="_blank" rel="noopener">Decky Loader</a> installed',
      'A server share link or subscription — <code>vless://</code>, <code>vmess://</code>, <code>trojan://</code>, <code>ss://</code>, <code>hysteria2://</code>, <code>tuic://</code> or a subscription URL',
    ],
    stepsTitle: 'Five steps to a working VPN',
    stepsHtml: [
      '<b>Install Decky Loader</b> — follow the <a href="https://wiki.deckbrew.xyz/" target="_blank" rel="noopener">deckbrew.xyz wiki</a>; skip if you already have it.',
      '<b>Install Xray Decky</b> — in Desktop Mode run the installer script (<code>curl -sSL https://raw.githubusercontent.com/VadimOnix/xray-decky/master/scripts/install-xray-decky.sh | bash</code>), or install the release zip via Decky → Settings → Developer → Install Plugin from URL. The plugin is not in the Decky Plugin Store.',
      '<b>Import your server</b> — open the plugin card in Quick Access and paste a share link or subscription URL; or scan the QR code and paste it from your phone.',
      '<b>Enable TUN mode</b> — one toggle in the plugin options; routes and cleanup are automatic. Optionally arm the kill switch for strict leak protection.',
      '<b>Connect and verify</b> — flip the connection toggle and watch the live speed in the card; open any geo-restricted store page or a what-is-my-ip site in the Deck browser to confirm the new exit IP.',
    ],
    troubleshootingTitle: 'Something not working?',
    troubleshootingHtml: `Check the <a href="${landingFaqHref}">troubleshooting FAQ</a> on the landing page — it covers connection failures, TUN mode, the kill switch, and reaching the admin panel. Worst case, <code>defaults/recover.sh</code> ships with the plugin and restores networking unconditionally.`,
  },
} satisfies Dict;
