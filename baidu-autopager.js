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
 *
 * 2026-11-01 修复“第二页之后全是第二页”：抓取页的分页控制器里提取到的
 * 链接可能不是真正的下一页（第二页起控制器首个链接常是自引用/上一页，
 * 且链接里的会话令牌每次都变，旧版按整串 URL 去重失效，无限重复抓第二页）。
 * 现在按页码参数（百度 pn / Bing first / Google start）校验推进：候选链接
 * 页码必须大于刚抓的页码，否则按步长在上一条真实链接上递增页码合成；
 * 再按每页首条结果的签名去重，重复即停，杜绝任何形式的原地打转。
 * 触发方式（同日晚间按用户要求调整）：以“当前已加载内容的真正末尾”
 * （结果容器内的页尾锚点，追加内容会把它往下推）为触发点，浏览到末尾
 * 才加载下一页、接在下面，逐页推进，不预加载、不一次性灌入全部页面。
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
    function abs(u) {
      if (!u) return null;
      try { return new URL(u, location.href).href; } catch (e) { return u; }
    }
    function getParam(u, name) {
      if (!u) return null;
      var m = new RegExp('[?&]' + name + '=(\\d+)').exec(u);
      return m ? parseInt(m[1], 10) : null;
    }
    function setParam(u, name, value) {
      var re = new RegExp('([?&]' + name + '=)\\d+');
      if (re.test(u)) return u.replace(re, '$1' + value);
      return u + (u.indexOf('?') >= 0 ? '&' : '?') + name + '=' + value;
    }
    var engine = null;
    if (/(^|\.)baidu\.com$/.test(host)) {
      engine = {
        param: 'pn',
        box: function (doc) { return qs('#results', doc) || qs('#content_left', doc); },
        next: function (doc) {
          var a = qs('a.new-nextpage-only', doc) || qs('#page-controller a[href]', doc) || qs('#page a.np', doc);
          return a ? abs(a.href) : null;
        },
        sentinel: function () { return qs('#page-controller') || qs('#page'); },
        anchor: function (box) { return qs('#results-after', box) || qs('.se-results-after', box) || qs('.results-after', box); },
        junk: function (el) {
          var c = (el.className && el.className.toString()) || '';
          if ((el.id || '') === 'results-after' || hasClass(el, 'results-after') || hasClass(el, 'se-results-after')) return true;
          if ((el.id || '').indexOf('ec_r_') === 0 || c.indexOf('ec_r_') >= 0 || c.indexOf('ec_ad_results') >= 0 || c.indexOf('ec_wise_ad') >= 0) return true;
          return false;
        },
        liveNext: function () { return qs('a.new-nextpage-only') || qs('#page-controller a[href]'); }
      };
    } else if (/(^|\.)bing\.com$/.test(host)) {
      engine = {
        param: 'first',
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
          return a ? abs(a.href) : null;
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
        param: 'start',
        box: function (doc) { return qs('#rso', doc) || qs('#search', doc); },
        next: function (doc) {
          var a = qs('a#pnnext', doc);
          return a ? abs(a.href) : null;
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
    var box = engine.box(document);
    var ctrl = engine.sentinel();
    if (!box || !ctrl) return;
    var nextUrl = engine.next(document);
    if (!nextUrl) return;
    var curPage = getParam(nextUrl, engine.param);
    var step = null;
    var seenPages = {};
    var seenSigs = {};
    if (curPage !== null) seenPages[curPage] = true;
    function pageSig(srcBox) {
      var kids = srcBox.children;
      for (var i = 0; i < kids.length; i++) {
        var el = kids[i];
        if (el.tagName === 'SCRIPT' || engine.junk(el)) continue;
        return (el.textContent || '').replace(/\s+/g, ' ').slice(0, 80);
      }
      return '';
    }
    function load() {
      if (loading || stopped || !nextUrl || loaded >= MAX_PAGES) return;
      loading = true;
      var fetchedUrl = nextUrl;
      var fetchedPage = curPage;
      fetch(fetchedUrl, { credentials: 'include' }).then(function (r) { return r.text(); }).then(function (html) {
        var doc = new DOMParser().parseFromString(html, 'text/html');
        var src = engine.box(doc);
        if (!src) { stopped = true; return; }
        var sig = pageSig(src);
        if (sig && seenSigs[sig]) { stopped = true; nextUrl = null; return; }
        if (sig) seenSigs[sig] = true;
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
        /* 计算下一页：候选链接页码必须严格大于刚抓的页码，否则按步长合成 */
        var nu = engine.next(doc);
        var nuPage = getParam(nu, engine.param);
        if (nu && fetchedPage !== null && nuPage !== null && nuPage > fetchedPage) {
          if (step === null && nuPage - fetchedPage > 0) step = nuPage - fetchedPage;
          if (seenPages[nuPage]) { stopped = true; nextUrl = null; return; }
          seenPages[nuPage] = true;
          curPage = nuPage;
          nextUrl = nu;
        } else if (fetchedPage !== null) {
          var np = fetchedPage + (step || 10);
          if (seenPages[np]) { stopped = true; nextUrl = null; return; }
          seenPages[np] = true;
          curPage = np;
          nextUrl = setParam(fetchedUrl, engine.param, np);
        } else {
          stopped = true; nextUrl = null; return;
        }
        var a = engine.liveNext();
        if (a) a.href = nextUrl;
        armObserver();
      }).catch(function () { /* 网络抖动时不终止，下次滚动到页脚再试 */ }).then(function () {
        loading = false;
        if (!stopped && nearBottom()) load();
      });
    }
    /* 当前已加载内容的真正末尾：页尾锚点（追加内容会把它往下推），
       没有锚点时用结果容器的最后一个子元素，再不行才用分页控制器。 */
    function bottomEl() {
      var a = engine.anchor(box);
      if (a) return a;
      if (box.lastElementChild) return box.lastElementChild;
      return ctrl;
    }
    function nearBottom() {
      var el = bottomEl();
      if (!el) return false;
      var r = el.getBoundingClientRect();
      return r.top < window.innerHeight + 1000;
    }
    var io = null;
    function armObserver() {
      if (!('IntersectionObserver' in window)) return;
      var el = bottomEl();
      if (!el) return;
      if (io) io.disconnect();
      io = new IntersectionObserver(function (entries) { if (entries[0].isIntersecting) load(); }, { rootMargin: '1000px' });
      io.observe(el);
    }
    armObserver();
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
