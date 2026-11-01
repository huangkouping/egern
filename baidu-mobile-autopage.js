/* 百度移动搜索自动翻页 ©️ — standalone Egern response script */
function baiduMobilePager() {
  function start() {
    try {
      if (window.__egernBaiduPager) return;
      if (!/^(m|www)\.baidu\.com$/.test(location.hostname) || !/^\/s$/.test(location.pathname)) return;
      var root = document.querySelector('#results');
      if (!root) return;
      var search = new URL(location.href);
      if (!search.searchParams.get('word') && !search.searchParams.get('wd')) return;
      function offset(u) {
        var n = u.searchParams.get('pn');
        return n !== null && /^\d+$/.test(n) ? Number(n) : 0;
      }
      function nextUrl(doc, base, current) {
        var anchors = doc.querySelectorAll('a[href],a[data-href]');
        for (var i = 0; i < anchors.length; i++) {
          var a = anchors[i], raw = a.getAttribute('href') || a.getAttribute('data-href');
          if (!raw || /^(javascript:|#)/i.test(raw)) continue;
          var label = ((a.textContent || '') + ' ' + (a.getAttribute('aria-label') || '')).replace(/\s+/g, ' ').trim();
          if (!/下一页|下页|next|›|»/i.test(label) && !a.matches('.new-nextpage-only,.np,[rel="next"]')) continue;
          var u;
          try { u = new URL(raw, base); } catch (e) { continue; }
          if (u.hostname !== location.hostname || u.pathname !== '/s' || offset(u) <= current) continue;
          var oldQuery = search.searchParams.get('word') || search.searchParams.get('wd');
          var newQuery = u.searchParams.get('word') || u.searchParams.get('wd');
          if (newQuery && newQuery !== oldQuery) continue;
          return u;
        }
        return null;
      }
      function cards(doc) {
        var r = doc.querySelector('#results');
        if (!r) return [];
        var els = Array.prototype.slice.call(r.querySelectorAll(':scope > .c-result, :scope > [data-log], :scope > div'));
        return els.filter(function (e) {
          return e.id !== 'egern-baidu-page-status' && !e.matches('.new-pagenav,#page-controller,script,style') &&
            !!e.querySelector('a[href]') && (e.textContent || '').trim().length > 20;
        });
      }
      function key(e) {
        var title = e.querySelector('h3,h2');
        var a = title ? title.querySelector('a[href]') : e.querySelector('a[href]');
        return ((title ? title.textContent : e.textContent) || '').replace(/\s+/g, ' ').trim().slice(0, 140) +
          '|' + (a ? (a.getAttribute('href') || '') : '');
      }
      var next = nextUrl(document, search.href, offset(search));
      if (!next) return; // Preserve native pagination if unsupported.
      window.__egernBaiduPager = true;
      var seen = new Set(cards(document).map(key)), pages = new Set([offset(search)]);
      var status = document.createElement('div');
      status.id = 'egern-baidu-page-status';
      status.style.cssText = 'padding:16px 8px;text-align:center;color:#888;font-size:12px;clear:both';
      status.textContent = '继续下滑，加载下一页';
      root.parentNode.insertBefore(status, root.nextSibling);
      var busy = false, stopped = false, count = 0, observer;
      function stop(msg) { stopped = true; status.textContent = msg; if (observer) observer.disconnect(); }
      function load() {
        if (busy || stopped || !next || count >= 20) return;
        var requested = next, pn = offset(requested);
        if (pages.has(pn)) { stop('检测到重复页码，已停止自动翻页'); return; }
        busy = true;
        status.textContent = '正在加载下一页…';
        fetch(requested.href, { credentials: 'include' }).then(function (res) {
          if (!res.ok) throw Error('HTTP ' + res.status);
          var finalUrl = new URL(res.url);
          if (finalUrl.hostname !== location.hostname || offset(finalUrl) !== pn) throw Error('Unexpected redirect');
          return res.text().then(function (html) { return { html: html, url: finalUrl }; });
        }).then(function (response) {
          var doc = new DOMParser().parseFromString(response.html, 'text/html');
          var found = cards(doc), fresh = [], local = new Set();
          found.forEach(function (e) {
            var k = key(e);
            if (!seen.has(k) && !local.has(k)) { local.add(k); fresh.push(e); }
          });
          if (!found.length || !fresh.length || (found.length >= 4 && fresh.length * 2 < found.length)) {
            stop('未获得新的搜索结果，请使用百度原生分页'); return;
          }
          var fragment = document.createDocumentFragment();
          var sep = document.createElement('div');
          sep.style.cssText = 'padding:12px 8px;border-top:1px solid #ddd;color:#999;font-size:12px';
          sep.textContent = '第 ' + (count + 2) + ' 页';
          fragment.appendChild(sep);
          fresh.forEach(function (e) {
            var copy = document.importNode(e, true);
            copy.querySelectorAll('script,iframe').forEach(function (x) { x.remove(); });
            fragment.appendChild(copy);
          });
          root.appendChild(fragment);
          local.forEach(function (k) { seen.add(k); });
          pages.add(pn);
          count++;
          next = nextUrl(doc, response.url.href, pn);
          if (!next) stop('后续分页未识别，请使用百度原生分页');
          else status.textContent = '继续下滑，加载下一页';
        }).catch(function () { status.textContent = '加载失败，下滑可重试'; })
          .then(function () { busy = false; });
      }
      if ('IntersectionObserver' in window) {
        observer = new IntersectionObserver(function (entries) {
          if (entries.some(function (e) { return e.isIntersecting; })) load();
        }, { rootMargin: '0px 0px 400px 0px' });
        observer.observe(status);
      } else {
        window.addEventListener('scroll', function () {
          if (status.getBoundingClientRect().top < window.innerHeight + 400) load();
        }, { passive: true });
      }
    } catch (e) { /* Keep Baidu's native pagination working. */ }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, { once: true });
  else start();
}
(function () {
  try {
    var body = $response && $response.body;
    if (typeof body !== 'string' || !/<\/body\s*>/i.test(body)) { $done({}); return; }
    var script = '<script>(' + baiduMobilePager.toString() + ')();</script>';
    $done({ body: body.replace(/<\/body\s*>/i, script + '</body>') });
  } catch (e) { $done({}); }
})();
