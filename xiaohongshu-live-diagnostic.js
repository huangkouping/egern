/*
 * 小红书直播来源诊断（临时）
 * 仅记录可能携带直播状态的接口和字段，不修改响应内容。
 */
(function () {
  if (typeof $response === "undefined" || !$response.body) return $done({});
  const body = $response.body;
  const url = typeof $request !== "undefined" ? $request.url : "unknown";
  if (!/(直播|live|room_id|roomid)/i.test(body)) return $done({});
  let data;
  try {
    data = JSON.parse(body);
  } catch (_) {
    console.log(`[XHS直播诊断] 命中非JSON接口：${url}`);
    return $done({});
  }
  const hits = [];
  const walk = (value, path, depth) => {
    if (hits.length >= 30 || depth > 9 || value == null) return;
    if (Array.isArray(value)) {
      value.slice(0, 20).forEach((child, index) => walk(child, `${path}[${index}]`, depth + 1));
      return;
    }
    if (typeof value !== "object") return;
    for (const [key, child] of Object.entries(value)) {
      const childPath = path ? `${path}.${key}` : key;
      const keyHit = /(live|room_id|roomid|直播)/i.test(key);
      const valueHit = typeof child === "string" && /(直播|live)/i.test(child);
      if (keyHit || valueHit) {
        let preview;
        try {
          preview = typeof child === "object" ? JSON.stringify(child).slice(0, 160) : String(child).slice(0, 160);
        } catch (_) {
          preview = "[unavailable]";
        }
        hits.push(`${childPath}=${preview}`);
      }
      walk(child, childPath, depth + 1);
      if (hits.length >= 30) break;
    }
  };
  walk(data, "", 0);
  console.log(`[XHS直播诊断] URL: ${url}`);
  console.log(`[XHS直播诊断] 字段: ${hits.join(" | ") || "正文含直播/live但未定位字段"}`);
  return $done({});
})();
