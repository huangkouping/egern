/* Egern response script. Version 3, 2026-10-06. */
(function () {
  if (typeof $response === 'undefined' || !$response.body) return $done({});
  let body = $response.body;
  const url = String($request.url || '');
  try {
    if (/\/storage\/static\/popup-feed\.json/.test(url)) {
      const data = JSON.parse(body);
      data.enabled = false;
      data.ads = [];
      return $done({body: JSON.stringify(data)});
    }
    if (/\/storage\/static\/player-pause-ad\.json/.test(url)) {
      return $done({body: JSON.stringify({img: '', link: ''})});
    }
    if (!/^\s*(?:<![^>]*>\s*)*<html\b/i.test(body)) return $done({});
    // Change only explicit player advertising fields; keep signed video URLs intact.
    body = body.replace(/data-config='([^']+)'/g, (whole, raw) => {
      try {
        const config = JSON.parse(raw);
        if (!config.video) return whole;
        config.pre_ads = [];
        config.post_ads = [];
        config.pause_ad = {img: '', link: ''};
        config.ads_jump_time = 0;
        return "data-config='" + JSON.stringify(config).replace(/'/g, '\\u0027') + "'";
      } catch (_) { return whole; }
    });
    // Remove complete matched elements, including nested divs, without a greedy regex.
    body = body.replace(/<script\b[^>]*src=["'][^"']*(?:\/bottom_ad_poll\.js|\/activity\/national-day\/home\.js|\/activity\/js\/popup-lottery\.js)[^"']*["'][^>]*>\s*<\/script>/gi, '');
    // Protect script strings from markup scanning; site scripts contain HTML templates.
    const scripts = [];
    body = body.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, script => {
      const index = scripts.push(script) - 1;
      return '<!--H_SCRIPT_' + index + '-->';
    });
    const opening = /<(a|div|aside)\b[^>]*>/gi;
    let match;
    const ranges = [];
    while ((match = opening.exec(body))) {
      const tag = match[0];
      if (!/\brel\s*=\s*["'][^"']*\bsponsored\b/i.test(tag) &&
          !/\bdata-event\s*=\s*["']ad_click["']/i.test(tag) &&
          !/\bclass\s*=\s*["'][^"']*\b(?:horizontal-banner|txt-apps|home-a2hs-bar|adspop|application-popup|newyear-popup|national-day-home-banner|xqbj-component-adfloat|article-download)\b/i.test(tag) &&
          !/\bid\s*=\s*["'](?:post-card-ad-|adFloat["']|nd-national-day-float["'])/i.test(tag)) continue;
      const scan = new RegExp('<\\/?' + match[1] + '\\b[^>]*>', 'gi');
      scan.lastIndex = opening.lastIndex;
      let depth = 1, next;
      while ((next = scan.exec(body))) {
        depth += /^<\//.test(next[0]) ? -1 : 1;
        if (!depth) break;
      }
      if (!depth) {
        ranges.push([match.index, scan.lastIndex]);
        opening.lastIndex = scan.lastIndex;
      }
    }
    for (let i = ranges.length - 1; i >= 0; i--) body = body.slice(0, ranges[i][0]) + body.slice(ranges[i][1]);
    body = body.replace(/<!--H_SCRIPT_(\d+)-->/g, (_, index) => scripts[Number(index)]);
    const selector = '[data-event="ad_click"],a[rel~="sponsored"],[id^="post-card-ad-"],.horizontal-banner,.txt-apps,.home-a2hs-bar,#adFloat,.xqbj-component-adfloat,.adspop,.application-popup,.newyear-popup,.national-day-home-banner,.national-day-floating-slide,#nd-national-day-float,.article-download';
    const guard = '<style>' + selector + '{display:none!important}</style><script>(function(){const s=' + JSON.stringify(selector) + ';function clean(){document.querySelectorAll(s).forEach(function(n){n.remove()})}new MutationObserver(clean).observe(document.documentElement,{childList:true,subtree:true});document.addEventListener("DOMContentLoaded",clean);clean()})();</script>';
    body = body.replace(/<head\b[^>]*>/i, '$&' + guard);
    console.log('[网页去广告 v3] 移除广告区块 ' + ranges.length + ' 个');
    return $done({body});
  } catch (error) {
    console.log('[网页去广告] ' + error);
    return $done({});
  }
})();
