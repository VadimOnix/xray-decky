# Xray Decky — VPN и прокси-клиент для Steam Deck

[English](README.md) · **Русский** · [中文](README.zh-CN.md) · [فارسی](README.fa.md) · [Español](README.es.md)

Запустите VPN на своём Steam Deck — в том числе в игровом режиме (Gaming
Mode). Xray Decky — это плагин для [Decky Loader](https://wiki.deckbrew.xyz/):
полнофункциональный прокси-клиент (VLESS/VMess/Trojan/Shadowsocks/Hysteria2/TUIC),
чей режим TUN пропускает **весь** системный трафик через зашифрованный
туннель — покрытие в стиле VPN на уровне всей системы, которое не смогут
проигнорировать даже игры. В комплекте — мультисерверные подписки, веб-панель
администратора в стиле Steam, kill switch и статистика трафика в реальном
времени.

## Возможности

- **Широкая поддержка протоколов и транспортов** — импортирует **VLESS**
  (REALITY / XTLS-Vision), **VMess**, **Trojan** и **Shadowsocks** (включая
  шифры 2022) поверх RAW/TCP, WebSocket, gRPC, HTTPUpgrade, XHTTP и mKCP, с
  полным набором параметров TLS / REALITY / uTLS-фингерпринта. **Hysteria2**
  и **TUIC** работают на ядре sing-box, которое загружается по требованию.
- **Мультисерверные профили и подписки** — хранит множество серверов;
  импортирует URL подписки (base64 или списки ссылок в виде обычного текста)
  и обновляет её на месте. Вручную добавленные серверы сохраняются при
  обновлении, а квота трафика / срок действия от провайдера
  (`Subscription-Userinfo`) отображается, когда доступна.
- **Проверка задержки** — TCPing всех серверов с цветовой индикацией
  результатов по каждому серверу как в пикере QAM, так и в веб-панели.
- **Статистика трафика в реальном времени** — скорость загрузки / отдачи и
  итоги за сессию в QAM, а также график скорости в реальном времени в
  веб-панели.
- **Веб-панель администратора** — управляющий интерфейс в стиле Steam на
  телефоне/ПК (QR-сопряжение из QAM): статус в реальном времени + график
  скорости, список серверов, информация о подписке, импорт, переключатели
  TUN / kill switch и проверка обновлений ядра. Защищена случайным токеном
  для каждой установки с ограничением частоты неудачных попыток авторизации.
- **Меню быстрого доступа (Quick Access Menu)** — переключатель подключения,
  выбор сервера, статус/скорость в реальном времени, TUN + kill switch и
  QR-код панели администратора.
- **Английский / Русский** — и QAM, и веб-панель локализованы (определяются
  автоматически по локали Steam / браузера).
- **Переключение подключения** — включайте/выключайте прокси прямо из меню
  быстрого доступа.
- **Режим TUN** — общесистемная маршрутизация в стиле VPN через виртуальный
  сетевой интерфейс, **рекомендуется для игрового режима (Gaming Mode)**.
- **Kill Switch** — блокирует трафик при отключении прокси (опционально).
- **Отказоустойчивость** — падение xray-core обнаруживается мгновенно, и он
  перезапускается с нарастающей задержкой (backoff); маршруты TUN
  восстанавливаются после сна/пробуждения; закреплённое ядро
  самовосстанавливается, если неизменяемая файловая система стирает
  встроенный бинарник.

**Восстановление сети:** если на Deck пропала связь из-за некорректного
завершения работы плагина, запустите `sudo bash recover.sh` (поставляется в
папке плагина, также доступен по пути [defaults/recover.sh](defaults/recover.sh))
из терминала в Desktop Mode — скрипт удалит цепочку файрвола kill switch,
устаревшие маршруты TUN и системный прокси.

## Установка

**Требования:** Steam Deck с установленным [Decky Loader](https://wiki.deckbrew.xyz/).

- **Plugin Store (рекомендуется):** Decky Loader → Plugin Store → найдите «Xray Decky» → Install.
- **Desktop Mode (в один клик):** Скачайте [Install-Xray-Decky.desktop](https://raw.githubusercontent.com/VadimOnix/xray-decky/master/scripts/Install-Xray-Decky.desktop), сделайте файл исполняемым (Properties → Permissions), запустите двойным щелчком. См. [scripts/README.md](scripts/README.md).
- **Вручную:** Скачайте zip-архив [последнего релиза](https://github.com/VadimOnix/xray-decky/releases/latest) → Decky Loader → Settings → Developer → Install Plugin from URL → вставьте URL zip-архива.

**Режим TUN (рекомендуется):** В игровом режиме (Gaming Mode) Steam не
учитывает системные настройки SOCKS-прокси — игры и большинство системных
служб их игнорируют. Режим TUN создаёт виртуальный сетевой интерфейс,
который пропускает **весь** системный трафик через прокси, что делает его
единственным надёжным способом проксировать трафик в игровом режиме.
Включите TUN в настройках плагина — дополнительная настройка не требуется.

Без TUN плагин переключается на режим SOCKS-прокси, который работает в
Desktop Mode, но может не охватывать игры и системные службы в игровом
режиме.

**Использование, устранение неполадок и другое:** [документация на GitHub Pages](https://vadimonix.github.io/xray-decky/).

## Разработка

### Требования

- Node.js v16.14+
- pnpm v9 (обязательно)
- Python 3.x
- бинарник xray-core

### Настройка

```bash
pnpm install
pnpm run build
# Backend: pip install -r requirements-dev.txt
# xray-core: place in bin/xray-core
```

Тесты и линтеры (устройство не требуется): `pnpm test`, `pnpm run lint`,
`pytest tests/`, `ruff check py_modules/ tests/ main.py conftest.py`.
См. [Tests and linters](CONTRIBUTING.md#tests-and-linters).

### Структура проекта

```
├── src/                      # Frontend TypeScript/React
├── py_modules/backend/src/   # Backend Python, xray-core/sing-box managers
├── defaults/static/          # Embedded web admin panel (ships to plugin root)
├── defaults/recover.sh       # Network recovery script (ships to plugin root)
├── tests/                    # Python test suite (pytest)
├── tests/frontend/           # Frontend test suite (vitest: src/ + admin panel)
├── bin/                      # Local dev core binaries (xray-core, sing-box)
├── docs/                     # GitHub Pages (index.html, styles, assets)
├── main.py                   # Backend entry point
├── plugin.json
└── package.json
```

Подробнее см. [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) и [docs/RELEASING.md](docs/RELEASING.md).

## Лицензия

MIT — см. LICENSE.

## Ресурсы

- [Decky Loader](https://wiki.deckbrew.xyz/)
- [xray-core](https://xtls.github.io/)
- [Спецификация плагина](./specs/001-xray-vless-decky/spec.md)
