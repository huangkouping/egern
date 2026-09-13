/*
 * 小红书首页广告与直播过滤
 * 精确适配 rec.xiaohongshu.com/api/sns/v6/homefeed
 * 保留普通图文和视频；删除广告及带 user.live 的直播推荐卡片。
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
    console.log("[小红书首页过滤] JSON解析失败：" + error);
    return $done({});
  }

  const isAd = (item) => {
    if (!item || typeof item !== "object") return false;
    return (
      item.is_ads === true ||
      item.is_ads === 1 ||
      item.is_ads === "1" ||
      item.is_ad === true ||
      item.is_ad === 1 ||
      item.is_ad === "1" ||
      (item.ads_info && typeof item.ads_info === "object") ||
      (item.ad_info && typeof item.ad_info === "object") ||
      item.model_type === "ads" ||
      item.model_type === "ad"
    );
  };

  const isLive = (item) => {
    if (!item || typeof item !== "object") return false;

    // 2026-09-13 实际抓包字段：
    // data[].user.live = { room_id, live_status, live_link, ... }
    const live = item.user && item.user.live;
    if (!live || typeof live !== "object") return false;

    return (
      Object.keys(live).length > 0 &&
      (live.room_id ||
        live.user_id ||
        live.live_link ||
        live.live_status === 1 ||
        live.live_status === 2 ||
        live.live_status === "1" ||
        live.live_status === "2")
    );
  };

  const filterItems = (items) => {
    if (!Array.isArray(items)) return items;

    let adsRemoved = 0;
    let liveRemoved = 0;

    const filtered = items.filter((item) => {
      if (isAd(item)) {
        adsRemoved += 1;
        return false;
      }
      if (isLive(item)) {
        liveRemoved += 1;
        return false;
      }
      return true;
    });

    console.log(
      "[小红书首页过滤] 扫描 " +
        items.length +
        " 条，删除广告 " +
        adsRemoved +
        " 条，删除直播 " +
        liveRemoved +
        " 条"
    );

    return filtered;
  };

  if (Array.isArray(payload.data)) {
    payload.data = filterItems(payload.data);
  } else if (payload.data && typeof payload.data === "object") {
    if (Array.isArray(payload.data.items)) {
      payload.data.items = filterItems(payload.data.items);
    }
    if (Array.isArray(payload.data.feeds)) {
      payload.data.feeds = filterItems(payload.data.feeds);
    }
  }

  return $done({ body: JSON.stringify(payload) });
})();
