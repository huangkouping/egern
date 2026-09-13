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
    console.log(`[小红书首页广告过滤] JSON 解析失败：${error}`);
    return $done({});
  }

  const hasOwn = (object, key) =>
    Object.prototype.hasOwnProperty.call(object, key);

  const isPromotedAd = (item) => {
    if (!item || typeof item !== "object") return false;

    // 小红书 App 首页投放内容的主要标记，以及兼容可能出现的同义字段。
    if (hasOwn(item, "ads_info") || hasOwn(item, "ad_info")) return true;
    if (item.is_ad === true || item.is_ad === 1 || item.is_ad === "1") return true;
    if (item.model_type === "ads" || item.model_type === "ad") return true;

    return false;
  };

  const isLiveCard = (item) => {
    if (!item || typeof item !== "object") return false;

    const modelType = String(item.model_type || "").toLowerCase();
    const itemType = String(item.type || "").toLowerCase();

    if (modelType === "live" || modelType.startsWith("live_")) return true;
    if (itemType === "live" || itemType.startsWith("live_")) return true;
    if (hasOwn(item, "live_info") || hasOwn(item, "live_card_info")) return true;

    return false;
  };

  const filterBlockedCards = (items) => {
    if (!Array.isArray(items)) return items;
    const filtered = items.filter(
      (item) => !isPromotedAd(item) && !isLiveCard(item)
    );
    const removed = items.length - filtered.length;
    if (removed > 0) {
      console.log(`[小红书首页过滤] 已移除 ${removed} 条广告或直播卡片`);
    }
    return filtered;
  };

  // App 常见结构：data 为数组；兼容 data.items / data.feeds 两种结构。
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
