/*
 * 小红书首页广告、直播与开屏广告过滤
 * 移除首页商业投放广告、首页直播卡片和开屏广告候选素材。
 * 保留普通图文、普通视频及普通商品笔记。
 * 适用于 Egern HTTP Response Script。
 * Updated: 2026-10-03
 */

(function () {
  if (typeof $response === "undefined" || !$response.body) {
    return $done({});
  }

  let payload;
  try {
    payload = JSON.parse($response.body);
  } catch (error) {
    console.log(`[小红书过滤] JSON 解析失败：${error}`);
    return $done({});
  }

  const requestUrl = String(
    typeof $request !== "undefined" && $request.url ? $request.url : ""
  );

  const hasOwn = (object, key) =>
    Object.prototype.hasOwnProperty.call(object, key);

  const boolLikeTrue = (value) =>
    value === true || value === 1 || value === "1";

  const isPromotedAd = (item) => {
    if (!item || typeof item !== "object") return false;

    const modelType = String(item.model_type || "").toLowerCase();

    if (boolLikeTrue(item.is_ads) || boolLikeTrue(item.is_ad)) return true;
    if (hasOwn(item, "ads_info") || hasOwn(item, "ad_info")) return true;
    if (modelType === "ads" || modelType === "ad") return true;

    return false;
  };

  const isLiveCard = (item) => {
    if (!item || typeof item !== "object") return false;

    const modelType = String(item.model_type || "").toLowerCase();
    const itemType = String(item.type || "").toLowerCase();

    if (modelType === "live" || modelType.startsWith("live_")) return true;
    if (itemType === "live" || itemType.startsWith("live_")) return true;

    if (
      hasOwn(item, "live") ||
      hasOwn(item, "live_info") ||
      hasOwn(item, "live_card_info")
    ) {
      return true;
    }

    return false;
  };

  const filterBlockedCards = (items) => {
    if (!Array.isArray(items)) return items;

    let adsRemoved = 0;
    let liveRemoved = 0;

    const filtered = items.filter((item) => {
      if (isPromotedAd(item)) {
        adsRemoved += 1;
        return false;
      }
      if (isLiveCard(item)) {
        liveRemoved += 1;
        return false;
      }
      return true;
    });

    if (adsRemoved > 0 || liveRemoved > 0) {
      console.log(
        `[小红书首页过滤] 广告 ${adsRemoved} 条，直播 ${liveRemoved} 条，保留 ${filtered.length} 条`
      );
    }

    return filtered;
  };

  const filterSplashConfig = () => {
    if (!payload?.data || typeof payload.data !== "object") return;

    const groupAds = Array.isArray(payload.data.ads_groups)
      ? payload.data.ads_groups.reduce(
          (sum, group) => sum + (Array.isArray(group?.ads) ? group.ads.length : 0),
          0
        )
      : 0;
    const biddingAds = Array.isArray(payload.data.bidding_ads)
      ? payload.data.bidding_ads.length
      : 0;

    payload.data.ads_groups = [];
    payload.data.bidding_ads = [];

    console.log(
      `[小红书开屏过滤] 清除候选广告 ${groupAds + biddingAds} 条`
    );
  };

  const rejectSplashDecision = () => {
    if (!payload?.data || typeof payload.data !== "object") return;

    payload.data.ads_id = "-1";
    payload.data.track_id = "";
    payload.data.track_url = "";
    console.log("[小红书开屏过滤] 已取消本次开屏广告投放");
  };

  if (requestUrl.includes("/system_service/splash_config")) {
    filterSplashConfig();
  } else if (
    requestUrl.includes("/system_service/splash_online_decision") ||
    requestUrl.includes("/system_service/splash_async_optimization")
  ) {
    rejectSplashDecision();
  } else if (Array.isArray(payload?.data)) {
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
