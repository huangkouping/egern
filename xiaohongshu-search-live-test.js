/* 小红书搜索结果直播过滤 🅗 · 独立测试版 2026-11-08
 * 仅处理搜索结果 JSON，避免修改首页及其他功能。
 */
(function () {
  if (typeof $response === "undefined" || !$response.body) return $done({});
  const url = String(typeof $request !== "undefined" ? ($request.url || "") : "");
  if (!/\/search\//i.test(url)) return $done({});
  let json;
  try { json = JSON.parse($response.body); } catch (_) { return $done({}); }
  const env = typeof ctx !== "undefined" && ctx && ctx.env ? ctx.env : {};
  if (String(env.BLOCK_SEARCH_LIVE ?? "true").toLowerCase() === "false") return $done({});
  const own = (o, k) => Object.prototype.hasOwnProperty.call(o, k);
  const liveStatus = (v) => {
    if (!v || typeof v !== "object") return false;
    const s = Number(v.live_status ?? v.status ?? v.room_status);
    return s === 1 || s === 2 || (!!v.room_id && !!(v.live_link || v.stream_url || v.cover));
  };
  const isLive = (o) => {
    if (!o || typeof o !== "object") return false;
    const candidates = [o, o.note_card, o.card, o.content].filter(v => v && typeof v === "object");
    return candidates.some(v => {
      const type = String(v.model_type || v.type || v.card_type || "").toLowerCase();
      if (/^(live|live[_-].*|.*[_-]live)$/.test(type)) return true;
      if (own(v, "live_card_info") || own(v, "live_room_info")) return true;
      if (liveStatus(v.live_info) || liveStatus(v.live)) return true;
      return [v.user?.live, v.author?.live, v.note_card?.user?.live, v.note_card?.author?.live].some(liveStatus);
    });
  };
  let scanned = 0, removed = 0;
  const filter = (arr) => {
    if (!Array.isArray(arr)) return;
    scanned += arr.length;
    const kept = arr.filter(v => { if (isLive(v)) { removed++; return false; } return true; });
    arr.splice(0, arr.length, ...kept);
  };
  const data = json?.data;
  if (Array.isArray(data)) filter(data);
  else if (data && typeof data === "object") {
    for (const key of ["items", "notes", "feeds", "results", "list"]) filter(data[key]);
    if (data.result && typeof data.result === "object")
      for (const key of ["items", "notes", "feeds", "list"]) filter(data.result[key]);
  }
  console.log("[小红书搜索直播测试] 扫描 " + scanned + " 条，移除 " + removed + " 条");
  return removed ? $done({body: JSON.stringify(json)}) : $done({});
})();
