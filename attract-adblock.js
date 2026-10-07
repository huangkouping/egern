/* Egern response script. Version 4, 2026-10-07. */
(function () {
  if (typeof $response === 'undefined' || !$response.body) return $done({});
  let body = $response.body;
  const url = String($request.url || '');
  try {
    if (/\/(?:storage\/static|html)\/popup-feed\.json(?:[?#]|$)/.test(url)) {
      if (!/^\s*\{/.test(body)) return $done({});
      const data = JSON.parse(body);
      data.enabled = false;
      data.ads = [];
      return $done({body: JSON.stringify(data)});
    }
    if (/\/storage\/static\/player-pause-ad\.json/.test(url)) {
      return $done({body: JSON.stringify({img: '', link: ''})});
    }
    if (!/^\s*(?:<![^>]*>\s*)*<html\b/i.test(body)) return $done({});
    // Decode only the captured 91JQ wrapper. Never evaluate website JavaScript.
    if (/^https?:\/\/(?:[a-z0-9-]+\.)?91jq508\.com(?::\d+)?\//i.test(url) && /document\.open\(\);document\.write\(/.test(body)) {
      const wrapper = /var (\w+)="([A-Za-z0-9+/=]+)";\s*var (\w+)="([^"]+)";\s*var (\w+)=(\{[^;]+\});/.exec(body);
      if (wrapper) {
        const mapping = JSON.parse(wrapper[6]);
        const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
        const encoded = wrapper[2].split('').map(c => mapping[c] || c).join('');
        let bits = 0, value = 0, bytes = '';
        for (const c of encoded.replace(/=+$/, '')) {
          const n = alphabet.indexOf(c);
          if (n < 0) throw new Error('Invalid page encoding');
          value = (value << 6) | n; bits += 6;
          if (bits >= 8) { bits -= 8; bytes += String.fromCharCode((value >>> bits) & 255); }
        }
        let escaped = '';
        for (let i = 0; i < bytes.length; i++) {
          const n = bytes.charCodeAt(i) ^ wrapper[4].charCodeAt(i % wrapper[4].length);
          escaped += '%' + n.toString(16).padStart(2, '0');
        }
        const decoded = decodeURIComponent(escaped);
        if (!/^\s*(?:<![^>]*>\s*)*<html\b/i.test(decoded)) throw new Error('Unrecognized decoded page');
        body = decoded;
        // These inline blocks exclusively build advertising cards.
        body = body.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, s => /\bvar\s+pgglist\s*=\s*pgglists\(\)/.test(s) ? '' : s);
      }
    }
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
    body = body.replace(/<script\b[^>]*src=["'][^"']*(?:\/bottom_ad_poll\.js|\/bottom_popup_poll\.js|\/bottom-popup-ads-core\.js|\/slot-ads\.js|\/activity\/national-day\/home\.js|\/activity\/js\/popup-lottery\.js)[^"']*["'][^>]*>\s*<\/script>/gi, '');
    // Protect script strings from markup scanning; site scripts contain HTML templates.
    const scripts = [];
    body = body.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, script => {
      const index = scripts.push(script) - 1;
      return '<!--H_SCRIPT_' + index + '-->';
    });
    const opening = /<(a|div|aside|button|section)\b[^>]*>/gi;
    let match;
    const ranges = [];
    while ((match = opening.exec(body))) {
      const tag = match[0];
      if (!/\brel\s*=\s*["'][^"']*\bsponsored\b/i.test(tag) &&
          !/\bdata-event\s*=\s*["']ad_click["']/i.test(tag) &&
          !/\bclass\s*=\s*["'][^"']*\b(?:horizontal-banner|txt-apps|home-a2hs-bar|adspop|application-popup|newyear-popup|national-day-home-banner|xqbj-component-adfloat|article-download|pgx-slot|pgx-card|component-advertises(?:-\d+)?|slider-banners|redpack-popup|redpack-float-icon|nd-entry-float)\b/i.test(tag) &&
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
    const extra = '.pgx-slot,.pgx-card,.component-advertises,[class^="component-advertises-"],.slider-banners,.redpack-popup,.redpack-float-icon,.nd-entry-float,img[src*="adhh"],img[data-src*="adhh"]';
    const sfAds = 'a[onclick^="xm("],a[onclick^="xc("],a[onclick^="jump99"],a[onclick^="jump1973qp"],a[onclick^="jump5768qp"],a[onclick^="jumpv88"],a[onclick^="jump5413qp"]';
    const all = selector + ',' + extra + (/91jq508\.com/.test(url) ? ',' + sfAds : '');
    const guard = '<style>' + all + '{display:none!important}</style><script>(function(){const s=' + JSON.stringify(all) + ';function clean(){document.querySelectorAll(s).forEach(function(n){n.remove()})}new MutationObserver(clean).observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:["src","data-src","class","onclick"]});document.addEventListener("DOMContentLoaded",clean);clean()})();</script>';
    body = body.replace(/<head\b[^>]*>/i, '$&' + guard);
    console.log('[网页去广告 v4] 移除广告区块 ' + ranges.length + ' 个');
    return $done({body});
  } catch (error) {
    console.log('[网页去广告] ' + error);
    return $done({});
  }
})();
