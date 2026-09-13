/*
 * 小红书首页信息流广告与直播过滤
 * 移除带有明确广告标识的卡片和首页直播卡片，保留普通图文、视频及普通商品笔记。
 * 适用于 Egern 的 HTTP Response Script。
 * Updated: 2026-09-13
 */

(function () {
  if (typeof $response === "undefined" || !$response.body) {
    return $done({});
  }

  let payload;
  try {
    payload = JSON.parse($response.body);
  } catch (error) {
    console.log(`[小红书首页过滤] JSON 解析失败：${error}`);
    return $done({});
  }

  const hasOwn = (object, key) =>
    Object.prototype.hasOwnProperty.call(object, key);

  const hasMeaningfulValue = (value) => {
    if (value === null || value === undefined || value === false) return false;
    if (value === 0 || value === "0" || value === "") return false;
    if (Array.isArray(value)) return value.length > 0;
    if (typeof value === "object") return Object.keys(value).length > 0;
    return true;
  };

  const isPromotedAd = (item) => {
    if (!item || typeof item !== "object") return false;

    if (hasOwn(item, "ads_info") || hasOwn(item, "ad_info")) return true;
    if (item.is_ad === true || item.is_ad === 1 || item.is_ad === "1") return true;
    if (item.model_type === "ads" || item.model_type === "ad") return true;

    return false;
  };

  // 直播标记经常藏在 note_card、user 等嵌套对象中，不能只检查卡片最外层。
  const containsLiveMarker = (value, depth = 0) => {
    if (!value || typeof value !== "object" || depth > 8) return false;

    for (const [rawKey, child] of Object.entries(value)) {
      const key = rawKey.toLowerCase();

      if (
        ["live_info", "live_card_info", "live_room_info", "live_room", "live_data"]
          .includes(key) &&
        hasMeaningfulValue(child)
      ) {
        return true;
      }

      if (
        ["live_id", "live_room_id", "room_id"].includes(key) &&
        hasMeaningfulValue(child)
      ) {
        return true;
      }

      if (
        key === "is_live" &&
        (child === true || child === 1 || child === "1")
      ) {
        return true;
      }

      if (
        ["live_status", "live_state"].includes(key) &&
        ["1", "live", "living", "on", "online"].includes(
          String(child).toLowerCase()
        )
      ) {
        return true;
      }

      if (
        ["model_type", "type", "card_type"].includes(key) &&
        (String(child).toLowerCase() === "live" ||
          String(child).toLowerCase().startsWith("live_"))
      ) {
        return true;
      }

      if (containsLiveMarker(child, depth + 1)) return true;
    }

    return false;
  };

  const filterBlockedCards = (items) => {
    if (!Array.isArray(items)) return items;

    const filtered = items.filter(
      (item) => !isPromotedAd(item) && !containsLiveMarker(item)
    );

    const removed = items.length - filtered.length;
    if (removed > 0) {
      console.log(`[小红书首页过滤] 已移除 ${removed} 条广告或直播卡片`);
    }
    return filtered;
  };

  if (Array.isArray(payload?.data)) {
    payload.data = filterBlockedCards(payload.data);
  } else if (payload?.data && typeof payload.data === "object") {
    if (Array.isArray(payload.data.items)) {
      payload.data.items = filterBlockedCards(payload.data.items);
    }
    if (Array.isArray(payload.data.feeds)) {
      payload.data.feeds = filterBlockedCards(payload.data.feeds);
    }
  }

  return $done({ body: JSON.stringify(payload) });
})();
