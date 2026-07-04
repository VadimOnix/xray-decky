/**
 * Minimal i18n for the QAM UI (EN / RU).
 *
 * The language is detected once from the Steam client locale
 * (`navigator.language`) — `ru*` → Russian, otherwise English. There is no
 * runtime toggle here (unlike the web admin panel), so `t()` is a pure
 * function and components need no re-render wiring. A missing key falls back
 * to English, then to the key itself.
 */

export type Lang = 'en' | 'ru';

type Dict = Record<string, string>;

const en: Dict = {
  'status.title': 'Connection status',
  'status.connected': 'Connected',
  'status.connecting': 'Connecting...',
  'status.error': 'Error',
  'status.blocked': 'Blocked (Kill Switch)',
  'status.disconnected': 'Disconnected',
  'status.uptime': 'Uptime',
  'status.connectedAt': 'Connected at',
  'status.speed': 'Speed',
  'status.total': 'total',
  'status.errorLabel': 'Error',
  'status.killSwitch': 'Kill Switch',
  'status.blockedMsg': 'All traffic is blocked. Reconnect to restore.',

  'conn.enable': 'Enable connection',
  'conn.blockedDesc': 'Kill switch is active. Disable it to reconnect.',
  'conn.connecting': 'Connecting…',
  'conn.disconnecting': 'Disconnecting…',
  'conn.active': 'Proxy is active.',
  'conn.inactive': 'Proxy is inactive',
  'conn.toggleFail': 'Failed to toggle connection',
  'conn.netErr': 'Network error. Please check your connection and try again.',
  'conn.errorLabel': 'Error:',
  'conn.ksActiveLabel': 'Kill Switch Active:',
  'conn.ksActiveMsg': 'Connection is blocked. Please disable kill switch first.',

  'servers.offline': 'offline',
  'servers.unnamed': 'Unnamed server',
  'servers.menuLabel': 'Servers',
  'servers.pingAll': 'Ping all servers',
  'servers.server': 'Server',
  'servers.select': 'Select a server',
  'servers.pingHint': 'Press ✕ / … on the picker to ping all servers.',

  'tabs.connection': 'Connection',
  'tabs.config': 'Config',
  'tabs.options': 'Options',
  'setup.title': 'Setup',
  'layout.status': 'Status',
  'layout.reset': 'Reset configuration',
  'layout.helpStatus': 'Help: status',
  'layout.helpReset': 'Help: reset configuration',

  'common.netErr': 'Network error. Please check your connection and try again.',
  'common.errorLabel': 'Error:',

  'tun.title': 'TUN Mode',
  'tun.help': 'Help: TUN mode',
  'tun.enable': 'Enable TUN Mode',
  'tun.enableDesc': 'Routes all system traffic through the proxy.',
  'tun.privReqLabel': 'Privileges Required:',
  'tun.privReqMsg': 'TUN mode requires elevated privileges.',
  'tun.privSteps':
    'Please complete the installation steps to enable TUN mode. See INSTALLATION.md for details.',
  'tun.checking': 'Checking...',
  'tun.checkPriv': 'Check Privileges',
  'tun.checkFail': 'Failed to check privileges. Please try again.',
  'tun.toggleFail': 'Failed to toggle TUN mode',
  'tun.enabled': '✓ TUN Mode Enabled',
  'tun.activeOn': 'Active on interface: {iface}',
  'tun.connectToActivate': 'Connect to proxy to activate TUN mode.',
  'tun.disabling': 'Disabling TUN mode...',
  'tun.enabling': 'Enabling TUN mode...',

  'ks.title': 'Kill Switch',
  'ks.help': 'Help: Kill switch',
  'ks.enable': 'Enable Kill Switch',
  'ks.enableDesc': 'Blocks all traffic if the proxy disconnects unexpectedly.',
  'ks.toggleFail': 'Failed to toggle kill switch',
  'ks.deactivateFail': 'Failed to deactivate kill switch',
  'ks.activeTitle': '⚠️ KILL SWITCH ACTIVE',
  'ks.activeMsg':
    'All system traffic is currently blocked. This happened because the proxy disconnected unexpectedly.',
  'ks.activatedAt': 'Activated at: {time}',
  'ks.deactivating': 'Deactivating...',
  'ks.deactivate': 'Deactivate Kill Switch',
  'ks.enabledTitle': '✓ Kill Switch Enabled',
  'ks.enabledMsg': 'Traffic will be blocked if the proxy disconnects unexpectedly.',
  'ks.disabling': 'Disabling kill switch...',
  'ks.enabling': 'Enabling kill switch...',

  'import.saving': 'Saving…',
  'import.save': 'Save configuration',
  'import.shareLink': 'Share link',
  'import.shareDesc':
    'Paste a vless://, vmess://, trojan:// or ss:// link. We validate it before saving.',
  'import.helpShare': 'Help: share link',
  'import.successLabel': 'Success:',
  'import.saveDesc': 'Save the VLESS link and switch to the configured layout.',

  'qr.title': 'Import via QR',
  'qr.help': 'Help: QR import',
  'qr.loading': 'Loading import address…',
  'qr.desc': 'Scan with your phone or open the link below to import your proxy configuration.',
  'qr.importUrl': 'Import URL',
  'qr.helpLan': 'Help: LAN address',

  'admin.title': 'Admin panel',
  'admin.help': 'Help: admin panel',
  'admin.loading': 'Loading admin panel address…',
  'admin.desc': 'Scan with your phone to manage the proxy from a browser on the same network.',
  'admin.url': 'Admin URL',

  'summary.valid': 'Valid',
  'summary.invalid': 'Invalid',
  'summary.name': 'Name',
  'summary.endpoint': 'Endpoint',
  'summary.status': 'Status',
  'summary.validationError': 'Validation error',
  'summary.source': 'Source',

  'reset.resetting': 'Resetting…',
  'reset.reset': 'Reset configuration',
  'reset.disabledDesc': 'Disconnect before resetting configuration.',
  'reset.desc': 'Clears the saved proxy link and returns to setup.',
  'reset.fail': 'Failed to reset configuration',
  'reset.netErr': 'Network error. Please try again.',

  'help.setup.qr_import.title': 'QR import',
  'help.setup.qr_import.body':
    'Scan the QR code with your phone to open the import page on the same LAN.',
  'help.setup.lan_address.title': 'LAN address',
  'help.setup.lan_address.body': 'Open the import URL from a device on the same local network.',
  'help.setup.vless_link.title': 'Share link',
  'help.setup.vless_link.body':
    'Paste a vless://, vmess://, trojan:// or ss:// link, or a subscription URL (https://). Invalid links are rejected and do not overwrite a valid config.',
  'help.configured.status.title': 'Status meanings',
  'help.configured.status.body':
    'Connected: proxy active. Connecting: starting up. Blocked: kill switch active. Disconnected: idle.',
  'help.configured.reset.title': 'Reset configuration',
  'help.configured.reset.body':
    'Clears the saved configuration and returns to setup. Disabled while the connection is active.',
  'help.options.tun_mode.title': 'TUN mode',
  'help.options.tun_mode.body':
    'Routes all system traffic through the proxy. Requires elevated privileges from INSTALLATION.md.',
  'help.options.kill_switch.title': 'Kill switch',
  'help.options.kill_switch.body':
    'Blocks all traffic if the proxy disconnects unexpectedly. Enable only if you want strict leak prevention.',
  'help.options.admin_panel.title': 'Admin panel',
  'help.options.admin_panel.body':
    'Full management UI in a browser on the same LAN. The QR code embeds a per-install access token - do not share it.',
};

