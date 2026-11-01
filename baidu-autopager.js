/* 搜索结果自动翻页（自维护脚本，非 limbopro 上游内容，同步脚本不会覆盖本文件）。
 * 覆盖百度 / Bing / Google 三家搜索结果页：滚动接近页脚时自动抓取“下一页”
 * 并把新结果追加到当前列表，免去手动翻页。Egern http_response 脚本，
 * 按页面域名选择对应引擎配置；结构不符时静默退出，不干预页面原生行为。
 *
 * 百度：结构依据 2026-11-01 实测触屏版结果页（#results 容器、
 * #page-controller a.new-nextpage-only 下一页链接），已端到端验证。
 * Bing：分页变体用 a.sb_pagN / first= 参数链接；若页面是官方渐进加载
 * 变体（#progContPlaceHolder 占位、无服务端下一页链接）则不干预。
 * Google：a#pnnext（start= 参数）+ #rso 容器，为通用实现，待实机验证。
 * 追加节点会套用页面已有的去广告样式；广告块（百度的 ec_* 壳、Bing 的
 * li.b_ad、Google 的 [data-text-ad] 块）与页尾区不搬运。
 */
function searchAutoPagerPage() {
  try {
    if (window.__searchAutopager) return;
    window.__searchAutopager = true;
    var host = location.hostname;
    function qs(sel, root) { return (root || document).querySelector(sel); }
    function hasClass(el, name) {
      var c = (el.className && el.className.toString()) || '';
      return (' ' + c + ' ').indexOf(' ' + name + ' ') >= 0;
    }
    var engine = null;
    if (/(^|\.)baidu\.com$/.test(host)) {
      engine = {
        box: function (doc) { return qs('#results', doc) || qs('#content_left', doc); },
        next: function (doc) {
          var a = qs('a.new-nextpage-only', doc) || qs('#page-controller a[href]', doc) || qs('#page a.np', doc);
          return a ? a.href : null;
        },
        sentinel: function () { return qs('#page-controller') || qs('#page'); },
        anchor: function (box) { return qs('#results-after', box) || qs('.se-results-after', box) || qs('.results-after', box); },
        junk: function (el) {
          var c = (el.className && el.className.toString()) || '';
          if (hasClass(el, 'results-after') || hasClass(el, 'se-results-after')) return true;
          if ((el.id || '').indexOf('ec_r_') === 0 || c.indexOf('ec_r_') >= 0 || c.indexOf('ec_ad_results') >= 0 || c.indexOf('ec_wise_ad') >= 0) return true;
          return false;
        },
        liveNext: function () { return qs('a.new-nextpage-only') || qs('#page-controller a[href]'); }
      };
    } else if (/(^|\.)bing\.com$/.test(host)) {
      engine = {
        box: function (doc) { return qs('#b_results', doc); },
        next: function (doc) {
          var a = qs('a.sb_pagN_bp', doc) || qs('a.sb_pagN', doc) || qs('.sb_pager a[href*="first="]', doc);
          if (!a) {
            var links = (doc || document).querySelectorAll('a[href*="first="]');
            for (var i = 0; i < links.length; i++) {
              var t = (links[i].textContent || '') + '|' + (links[i].getAttribute('aria-label') || '');
              if (/下一页|Next page/i.test(t)) { a = links[i]; break; }
            }
          }
          return a ? a.href : null;
        },
        sentinel: function () { return qs('.sb_pager') || qs('#b_results'); },
        anchor: function (box) { return qs('#progContPlaceHolder', box) || qs('.b_fpage', box); },
        junk: function (el) {
          if (hasClass(el, 'b_ad') || hasClass(el, 'b_fpage') || el.id === 'progContPlaceHolder') return true;
          if (el.querySelector && el.querySelector('li.b_ad, .b_ad')) return true;
          return false;
        },
        liveNext: function () { return qs('a.sb_pagN_bp') || qs('a.sb_pagN'); }
      };
      /* 官方渐进加载变体：有占位符且无分页链接时不干预 */
      if (qs('#progContPlaceHolder') && !engine.next(document)) return;
    } else if (/(^|\.)google\.com(\.hk|\.tw)?$/.test(host)) {
      engine = {
        box: function (doc) { return qs('#rso', doc) || qs('#search', doc); },
        next: function (doc) {
          var a = qs('a#pnnext', doc);
          return a ? a.href : null;
        },
        sentinel: function () { return qs('#pnnext') || qs('#botstuff') || qs('#footcnt') || qs('#search'); },
        anchor: function () { return null; },
        junk: function (el) {
          if (el.id === 'tvcap' || el.id === 'bottomads') return true;
          if (el.hasAttribute && el.hasAttribute('data-text-ad')) return true;
          if (el.querySelector && el.querySelector('[data-text-ad]')) return true;
          return false;
        },
        liveNext: function () { return qs('a#pnnext'); }
      };
    }
    if (!engine) return;
    var MAX_PAGES = 50;
    var loaded = 0, loading = false, stopped = false;
    var seen = {};
    var box = engine.box(document);
    var ctrl = engine.sentinel();
    if (!box || !ctrl) return;
    var nextUrl = engine.next(document);
    if (!nextUrl) return;
    seen[nextUrl] = true;
    function load() {
      if (loading || stopped || !nextUrl || loaded >= MAX_PAGES) return;
      loading = true;
      fetch(nextUrl, { credentials: 'include' }).then(function (r) { return r.text(); }).then(function (html) {
        var doc = new DOMParser().parseFromString(html, 'text/html');
        var src = engine.box(doc);
        if (!src) { stopped = true; return; }
        var anchor = engine.anchor(box);
        var moved = 0;
        Array.prototype.slice.call(src.children).forEach(function (el) {
          if (el.tagName === 'SCRIPT' || engine.junk(el)) return;
          var node = document.importNode(el, true);
          if (node.querySelectorAll) {
            Array.prototype.slice.call(node.querySelectorAll('script')).forEach(function (s) { s.parentNode.removeChild(s); });
          }
          if (anchor) box.insertBefore(node, anchor); else box.appendChild(node);
          moved++;
        });
        if (!moved) { stopped = true; return; }
        loaded++;
        var nu = engine.next(doc);
        if (!nu || seen[nu]) { stopped = true; nextUrl = null; return; }
        seen[nu] = true;
        nextUrl = nu;
        var a = engine.liveNext();
        if (a) a.href = nu;
      }).catch(function () { /* 网络抖动时不终止，下次滚动到页脚再试 */ }).then(function () {
        loading = false;
        if (!stopped && nearBottom()) load();
      });
    }
    function nearBottom() {
      var r = ctrl.getBoundingClientRect();
      return r.top < window.innerHeight + 1000;
    }
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) { if (entries[0].isIntersecting) load(); }, { rootMargin: '1000px' }).observe(ctrl);
    }
    window.addEventListener('scroll', function () { if (nearBottom()) load(); }, { passive: true });
    if (nearBottom()) load();
  } catch (e) { /* 结构不符时静默退出，不影响页面 */ }
}
(function (complete) {
  let finished = false;
  const $done = value => { if (!finished) { finished = true; complete(value); } };
  try {
    const headers = ($response && $response.headers) || {};
    const contentType = String(headers['Content-Type'] || headers['content-type'] || '');
    let body = $response && $response.body;
    if (typeof body === 'string' && body &&
        (contentType === '' || /text\/html/i.test(contentType)) && /<\/body>/i.test(body)) {
      const tag = '<script>(' + searchAutoPagerPage.toString() + ')();</script>';
      body = body.replace(/<\/body>/i, tag + '</body>');
      $done({ body });
    } else {
      $done({});
    }
  } catch (_) { $done({}); }
})($done);
