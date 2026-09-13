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

  const containsAdMarker = (value, depth = 0) => {
    if (!value || typeof value !== "object" || depth > 8) return false;

    for (const [rawKey, child] of Object.entries(value)) {
      const key = rawKey.toLowerCase();
      const normalized = String(child).toLowerCase();

      // 商业投放标记可能位于 item、note_card 或推荐元数据内。
      if (
        ["ads_info", "ad_info", "advertise_info", "advertisement_info",
         "promotion_info", "sponsor_info", "commercial_info"].includes(key) &&
        hasMeaningfulValue(child)
      ) {
        return true;
      }

      if (
        ["is_ad", "is_ads", "is_advertise", "is_sponsored", "is_promotion"]
          .includes(key) &&
        (child === true || child === 1 || child === "1")
      ) {
        return true;
      }

      if (
        ["model_type", "card_type", "feed_type"].includes(key) &&
        ["ad", "ads", "advertise", "advertisement", "sponsor", "sponsored",
         "promotion", "commercial"].includes(normalized)
      ) {
        return true;
      }

      // 只在角标/标签元数据中识别广告文案，不检查标题和正文。
      if (
        /(tag|badge|label|icon|subscript|corner|mark)/i.test(key) &&
        typeof child === "string" &&
        ["广告", "推广", "赞助", "商业推广"].some((word) => child.includes(word))
      ) {
        return true;
      }

      if (containsAdMarker(child, depth + 1)) return true;
    }

    return false;
  };

  const isPromotedAd = (item) => containsAdMarker(item);


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

      // 新版 App 会把“直播”仅作为头像角标/标签返回。
      // 只检查角标、标签等元数据字段，不检查笔记标题和正文，避免误伤普通内容。
      if (
        /(tag|badge|label|icon|subscript|corner|mark)/i.test(key) &&
        typeof child === "string" &&
        (child.includes("直播") || /(^|[^a-z])live([^a-z]|$)/i.test(child))
      ) {
        return true;
      }

      if (
        /(tag|badge|label|icon|subscript|corner|mark)/i.test(key) &&
        child &&
        typeof child === "object" &&
        JSON.stringify(child).includes("直播")
      ) {
        return true;
      }

      if (containsLiveMarker(child, depth + 1)) return true;
    }

    return false;
  };

  // 临时诊断：输出仍被保留卡片的关键元数据，避免记录图片、令牌和长正文。
  const diagnosticMeta = (value, path = "item", depth = 0, hits = []) => {
    if (!value || typeof value !== "object" || depth > 7 || hits.length >= 60) {
      return hits;
    }

    for (const [rawKey, child] of Object.entries(value)) {
      const key = rawKey.toLowerCase();
      const childPath = `${path}.${rawKey}`;
      const relevant =
        /(ad|ads|advert|promot|sponsor|commercial|business|live|room|tag|badge|label|icon|subscript|corner|mark|reason|recommend|type|status|state|style|source)/i.test(key);

      if (relevant && (typeof child !== "object" || child === null)) {
        let preview = String(child);
        if (preview.length > 100) preview = preview.slice(0, 100);
        hits.push(`${childPath}=${preview}`);
      }

      if (child && typeof child === "object") {
        diagnosticMeta(child, childPath, depth + 1, hits);
      }
      if (hits.length >= 60) break;
    }
    return hits;
  };

  const getNickname = (item) =>
    item?.note_card?.user?.nickname ||
    item?.note_card?.user?.nick_name ||
    item?.user?.nickname ||
    item?.user?.nick_name ||
    "未知作者";

  const filterBlockedCards = (items) => {
    if (!Array.isArray(items)) return items;

    const filtered = [];
    let removed = 0;

    items.forEach((item, index) => {
      const ad = isPromotedAd(item);
      const live = containsLiveMarker(item);

      if (ad || live) {
        removed += 1;
        console.log(
          `[XHS过滤详情][删除${index}][${getNickname(item)}] 原因=${ad ? "广告" : "直播"}`
        );
        return;
      }

      filtered.push(item);
      const noteCard = item?.note_card || {};
      const user = noteCard?.user || item?.user || {};
      const meta = diagnosticMeta(item).join(" | ");
      console.log(
        `[XHS诊断][保留${index}][${getNickname(item)}] 顶层=${Object.keys(item || {}).join(",")}; note_card=${Object.keys(noteCard).join(",")}; user=${Object.keys(user).join(",")}; 元数据=${meta || "无"}`
      );
    });

    console.log(
      `[小红书首页过滤] 本批扫描 ${items.length} 条，移除 ${removed} 条，保留 ${filtered.length} 条`
    );
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
