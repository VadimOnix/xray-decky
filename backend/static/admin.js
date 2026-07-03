/* Xray Decky admin panel client. Vanilla JS, no build step. */
;(function () {
  'use strict'

  var POLL_INTERVAL_MS = 3000
  var TOKEN_KEY = 'xray-decky-admin-token'

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
    serverProtocol: document.getElementById('server-protocol'),
    serverEmpty: document.getElementById('server-empty'),
    serverInfo: document.getElementById('server-info'),
    serverName: document.getElementById('server-name'),
    serverAddress: document.getElementById('server-address'),
    serverNetwork: document.getElementById('server-network'),
    serverSecurity: document.getElementById('server-security'),
    serverImported: document.getElementById('server-imported'),
    tunToggle: document.getElementById('tun-toggle'),
    killswitchToggle: document.getElementById('killswitch-toggle'),
    optionsNote: document.getElementById('options-note'),
    importForm: document.getElementById('import-form'),
    importInput: document.getElementById('import-input'),
    importBtn: document.getElementById('import-btn'),
    importMsg: document.getElementById('import-msg'),
    toast: document.getElementById('toast'),
  }

  var state = {
    token: null,
    status: 'unknown',
    busy: false,
    pollTimer: null,
    toastTimer: null,
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

  var STATUS_TEXT = {
    connected: ['Connected', 'Traffic is routed through the proxy'],
    connecting: ['Connecting…', 'Starting xray-core'],
    disconnected: ['Disconnected', 'Proxy is idle'],
    error: ['Error', 'Something went wrong'],
    blocked: ['Blocked', 'Kill switch is active — traffic is stopped'],
    unknown: ['Loading…', 'Fetching current status'],
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
    var connection = data.connection || {}
    var status = connection.status || 'unknown'
    state.status = status

    var text = STATUS_TEXT[status] || STATUS_TEXT.unknown
    els.statusPill.dataset.status = status
    els.statusPillText.textContent = text[0]
    els.statusOrb.dataset.status = status
    els.heroTitle.textContent = text[0]

    var sub = text[1]
    if (status === 'connected') {
      var uptime = formatUptime(connection.uptime)
      if (uptime) sub = 'Up for ' + uptime
    } else if (status === 'error' && connection.errorMessage) {
      sub = connection.errorMessage
    }
    els.heroSub.textContent = sub

    var hasConfig = Boolean(data.config)
    var connectable = status === 'disconnected' || status === 'error'
    els.connectBtn.disabled = state.busy || (!connectable && status !== 'connected') || (connectable && !hasConfig)
    if (status === 'connected') {
      els.connectBtn.dataset.mode = 'disconnect'
      els.connectBtnLabel.textContent = 'Disconnect'
    } else {
      delete els.connectBtn.dataset.mode
      els.connectBtnLabel.textContent = 'Connect'
    }
    els.unblockBtn.hidden = status !== 'blocked'

    // Server card
    var config = data.config
    if (config) {
      els.serverEmpty.hidden = true
      els.serverInfo.hidden = false
      els.serverProtocol.hidden = false
      els.serverProtocol.textContent = config.protocol || 'vless'
      els.serverName.textContent = config.name || '—'
      els.serverAddress.textContent =
        (config.address || '?') + ':' + (config.port || '?')
      els.serverNetwork.textContent = config.network || 'tcp'
      els.serverSecurity.textContent = config.security || 'none'
      els.serverImported.textContent = config.importedAt
        ? new Date(config.importedAt * 1000).toLocaleString()
        : '—'
    } else {
      els.serverEmpty.hidden = false
      els.serverInfo.hidden = true
      els.serverProtocol.hidden = true
    }

    // Options
    if (!state.busy) {
      els.tunToggle.checked = Boolean(data.tun && data.tun.enabled)
      els.killswitchToggle.checked = Boolean(data.killSwitch && data.killSwitch.enabled)
    }
    if (data.tun && data.tun.enabled && !data.tun.hasPrivileges) {
      els.optionsNote.textContent =
        'TUN mode is enabled but privileges are missing — see INSTALLATION.md on the Deck.'
      els.optionsNote.hidden = false
    } else {
      els.optionsNote.hidden = true
    }
  }

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
        showLocked('Session expired or token is invalid. Pair again.')
        return
      }
      if (res.status === 200 && res.data.success) {
        showPanel()
        render(res.data)
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
        toast('Network error', true)
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
        toast(enable ? 'Connected' : 'Disconnected')
      } else {
        toast(res.data.error || 'Action failed', true)
      }
    })
  })

  els.unblockBtn.addEventListener('click', function () {
    withBusy(api('/api/v1/killswitch/deactivate', { method: 'POST' })).then(
      function (res) {
        if (!res) return
        if (res.status === 200 && res.data.success) {
          toast('Traffic unblocked')
        } else {
          toast(res.data.error || 'Failed to unblock', true)
        }
      }
    )
  })

  function bindToggle(input, path, key, label) {
    input.addEventListener('change', function () {
      var value = input.checked
      var body = {}
      body[key] = value
      withBusy(api(path, { method: 'POST', body: JSON.stringify(body) })).then(
        function (res) {
          if (!res) return
          if (res.status === 200 && res.data.success !== false) {
            toast(label + (value ? ' enabled' : ' disabled'))
          } else {
            input.checked = !value
            toast(res.data.error || 'Failed to toggle ' + label, true)
          }
        }
      )
    })
  }

  bindToggle(els.tunToggle, '/api/v1/tun', 'enabled', 'TUN mode')
  bindToggle(els.killswitchToggle, '/api/v1/killswitch', 'enabled', 'Kill switch')

  els.importForm.addEventListener('submit', function (e) {
    e.preventDefault()
    var link = (els.importInput.value || '').trim()
    els.importMsg.hidden = true
    if (!link) {
      els.importMsg.textContent = 'Please enter a share link'
      els.importMsg.className = 'form-error'
      els.importMsg.hidden = false
      return
    }
    els.importBtn.disabled = true
    api('/api/v1/import', { method: 'POST', body: JSON.stringify({ link: link }) })
      .then(function (res) {
        if (res.status === 200 && res.data.success) {
          els.importMsg.textContent = 'Saved.'
          els.importMsg.className = 'form-error ok'
          els.importInput.value = ''
        } else {
          els.importMsg.textContent = res.data.error || 'Import failed'
          els.importMsg.className = 'form-error'
        }
        els.importMsg.hidden = false
        return poll()
      })
      .catch(function () {
        els.importMsg.textContent = 'Network error'
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
      } else {
        state.token = null
        showLocked('That token was rejected. Check the QR code in the plugin.')
      }
    })
  })

  // ----- init -----

  state.token = loadToken()
  if (state.token) {
    startPolling()
  } else {
    showLocked(null)
  }
})()