const ru: Dict = {
  'status.title': 'Статус подключения',
  'status.connected': 'Подключено',
  'status.connecting': 'Подключение…',
  'status.error': 'Ошибка',
  'status.blocked': 'Заблокировано (Kill Switch)',
  'status.disconnected': 'Отключено',
  'status.uptime': 'В сети',
  'status.connectedAt': 'Подключено в',
  'status.speed': 'Скорость',
  'status.total': 'всего',
  'status.errorLabel': 'Ошибка',
  'status.killSwitch': 'Kill Switch',
  'status.blockedMsg': 'Весь трафик заблокирован. Переподключитесь для восстановления.',

  'conn.enable': 'Подключение',
  'conn.blockedDesc': 'Kill switch активен. Отключите его для переподключения.',
  'conn.connecting': 'Подключение…',
  'conn.disconnecting': 'Отключение…',
  'conn.active': 'Прокси активен.',
  'conn.inactive': 'Прокси неактивен',
  'conn.toggleFail': 'Не удалось переключить подключение',
  'conn.netErr': 'Ошибка сети. Проверьте подключение и повторите попытку.',
  'conn.errorLabel': 'Ошибка:',
  'conn.ksActiveLabel': 'Kill Switch активен:',
  'conn.ksActiveMsg': 'Подключение заблокировано. Сначала отключите kill switch.',

  'servers.offline': 'недоступен',
  'servers.unnamed': 'Без имени',
  'servers.menuLabel': 'Серверы',
  'servers.pingAll': 'Пинговать все',
  'servers.server': 'Сервер',
  'servers.select': 'Выберите сервер',
  'servers.pingHint': 'Нажмите ✕ / … на списке, чтобы пропинговать все серверы.',

  'tabs.connection': 'Подключение',
  'tabs.config': 'Конфиг',
  'tabs.options': 'Опции',
  'setup.title': 'Настройка',
  'layout.status': 'Статус',
  'layout.reset': 'Сброс конфигурации',
  'layout.helpStatus': 'Справка: статус',
  'layout.helpReset': 'Справка: сброс конфигурации',

  'common.netErr': 'Ошибка сети. Проверьте подключение и повторите попытку.',
  'common.errorLabel': 'Ошибка:',

  'tun.title': 'Режим TUN',
  'tun.help': 'Справка: режим TUN',
  'tun.enable': 'Включить режим TUN',
  'tun.enableDesc': 'Направляет весь системный трафик через прокси.',
  'tun.privReqLabel': 'Требуются права:',
  'tun.privReqMsg': 'Режиму TUN нужны повышенные права.',
  'tun.privSteps':
    'Выполните шаги установки, чтобы включить режим TUN. Подробности в INSTALLATION.md.',
  'tun.checking': 'Проверка…',
  'tun.checkPriv': 'Проверить права',
  'tun.checkFail': 'Не удалось проверить права. Повторите попытку.',
  'tun.toggleFail': 'Не удалось переключить режим TUN',
  'tun.enabled': '✓ Режим TUN включён',
  'tun.activeOn': 'Активен на интерфейсе: {iface}',
  'tun.connectToActivate': 'Подключитесь к прокси, чтобы активировать режим TUN.',
  'tun.disabling': 'Отключение режима TUN…',
  'tun.enabling': 'Включение режима TUN…',

  'ks.title': 'Kill Switch',
  'ks.help': 'Справка: Kill switch',
  'ks.enable': 'Включить Kill Switch',
  'ks.enableDesc': 'Блокирует весь трафик при внезапном отключении прокси.',
  'ks.toggleFail': 'Не удалось переключить kill switch',
  'ks.deactivateFail': 'Не удалось отключить kill switch',
  'ks.activeTitle': '⚠️ KILL SWITCH АКТИВЕН',
  'ks.activeMsg': 'Весь системный трафик заблокирован — прокси внезапно отключился.',
  'ks.activatedAt': 'Активирован: {time}',
  'ks.deactivating': 'Отключение…',
  'ks.deactivate': 'Отключить Kill Switch',
  'ks.enabledTitle': '✓ Kill Switch включён',
  'ks.enabledMsg': 'Трафик будет заблокирован при внезапном отключении прокси.',
  'ks.disabling': 'Отключение kill switch…',
  'ks.enabling': 'Включение kill switch…',

  'import.saving': 'Сохранение…',
  'import.save': 'Сохранить конфигурацию',
  'import.shareLink': 'Ссылка',
  'import.shareDesc':
    'Вставьте ссылку vless://, vmess://, trojan:// или ss://. Мы проверим её перед сохранением.',
  'import.helpShare': 'Справка: ссылка',
  'import.successLabel': 'Успех:',
  'import.saveDesc': 'Сохранить ссылку и перейти к настроенному виду.',

  'qr.title': 'Импорт по QR',
  'qr.help': 'Справка: импорт по QR',
  'qr.loading': 'Загрузка адреса импорта…',
  'qr.desc': 'Отсканируйте телефоном или откройте ссылку ниже, чтобы импортировать конфигурацию.',
  'qr.importUrl': 'Ссылка импорта',
  'qr.helpLan': 'Справка: адрес в сети',

  'admin.title': 'Панель управления',
  'admin.help': 'Справка: панель управления',
  'admin.loading': 'Загрузка адреса панели…',
  'admin.desc': 'Отсканируйте телефоном, чтобы управлять прокси из браузера в той же сети.',
  'admin.url': 'Адрес панели',

  'summary.valid': 'Действителен',
  'summary.invalid': 'Недействителен',
  'summary.name': 'Имя',
  'summary.endpoint': 'Адрес',
  'summary.status': 'Статус',
  'summary.validationError': 'Ошибка проверки',
  'summary.source': 'Источник',

  'reset.resetting': 'Сброс…',
  'reset.reset': 'Сброс конфигурации',
  'reset.disabledDesc': 'Отключитесь перед сбросом конфигурации.',
  'reset.desc': 'Удаляет сохранённую ссылку и возвращает к настройке.',
  'reset.fail': 'Не удалось сбросить конфигурацию',
  'reset.netErr': 'Ошибка сети. Повторите попытку.',

  'help.setup.qr_import.title': 'Импорт по QR',
  'help.setup.qr_import.body':
    'Отсканируйте QR-код телефоном, чтобы открыть страницу импорта в той же сети.',
  'help.setup.lan_address.title': 'Адрес в сети',
  'help.setup.lan_address.body': 'Откройте ссылку импорта с устройства в той же локальной сети.',
  'help.setup.vless_link.title': 'Ссылка',
  'help.setup.vless_link.body':
    'Вставьте ссылку vless://, vmess://, trojan:// или ss:// либо URL подписки (https://). Неверные ссылки отклоняются и не затирают рабочую конфигурацию.',
  'help.configured.status.title': 'Значения статусов',
  'help.configured.status.body':
    'Подключено: прокси активен. Подключение: запуск. Заблокировано: активен kill switch. Отключено: простой.',
  'help.configured.reset.title': 'Сброс конфигурации',
  'help.configured.reset.body':
    'Удаляет сохранённую конфигурацию и возвращает к настройке. Недоступно при активном подключении.',
  'help.options.tun_mode.title': 'Режим TUN',
  'help.options.tun_mode.body':
    'Направляет весь системный трафик через прокси. Требует повышенных прав из INSTALLATION.md.',
  'help.options.kill_switch.title': 'Kill switch',
  'help.options.kill_switch.body':
    'Блокирует весь трафик при внезапном отключении прокси. Включайте только для строгой защиты от утечек.',
  'help.options.admin_panel.title': 'Панель управления',
  'help.options.admin_panel.body':
    'Полноценный интерфейс управления в браузере в той же сети. QR-код содержит персональный токен доступа — не делитесь им.',
};

const dicts: Record<Lang, Dict> = { en, ru };

function detectLang(): Lang {
  try {
    const nav = typeof navigator !== 'undefined' ? navigator.language || 'en' : 'en';
    return nav.toLowerCase().startsWith('ru') ? 'ru' : 'en';
  } catch {
    return 'en';
  }
}

export const LANG: Lang = detectLang();

export function t(key: string, params?: Record<string, string | number>): string {
  let value = dicts[LANG][key] ?? en[key] ?? key;
  if (params) {
    for (const name of Object.keys(params)) {
      value = value.replace(`{${name}}`, String(params[name]));
    }
  }
  return value;
}
