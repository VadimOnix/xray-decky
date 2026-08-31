/* Xray Decky admin panel client. Vanilla JS, no build step. */
;(function () {
  'use strict'

  var POLL_INTERVAL_MS = 3000
  var TOKEN_KEY = 'xray-decky-admin-token'
  var LANG_KEY = 'xray-decky-admin-lang'
  // 40 samples at 3s each ≈ the last two minutes of traffic.
  var SPEED_HISTORY_MAX = 40

  // ----- i18n (EN / RU / ZH) -----

  var I18N = {
    en: {
      'lang.self': 'EN',
      'lang.switch': 'Switch language',
      'meta.title': 'Xray Decky – Admin Panel',
      'lock.title': 'Pairing required',
      'lock.desc':
        'This panel is protected by a per-install token. Open the plugin on ' +
        'your Steam Deck and scan the Admin panel QR code from the Options ' +
        'tab, or paste the token below.',
      'lock.ph': 'Admin token',
      'lock.unlock': 'Unlock',
      'lock.rejected': 'That token was rejected. Check the QR code in the plugin.',
      'lock.expired': 'Session expired or token is invalid. Pair again.',
      'st.connected.t': 'Connected',
      'st.connected.s': 'Traffic is routed through the proxy',
      'st.connecting.t': 'Connecting…',
      'st.connecting.s': 'Starting xray-core',
      'st.disconnected.t': 'Disconnected',
      'st.disconnected.s': 'Proxy is idle',
      'st.error.t': 'Error',
      'st.error.s': 'Something went wrong',
      'st.blocked.t': 'Blocked',
      'st.blocked.s': 'Kill switch is active — traffic is stopped',
      'st.unknown.t': 'Loading…',
      'st.unknown.s': 'Fetching current status',
      'hero.connect': 'Connect',
      'hero.disconnect': 'Disconnect',
      'hero.unblock': 'Unblock traffic',
      'hero.upFor': 'Up for {t}',
      'stat.total': 'total',
      'stat.download': 'Download speed',
      'stat.upload': 'Upload speed',
      'stat.session': 'Session traffic',
      'graph.download': 'Download',
      'graph.upload': 'Upload',
      'graph.window': 'peak · last 2 min',
      'graph.aria': 'Live download and upload speed over the last two minutes',
      'time.hours': 'h',
      'time.minutes': 'm',
      'time.seconds': 's',
      'servers.title': 'Servers',
      'servers.pingAll': 'Ping all',
      'servers.pinging': 'Pinging…',
      'servers.empty': 'No servers yet. Use the import form to add one.',
      'servers.footnote':
        'Tap a server to make it active — a live connection switches over ' +
        'automatically.',
      'servers.offline': 'offline',
      'servers.unnamed': 'Unnamed server',
      'servers.activate': 'Activate {name}',
      'servers.remove': 'Remove server',
      'servers.singboxCore': 'Uses the sing-box core',
      'sub.info': '{name} · {n} servers · updated {date}',
      'sub.default': 'Subscription',
      'sub.expires': 'expires {date}',
      'sub.refresh': 'Refresh',
      'sub.refreshing': 'Refreshing…',
      'sub.rename': 'Rename',
      'sub.renamePrompt': 'Subscription name:',
      'sub.renamed': 'Subscription renamed',
      'sub.renameFail': 'Rename failed',
      'sub.auto': 'Auto-refresh',
      'sub.autoAria': 'Auto-refresh interval',
      'sub.intervalOff': 'Off',
      'sub.interval6': 'Every 6h',
      'sub.interval12': 'Every 12h',
      'sub.interval24': 'Daily',
      'sub.interval48': 'Every 2 days',
      'sub.intervalSet': 'Auto-refresh set',
      'sub.intervalOffSet': 'Auto-refresh off',
      'sub.intervalFail': 'Could not set auto-refresh',
      'options.title': 'Options',
      'options.tun': 'TUN mode',
      'options.tunDesc': 'Route all system traffic through the proxy',
      'options.ks': 'Kill switch',
      'options.ksDesc': 'Block all traffic if the proxy drops unexpectedly',
      'options.tunNote':
        'TUN mode is enabled but privileges are missing — see ' +
        'INSTALLATION.md on the Deck.',
      'import.title': 'Import configuration',
      'import.seg': [
        'Paste a ',
        { mono: 'vless://' },
        ', ',
        { mono: 'vmess://' },
        ', ',
        { mono: 'trojan://' },
        ', ',
        { mono: 'ss://' },
        ', ',
        { mono: 'socks://' },
        ', ',
        { mono: 'hysteria2://' },
        ' or ',
        { mono: 'tuic://' },
        ' link, a subscription URL (',
        { mono: 'https://…' },
        ') or its base64 content.',
      ],
      'import.ph': 'vless:// / vmess:// / trojan:// / ss:// / socks:// / hysteria2:// / tuic://',
      'import.aria': 'Share link',
      'import.save': 'Save',
      'import.saved': 'Saved.',
      'import.enter': 'Please enter a share link',
      'import.failed': 'Import failed',
      'updates.title': 'Updates',
      'updates.check': 'Check',
      'updates.checking': 'Checking…',
      'updates.hint': 'Check whether newer core versions are available.',
      'updates.upToDate': 'up to date',
      'updates.available': '{v} available',
      'updates.failed': 'check failed',
      'export.title': 'Export servers',
      'export.reveal': 'Reveal',
      'export.hide': 'Hide',
      'export.hint':
        'Reveal share links for every saved server. They contain credentials — ' +
        'handle with care.',
      'export.aria': 'Exported servers',
      'export.count': '{n} servers exported',
      'export.empty': 'No servers to export',
      'export.copyLinks': 'Copy links',
      'export.copySub': 'Copy subscription',
      'export.copied': 'Copied to clipboard',
      'export.copyFail': 'Copy failed — select the text and copy manually',
      'toast.exportFail': 'Export failed',
      'toast.updatesFail': 'Update check failed',
      'toast.netErr': 'Network error',
      'toast.removed': 'Server removed',
      'toast.removeFail': 'Failed to remove server',
      'toast.switched': 'Switched and reconnected',
      'toast.activated': 'Server activated',
      'toast.switchFail': 'Failed to switch server',
      'toast.subRefreshed': 'Subscription refreshed',
      'toast.refreshFail': 'Refresh failed',
      'toast.latency': 'Latency updated',
      'toast.pingFail': 'Ping failed',
      'toast.connected': 'Connected',
      'toast.disconnected': 'Disconnected',
      'toast.actionFail': 'Action failed',
      'toast.unblocked': 'Traffic unblocked',
      'toast.unblockFail': 'Failed to unblock',
      'toast.toggleOn': '{label} enabled',
      'toast.toggleOff': '{label} disabled',
      'toast.toggleFail': 'Failed to toggle {label}',
      'routes.title': 'Routing rules',
      'routes.add': 'Add rule',
      'routes.sub': 'Domain / IP / geosite / geoip \u2192 proxy or direct. Rules are tried in order; LAN traffic is always bypassed first. Drag rows to reorder.',
      'routes.empty': 'No routing rules yet. Click "Add rule" to direct specific domains or IPs through the proxy (or directly, bypassing it).',
      'routes.matchType': 'Match type',
      'routes.type.domain': 'Domain',
      'routes.type.ip': 'IP CIDR',
      'routes.type.geosite': 'Geosite',
      'routes.type.geoip': 'GeoIP',
      'routes.value': 'Value',
      'routes.presetPh': 'e.g. example.com / 10.0.0.0/8 / geosite:google',
      'routes.action': 'Action',
      'routes.action.proxy': 'Proxy',
      'routes.action.direct': 'Direct',
      'routes.action.reject': 'Reject',
      'routes.enabled': 'Enabled',
      'routes.valueRequired': 'value required',
      'routes.cancel': 'Cancel',
      'routes.save': 'Save',
      'routes.edit': 'Edit rule',
      'routes.delete': 'Delete rule',
      'routes.drag': 'Drag',
      'routes.dragHint': 'Drag to reorder',
      'routes.saved': 'Routing rules saved',
      'routes.deleted': 'Rule deleted',
      'routes.invalid': 'Invalid rule: {msg}',
      'routes.reorderFail': 'Failed to save new order',
    },
    ru: {
      'lang.self': 'RU',
      'lang.switch': 'Переключить язык',
      'meta.title': 'Xray Decky – Панель администратора',
      'lock.title': 'Требуется сопряжение',
      'lock.desc':
        'Панель защищена персональным токеном. Откройте плагин на Steam Deck ' +
        'и отсканируйте QR-код «Admin panel» на вкладке «Опции» или вставьте ' +
        'токен ниже.',
      'lock.ph': 'Токен доступа',
      'lock.unlock': 'Разблокировать',
      'lock.rejected': 'Токен отклонён. Проверьте QR-код в плагине.',
      'lock.expired': 'Сессия истекла или токен неверен. Выполните сопряжение заново.',
      'st.connected.t': 'Подключено',
      'st.connected.s': 'Трафик идёт через прокси',
      'st.connecting.t': 'Подключение…',
      'st.connecting.s': 'Запуск xray-core',
      'st.disconnected.t': 'Отключено',
      'st.disconnected.s': 'Прокси не активен',
      'st.error.t': 'Ошибка',
      'st.error.s': 'Что-то пошло не так',
      'st.blocked.t': 'Заблокировано',
      'st.blocked.s': 'Kill switch активен — трафик остановлен',
      'st.unknown.t': 'Загрузка…',
      'st.unknown.s': 'Получение статуса',
      'hero.connect': 'Подключить',
      'hero.disconnect': 'Отключить',
      'hero.unblock': 'Разблокировать трафик',
      'hero.upFor': 'В сети {t}',
      'stat.total': 'всего',
      'stat.download': 'Скорость загрузки',
      'stat.upload': 'Скорость отдачи',
      'stat.session': 'Трафик сессии',
      'graph.download': 'Загрузка',
      'graph.upload': 'Отдача',
      'graph.window': 'пик · за 2 мин',
      'graph.aria': 'Скорость загрузки и отдачи за последние две минуты',
      'time.hours': 'ч',
      'time.minutes': 'мин',
      'time.seconds': 'с',
      'servers.title': 'Серверы',
      'servers.pingAll': 'Пинг всех',
      'servers.pinging': 'Пинг…',
      'servers.empty': 'Серверов пока нет. Добавьте через форму импорта.',
      'servers.footnote':
        'Коснитесь сервера, чтобы сделать его активным — активное ' +
        'подключение переключится автоматически.',
      'servers.offline': 'недоступен',
      'servers.unnamed': 'Без имени',
      'servers.activate': 'Выбрать {name}',
      'servers.remove': 'Удалить сервер',
      'servers.singboxCore': 'Использует ядро sing-box',
      'sub.info': '{name} · серверов: {n} · обновлено {date}',
      'sub.default': 'Подписка',
      'sub.expires': 'истекает {date}',
      'sub.refresh': 'Обновить',
      'sub.refreshing': 'Обновление…',
      'sub.rename': 'Переименовать',
      'sub.renamePrompt': 'Название подписки:',
      'sub.renamed': 'Подписка переименована',
      'sub.renameFail': 'Не удалось переименовать',
      'sub.auto': 'Автообновление',
      'sub.autoAria': 'Интервал автообновления',
      'sub.intervalOff': 'Выкл',
      'sub.interval6': 'Каждые 6 ч',
      'sub.interval12': 'Каждые 12 ч',
      'sub.interval24': 'Ежедневно',
      'sub.interval48': 'Каждые 2 дня',
      'sub.intervalSet': 'Автообновление включено',
      'sub.intervalOffSet': 'Автообновление выключено',
      'sub.intervalFail': 'Не удалось настроить автообновление',
      'options.title': 'Опции',
      'options.tun': 'Режим TUN',
      'options.tunDesc': 'Направлять весь системный трафик через прокси',
      'options.ks': 'Kill switch',
      'options.ksDesc': 'Блокировать весь трафик при внезапном обрыве прокси',
      'options.tunNote':
        'Режим TUN включён, но нет прав — см. INSTALLATION.md на Deck.',
      'import.title': 'Импорт конфигурации',
      'import.seg': [
        'Вставьте ссылку ',
        { mono: 'vless://' },
        ', ',
        { mono: 'vmess://' },
        ', ',
        { mono: 'trojan://' },
        ', ',
        { mono: 'ss://' },
        ', ',
        { mono: 'socks://' },
        ', ',
        { mono: 'hysteria2://' },
        ' или ',
        { mono: 'tuic://' },
        ', URL подписки (',
        { mono: 'https://…' },
        ') или её base64-содержимое.',
      ],
      'import.ph': 'vless:// / vmess:// / trojan:// / ss:// / socks:// / hysteria2:// / tuic://',
      'import.aria': 'Ссылка',
      'import.save': 'Сохранить',
      'import.saved': 'Сохранено.',
      'import.enter': 'Введите ссылку',
      'import.failed': 'Ошибка импорта',
      'updates.title': 'Обновления',
      'updates.check': 'Проверить',
      'updates.checking': 'Проверка…',
      'updates.hint': 'Проверьте, доступны ли новые версии ядер.',
      'updates.upToDate': 'актуально',
      'updates.available': 'доступна {v}',
      'updates.failed': 'ошибка проверки',
      'export.title': 'Экспорт серверов',
      'export.reveal': 'Показать',
      'export.hide': 'Скрыть',
      'export.hint':
        'Показать ссылки для всех сохранённых серверов. Они содержат учётные ' +
        'данные — обращайтесь осторожно.',
      'export.aria': 'Экспортированные серверы',
      'export.count': 'Экспортировано серверов: {n}',
      'export.empty': 'Нет серверов для экспорта',
      'export.copyLinks': 'Скопировать ссылки',
      'export.copySub': 'Скопировать подписку',
      'export.copied': 'Скопировано в буфер обмена',
      'export.copyFail': 'Не удалось скопировать — выделите текст вручную',
      'toast.exportFail': 'Не удалось экспортировать',
      'toast.updatesFail': 'Не удалось проверить обновления',
      'toast.netErr': 'Ошибка сети',
      'toast.removed': 'Сервер удалён',
      'toast.removeFail': 'Не удалось удалить сервер',
      'toast.switched': 'Переключено и переподключено',
      'toast.activated': 'Сервер выбран',
      'toast.switchFail': 'Не удалось сменить сервер',
      'toast.subRefreshed': 'Подписка обновлена',
      'toast.refreshFail': 'Не удалось обновить',
      'toast.latency': 'Задержка обновлена',
      'toast.pingFail': 'Ошибка пинга',
      'toast.connected': 'Подключено',
      'toast.disconnected': 'Отключено',
      'toast.actionFail': 'Действие не выполнено',
      'toast.unblocked': 'Трафик разблокирован',
      'toast.unblockFail': 'Не удалось разблокировать',
      'toast.toggleOn': '{label} включён',
      'toast.toggleOff': '{label} выключен',
      'toast.toggleFail': 'Не удалось переключить: {label}',
      'routes.title': 'Маршруты',
      'routes.add': 'Добавить правило',
      'routes.sub': 'Домен / IP / geosite / geoip \u2192 прокси или напрямую. Правила применяются по порядку; LAN-трафик всегда идёт в обход. Перетащите строки мышью для изменения порядка.',
      'routes.empty': 'Правил маршрутизации пока нет. Нажмите «Добавить правило», чтобы направить отдельные домены или IP через прокси или напрямую.',
      'routes.matchType': 'Тип совпадения',
      'routes.type.domain': 'Домен',
      'routes.type.ip': 'IP CIDR',
      'routes.type.geosite': 'Geosite',
      'routes.type.geoip': 'GeoIP',
      'routes.value': 'Значение',
      'routes.presetPh': 'например example.com / 10.0.0.0/8 / geosite:google',
      'routes.action': 'Действие',
      'routes.action.proxy': 'Прокси',
      'routes.action.direct': 'Напрямую',
      'routes.action.reject': 'Отклонить',
      'routes.enabled': 'Включено',
      'routes.valueRequired': 'необходимо указать значение',
      'routes.cancel': 'Отмена',
      'routes.save': 'Сохранить',
      'routes.edit': 'Изменить правило',
      'routes.delete': 'Удалить правило',
      'routes.drag': 'Перетащить',
      'routes.dragHint': 'Перетащите для изменения порядка',
      'routes.saved': 'Маршруты сохранены',
      'routes.deleted': 'Правило удалено',
      'routes.invalid': 'Некорректное правило: {msg}',
      'routes.reorderFail': 'Не удалось сохранить порядок',
    },
    zh: {
      'lang.self': '中文',
      'lang.switch': '切换语言',
      'meta.title': 'Xray Decky – 管理面板',
      'lock.title': '需要配对',
      'lock.desc': '此面板受每个安装独立的令牌保护。请在 Steam Deck 上打开插件并扫描「选项」选项卡中的「管理面板」二维码,或在下方粘贴令牌。',
      'lock.ph': '管理令牌',
      'lock.unlock': '解锁',
      'lock.rejected': '令牌被拒绝,请检查插件中的二维码。',
      'lock.expired': '会话已过期或令牌无效,请重新配对。',
      'st.connected.t': '已连接',
      'st.connected.s': '流量已通过代理转发',
      'st.connecting.t': '正在连接…',
      'st.connecting.s': '正在启动 xray-core',
      'st.disconnected.t': '已断开',
      'st.disconnected.s': '代理处于空闲状态',
      'st.error.t': '错误',
      'st.error.s': '出现了一些问题',
      'st.blocked.t': '已拦截',
      'st.blocked.s': 'Kill Switch 已启用 — 流量已被阻止',
      'st.unknown.t': '加载中…',
      'st.unknown.s': '正在获取当前状态',
      'hero.connect': '连接',
      'hero.disconnect': '断开',
      'hero.unblock': '解除拦截',
      'hero.upFor': '已运行 {t}',
      'stat.total': '总计',
      'stat.download': '下载速度',
      'stat.upload': '上传速度',
      'stat.session': '会话流量',
      'graph.download': '下载',
      'graph.upload': '上传',
      'graph.window': '近 2 分钟峰值',
      'graph.aria': '最近两分钟的实时下载和上传速度',
      'time.hours': '小时',
      'time.minutes': '分钟',
      'time.seconds': '秒',
      'servers.title': '服务器',
      'servers.pingAll': '全部测速',
      'servers.pinging': '测速中…',
      'servers.empty': '尚无服务器。请使用导入表单添加。',
      'servers.footnote': '点击服务器即可设为活动服务器 — 如已连接,将自动切换。',
      'servers.offline': '离线',
      'servers.unnamed': '未命名服务器',
      'servers.activate': '启用 {name}',
      'servers.remove': '移除服务器',
      'servers.singboxCore': '使用 sing-box 内核',
      'sub.info': '{name} · {n} 台服务器 · 更新于 {date}',
      'sub.default': '订阅',
      'sub.expires': '{date} 过期',
      'sub.refresh': '刷新',
      'sub.refreshing': '刷新中…',
      'sub.rename': '重命名',
      'sub.renamePrompt': '订阅名称:',
      'sub.renamed': '订阅已重命名',
      'sub.renameFail': '重命名失败',
      'sub.auto': '自动刷新',
      'sub.autoAria': '自动刷新间隔',
      'sub.intervalOff': '关闭',
      'sub.interval6': '每 6 小时',
      'sub.interval12': '每 12 小时',
      'sub.interval24': '每天',
      'sub.interval48': '每 2 天',
      'sub.intervalSet': '自动刷新已设置',
      'sub.intervalOffSet': '自动刷新已关闭',
      'sub.intervalFail': '无法设置自动刷新',
      'options.title': '选项',
      'options.tun': 'TUN 模式',
      'options.tunDesc': '将所有系统流量通过代理转发',
      'options.ks': 'Kill Switch',
      'options.ksDesc': '若代理意外中断则阻断所有流量',
      'options.tunNote': 'TUN 模式已启用但缺少权限 — 请参阅 Deck 上的 INSTALLATION.md。',
      'import.title': '导入配置',
      'import.ph': 'vless:// / vmess:// / trojan:// / ss:// / socks:// / hysteria2:// / tuic://',
      'import.aria': '分享链接',
      'import.save': '保存',
      'import.saved': '已导入',
      'import.enter': '请粘贴分享链接或订阅 URL',
      'import.failed': '导入失败',
      'updates.title': '更新',
      'updates.check': '检查',
      'updates.checking': '检查中…',
      'updates.hint': '检查是否有新的核心版本可用。',
      'updates.upToDate': '已是最新版本',
      'updates.available': '{v} 有更新',
      'updates.failed': '检查更新失败',
      'export.title': '导出服务器',
      'export.reveal': '显示',
      'export.hide': '隐藏',
      'export.hint': '显示所有已保存服务器的分享链接。链接包含凭据,请妥善保管。',
      'export.aria': '已导出服务器',
      'export.count': '{n} 个服务器',
      'export.empty': '未导出任何服务器。',
      'export.copyLinks': '复制链接',
      'export.copySub': '复制订阅',
      'export.copied': '已复制',
      'export.copyFail': '复制失败',
      'toast.exportFail': '导出失败',
      'toast.updatesFail': '检查更新失败',
      'toast.netErr': '网络错误',
      'toast.removed': '服务器已移除',
      'toast.removeFail': '移除失败',
      'toast.switched': '已切换并重新连接',
      'toast.activated': '服务器已激活',
      'toast.switchFail': '切换服务器失败',
      'toast.subRefreshed': '订阅已刷新',
      'toast.refreshFail': '刷新失败',
      'toast.latency': '测速完成',
      'toast.pingFail': '测速失败',
      'toast.connected': '已连接',
      'toast.disconnected': '已断开',
      'toast.actionFail': '操作失败',
      'toast.unblocked': '流量已解除拦截',
      'toast.unblockFail': '解除拦截失败',
      'toast.toggleOn': '{label} 已启用',
      'toast.toggleOff': '{label} 已关闭',
      'toast.toggleFail': '切换失败:{label}',
      'routes.title': '路由规则',
      'routes.add': '添加规则',
      'routes.sub': '域名 / IP / geosite / geoip → 代理或直连。规则按顺序匹配；局域网流量始终绕过代理。拖动规则行调整顺序。',
      'routes.empty': '暂无路由规则。点击“添加规则”，将指定域名或 IP 通过代理或直连。',
      'routes.matchType': '匹配类型',
      'routes.type.domain': '域名',
      'routes.type.ip': 'IP CIDR',
      'routes.type.geosite': '域名集合',
      'routes.type.geoip': 'IP 集合',
      'routes.value': '值',
      'routes.presetPh': '例如 example.com / 10.0.0.0/8 / geosite:google',
      'routes.action': '操作',
      'routes.action.proxy': '代理',
      'routes.action.direct': '直连',
      'routes.action.reject': '拒绝',
      'routes.enabled': '已启用',
      'routes.valueRequired': '请输入值',
      'routes.cancel': '取消',
      'routes.save': '保存',
      'routes.edit': '编辑规则',
      'routes.delete': '删除规则',
      'routes.drag': '拖动',
      'routes.dragHint': '拖动以调整顺序',
      'routes.saved': '路由规则已保存',
      'routes.deleted': '规则已删除',
      'routes.invalid': '无效规则：{msg}',
      'routes.reorderFail': '保存新顺序失败',
      'import.seg': ["粘贴 ", {mono: "vless://"}, "、", {mono: "vmess://"}, "、", {mono: "trojan://"}, "、", {mono: "ss://"}, "、", {mono: "socks://"}, "、", {mono: "hysteria2://"}, " 或 ", {mono: "tuic://"}, " 分享链接,或订阅 URL (", {mono: "https://…"}, ") 及其 base64 内容。"],
    },
  }

  function detectLang() {
    var saved = window.localStorage.getItem(LANG_KEY)
    if (saved === 'en' || saved === 'ru' || saved === 'zh') return saved
    var nav = (window.navigator.language || 'en').toLowerCase()
    if (nav.indexOf('zh') === 0) return 'zh'
    return nav.indexOf('ru') === 0 ? 'ru' : 'en'
  }

  function t(key, params) {
    var dict = I18N[state.lang] || I18N.en
    var str = dict[key]
    if (str === undefined) str = I18N.en[key] !== undefined ? I18N.en[key] : key
    if (params) {
      Object.keys(params).forEach(function (k) {
        // split/join rather than String.replace: replace() substitutes only
        // the first occurrence, and it interprets `$&`/`$'`/`` $` `` in the
        // replacement as capture references. Values here include server names
        // from a remote subscription, so they must go in verbatim.
        str = str.split('{' + k + '}').join(String(params[k]))
      })
    }
    return str
  }

  function applyStaticI18n() {
    document.documentElement.lang = state.lang
    var nodes = document.querySelectorAll('[data-i18n]')
    var i
    for (i = 0; i < nodes.length; i++) {
      nodes[i].textContent = t(nodes[i].getAttribute('data-i18n'))
    }
    renderImportHint()
    var phNodes = document.querySelectorAll('[data-i18n-ph]')
    for (i = 0; i < phNodes.length; i++) {
      phNodes[i].setAttribute('placeholder', t(phNodes[i].getAttribute('data-i18n-ph')))
    }
    var ariaNodes = document.querySelectorAll('[data-i18n-aria]')
    for (i = 0; i < ariaNodes.length; i++) {
      ariaNodes[i].setAttribute('aria-label', t(ariaNodes[i].getAttribute('data-i18n-aria')))
    }
    if (els.langToggle) els.langToggle.textContent = t('lang.self')
  }

  // Build the import hint from structured segments (text + mono chips) using
  // DOM nodes only — never innerHTML — so the scheme tokens can't be
  // reinterpreted as markup.
  function renderImportHint() {
    var el = els.importSub
    if (!el) return
    var dict = I18N[state.lang] || I18N.en
    var segs = dict['import.seg'] || I18N.en['import.seg']
    el.textContent = ''
    segs.forEach(function (seg) {
      if (typeof seg === 'string') {
        el.appendChild(document.createTextNode(seg))
      } else {
        var span = document.createElement('span')
        span.className = 'mono'
        span.textContent = seg.mono
        el.appendChild(span)
      }
    })
  }

  function setLang(lang) {
    state.lang = lang
    window.localStorage.setItem(LANG_KEY, lang)
    applyStaticI18n()
    // Re-render dynamic strings that aren't driven by data-i18n attributes.
    if (state.lastData) render(state.lastData)
    if (state.lastProfiles) {
      renderProfiles(state.lastProfiles.activeId, state.lastProfiles.profiles)
      renderSubscription(state.lastProfiles.subscription)
    }
    if (state.lastUpdates) renderUpdates(state.lastUpdates)
    if (state.lastRules) renderRules(state.lastRules)
  }

  var els = {
    locked: document.getElementById('locked'),
    panel: document.getElementById('panel'),
    tokenForm: document.getElementById('token-form'),
    tokenInput: document.getElementById('token-input'),
    tokenError: document.getElementById('token-error'),
    statusPill: document.getElementById('status-pill'),
    statusPillText: document.getElementById('status-pill-text'),
    statusOrb: document.getElementById('status-orb'),
    heroTitle: document.getElementById('hero-title'),
    heroSub: document.getElementById('hero-sub'),
    connectBtn: document.getElementById('connect-btn'),
    connectBtnLabel: document.getElementById('connect-btn-label'),
    unblockBtn: document.getElementById('unblock-btn'),
    serversEmpty: document.getElementById('servers-empty'),
    serverList: document.getElementById('server-list'),
    pingBtn: document.getElementById('ping-btn'),
    subscriptionRow: document.getElementById('subscription-row'),
    subscriptionInfo: document.getElementById('subscription-info'),
    refreshSubBtn: document.getElementById('refresh-sub-btn'),
    renameSubBtn: document.getElementById('rename-sub-btn'),
    subInterval: document.getElementById('sub-interval'),
    heroStats: document.getElementById('hero-stats'),
    statDown: document.getElementById('stat-down'),
    statUp: document.getElementById('stat-up'),
    statTotal: document.getElementById('stat-total'),
    heroGraph: document.getElementById('hero-graph'),
    speedCanvas: document.getElementById('speed-canvas'),
    graphDownPeak: document.getElementById('graph-down-peak'),
    graphUpPeak: document.getElementById('graph-up-peak'),
    tunToggle: document.getElementById('tun-toggle'),
    killswitchToggle: document.getElementById('killswitch-toggle'),
    optionsNote: document.getElementById('options-note'),
    importForm: document.getElementById('import-form'),
    importSub: document.getElementById('import-sub'),
    importInput: document.getElementById('import-input'),
    importBtn: document.getElementById('import-btn'),
    importMsg: document.getElementById('import-msg'),
    checkUpdatesBtn: document.getElementById('check-updates-btn'),
    updatesList: document.getElementById('updates-list'),
    updatesHint: document.getElementById('updates-hint'),
    exportBtn: document.getElementById('export-btn'),
    exportHint: document.getElementById('export-hint'),
    exportResult: document.getElementById('export-result'),
    exportCount: document.getElementById('export-count'),
    exportText: document.getElementById('export-text'),
    exportCopyLinks: document.getElementById('export-copy-links'),
    exportCopySub: document.getElementById('export-copy-sub'),
    toast: document.getElementById('toast'),
    langToggle: document.getElementById('lang-toggle'),
    // Routing rules
    rulesList: document.getElementById('rules-list'),
    rulesEmpty: document.getElementById('rules-empty'),
    rulesAddBtn: document.getElementById('routes-add-btn'),
    rulesMsg: document.getElementById('rules-msg'),
    ruleDialog: document.getElementById('rule-dialog'),
    ruleForm: document.getElementById('rule-form'),
    ruleType: document.getElementById('rule-type'),
    ruleValue: document.getElementById('rule-value'),
    ruleAction: document.getElementById('rule-action'),
    ruleEnabled: document.getElementById('rule-enabled'),
    ruleDialogError: document.getElementById('rule-dialog-error'),
    rulePresets: document.getElementById('rule-presets'),
    ruleSave: document.getElementById('rule-save'),
    ruleCancel: document.getElementById('rule-cancel'),
  }

  var state = {
    token: null,
    status: 'unknown',
    busy: false,
    pollTimer: null,
    toastTimer: null,
    speedHistory: [],
    lang: 'en',
    lastData: null,
    lastProfiles: null,
    lastUpdates: null,
    lastExport: null,
    exportShown: false,
    // Routing rules
    lastRules: null,
    ruleEditingId: null,
    rulePresetsList: [],
    draggedRuleId: null,
  }

  // ----- token handling -----

  function loadToken() {
    var params = new URLSearchParams(window.location.search)
    var fromUrl = params.get('token')
    if (fromUrl) {
      sessionStorage.setItem(TOKEN_KEY, fromUrl)
      // Strip the token from the address bar / browser history.
      params.delete('token')
      var clean =
        window.location.pathname + (params.toString() ? '?' + params.toString() : '')
      window.history.replaceState(null, '', clean)
    }
    return sessionStorage.getItem(TOKEN_KEY)
  }

  function showLocked(message) {
    els.panel.hidden = true
    els.locked.hidden = false
    if (message) {
      els.tokenError.textContent = message
      els.tokenError.hidden = false
    } else {
      els.tokenError.hidden = true
    }
  }

  function showPanel() {
    els.locked.hidden = true
    els.panel.hidden = false
  }

  // ----- API -----

  function api(path, options) {
    options = options || {}
    options.headers = Object.assign(
      { 'X-Admin-Token': state.token || '' },
      options.headers || {}
    )
    if (options.body && !options.headers['Content-Type']) {
      options.headers['Content-Type'] = 'application/json'
    }
    return fetch(path, options).then(function (res) {
      return res
        .json()
        .catch(function () {
          return {}
        })
        .then(function (data) {
          return { status: res.status, data: data }
        })
    })
  }

  // ----- rendering -----

  var STATUS_KEYS = {
    connected: 'connected',
    connecting: 'connecting',
    disconnected: 'disconnected',
    error: 'error',
    blocked: 'blocked',
    unknown: 'unknown',
  }

  function statusText(status) {
    var s = STATUS_KEYS[status] ? status : 'unknown'
    return [t('st.' + s + '.t'), t('st.' + s + '.s')]
  }

  function formatBytes(bytes, perSecond) {
    var units = ['B', 'KB', 'MB', 'GB', 'TB']
    var value = Math.max(0, bytes || 0)
    var unit = 0
    while (value >= 1024 && unit < units.length - 1) {
      value = value / 1024
      unit++
    }
    var text = (unit === 0 ? value : value.toFixed(1)) + ' ' + units[unit]
    return perSecond ? text + '/s' : text
  }

  function renderStats(stats) {
    if (state.status === 'connected' && stats && stats.available) {
      els.statDown.textContent = formatBytes(stats.downlinkSpeed, true)
      els.statUp.textContent = formatBytes(stats.uplinkSpeed, true)
      els.statTotal.textContent =
        formatBytes((stats.uplink || 0) + (stats.downlink || 0)) + ' ' + t('stat.total')
      els.heroStats.hidden = false
      pushSpeedSample(stats.downlinkSpeed || 0, stats.uplinkSpeed || 0)
    } else {
      els.heroStats.hidden = true
      resetGraph()
    }
  }

  // ----- live speed graph -----

  function pushSpeedSample(down, up) {
    state.speedHistory.push({ down: Math.max(0, down), up: Math.max(0, up) })
    if (state.speedHistory.length > SPEED_HISTORY_MAX) {
      state.speedHistory.shift()
    }
    els.heroGraph.hidden = false
    drawGraph()
  }

  function resetGraph() {
    if (state.speedHistory.length === 0 && els.heroGraph.hidden) return
    state.speedHistory = []
    els.heroGraph.hidden = true
  }

  function drawGraph() {
    var canvas = els.speedCanvas
    if (!canvas || els.heroGraph.hidden) return
    var ctx = canvas.getContext('2d')
    if (!ctx) return

    var ratio = window.devicePixelRatio || 1
    var cssW = canvas.clientWidth || 600
    var cssH = canvas.clientHeight || 128
    var w = Math.round(cssW * ratio)
    var h = Math.round(cssH * ratio)
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w
      canvas.height = h
    }
    ctx.clearRect(0, 0, w, h)

    var hist = state.speedHistory
    var n = hist.length

    var downPeak = 0
    var upPeak = 0
    for (var i = 0; i < n; i++) {
      if (hist[i].down > downPeak) downPeak = hist[i].down
      if (hist[i].up > upPeak) upPeak = hist[i].up
    }
    els.graphDownPeak.textContent = formatBytes(downPeak, true)
    els.graphUpPeak.textContent = formatBytes(upPeak, true)
    // Scale to the largest sample in view, with a 1 KB/s floor so an idle
    // line sits flat at the bottom instead of amplifying noise.
    var peak = Math.max(downPeak, upPeak, 1024)

    // Horizontal gridlines.
    ctx.lineWidth = ratio
    ctx.strokeStyle = 'rgba(103, 193, 245, 0.10)'
    for (var g = 1; g < 4; g++) {
      var gy = Math.round((h * g) / 4) + 0.5
      ctx.beginPath()
      ctx.moveTo(0, gy)
      ctx.lineTo(w, gy)
      ctx.stroke()
    }

    if (n < 2) return

    var pad = 4 * ratio
    var innerH = h - pad * 2
    var stepX = w / (SPEED_HISTORY_MAX - 1)

    function series(key, stroke, fill) {
      var lastX = (n - 1) * stepX
      ctx.beginPath()
      for (var j = 0; j < n; j++) {
        var x = j * stepX
        var y = h - pad - (hist[j][key] / peak) * innerH
        if (j === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
      }
      ctx.lineTo(lastX, h)
      ctx.lineTo(0, h)
      ctx.closePath()
      ctx.fillStyle = fill
      ctx.fill()

      ctx.beginPath()
      for (var k = 0; k < n; k++) {
        var lx = k * stepX
        var ly = h - pad - (hist[k][key] / peak) * innerH
        if (k === 0) ctx.moveTo(lx, ly)
        else ctx.lineTo(lx, ly)
      }
      ctx.lineWidth = 2 * ratio
      ctx.lineJoin = 'round'
      ctx.strokeStyle = stroke
      ctx.stroke()
    }

    // Download drawn first (under), upload on top.
    series('down', '#a1cd44', 'rgba(161, 205, 68, 0.16)')
    series('up', '#66c0f4', 'rgba(102, 192, 244, 0.16)')
  }

  function fetchStats() {
    if (state.status !== 'connected') {
      els.heroStats.hidden = true
      resetGraph()
      return Promise.resolve()
    }
    return api('/api/v1/stats')
      .then(function (res) {
        if (res.status === 200 && res.data.success) {
          renderStats(res.data)
        }
      })
      .catch(function () {
        /* transient */
      })
  }

  function formatUptime(seconds) {
    if (!seconds || seconds < 0) return null
    var h = Math.floor(seconds / 3600)
    var m = Math.floor((seconds % 3600) / 60)
    var s = Math.floor(seconds % 60)
    if (h > 0) return h + t('time.hours') + ' ' + m + t('time.minutes')
    if (m > 0) return m + t('time.minutes') + ' ' + s + t('time.seconds')
    return s + t('time.seconds')
  }

  function render(data) {
    state.lastData = data
    var connection = data.connection || {}
    var status = connection.status || 'unknown'
    state.status = status

    var text = statusText(status)
    els.statusPill.dataset.status = status
    els.statusPillText.textContent = text[0]
    els.statusOrb.dataset.status = status
    els.heroTitle.textContent = text[0]

    var sub = text[1]
    if (status === 'connected') {
      var uptime = formatUptime(connection.uptime)
      if (uptime) sub = t('hero.upFor', { t: uptime })
    } else if (status === 'error' && connection.errorMessage) {
      sub = connection.errorMessage
    }
    els.heroSub.textContent = sub

    var hasConfig = Boolean(data.config)
    var connectable = status === 'disconnected' || status === 'error'
    els.connectBtn.disabled = state.busy || (!connectable && status !== 'connected') || (connectable && !hasConfig)
    if (status === 'connected') {
      els.connectBtn.dataset.mode = 'disconnect'
      els.connectBtnLabel.textContent = t('hero.disconnect')
    } else {
      delete els.connectBtn.dataset.mode
      els.connectBtnLabel.textContent = t('hero.connect')
    }
    els.unblockBtn.hidden = status !== 'blocked'

    // Options
    if (!state.busy) {
      els.tunToggle.checked = Boolean(data.tun && data.tun.enabled)
      els.killswitchToggle.checked = Boolean(data.killSwitch && data.killSwitch.enabled)
    }
    if (data.tun && data.tun.enabled && !data.tun.hasPrivileges) {
      els.optionsNote.textContent = t('options.tunNote')
      els.optionsNote.hidden = false
    } else {
      els.optionsNote.hidden = true
    }
  }

  // ----- server list -----

  function latencyBadge(profile) {
    var span = document.createElement('span')
    var ms = profile.latencyMs
    if (typeof ms === 'number') {
      span.textContent = ms + ' ms'
      span.className = 'latency ' + (ms < 150 ? 'good' : ms < 400 ? 'ok' : 'bad')
    } else if (profile.latencyTestedAt) {
      span.textContent = t('servers.offline')
      span.className = 'latency bad'
    } else {
      span.textContent = '— ms'
      span.className = 'latency unknown'
    }
    return span
  }

  // Sort key: measured servers first (fastest → slowest), then untested,
  // then offline. Real latencies never reach these sentinels, and a stable
  // sort keeps the stored order within each group (so an unpinged list is
  // unchanged).
  function latencyRank(profile) {
    if (typeof profile.latencyMs === 'number') return profile.latencyMs
    return profile.latencyTestedAt ? 1e9 : 1e8
  }

  function renderProfiles(activeId, profiles) {
    els.serverList.textContent = ''
    var hasProfiles = profiles && profiles.length > 0
    els.serversEmpty.hidden = hasProfiles
    els.serverList.hidden = !hasProfiles
    if (!hasProfiles) return

    var ordered = profiles.slice().sort(function (a, b) {
      return latencyRank(a) - latencyRank(b)
    })
    ordered.forEach(function (profile) {
      var li = document.createElement('li')
      var row = document.createElement('button')
      row.type = 'button'
      row.className = 'server-row' + (profile.id === activeId ? ' active' : '')
      row.setAttribute(
        'aria-label',
        t('servers.activate', {
          name: profile.name || profile.address || t('servers.unnamed'),
        })
      )

      var chips = document.createElement('span')
      chips.className = 'server-row-chips'
      var chip = document.createElement('span')
      chip.className = 'chip chip-accent'
      // Keep chips narrow on phone screens.
      chip.textContent =
        profile.protocol === 'shadowsocks' ? 'ss' : profile.protocol || 'vless'
      chips.appendChild(chip)
      // Flag servers that need the second core (hysteria2 / tuic).
      if (profile.core === 'sing-box') {
        var coreChip = document.createElement('span')
        coreChip.className = 'chip chip-core'
        coreChip.textContent = 'sing-box'
        coreChip.title = t('servers.singboxCore')
        chips.appendChild(coreChip)
      }

      var main = document.createElement('span')
      main.className = 'server-row-main'
      var name = document.createElement('span')
      name.className = 'server-row-name'
      name.textContent = profile.name || profile.address || t('servers.unnamed')
      var addr = document.createElement('span')
      addr.className = 'server-row-addr'
      addr.textContent =
        (profile.address || '?') +
        ':' +
        (profile.port || '?') +
        ' · ' +
        (profile.network || 'tcp') +
        ' / ' +
        (profile.security || 'none')
      main.appendChild(name)
      main.appendChild(addr)

      var del = document.createElement('button')
      del.type = 'button'
      del.className = 'server-delete'
      del.textContent = '✕'
      del.setAttribute('aria-label', t('servers.remove'))
      del.addEventListener('click', function (e) {
        e.stopPropagation()
        api('/api/v1/profiles/remove', {
          method: 'POST',
          body: JSON.stringify({ id: profile.id }),
        }).then(function (res) {
          if (res.status === 200 && res.data.success) {
            toast(t('toast.removed'))
            fetchProfiles()
          } else {
            toast(res.data.error || t('toast.removeFail'), true)
          }
        })
      })

      row.addEventListener('click', function () {
        if (profile.id === activeId) return
        withBusy(
          api('/api/v1/profiles/activate', {
            method: 'POST',
            body: JSON.stringify({ id: profile.id }),
          })
        ).then(function (res) {
          if (!res) return
          if (res.status === 200 && res.data.success) {
            toast(res.data.reconnected ? t('toast.switched') : t('toast.activated'))
          } else {
            toast(res.data.error || t('toast.switchFail'), true)
          }
          fetchProfiles()
        })
      })

      row.appendChild(chips)
      row.appendChild(main)
      row.appendChild(latencyBadge(profile))
      row.appendChild(del)
      li.appendChild(row)
      els.serverList.appendChild(li)
    })
  }

  function renderSubscription(subscription) {
    if (subscription && subscription.url) {
      var updated = subscription.updatedAt
        ? new Date(subscription.updatedAt * 1000).toLocaleString()
        : '—'
      var parts = [
        t('sub.info', {
          name: subscription.name || t('sub.default'),
          n: subscription.nodeCount || 0,
          date: updated,
        }),
      ]
      var ui = subscription.userinfo
      if (ui) {
        var used = (ui.upload || 0) + (ui.download || 0)
        if (ui.total) {
          parts.push(formatBytes(used) + ' / ' + formatBytes(ui.total))
        } else if (used) {
          parts.push(formatBytes(used))
        }
        if (ui.expire) {
          parts.push(
            t('sub.expires', {
              date: new Date(ui.expire * 1000).toLocaleDateString(),
            })
          )
        }
      }
      els.subscriptionInfo.textContent = parts.join(' · ')
      if (els.subInterval) {
        els.subInterval.value = String(subscription.refreshIntervalHours || 0)
      }
      els.subscriptionRow.hidden = false
    } else {
      els.subscriptionRow.hidden = true
    }
  }

  function fetchProfiles() {
    return api('/api/v1/profiles')
      .then(function (res) {
        if (res.status === 200 && res.data.success) {
          state.lastProfiles = {
            activeId: res.data.activeId,
            profiles: res.data.profiles || [],
            subscription: res.data.subscription,
          }
          renderProfiles(res.data.activeId, res.data.profiles || [])
          renderSubscription(res.data.subscription)
        }
      })
      .catch(function () {
        /* transient */
      })
  }

  function renderUpdates(cores) {
    els.updatesList.textContent = ''
    var hasCores = cores && cores.length > 0
    els.updatesHint.hidden = hasCores
    els.updatesList.hidden = !hasCores
    if (!hasCores) return
    cores.forEach(function (core) {
      var li = document.createElement('li')
      li.className = 'update-row'
      var name = document.createElement('span')
      name.className = 'update-name'
      name.textContent = core.name
      var ver = document.createElement('span')
      ver.className = 'update-ver'
      ver.textContent = core.current
      var badge = document.createElement('span')
      if (core.updateAvailable && core.latest) {
        badge.className = 'update-badge new'
        badge.textContent = t('updates.available', { v: core.latest })
      } else if (core.latest) {
        badge.className = 'update-badge ok'
        badge.textContent = t('updates.upToDate')
      } else {
        badge.className = 'update-badge err'
        badge.textContent = t('updates.failed')
      }
      li.appendChild(name)
      li.appendChild(ver)
      li.appendChild(badge)
      els.updatesList.appendChild(li)
    })
  }

  els.checkUpdatesBtn.addEventListener('click', function () {
    els.checkUpdatesBtn.disabled = true
    els.checkUpdatesBtn.textContent = t('updates.checking')
    api('/api/v1/updates')
      .then(function (res) {
        if (res.status === 200 && res.data.success) {
          state.lastUpdates = res.data.components || []
          renderUpdates(state.lastUpdates)
        } else {
          toast(res.data.error || t('toast.updatesFail'), true)
        }
      })
      .catch(function () {
        toast(t('toast.netErr'), true)
      })
      .then(function () {
        els.checkUpdatesBtn.disabled = false
        els.checkUpdatesBtn.textContent = t('updates.check')
      })
  })

  // ----- export -----

  function hideExport() {
    // Clear the revealed credentials off-screen when collapsing.
    state.exportShown = false
    els.exportText.value = ''
    els.exportResult.hidden = true
    els.exportHint.hidden = false
    els.exportBtn.textContent = t('export.reveal')
  }

  function showExport(data) {
    state.lastExport = data
    state.exportShown = true
    var links = (data.links || []).map(function (item) {
      return item.link
    })
    els.exportText.value = links.join('\n')
    els.exportText.rows = Math.min(Math.max(links.length, 2), 8)
    els.exportCount.textContent = t('export.count', { n: data.count || 0 })
    els.exportHint.hidden = true
    els.exportResult.hidden = false
    els.exportBtn.textContent = t('export.hide')
  }

  function copyText(text) {
    var clip = window.navigator && window.navigator.clipboard
    if (clip && clip.writeText) {
      clip.writeText(text).then(
        function () {
          toast(t('export.copied'))
        },
        function () {
          els.exportText.select()
          toast(t('export.copyFail'), true)
        }
      )
    } else {
      els.exportText.select()
      toast(t('export.copyFail'), true)
    }
  }

  els.exportBtn.addEventListener('click', function () {
    if (state.exportShown) {
      hideExport()
      return
    }
    els.exportBtn.disabled = true
    api('/api/v1/export')
      .then(function (res) {
        if (res.status === 200 && res.data.success) {
          if (!res.data.count) {
            toast(t('export.empty'))
          } else {
            showExport(res.data)
          }
        } else {
          toast(res.data.error || t('toast.exportFail'), true)
        }
      })
      .catch(function () {
        toast(t('toast.netErr'), true)
      })
      .then(function () {
        els.exportBtn.disabled = false
      })
  })

  els.exportCopyLinks.addEventListener('click', function () {
    if (!state.lastExport) return
    var links = (state.lastExport.links || []).map(function (item) {
      return item.link
    })
    copyText(links.join('\n'))
  })

  els.exportCopySub.addEventListener('click', function () {
    if (!state.lastExport) return
    copyText(state.lastExport.subscription || '')
  })

  els.renameSubBtn.addEventListener('click', function () {
    var current =
      (state.lastProfiles &&
        state.lastProfiles.subscription &&
        state.lastProfiles.subscription.name) ||
      ''
    var name = window.prompt(t('sub.renamePrompt'), current)
    if (name == null) return
    name = name.trim()
    if (!name) return
    api('/api/v1/subscription/rename', {
      method: 'POST',
      body: JSON.stringify({ name: name }),
    })
      .then(function (res) {
        if (res.status === 200 && res.data.success) {
          toast(t('sub.renamed'))
        } else {
          toast(res.data.error || t('sub.renameFail'), true)
        }
        return fetchProfiles()
      })
      .catch(function () {
        toast(t('toast.netErr'), true)
      })
  })

  els.subInterval.addEventListener('change', function () {
    var hours = parseInt(els.subInterval.value, 10) || 0
    els.subInterval.disabled = true
    api('/api/v1/subscription/interval', {
      method: 'POST',
      body: JSON.stringify({ hours: hours }),
    })
      .then(function (res) {
        if (res.status === 200 && res.data.success) {
          toast(t(hours > 0 ? 'sub.intervalSet' : 'sub.intervalOffSet'))
        } else {
          toast(res.data.error || t('sub.intervalFail'), true)
        }
        return fetchProfiles()
      })
      .catch(function () {
        toast(t('toast.netErr'), true)
      })
      .then(function () {
        els.subInterval.disabled = false
      })
  })

  els.refreshSubBtn.addEventListener('click', function () {
    els.refreshSubBtn.disabled = true
    els.refreshSubBtn.textContent = t('sub.refreshing')
    api('/api/v1/subscription/refresh', { method: 'POST' })
      .then(function (res) {
        if (res.status === 200 && res.data.success) {
          toast(t('toast.subRefreshed'))
        } else {
          toast(res.data.error || t('toast.refreshFail'), true)
        }
        return fetchProfiles()
      })
      .catch(function () {
        toast(t('toast.netErr'), true)
      })
      .then(function () {
        els.refreshSubBtn.disabled = false
        els.refreshSubBtn.textContent = t('sub.refresh')
      })
  })

  els.pingBtn.addEventListener('click', function () {
    els.pingBtn.disabled = true
    els.pingBtn.textContent = t('servers.pinging')
    api('/api/v1/profiles/ping', { method: 'POST' })
      .then(function (res) {
        if (res.status === 200 && res.data.success) {
          toast(t('toast.latency'))
        } else {
          toast(res.data.error || t('toast.pingFail'), true)
        }
        return fetchProfiles()
      })
      .catch(function () {
        toast(t('toast.netErr'), true)
      })
      .then(function () {
        els.pingBtn.disabled = false
        els.pingBtn.textContent = t('servers.pingAll')
      })
  })

  function toast(message, isError) {
    els.toast.textContent = message
    els.toast.className = 'toast' + (isError ? ' error' : '')
    els.toast.hidden = false
    clearTimeout(state.toastTimer)
    state.toastTimer = setTimeout(function () {
      els.toast.hidden = true
    }, 4000)
  }

  // ----- polling -----

  function poll() {
    return api('/api/v1/status').then(function (res) {
      if (res.status === 401) {
        stopPolling()
        sessionStorage.removeItem(TOKEN_KEY)
        showLocked(t('lock.expired'))
        return
      }
      if (res.status === 200 && res.data.success) {
        showPanel()
        render(res.data)
        return fetchStats()
      }
    })
  }

  function startPolling() {
    stopPolling()
    var tick = function () {
      poll()
        .catch(function () {
          /* transient network error: keep polling */
        })
        .then(function () {
          state.pollTimer = setTimeout(tick, POLL_INTERVAL_MS)
        })
    }
    tick()
  }

  function stopPolling() {
    clearTimeout(state.pollTimer)
    state.pollTimer = null
  }

  // ----- actions -----

  function withBusy(promise) {
    state.busy = true
    els.connectBtn.disabled = true
    return promise
      .catch(function () {
        toast(t('toast.netErr'), true)
        return null
      })
      .then(function (res) {
        state.busy = false
        return poll().then(function () {
          return res
        })
      })
  }

  els.connectBtn.addEventListener('click', function () {
    var enable = state.status !== 'connected'
    withBusy(
      api('/api/v1/connection', {
        method: 'POST',
        body: JSON.stringify({ enable: enable }),
      })
    ).then(function (res) {
      if (!res) return
      if (res.status === 200 && res.data.success) {
        toast(enable ? t('toast.connected') : t('toast.disconnected'))
      } else {
        toast(res.data.error || t('toast.actionFail'), true)
      }
    })
  })

  els.unblockBtn.addEventListener('click', function () {
    withBusy(api('/api/v1/killswitch/deactivate', { method: 'POST' })).then(
      function (res) {
        if (!res) return
        if (res.status === 200 && res.data.success) {
          toast(t('toast.unblocked'))
        } else {
          toast(res.data.error || t('toast.unblockFail'), true)
        }
      }
    )
  })

  function bindToggle(input, path, key, labelKey) {
    input.addEventListener('change', function () {
      var value = input.checked
      var body = {}
      body[key] = value
      withBusy(api(path, { method: 'POST', body: JSON.stringify(body) })).then(
        function (res) {
          if (!res) return
          var label = t(labelKey)
          if (res.status === 200 && res.data.success !== false) {
            toast(t(value ? 'toast.toggleOn' : 'toast.toggleOff', { label: label }))
          } else {
            input.checked = !value
            toast(res.data.error || t('toast.toggleFail', { label: label }), true)
          }
        }
      )
    })
  }

  bindToggle(els.tunToggle, '/api/v1/tun', 'enabled', 'options.tun')
  bindToggle(els.killswitchToggle, '/api/v1/killswitch', 'enabled', 'options.ks')

  els.importForm.addEventListener('submit', function (e) {
    e.preventDefault()
    var link = (els.importInput.value || '').trim()
    els.importMsg.hidden = true
    if (!link) {
      els.importMsg.textContent = t('import.enter')
      els.importMsg.className = 'form-error'
      els.importMsg.hidden = false
      return
    }
    els.importBtn.disabled = true
    api('/api/v1/import', { method: 'POST', body: JSON.stringify({ link: link }) })
      .then(function (res) {
        if (res.status === 200 && res.data.success) {
          els.importMsg.textContent = t('import.saved')
          els.importMsg.className = 'form-error ok'
          els.importInput.value = ''
          fetchProfiles()
        } else {
          els.importMsg.textContent = res.data.error || t('import.failed')
          els.importMsg.className = 'form-error'
        }
        els.importMsg.hidden = false
        return poll()
      })
      .catch(function () {
        els.importMsg.textContent = t('toast.netErr')
        els.importMsg.className = 'form-error'
        els.importMsg.hidden = false
      })
      .then(function () {
        els.importBtn.disabled = false
      })
  })

  els.tokenForm.addEventListener('submit', function (e) {
    e.preventDefault()
    var token = (els.tokenInput.value || '').trim()
    if (!token) return
    state.token = token
    api('/api/v1/status').then(function (res) {
      if (res.status === 200 && res.data.success) {
        sessionStorage.setItem(TOKEN_KEY, token)
        els.tokenInput.value = ''
        showPanel()
        startPolling()
        fetchProfiles()
      } else {
        state.token = null
        showLocked(t('lock.rejected'))
      }
    })
  })

  // Language toggle: cycle EN → RU → ZH, persist, re-render.
  if (els.langToggle) {
    els.langToggle.addEventListener('click', function () {
      var order = ['en', 'ru', 'zh']
      var idx = order.indexOf(state.lang)
      setLang(order[(idx + 1) % order.length])
    })
  }

  // Keep the canvas backing store aligned with its CSS size on resize.
  window.addEventListener('resize', function () {
    if (!els.heroGraph.hidden) drawGraph()
  })

  // ----- routing rules -----

  function fetchRouteRules() {
    return api('/api/v1/route-rules', { method: 'GET' }).then(function (res) {
      if (res.status === 200 && res.data && res.data.success) {
        state.lastRules = res.data.rules || []
        state.rulePresetsList = res.data.presets || []
        renderRules(state.lastRules)
        populatePresets()
      }
    })
  }

  function populatePresets() {
    if (!els.rulePresets) return
    els.rulePresets.textContent = ''
    state.rulePresetsList.forEach(function (p) {
      var opt = document.createElement('option')
      opt.value = p.value
      opt.dataset.type = p.type
      els.rulePresets.appendChild(opt)
    })
  }

  function renderRules(rules) {
    if (!els.rulesList) return
    els.rulesList.textContent = ''
    var list = (rules || []).slice()
    var hasRules = list.length > 0
    els.rulesList.hidden = !hasRules
    if (els.rulesEmpty) els.rulesEmpty.hidden = hasRules
    list.forEach(function (rule) {
      var li = document.createElement('li')
      li.className = 'rule-item'
      li.dataset.ruleId = rule.id || ''
      li.draggable = true

      var handle = document.createElement('span')
      handle.className = 'rule-handle'
      handle.textContent = '⋮⋮'
      handle.title = t('routes.dragHint')
      handle.setAttribute('aria-label', t('routes.drag'))
      li.appendChild(handle)

      var enabled = document.createElement('input')
      enabled.type = 'checkbox'
      enabled.checked = !!rule.enabled
      enabled.title = t('routes.enabled')
      enabled.addEventListener('change', function () {
        rule.enabled = enabled.checked
        putRouteRules(toast)
      })
      li.appendChild(enabled)

      var typeBadge = document.createElement('span')
      typeBadge.className = 'rule-badge rule-badge-type'
      typeBadge.textContent = rule.match ? t('routes.type.' + rule.match.type) : ''
      li.appendChild(typeBadge)

      var valueCell = document.createElement('span')
      valueCell.className = 'rule-value mono'
      valueCell.textContent = rule.match ? rule.match.value : ''
      li.appendChild(valueCell)

      var arrow = document.createElement('span')
      arrow.className = 'rule-arrow'
      arrow.textContent = '→'
      li.appendChild(arrow)

      var actionBadge = document.createElement('span')
      actionBadge.className =
        'rule-badge rule-badge-action rule-action-' + (rule.action || 'proxy')
      actionBadge.textContent = rule.action ? t('routes.action.' + rule.action) : ''
      li.appendChild(actionBadge)

      var edit = document.createElement('button')
      edit.type = 'button'
      edit.className = 'btn btn-ghost btn-small'
      edit.textContent = t('routes.edit')
      edit.addEventListener('click', function () {
        openRuleDialog(rule)
      })
      li.appendChild(edit)

      var del = document.createElement('button')
      del.type = 'button'
      del.className = 'btn btn-ghost btn-small'
      del.textContent = t('routes.delete')
      del.addEventListener('click', function () {
        if (!window.confirm(t('routes.delete') + '?')) return
        var newList = state.lastRules.filter(function (r) {
          return r.id !== rule.id
        })
        putRouteRules(function (ok, msg) {
          if (ok) {
            toast(t('routes.deleted'))
          } else if (msg) {
            toast(msg, true)
          }
        }, newList)
      })
      li.appendChild(del)

      // Drag and drop reordering
      li.addEventListener('dragstart', function (e) {
        state.draggedRuleId = rule.id
        e.dataTransfer.effectAllowed = 'move'
        e.dataTransfer.setData('text/plain', rule.id)
      })
      li.addEventListener('dragover', function (e) {
        e.preventDefault()
        e.dataTransfer.dropEffect = 'move'
      })
      li.addEventListener('drop', function (e) {
        e.preventDefault()
        var draggedId = state.draggedRuleId
        state.draggedRuleId = null
        if (!draggedId || draggedId === rule.id) return
        var order = state.lastRules.map(function (r) {
          return r.id
        })
        var fromPos = order.indexOf(draggedId)
        var toPos = order.indexOf(rule.id)
        if (fromPos === -1 || toPos === -1) return
        order.splice(fromPos, 1)
        order.splice(toPos, 0, draggedId)
        // Reorder state.lastRules accordingly and PUT.
        var byId = {}
        state.lastRules.forEach(function (r) {
          byId[r.id] = r
        })
        state.lastRules = order.map(function (id) {
          return byId[id]
        })
        renderRules(state.lastRules)
        putRouteRules(function (ok, msg) {
          if (!ok && msg) toast(msg, true)
        })
      })

      els.rulesList.appendChild(li)
    })
  }

  function putRouteRules(done, newList) {
    var payload = { rules: newList || state.lastRules || [] }
    api('/api/v1/route-rules', {
      method: 'PUT',
      body: JSON.stringify(payload),
    }).then(function (res) {
      var ok = res.status === 200 && res.data && res.data.success
      var msg =
        res.data && res.data.error
          ? t('routes.invalid', { msg: res.data.error })
          : ''
      if (ok) {
        state.lastRules = payload.rules
        renderRules(state.lastRules)
      }
      if (typeof done === 'function') done(ok, msg)
    })
  }

  function openRuleDialog(rule) {
    if (!els.ruleDialog) return
    state.ruleEditingId = rule && rule.id ? rule.id : null
    var title = els.ruleDialog.querySelector('#rule-dialog-title')
    if (title) title.textContent = rule ? t('routes.edit') : t('routes.add')
    if (els.ruleType) els.ruleType.value = rule && rule.match ? rule.match.type : 'domain'
    if (els.ruleValue) els.ruleValue.value = rule && rule.match ? rule.match.value : ''
    if (els.ruleAction) els.ruleAction.value = rule ? rule.action : 'proxy'
    if (els.ruleEnabled) els.ruleEnabled.checked = rule ? !!rule.enabled : true
    if (els.ruleDialogError) {
      els.ruleDialogError.hidden = true
      els.ruleDialogError.textContent = ''
    }
    if (typeof els.ruleDialog.showModal === 'function') {
      els.ruleDialog.showModal()
    }
  }

  function closeRuleDialog() {
    if (els.ruleDialog && typeof els.ruleDialog.close === 'function') {
      els.ruleDialog.close()
    }
    state.ruleEditingId = null
  }

  function handleRuleFormSubmit(e) {
    e.preventDefault()
    if (!els.ruleType || !els.ruleValue || !els.ruleAction) return
    var mType = els.ruleType.value
    var value = els.ruleValue.value.trim()
    var action = els.ruleAction.value
    var enabled = els.ruleEnabled ? els.ruleEnabled.checked : true
    if (!value) {
      if (els.ruleDialogError) {
        els.ruleDialogError.textContent = t('routes.invalid', {
          msg: t('routes.valueRequired'),
        })
        els.ruleDialogError.hidden = false
      }
      return
    }
    var rule = {
      enabled: enabled,
      action: action,
      match: { type: mType, value: value },
    }
    var list = state.lastRules.slice()
    if (state.ruleEditingId) {
      list = list.map(function (r) {
        if (r.id !== state.ruleEditingId) return r
        var merged = Object.assign({}, r, rule)
        return merged
      })
    } else {
      rule.id = 'tmp_' + Date.now()
      list.push(rule)
    }
    putRouteRules(function (ok, msg) {
      if (ok) {
        toast(t('routes.saved'))
        closeRuleDialog()
      } else if (msg && els.ruleDialogError) {
        els.ruleDialogError.textContent = msg
        els.ruleDialogError.hidden = false
      }
    }, list)
  }

  if (els.rulesAddBtn) {
    els.rulesAddBtn.addEventListener('click', function () {
      openRuleDialog(null)
    })
  }
  if (els.ruleForm) {
    els.ruleForm.addEventListener('submit', handleRuleFormSubmit)
  }
  if (els.ruleCancel) {
    els.ruleCancel.addEventListener('click', function () {
      closeRuleDialog()
    })
  }

  // ----- init -----

  state.lang = detectLang()
  applyStaticI18n()
  state.token = loadToken()
  if (state.token) {
    startPolling()
    fetchProfiles()
    fetchRouteRules()
  } else {
    showLocked(null)
  }
})()
