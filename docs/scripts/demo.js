/*
 * Landing page interactivity: the Deck+phone connection demo loop,
 * scroll-reveal animations, hero stat count-ups and nav scroll state.
 * No dependencies, no build step; honors prefers-reduced-motion.
 */
(function () {
  'use strict'

  var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

  // ----- nav scroll state -----
  var nav = document.getElementById('site-nav')
  function onScroll() {
    if (nav) nav.classList.toggle('is-scrolled', window.scrollY > 8)
  }
  window.addEventListener('scroll', onScroll, { passive: true })
  onScroll()

  // ----- scroll reveal -----
  var revealEls = Array.prototype.slice.call(document.querySelectorAll('.reveal'))
  if ('IntersectionObserver' in window && !reducedMotion) {
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-in')
            io.unobserve(entry.target)
          }
        })
      },
      { threshold: 0.12 }
    )
    revealEls.forEach(function (el) {
      io.observe(el)
    })
  } else {
    revealEls.forEach(function (el) {
      el.classList.add('is-in')
    })
  }

  // ----- hero stat count-up -----
  function countUp(el) {
    var target = parseInt(el.getAttribute('data-countup'), 10) || 0
    if (reducedMotion) {
      el.textContent = String(target)
      return
    }
    var start = null
    var duration = 1200
    function tick(ts) {
      if (start === null) start = ts
      var progress = Math.min((ts - start) / duration, 1)
      // ease-out cubic
      var eased = 1 - Math.pow(1 - progress, 3)
      el.textContent = String(Math.round(target * eased))
      if (progress < 1) window.requestAnimationFrame(tick)
    }
    window.requestAnimationFrame(tick)
  }
  Array.prototype.forEach.call(document.querySelectorAll('[data-countup]'), countUp)

  // ----- demo scene -----
  var demo = document.getElementById('demo')
  if (!demo) return

  function el(name) {
    return demo.querySelector('[data-demo="' + name + '"]')
  }
  var refs = {
    deckStatus: el('deck-status'),
    deckDown: el('deck-down'),
    deckUp: el('deck-up'),
    deckLat: el('deck-lat'),
    phonePill: el('phone-pill'),
    phoneStatus: el('phone-status'),
    phoneSub: el('phone-sub'),
    phoneDown: el('phone-down'),
    phoneUp: el('phone-up'),
    lineDown: el('line-down'),
    lineUp: el('line-up'),
    lat1: el('lat-1'),
    lat2: el('lat-2'),
    lat3: el('lat-3'),
  }

  var GRAPH_POINTS = 34
  var downHistory = []
  var upHistory = []
  var timers = []
  var speedTimer = null

  function fmtSpeed(kb) {
    if (kb >= 1024) return (kb / 1024).toFixed(1) + ' MB/s'
    return Math.round(kb) + ' KB/s'
  }

  function polyline(history, max) {
    // Map history onto the 100x26 viewBox, newest point on the right.
    var points = []
    for (var i = 0; i < history.length; i++) {
      var x = (i / (GRAPH_POINTS - 1)) * 100
      var y = 25 - (history[i] / max) * 22
      points.push(x.toFixed(1) + ',' + y.toFixed(1))
    }
    return points.join(' ')
  }

  function renderGraph() {
    var max = 1
    var i
    for (i = 0; i < downHistory.length; i++) max = Math.max(max, downHistory[i])
    for (i = 0; i < upHistory.length; i++) max = Math.max(max, upHistory[i])
    refs.lineDown.setAttribute('points', polyline(downHistory, max))
    refs.lineUp.setAttribute('points', polyline(upHistory, max))
  }

  function setSpeeds(down, up) {
    var d = fmtSpeed(down)
    var u = fmtSpeed(up)
    refs.deckDown.textContent = d
    refs.deckUp.textContent = u
    refs.phoneDown.textContent = d
    refs.phoneUp.textContent = u
  }

  function setState(state) {
    demo.setAttribute('data-state', state)
  }

  function toIdle() {
    setState('idle')
    refs.deckStatus.textContent = 'Disconnected'
    refs.phoneStatus.textContent = 'Disconnected'
    refs.phoneSub.textContent = 'Proxy is idle'
    refs.phonePill.textContent = 'OFFLINE'
    refs.deckLat.textContent = '— ms'
    refs.lat1.textContent = '—'
    refs.lat2.textContent = '—'
    refs.lat3.textContent = '—'
    setSpeeds(0, 0)
    downHistory = []
    upHistory = []
    renderGraph()
  }

  function toConnecting() {
    setState('connecting')
    refs.deckStatus.textContent = 'Connecting…'
    refs.phoneStatus.textContent = 'Connecting…'
    refs.phoneSub.textContent = 'Starting xray-core'
    refs.phonePill.textContent = 'CONNECTING'
  }

  function toConnected() {
    setState('connected')
    refs.deckStatus.textContent = 'Connected'
    refs.phoneStatus.textContent = 'Connected'
    refs.phoneSub.textContent = 'Traffic is routed through the proxy'
    refs.phonePill.textContent = 'CONNECTED'
    refs.deckLat.textContent = '38 ms'
    refs.lat1.textContent = '38 ms'
    refs.lat2.textContent = '72 ms'
    refs.lat3.textContent = '95 ms'

    // Live speed simulation: a busy download with a lighter upload.
    var down = 340
    var up = 60
    speedTimer = window.setInterval(function () {
      down = Math.max(120, Math.min(2400, down + (Math.random() - 0.45) * 320))
      up = Math.max(20, Math.min(320, up + (Math.random() - 0.45) * 60))
      setSpeeds(down, up)
      downHistory.push(down)
      upHistory.push(up)
      if (downHistory.length > GRAPH_POINTS) downHistory.shift()
      if (upHistory.length > GRAPH_POINTS) upHistory.shift()
      renderGraph()
    }, 380)
  }

  function stopSpeeds() {
    if (speedTimer !== null) {
      window.clearInterval(speedTimer)
      speedTimer = null
    }
  }

  function schedule(fn, ms) {
    timers.push(window.setTimeout(fn, ms))
  }

  function runLoop() {
    toIdle()
    schedule(toConnecting, 1600)
    schedule(toConnected, 3400)
    schedule(function () {
      stopSpeeds()
      runLoop()
    }, 13000)
  }

  if (reducedMotion) {
    // Static "connected" snapshot — no loop, no timers.
    toIdle()
    toConnected()
    stopSpeeds()
    setSpeeds(860, 120)
    downHistory = [300, 520, 480, 700, 640, 900, 820, 760, 880, 860]
    upHistory = [60, 90, 80, 120, 100, 140, 120, 110, 130, 120]
    renderGraph()
  } else {
    // Pause the loop while the demo is off-screen (battery friendliness).
    var running = false
    function start() {
      if (running) return
      running = true
      runLoop()
    }
    function stop() {
      running = false
      stopSpeeds()
      timers.forEach(window.clearTimeout)
      timers = []
    }
    if ('IntersectionObserver' in window) {
      var demoIo = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) start()
            else stop()
          })
        },
        { threshold: 0.2 }
      )
      demoIo.observe(demo)
    } else {
      start()
    }
  }
})()
