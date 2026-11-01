/* 百度搜索自动翻页 ©️ | 独立模块，2026-11-01
 * 仅适配百度 HTML 搜索结果。不能确认下一页或结果重复时安全停止。
 * 不猜测 pn，不执行抓取页面中的脚本，不修改原有分页链接。
 */
function baiduInfiniteScroll() {
  try {
    if (window.__baiduInfiniteScroll || !/(^|\.)baidu\.com$/.test(location.hostname)) return;
    var search = new URL(location.href);
    if (!(/^\/s$/.test(search.pathname) || /^\/from=/.test(search.pathname))) return;
    var doc = document;
    var box = doc.querySelector('#results') || doc.querySelector('#content_left');
    if (!box) return;
    function pageNumber(url) {
      var value = url.searchParams.get('pn');
      return value !== null && /^\d+$/.test(value) ? Number(value) : 0;
    }
    function nextLink(root, base, current) {
      // Mobile Baidu frequently renders its next button outside #page.
      // Read real anchors across the document; never manufacture a pn value.
      var links = root.querySelectorAll('a[href], a[data-href], [rel="next"][href]');
      for (var i = 0; i < links.length; i++) {
        var a = links[i];
        var href = a.getAttribute('href') || a.getAttribute('data-href');
        if (!href || /^javascript:|^#/.test(href)) continue;
        var label = ((a.textContent || '') + ' ' + (a.getAttribute('aria-label') || '') + ' ' + (a.getAttribute('title') || '')).replace(/\s+/g, ' ').trim();
        if (!/下一页|下页|next|›|»/i.test(label) && a.getAttribute('rel') !== 'next' && !a.matches('.new-nextpage-only, .np')) continue;
        var url;
        try { url = new URL(href, base); } catch (_) { continue; }
        if (url.hostname !== location.hostname || !/^https?:$/.test(url.protocol)) continue;
        if (!/^\/s$/.test(url.pathname) && !/^\/from=/.test(url.pathname)) continue;
        if (pageNumber(url) <= current) continue;
        return url;
      }
      return null;
    }
    function isJunk(el) {
      if (el.matches('script,style,#results-after,.results-after,.se-results-after,[id^="ec_r_"],.ec_ad_results,.ec_wise_ad,#page-controller,#page')) return true;
      return false;
    }
    function items(root) {
      var children = Array.prototype.slice.call(root.children).filter(function (el) { return !isJunk(el); });
      return children.filter(function (el) {
        return el.querySelector('a[href],h3,h2') && (el.textContent || '').trim().length > 15;
      });
    }
    function fingerprint(el, base) {
      var a = el.querySelector('h3 a[href],h2 a[href],a[href]');
      var href = '';
      if (a) {
        try { var u = new URL(a.getAttribute('href'), base); u.hash = ''; href = u.href; } catch (_) {}
      }
      var title = (el.querySelector('h3,h2') || el).textContent.replace(/\s+/g, ' ').trim().slice(0, 120);
      return href + '|' + title;
    }
    var current = pageNumber(search);
    var next = nextLink(doc, search.href, current);
    if (!next) return;
    window.__baiduInfiniteScroll = true;
    var seenPages = new Set([current]), seenResults = new Set(), busy = false, stopped = false, count = 0;
    items(box).forEach(function (el) { seenResults.add(fingerprint(el, search.href)); });
    var marker = doc.createElement('div');
    marker.id = 'egern-baidu-autopage-status';
    marker.style.cssText = 'clear:both;text-align:center;padding:16px 6px;color:#888;font-size:13px;';
    marker.textContent = '继续下滑，加载下一页';
    box.parentNode.insertBefore(marker, box.nextSibling);
    function stop(message) {
      stopped = true;
      marker.textContent = message;
      if (observer) observer.disconnect();
    }
    function load() {
      if (busy || stopped || !next || count >= 30) return;
      var requested = next, requestedPage = pageNumber(requested);
      if (seenPages.has(requestedPage)) { stop('检测到重复页码，已停止自动翻页'); return; }
      busy = true;
      marker.textContent = '正在加载下一页…';
      fetch(requested.href, { credentials: 'include', redirect: 'follow' }).then(function (response) {
        if (!response.ok) throw new Error('HTTP ' + response.status);
        var finalUrl = new URL(response.url);
        if (finalUrl.hostname !== location.hostname || pageNumber(finalUrl) !== requestedPage) throw new Error('分页跳转异常');
        return response.text().then(function (html) { return { html: html, url: finalUrl }; });
      }).then(function (result) {
        var parsed = new DOMParser().parseFromString(result.html, 'text/html');
        var source = parsed.querySelector('#results') || parsed.querySelector('#content_left');
        if (!source) { stop('页面结构发生变化，已停止自动翻页'); return; }
        var candidates = items(source), fresh = [], keys = [];
        candidates.forEach(function (el) {
          var key = fingerprint(el, result.url.href);
          if (!seenResults.has(key) && keys.indexOf(key) < 0) { fresh.push(el); keys.push(key); }
        });
        if (!candidates.length || !fresh.length || (candidates.length >= 4 && fresh.length / candidates.length < 0.5)) {
          stop('检测到重复搜索结果，已停止自动翻页'); return;
        }
        var following = nextLink(parsed, result.url.href, requestedPage);
        var fragment = doc.createDocumentFragment();
        var heading = doc.createElement('div');
        heading.style.cssText = 'clear:both;padding:10px 4px;color:#888;font-size:12px;border-top:1px solid #ddd;';
        heading.textContent = '第 ' + (count + 2) + ' 页';
        fragment.appendChild(heading);
        fresh.forEach(function (el) {
          var node = doc.importNode(el, true);
          node.querySelectorAll('script,iframe').forEach(function (child) { child.remove(); });
          fragment.appendChild(node);
        });
        box.appendChild(fragment);
        keys.forEach(function (key) { seenResults.add(key); });
        seenPages.add(requestedPage);
        count++;
        next = following;
        if (!next) stop('未识别后续分页，请使用下方百度原生“下一页”');
        else marker.textContent = '继续下滑，加载下一页';
      }).catch(function () {
        marker.textContent = '加载失败，继续下滑可重试';
      }).then(function () { busy = false; });
    }
    var observer = null;
    if ('IntersectionObserver' in window) {
      observer = new IntersectionObserver(function (entries) {
        if (entries[0] && entries[0].isIntersecting) load();
      }, { rootMargin: '0px 0px 120px 0px' });
      observer.observe(marker);
    } else {
      window.addEventListener('scroll', function () {
        if (marker.getBoundingClientRect().top < window.innerHeight + 120) load();
      }, { passive: true });
    }
  } catch (_) {}
}
(function (complete) {
  var done = false;
  function finish(result) { if (!done) { done = true; complete(result); } }
  try {
    var body = $response && $response.body;
    var headers = ($response && $response.headers) || {};
    var type = String(headers['Content-Type'] || headers['content-type'] || '');
    if (typeof body === 'string' && /<\/body\s*>/i.test(body) && (!type || /text\/html/i.test(type))) {
      var injection = '<script>(' + baiduInfiniteScroll.toString() + ')();</script>';
      finish({ body: body.replace(/<\/body\s*>/i, injection + '</body>') });
    } else finish({});
  } catch (_) { finish({}); }
})($done);
