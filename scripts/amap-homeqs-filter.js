/**
 * Egern Script for Amap home_qs (首页 AI 流, text/event-stream)
 * 逐事件解析 SSE：布局事件只保留探索本地区域，非探索模块载荷直接丢弃。
 * 任何异常原样放行 (fail-open)。
 */

const KEEP_REGIONS = new Set(['MdCard_QS_0', 'MdCard_Explore_0']);

export default async function (ctx) {
  const { response } = ctx ?? {};
  if (!response?.body) return undefined;

  try {
    const rawText = typeof response.body === 'string'
      ? response.body
      : new TextDecoder('utf-8').decode(response.body);

    if (!rawText.includes('MdCard_')) return undefined;

    let modified = false;
    const outLines = [];

    for (const line of rawText.split('\n')) {
      if (!line.startsWith('data: ') || line.length < 10) {
        outLines.push(line);
        continue;
      }
      let evt;
      try { evt = JSON.parse(line.slice(6)); } catch (_) {
        outLines.push(line);
        continue;
      }

      const d = evt?.component?.data?.data;
      if (d && typeof d === 'object') {
        // 布局事件：区域只留探索本地
        if (Array.isArray(d.regions?.content)) {
          const before = d.regions.content.length;
          d.regions.content = d.regions.content.filter(r => KEEP_REGIONS.has(r));
          if (d.regions.content.length !== before) modified = true;
        }
        // 模块载荷事件：丢弃非探索模块的数据（瀑布流/推广容器本体）
        if (d.modules && typeof d.modules === 'object' && !Array.isArray(d.modules)) {
          for (const k of Object.keys(d.modules)) {
            if (!KEEP_REGIONS.has(k)) { delete d.modules[k]; modified = true; }
          }
        }
      }

      outLines.push('data: ' + JSON.stringify(evt));
    }

    if (modified) {
      return { body: outLines.join('\n') };
    }
    return undefined;
  } catch (_) {
    return undefined;
  }
}
