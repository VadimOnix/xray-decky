/* Xray Decky admin panel client. Vanilla JS, no build step. */
;(function () {
  'use strict'

  var POLL_INTERVAL_MS = 3000
  var TOKEN_KEY = 'xray-decky-admin-token'
  var LANG_KEY = 'xray-decky-admin-lang'
  // 40 samples at 3s each ≈ the last two minutes of traffic.
  var SPEED_HISTORY_MAX = 40

  // ----- i18n (EN / RU) -----

  var I18N = {
    en: {
      'lang.self': 'EN',
      'lang.switch': 'Switch to Russian',
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
      'graph.download': 'Download',
      'graph.upload': 'Upload',
      'graph.window': 'peak · last 2 min',
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
      'sub.info': 'Subscription · {n} servers · updated {date}',
      'sub.expires': 'expires {date}',
      'sub.refresh': 'Refresh',
      'sub.refreshing': 'Refreshing…',
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
        { mono: 'hysteria2://' },
        ' or ',
        { mono: 'tuic://' },
        ' link, a subscription URL (',
        { mono: 'https://…' },
        ') or its base64 content.',
      ],
      'import.ph': 'vless:// / vmess:// / trojan:// / ss:// / hysteria2:// / tuic://',
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
    },
    ru: {
      'lang.self': 'RU',
      'lang.switch': 'Переключить на английский',
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
      'graph.download': 'Загрузка',
      'graph.upload': 'Отдача',
      'graph.window': 'пик · за 2 мин',
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
      'sub.info': 'Подписка · серверов: {n} · обновлено {date}',
      'sub.expires': 'истекает {date}',
      'sub.refresh': 'Обновить',
      'sub.refreshing': 'Обновление…',
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
        { mono: 'hysteria2://' },
        ' или ',
        { mono: 'tuic://' },
        ', URL подписки (',
        { mono: 'https://…' },
        ') или её base64-содержимое.',
      ],
      'import.ph': 'vless:// / vmess:// / trojan:// / ss:// / hysteria2:// / tuic://',
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
    },
  }

  function detectLang() {
    var saved = window.localStorage.getItem(LANG_KEY)
    if (saved === 'en' || saved === 'ru') return saved
    var nav = (window.navigator.language || 'en').toLowerCase()
    return nav.indexOf('ru') === 0 ? 'ru' : 'en'
  }

  function t(key, params) {
    var dict = I18N[state.lang] || I18N.en
    var str = dict[key]
    if (str === undefined) str = I18N.en[key] !== undefined ? I18N.en[key] : key
    if (params) {
      Object.keys(params).forEach(function (k) {
        str = str.replace('{' + k + '}', params[k])
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
    toast: document.getElementById('toast'),
    langToggle: document.getElementById('lang-toggle'),
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
    if (h > 0) return h + 'h ' + m + 'm'
    if (m > 0) return m + 'm ' + s + 's'
    return s + 's'
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
        t('servers.activate', { name: profile.name || profile.address || 'server' })
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
        t('sub.info', { n: subscription.nodeCount || 0, date: updated }),
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

  // Language toggle: flip EN ↔ RU, persist, re-render.
  if (els.langToggle) {
    els.langToggle.addEventListener('click', function () {
      setLang(state.lang === 'ru' ? 'en' : 'ru')
    })
  }

  // Keep the canvas backing store aligned with its CSS size on resize.
  window.addEventListener('resize', function () {
    if (!els.heroGraph.hidden) drawGraph()
  })

  // ----- init -----

  state.lang = detectLang()
  applyStaticI18n()
  state.token = loadToken()
  if (state.token) {
    startPolling()
    fetchProfiles()
  } else {
    showLocked(null)
  }
})()
