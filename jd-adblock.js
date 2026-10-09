/* 京东去广告©️ v3 — Egern 原生 Response Script。 */
export default async function (ctx) {
  const request = ctx.request;
  if (!request || !ctx.response) return;
  const allowed = /^https?:\/\/api\.m\.jd\.com\/(?:client\.action|api)?(?:\?|$)/;
  if (!allowed.test(request.url)) return;
  let fid = '';
  const match = request.url.match(/[?&]functionId=([^&]+)/);
  if (match) { try { fid = decodeURIComponent(match[1]); } catch (_) {} }
  console.log('[京东去广告 v3] 已命中：' + (fid || 'API'));
  const original = await ctx.response.text();
  const pass = { body: original };
  if (!original) { console.log('[京东去广告 v3] 空响应'); return pass; }
  let obj;
  try { obj = JSON.parse(original); } catch (_) {
    console.log('[京东去广告 v3] 非 JSON，原样放行，长度：' + original.length);
    return pass;
  }
  if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return pass;
  let changed = 0;
  function set(o, key, value) {
    if (o && Object.prototype.hasOwnProperty.call(o, key) && JSON.stringify(o[key]) !== JSON.stringify(value)) {
      o[key] = value; changed++;
    }
  }
  function remove(o, key) {
    if (o && Object.prototype.hasOwnProperty.call(o, key)) { delete o[key]; changed++; }
  }
  function filter(o, key, keep) {
    if (!o || !Array.isArray(o[key])) return;
    const next = o[key].filter(keep);
    if (next.length !== o[key].length) { changed += o[key].length - next.length; o[key] = next; }
  }
  if (!fid && request.body && typeof request.text === 'function') {
    let requestText = '';
    try { requestText = await request.text(); } catch (_) {}
    const m = requestText.match(/(?:^|&)functionId=([^&]+)/);
    if (m) { try { fid = decodeURIComponent(m[1]); } catch (_) {} }
    else { try { fid = JSON.parse(requestText).functionId || ''; } catch (_) {} }
  }
  const p = obj.data && typeof obj.data === 'object' && !Array.isArray(obj.data) ? obj.data : obj;

  // 抓包中的全局配置：只关闭消息推荐，不动消息、物流、客服开关。
  if (fid === 'basicConfig' || (p.JDMessage && p.JDMyJd && p.JDUniformRecommend)) {
    const message = p.JDMessage || {};
    set(message.recommendfloor, 'support_recommendfloor', '0');
    set(message.recommendfeeds, 'support_recommendfeeds', '0');
    set(message.recommendfeeds, 'fetchfeeds_api', '0');
    set(p.JDMyJd && p.JDMyJd.recommendPreloadSwitchV15110, 'value', '0');
    set(p.JDUniformRecommend && p.JDUniformRecommend.JDUniformRecommendmMyJdCache, 'JDUniformRecommendmMyJdCache', '0');
  }
  // 抓包中的普通/深色导航，保留其余项及原有顺序、标识。
  if (fid === 'readCustomSurfaceList' || (obj.result && obj.result.modeMap)) {
    const modes = obj.result && obj.result.modeMap;
    const before = changed;
    if (modes) Object.keys(modes).forEach(k => {
      filter(modes[k], 'navigationAll', i => !i || i.functionId !== 'find');
      if (Array.isArray(modes[k].navigationAll)) modes[k].navigationAll.forEach((i, n) => {
        if (i && typeof i.position === 'number') set(i, 'position', n + 1);
      });
    });
    if (changed > before) {
      const result = obj.result;
      // 数组、顺序字符串和位置必须一致，避免仍按五栏配置渲染。
      if (typeof result.navigationOrder === 'string') set(result, 'navigationOrder', result.navigationOrder.split(',').filter(x => x !== 'find').join(','));
      if (typeof result.paramValues === 'string') set(result, 'paramValues', result.paramValues.split('_').filter(x => x !== 'Discover').join('_'));
      if (result.fromLocalCache === '1') set(result, 'fromLocalCache', '0');
      console.log('[京东去广告 v3] 导航顺序：' + (result.navigationOrder || '已更新'));
    }
  }
  // 首页仅移除悬浮推广，正常商品、搜索、分类均保留。
  if (fid === 'welcomeHome' || (Array.isArray(p.floorList) && p.naviVer !== undefined)) {
    filter(p, 'floorList', f => !f || !['float', 'bottomXview'].includes(f.type));
  }
  // 首页/我的的营销弹层配置；不处理支付、订单及其他页面的弹层。
  if (fid === 'xview2Config' || (Array.isArray(p.targets) && p.targets.some(t => t && t.targetName === 'JDMainPageViewController'))) {
    if (Array.isArray(p.targets)) p.targets.forEach(t => {
      if (t && ['JDMainPageViewController', 'MyJdHomeViewController'].includes(t.targetName)) set(t, 'layers', []);
    });
  }
  // 推荐流内的满意度调研开关，不清空首页商品流。
  if (/^uniformRecommend\d+$/.test(fid)) {
    set(p.tsConfig, 'manyiduwenjuan', '0');
  }
  // 兼容旧版我的页接口：仅推荐区及推广浮窗。
  const mineFloors = Array.isArray(p.floors) && p.floors.some(f => f && ['userinfo', 'basefloorinfo'].includes(f.mId));
  if (/^personinfoBusiness$/i.test(fid) || mineFloors) {
    filter(p, 'floors', f => !f || !(['recommendfloor', 'recommendFloor'].includes(f.mId) || ['为你推荐', '潮流好货', '潮流好物'].includes(f.title)));
    if (Array.isArray(p.floors)) p.floors.forEach(f => {
      if (f && f.mId === 'basefloorinfo' && f.data) {
        ['commonPopup', 'commonPopup_dynamic', 'floatLayer'].forEach(k => remove(f.data, k));
        ['commonWindows', 'commonTips'].forEach(k => set(f.data, k, []));
      }
    });
  }
  // 旧版我的推荐专用接口；不会匹配首页 uniformRecommend9。
  if (fid === 'uniformRecommend6') {
    ['wareInfoList', 'data', 'recommendList'].forEach(k => { if (Array.isArray(p[k])) set(p, k, []); });
  }
  // 开屏：保留响应状态和设备配置，只清空广告候选素材。
  if (['start', 'startup', 'getSplash'].includes(fid)) {
    [obj, p].forEach(o => {
      if (Array.isArray(o.images)) { set(o, 'images', []); set(o, 'showTimesDaily', 0); }
    });
  }
  console.log('[京东去广告 v3] ' + (fid || '配置') + '：处理 ' + changed + ' 项');
  return changed ? { body: JSON.stringify(obj) } : pass;
}
