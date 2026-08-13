// Copy-to-clipboard for the donation addresses. Progressive enhancement: the
// full address is always on the page as selectable text, so nothing breaks if
// this never runs, and every failure path still leaves the address selected
// so the visitor can copy it by hand.
(function () {
  'use strict';

  var RESET_MS = 1600;

  /** Select the address next to a button — the fallback when writing fails. */
  function selectAddress(btn) {
    var code = btn.parentElement && btn.parentElement.querySelector('.donate-address');
    if (!code || !window.getSelection || !document.createRange) return;

    var range = document.createRange();
    range.selectNodeContents(code);
    var selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
  }

  /** Pre-Clipboard-API path, still the only one that works in some in-app browsers. */
  function legacyCopy(text) {
    var field = document.createElement('textarea');
    field.value = text;
    field.setAttribute('readonly', '');
    field.style.position = 'fixed';
    field.style.opacity = '0';
    document.body.appendChild(field);
    field.select();

    var ok = false;
    try {
      ok = document.execCommand('copy');
    } catch (err) {
      ok = false;
    }
    document.body.removeChild(field);
    return ok;
  }

  document.querySelectorAll('.donate-copy').forEach(function (btn) {
    var original = (btn.textContent || '').trim();
    var copiedLabel = btn.getAttribute('data-copied-label') || original;
    var timer;

    function confirmCopied() {
      btn.textContent = copiedLabel;
      btn.classList.add('is-copied');
      clearTimeout(timer);
      timer = setTimeout(function () {
        btn.textContent = original;
        btn.classList.remove('is-copied');
      }, RESET_MS);
    }

    btn.textContent = original;

    btn.addEventListener('click', function () {
      var address = btn.getAttribute('data-copy');
      if (!address) return;

      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(address).then(confirmCopied, function () {
          if (legacyCopy(address)) confirmCopied();
          else selectAddress(btn);
        });
        return;
      }

      if (legacyCopy(address)) confirmCopied();
      else selectAddress(btn);
    });
  });
})();
