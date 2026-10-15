/* 京东定向净化 v1：按抓包结构处理，不阻断共享推荐接口。 */
export default async function (ctx) {
  if (!ctx.request || !ctx.response) return;
  const request = ctx.request;
  if (!/^https?:\/\/api\.m\.jd\.com\/(?:client\.action|api)?(?:\?|$)/.test(request.url)) return;
  function formValue(text, key) {
    const m = String(text || '').match(new RegExp('(?:^|[?&])' + key + '=([^&]*)'));
    if (!m) return '';
    try { return decodeURIComponent(m[1].replace(/\+/g, ' ')); } catch (_) { return ''; }
  }
  let fid = formValue(request.url, 'functionId');
  let requestText = '';
  try { if (typeof request.text === 'function') requestText = await request.text(); } catch (_) {}
  let requestObject = null;
  try { requestObject = JSON.parse(requestText); } catch (_) {}
  fid = fid || formValue(requestText, 'functionId') || requestObject?.functionId || '';
  const original = await ctx.response.text();
  const pass = { body: original };
  let obj;
  try { obj = JSON.parse(original); } catch (_) { return pass; }
  if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return pass;
  let changes = 0;
  function setExisting(o, key, value) {
    if (o && Object.prototype.hasOwnProperty.call(o, key) && JSON.stringify(o[key]) !== JSON.stringify(value)) {
      o[key] = value; changes++;
    }
  }
  function remove(o, key) {
    if (o && Object.prototype.hasOwnProperty.call(o, key)) { delete o[key]; changes++; }
  }
  function filter(o, key, keep) {
    if (!o || !Array.isArray(o[key])) return;
    const next = o[key].filter(keep);
    if (next.length !== o[key].length) { changes += o[key].length - next.length; o[key] = next; }
  }
  const data = obj.data && typeof obj.data === 'object' && !Array.isArray(obj.data) ? obj.data : obj;
  if (fid === 'welcomeHome') {
    // 10/15 抓包：floorId 6859 为 float；保留 ruleFloat 资质入口和全部普通楼层。
    filter(obj, 'floorList', f => !f || f.type !== 'float');
    filter(obj, 'futureFloorList', f => !f || f.type !== 'float');
  }
  if (fid === 'basicConfig') {
    const message = data.JDMessage || {};
    // 抓包中真实存在的推荐楼层、推荐流开关；不改物流、客服、消息提醒开关。
    setExisting(message.recommendfloor, 'support_recommendfloor', '0');
    setExisting(message.recommendfeeds, 'support_recommendfeeds', '0');
    setExisting(message.recommendfeeds, 'fetchfeeds_api', '0');
    // 我的：关闭推荐预加载及推荐缓存，不把共享 uniformRecommend9 整体拦截。
    setExisting(data.JDMyJd?.recommendPreloadSwitchV15110, 'value', '0');
    setExisting(data.JDUniformRecommend?.JDUniformRecommendmMyJdCache, 'JDUniformRecommendmMyJdCache', '0');
  }
  if (fid === 'msgConfig') {
    // 实际响应为数字 0。保留该类型；不修改 popMainSwitch 或 station 消息投递配置。
    setExisting(obj, 'promotionWidgetUserFlag', 0);
  }
  if (/^personinfoBusiness$/i.test(fid)) {
    // 旧版我的布局兼容分支；当前 HAR 没有该响应，效果尚未验证。
    filter(data, 'floors', f => !f || !(
      ['recommendfloor', 'recommendFloor'].includes(f.mId) ||
      ['为你推荐', '潮流好货', '潮流好物'].includes(f.title)
    ));
  }
  if (/^uniformRecommend\d+$/.test(fid)) {
    let body = requestObject?.body || formValue(requestText, 'body') || formValue(request.url, 'body');
    if (typeof body === 'string') { try { body = JSON.parse(body); } catch (_) { body = null; } }
    // 仅处理带明确文字场景标识的“我的”/消息推荐。加密或数字场景不猜测，原样保留。
    const hints = [requestObject, body, obj, data].filter(x => x && typeof x === 'object')
      .flatMap(x => ['page', 'pageId', 'pageName', 'scene', 'sceneName', 'source'].map(k => x[k]))
      .filter(x => typeof x === 'string');
    const target = hints.some(x => /^(?:myjd|my_jd|mine|我的|messagecenter|message_center|消息中心)$/i.test(x));
    if (target) {
      for (const o of [obj, data]) {
        for (const key of ['wareInfoList', 'recommendList', 'items']) filter(o, key, () => false);
      }
    } else {
      console.log('[京东定向 v1] ' + fid + '：未确认页面场景，保留共享推荐');
    }
  }
  if (['start', 'startup', 'getSplash', 'queryMaterialAdverts'].includes(fid)) {
    // 仅清理可识别的广告候选；保留 startup 设备配置，不返回无结构空字典。
    for (const o of [obj, data]) {
      if (Array.isArray(o.images)) { filter(o, 'images', () => false); setExisting(o, 'showTimesDaily', 0); }
      filter(o, 'ads', () => false);
      filter(o, 'advertList', () => false);
    }
  }
  console.log('[京东定向 v1] ' + (fid || '未知接口') + '：修改 ' + changes + ' 项');
  return changes ? { body: JSON.stringify(obj) } : pass;
}
