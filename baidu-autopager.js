/* 百度搜索结果自动翻页（自维护脚本，非 limbopro 上游内容，同步脚本不会覆盖本文件）。
 * Egern http_response 脚本：把页面脚本注入百度搜索结果页，滚动接近页脚时
 * 自动抓取“下一页”并把新结果追加到当前列表，免去手动翻页。
 * 结构依据 2026-11-01 实测的百度触屏版结果页：结果容器 #results（PC 版
 * #content_left），下一页链接 #page-controller a.new-nextpage-only（href 带 pn 参数）。
 * 追加的节点会套用页面已有的去广告样式；广告容器（ec_*）与页尾相关推荐区不搬运。
 */
function baiduAutoPagerPage() {
  try {
    if (window.__bdAutopager) return;
    window.__bdAutopager = true;
    var MAX_PAGES = 50;
    var loaded = 0, loading = false, stopped = false;
    var seen = {};
    function qs(sel, root) { return (root || document).querySelector(sel); }
    function resultsBox(doc) { return qs('#results', doc) || qs('#content_left', doc); }
    function findNext(doc) {
      var a = qs('a.new-nextpage-only', doc) || qs('#page-controller a[href]', doc) || qs('#page a.np', doc);
      return a ? a.href : null;
    }
    function isJunk(el) {
      if (el.tagName === 'SCRIPT') return true;
      var c = (el.className && el.className.toString()) || '';
      var id = el.id || '';
      if (/(^|\s)(results-after|se-results-after)(\s|$)/.test(c)) return true;
      if (id.indexOf('ec_r_') === 0 || c.indexOf('ec_r_') >= 0 || c.indexOf('ec_ad_results') >= 0 || c.indexOf('ec_wise_ad') >= 0) return true;
      return false;
    }
    var box = resultsBox(document);
    var ctrl = qs('#page-controller') || qs('#page');
    if (!box || !ctrl) return;
    var nextUrl = findNext(document);
    if (!nextUrl) return;
    seen[nextUrl] = true;
    function load() {
      if (loading || stopped || !nextUrl || loaded >= MAX_PAGES) return;
      loading = true;
      fetch(nextUrl, { credentials: 'include' }).then(function (r) { return r.text(); }).then(function (html) {
        var doc = new DOMParser().parseFromString(html, 'text/html');
        var src = resultsBox(doc);
        if (!src) { stopped = true; return; }
        var anchor = qs('#results-after', box) || qs('.se-results-after', box) || qs('.results-after', box);
        var moved = 0;
        Array.prototype.slice.call(src.children).forEach(function (el) {
          if (isJunk(el)) return;
          var node = document.importNode(el, true);
          if (node.querySelectorAll) {
            Array.prototype.slice.call(node.querySelectorAll('script')).forEach(function (s) { s.parentNode.removeChild(s); });
          }
          if (anchor) box.insertBefore(node, anchor); else box.appendChild(node);
          moved++;
        });
        if (!moved) { stopped = true; return; }
        loaded++;
        var nu = findNext(doc);
        if (!nu || seen[nu]) { stopped = true; nextUrl = null; return; }
        seen[nu] = true;
        nextUrl = nu;
        var a = qs('a.new-nextpage-only') || qs('#page-controller a[href]');
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
      const tag = '<script>(' + baiduAutoPagerPage.toString() + ')();</script>';
      body = body.replace(/<\/body>/i, tag + '</body>');
      $done({ body });
    } else {
      $done({});
    }
  } catch (_) { $done({}); }
})($done);
