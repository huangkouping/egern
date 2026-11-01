/* 搜索自动翻页：独立于 limbopro 上游。严格使用服务端“下一页”链接；
 * 百度、Bing、Google 分别识别，逐页追加，验证页码/结果去重；
 * 无法确定下一页时停止，绝不猜测 pn/first/start。
 */
function searchAutoPagerPage() {
  try {
    if (window.__searchAutopager) return;
    window.__searchAutopager = true;
    var host = location.hostname;
    var config = /(^|\.)baidu\.com$/.test(host) ? {
      param: 'pn', box: ['#results', '#content_left'],
      next: ['a.new-nextpage-only', '#page a.np', '#page-controller a[rel="next"]', '#page-controller a[href]'],
      items: ['.c-result', '.result', '.c-container', '.result-op'],
      exclude: /(^|\s)(ec_r_|ec_ad_results|ec_wise_ad|results-after|se-results-after)/,
      pager: ['#page-controller', '#page']
    } : /(^|\.)bing\.com$/.test(host) ? {
      param: 'first', box: ['#b_results'],
      next: ['a.sb_pagN_bp', 'a.sb_pagN', '.sb_pager a[rel="next"]', '.sb_pager a[href*="first="]'],
      items: ['li.b_algo'],
      exclude: /(^|\s)(b_ad|b_fpage|b_ans|b_pag)/,
      pager: ['.sb_pager']
    } : /(^|\.)google\.com(\.hk|\.tw)?$/.test(host) ? {
      param: 'start', box: ['#rso', '#search'],
      next: ['a#pnnext', 'a[rel="next"]'],
      items: ['div.MjjYud', 'div.g'],
      exclude: /(^|\s)(tvcap|bottomads)/,
      pager: ['#botstuff', '#footcnt']
    } : null;
    if (!config) return;
    function find(doc, selectors) {
      for (var i = 0; i < selectors.length; i++) {
        var el = doc.querySelector(selectors[i]);
        if (el) return el;
      }
      return null;
    }
    var box = find(document, config.box);
    if (!box) return;
    function urlOf(a, base) {
      if (!a) return null;
      try {
        var u = new URL(a.getAttribute('href'), base);
        if (u.protocol !== 'https:' && u.protocol !== 'http:') return null;
        if (u.hostname !== host) return null;
        return u;
      } catch (e) { return null; }
    }
    function offset(u) {
      if (!u) return null;
      var v = u.searchParams.get(config.param);
      return v !== null && /^\d+$/.test(v) ? Number(v) : null;
    }
    function findNext(doc, base, currentOffset) {
      for (var i = 0; i < config.next.length; i++) {
        var nodes = doc.querySelectorAll(config.next[i]);
        for (var j = 0; j < nodes.length; j++) {
          var a = nodes[j], u = urlOf(a, base);
          if (!u) continue;
          var n = offset(u);
          if (n === null || n <= currentOffset) continue;
          var label = ((a.textContent || '') + ' ' + (a.getAttribute('aria-label') || '')).trim();
          var explicit = a.matches('a.new-nextpage-only, #page a.np, a.sb_pagN_bp, a.sb_pagN, a#pnnext, a[rel="next"]');
          if (!explicit && !/下一页|下页|next|›|»|>/.test(label.toLowerCase())) continue;
          return u;
        }
      }
      return null;
    }
    var initialOffset = offset(new URL(location.href));
    if (initialOffset === null) initialOffset = config.param === 'first' ? 1 : 0;
    var next = findNext(document, location.href, initialOffset);
    if (!next) return;
    var seenOffsets = new Set([initialOffset]);
    var seenUrls = new Set();
    var seenResults = new Set();
    var loaded = 0, busy = false, stopped = false;
    var marker = document.createElement('div');
    marker.setAttribute('data-egern-autopager', '1');
    marker.style.cssText = 'text-align:center;padding:18px 8px;color:#777;font-size:13px;clear:both;';
    marker.textContent = '向下滚动，自动加载下一页';
    box.parentNode.insertBefore(marker, box.nextSibling);
    function key(el, base) {
      var a = el.matches('a[href]') ? el : el.querySelector('h3 a[href], h2 a[href], a[href]');
      var href = '';
      if (a) {
        try {
          var u = new URL(a.getAttribute('href'), base);
          u.hash = '';
          href = u.href;
        } catch (e) {}
      }
      var title = (el.querySelector('h3,h2') || el).textContent.replace(/\s+/g, ' ').trim().slice(0, 160);
      return href ? href + '|' + title : (title.length > 25 ? title : '');
    }
    function junk(el) {
      if (el.tagName === 'SCRIPT' || el.tagName === 'STYLE') return true;
      var c = (el.className && String(el.className)) || '';
      if (config.exclude.test(c) || config.exclude.test(el.id || '')) return true;
      if (el.matches('[data-text-ad], .b_ad, #progContPlaceHolder, #results-after, .results-after, .se-results-after')) return true;
      if (el.querySelector('[data-text-ad], .b_ad')) return true;
      return false;
    }
    function collect(root) {
      for (var i = 0; i < config.items.length; i++) {
        var nodes = Array.from(root.querySelectorAll(config.items[i])).filter(function (el) {
          return !junk(el);
        });
        if (nodes.length >= 2) return nodes.filter(function (el) {
          return !nodes.some(function (other) { return other !== el && other.contains(el); });
        });
      }
      return Array.from(root.children).filter(function (el) { return !junk(el); });
    }
    collect(box).forEach(function (el) {
      var k = key(el, location.href);
      if (k) seenResults.add(k);
    });
    function stop(message) {
      stopped = true;
      marker.textContent = message || '已加载全部可识别的搜索结果';
    }
    function load() {
      if (busy || stopped || !next || loaded >= 50) return;
      busy = true;
      var requested = next;
      var page = offset(requested);
      if (page === null || seenOffsets.has(page)) {
        stop('分页链接重复，已停止自动翻页'); busy = false; return;
      }
      marker.textContent = '正在加载下一页…';
      fetch(requested.href, { credentials: 'include', redirect: 'follow' }).then(function (response) {
        if (!response.ok) throw new Error('HTTP ' + response.status);
        if (new URL(response.url).hostname !== host) throw new Error('跳转到其他站点');
        return response.text().then(function (html) { return { html: html, base: response.url }; });
      }).then(function (result) {
        var doc = new DOMParser().parseFromString(result.html, 'text/html');
        var src = find(doc, config.box);
        if (!src) { stop('下一页结构已变化，停止自动翻页'); return; }
        var items = collect(src), unique = [], keys = [];
        items.forEach(function (el) {
          var k = key(el, result.base);
          if (k && !seenResults.has(k) && keys.indexOf(k) < 0) {
            unique.push(el); keys.push(k);
          }
        });
        if (!unique.length || (items.length >= 4 && unique.length / items.length < 0.35)) {
          stop('检测到重复搜索结果，已停止自动翻页'); return;
        }
        /* 验证本页真实内容后再推进；不合成分页 URL。 */
        var following = findNext(doc, result.base, page);
        var frag = document.createDocumentFragment();
        var divider = document.createElement('div');
        divider.style.cssText = 'padding:10px 4px;color:#888;font-size:12px;border-top:1px solid #ddd;';
        divider.textContent = '已加载下一页搜索结果';
        frag.appendChild(divider);
        unique.forEach(function (el) {
          var node = document.importNode(el, true);
          node.querySelectorAll('script, [data-egern-autopager]').forEach(function (s) { s.remove(); });
          frag.appendChild(node);
        });
        box.appendChild(frag);
        keys.forEach(function (k) { seenResults.add(k); });
        seenOffsets.add(page);
        seenUrls.add(requested.href);
        loaded++;
        next = following;
        if (!next || seenOffsets.has(offset(next)) || seenUrls.has(next.href)) {
          stop('已加载全部可识别的搜索结果');
        } else {
          marker.textContent = '向下滚动，自动加载下一页';
        }
      }).catch(function () {
        marker.textContent = '加载失败，继续滚动可重试';
      }).then(function () { busy = false; });
    }
    /* 仅监听末尾标记，加载完成后不会递归预取。 */
    if ('IntersectionObserver' in window) {
      var observer = new IntersectionObserver(function (entries) {
        if (entries[0] && entries[0].isIntersecting) load();
      }, { rootMargin: '0px 0px 160px 0px' });
      observer.observe(marker);
    } else {
      window.addEventListener('scroll', function () {
        if (marker.getBoundingClientRect().top < window.innerHeight + 160) load();
      }, { passive: true });
    }
  } catch (e) { /* 不影响原网页搜索 */ }
}
(function (complete) {
  var finished = false;
  function done(value) { if (!finished) { finished = true; complete(value); } }
  try {
    var headers = ($response && $response.headers) || {};
    var contentType = String(headers['Content-Type'] || headers['content-type'] || '');
    var body = $response && $response.body;
    if (typeof body === 'string' && body &&
        (!contentType || /text\/html/i.test(contentType)) && /<\/body>/i.test(body)) {
      var tag = '<script>(' + searchAutoPagerPage.toString() + ')();</script>';
      done({ body: body.replace(/<\/body>/i, tag + '</body>') });
    } else done({});
  } catch (e) { done({}); }
})($done);
