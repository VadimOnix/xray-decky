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
  'layout.status': 'Status',
  'layout.reset': 'Reset configuration',
  'layout.helpStatus': 'Help: status',
  'layout.helpReset': 'Help: reset configuration',
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
  'layout.status': 'Статус',
  'layout.reset': 'Сброс конфигурации',
  'layout.helpStatus': 'Справка: статус',
  'layout.helpReset': 'Справка: сброс конфигурации',
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
