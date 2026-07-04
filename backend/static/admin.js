/* Xray Decky admin panel client. Vanilla JS, no build step. */
;(function () {
  'use strict'

  var POLL_INTERVAL_MS = 3000
  var TOKEN_KEY = 'xray-decky-admin-token'
  // 40 samples at 3s each ≈ the last two minutes of traffic.
  var SPEED_HISTORY_MAX = 40

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
    speedHistory: [],
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
        formatBytes((stats.uplink || 0) + (stats.downlink || 0)) + ' total'
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

  // ----- server list -----

  function latencyBadge(profile) {
    var span = document.createElement('span')
    var ms = profile.latencyMs
    if (typeof ms === 'number') {
      span.textContent = ms + ' ms'
      span.className = 'latency ' + (ms < 150 ? 'good' : ms < 400 ? 'ok' : 'bad')
    } else if (profile.latencyTestedAt) {
      span.textContent = 'offline'
      span.className = 'latency bad'
    } else {
      span.textContent = '— ms'
      span.className = 'latency unknown'
    }
    return span
  }

  function renderProfiles(activeId, profiles) {
    els.serverList.textContent = ''
    var hasProfiles = profiles && profiles.length > 0
    els.serversEmpty.hidden = hasProfiles
    els.serverList.hidden = !hasProfiles
    if (!hasProfiles) return

    profiles.forEach(function (profile) {
      var li = document.createElement('li')
      var row = document.createElement('button')
      row.type = 'button'
      row.className = 'server-row' + (profile.id === activeId ? ' active' : '')
      row.setAttribute(
        'aria-label',
        'Activate ' + (profile.name || profile.address || 'server')
      )

      var chip = document.createElement('span')
      chip.className = 'chip chip-accent'
      // Keep chips narrow on phone screens.
      chip.textContent =
        profile.protocol === 'shadowsocks' ? 'ss' : profile.protocol || 'vless'

      var main = document.createElement('span')
      main.className = 'server-row-main'
      var name = document.createElement('span')
      name.className = 'server-row-name'
      name.textContent = profile.name || profile.address || 'Unnamed server'
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
      del.setAttribute('aria-label', 'Remove server')
      del.addEventListener('click', function (e) {
        e.stopPropagation()
        api('/api/v1/profiles/remove', {
          method: 'POST',
          body: JSON.stringify({ id: profile.id }),
        }).then(function (res) {
          if (res.status === 200 && res.data.success) {
            toast('Server removed')
            fetchProfiles()
          } else {
            toast(res.data.error || 'Failed to remove server', true)
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
            toast(
              res.data.reconnected
                ? 'Switched and reconnected'
                : 'Server activated'
            )
          } else {
            toast(res.data.error || 'Failed to switch server', true)
          }
          fetchProfiles()
        })
      })

      row.appendChild(chip)
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
        : 'unknown'
      els.subscriptionInfo.textContent =
        'Subscription · ' +
        (subscription.nodeCount || 0) +
        ' servers · updated ' +
        updated
      els.subscriptionRow.hidden = false
    } else {
      els.subscriptionRow.hidden = true
    }
  }

  function fetchProfiles() {
    return api('/api/v1/profiles')
      .then(function (res) {
        if (res.status === 200 && res.data.success) {
          renderProfiles(res.data.activeId, res.data.profiles || [])
          renderSubscription(res.data.subscription)
        }
      })
      .catch(function () {
        /* transient */
      })
  }

  els.refreshSubBtn.addEventListener('click', function () {
    els.refreshSubBtn.disabled = true
    els.refreshSubBtn.textContent = 'Refreshing…'
    api('/api/v1/subscription/refresh', { method: 'POST' })
      .then(function (res) {
        if (res.status === 200 && res.data.success) {
          toast('Subscription refreshed')
        } else {
          toast(res.data.error || 'Refresh failed', true)
        }
        return fetchProfiles()
      })
      .catch(function () {
        toast('Network error', true)
      })
      .then(function () {
        els.refreshSubBtn.disabled = false
        els.refreshSubBtn.textContent = 'Refresh'
      })
  })

  els.pingBtn.addEventListener('click', function () {
    els.pingBtn.disabled = true
    els.pingBtn.textContent = 'Pinging…'
    api('/api/v1/profiles/ping', { method: 'POST' })
      .then(function (res) {
        if (res.status === 200 && res.data.success) {
          toast('Latency updated')
        } else {
          toast(res.data.error || 'Ping failed', true)
        }
        return fetchProfiles()
      })
      .catch(function () {
        toast('Network error', true)
      })
      .then(function () {
        els.pingBtn.disabled = false
        els.pingBtn.textContent = 'Ping all'
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
        showLocked('Session expired or token is invalid. Pair again.')
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
          fetchProfiles()
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
        fetchProfiles()
      } else {
        state.token = null
        showLocked('That token was rejected. Check the QR code in the plugin.')
      }
    })
  })

  // Keep the canvas backing store aligned with its CSS size on resize.
  window.addEventListener('resize', function () {
    if (!els.heroGraph.hidden) drawGraph()
  })

  // ----- init -----

  state.token = loadToken()
  if (state.token) {
    startPolling()
    fetchProfiles()
  } else {
    showLocked(null)
  }
})()
