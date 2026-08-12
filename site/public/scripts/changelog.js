/*
 * Changelog page: fetches CHANGELOG.md (Keep a Changelog format) straight
 * from the repository and renders it as a timeline. No build step — the
 * page is always as current as master.
 */
(function () {
  'use strict';

  var RAW_URL = 'https://raw.githubusercontent.com/VadimOnix/xray-decky/master/CHANGELOG.md';
  var RELEASE_URL = 'https://github.com/VadimOnix/xray-decky/releases/tag/v';

  var KNOWN_CATEGORIES = {
    added: 'cl-cat-added',
    fixed: 'cl-cat-fixed',
    changed: 'cl-cat-changed',
    security: 'cl-cat-security',
    removed: 'cl-cat-removed',
    deprecated: 'cl-cat-deprecated',
  };

  function escapeHtml(text) {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  /* Inline markdown: `code`, **bold**, *italic*, [text](url). Escapes HTML first. */
  function renderInline(text) {
    var html = escapeHtml(text);
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    html = html.replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>');
    html = html.replace(/\*([^*\s][^*]*)\*/g, '<i>$1</i>');
    html = html.replace(
      /\[([^\]]+)\]\((https?:[^)\s]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener">$1</a>'
    );
    return html;
  }

  /*
   * Parse the markdown into entries:
   *   [{ version, date, blocks: [{type: 'category'|'list'|'para'|'quote', ...}] }]
   * Bullets may continue on indented lines; those are joined into the item.
   */
  function parse(markdown) {
    var entries = [];
    var entry = null;
    var list = null;
    var quote = null;
    var lines = markdown.split('\n');

    function flushList() {
      if (list && entry) entry.blocks.push({ type: 'list', items: list });
      list = null;
    }
    function flushQuote() {
      if (quote && entry) entry.blocks.push({ type: 'quote', text: quote.join(' ') });
      quote = null;
    }
    function flushAll() {
      flushList();
      flushQuote();
    }

    for (var i = 0; i < lines.length; i++) {
      var line = lines[i];
      var version = line.match(/^## \[([^\]]+)\](?:\s*-\s*(.+))?/);
      if (version) {
        flushAll();
        entry = { version: version[1], date: (version[2] || '').trim(), blocks: [] };
        entries.push(entry);
        continue;
      }
      if (!entry) continue; // preamble before the first version header

      var category = line.match(/^### (.+)/);
      if (category) {
        flushAll();
        entry.blocks.push({ type: 'category', name: category[1].trim() });
        continue;
      }
      var bullet = line.match(/^\s*[-*] (.*)/);
      if (bullet) {
        flushQuote();
        if (!list) list = [];
        list.push(bullet[1].trim());
        continue;
      }
      var quoted = line.match(/^> ?(.*)/);
      if (quoted) {
        flushList();
        if (!quote) quote = [];
        if (quoted[1].trim()) quote.push(quoted[1].trim());
        continue;
      }
      if (/^\s+\S/.test(line) && list) {
        // Hanging-indent continuation of the previous bullet.
        list[list.length - 1] += ' ' + line.trim();
        continue;
      }
      flushAll();
      if (line.trim()) entry.blocks.push({ type: 'para', text: line.trim() });
    }
    flushAll();

    // Drop versions with no content at all (e.g. an empty [Unreleased]).
    return entries.filter(function (e) {
      return e.blocks.length > 0 || e.version.toLowerCase() !== 'unreleased';
    });
  }

  function categoryClass(name) {
    return KNOWN_CATEGORIES[name.toLowerCase()] || 'cl-cat-other';
  }

  function render(entries) {
    var html = '';
    var latestSeen = false;

    entries.forEach(function (entry) {
      if (entry.version.toLowerCase() === 'unreleased' && entry.blocks.length === 0) return;

      var isUnreleased = entry.version.toLowerCase() === 'unreleased';
      var isPre = !isUnreleased && entry.version.indexOf('-') !== -1;
      var isLatest = !isUnreleased && !isPre && !latestSeen;
      if (isLatest) latestSeen = true;

      var classes = 'cl-entry' + (isLatest ? ' is-latest' : '') + (isPre ? ' is-pre' : '');
      var title = isUnreleased
        ? escapeHtml(entry.version)
        : '<a href="' + RELEASE_URL + encodeURIComponent(entry.version) + '" target="_blank" rel="noopener">v' + escapeHtml(entry.version) + '</a>';

      html += '<article class="' + classes + '"><div class="cl-card">';
      html += '<div class="cl-head"><h2 class="cl-version">' + title + '</h2>';
      if (entry.date) html += '<span class="cl-date">' + escapeHtml(entry.date) + '</span>';
      if (isLatest) html += '<span class="cl-tag cl-tag-latest">latest</span>';
      if (isPre) html += '<span class="cl-tag cl-tag-pre">pre-release</span>';
      html += '</div>';

      entry.blocks.forEach(function (block) {
        if (block.type === 'category') {
          html += '<span class="cl-cat ' + categoryClass(block.name) + '">' + escapeHtml(block.name) + '</span>';
        } else if (block.type === 'list') {
          html += '<ul>';
          block.items.forEach(function (item) {
            html += '<li>' + renderInline(item) + '</li>';
          });
          html += '</ul>';
        } else if (block.type === 'quote') {
          html += '<blockquote><p>' + renderInline(block.text) + '</p></blockquote>';
        } else {
          html += '<p>' + renderInline(block.text) + '</p>';
        }
      });

      html += '</div></article>';
    });

    return html;
  }

  function show(id, visible) {
    document.getElementById(id).hidden = !visible;
  }

  window
    .fetch(RAW_URL, { cache: 'no-cache' })
    .then(function (response) {
      if (!response.ok) throw new Error('HTTP ' + response.status);
      return response.text();
    })
    .then(function (markdown) {
      var entries = parse(markdown);
      if (!entries.length) throw new Error('no entries parsed');
      document.getElementById('cl-timeline').innerHTML = render(entries);
      show('cl-loading', false);
      show('cl-timeline', true);
    })
    .catch(function () {
      show('cl-loading', false);
      show('cl-error', true);
    });
})();
