/*
 * 小红书广告内容、直播与开屏广告过滤
 * 移除首页商业投放广告、首页直播卡片、开屏广告和广告素材库。
 * 保留普通图文、普通视频及普通商品笔记。
 * 适用于 Egern HTTP Response Script。
 * Updated: 2026-10-05 10:03
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

  const moduleEnv =
    typeof ctx !== "undefined" && ctx && ctx.env ? ctx.env : {};

  // 未设置、旧版 Egern 不支持设置或读取异常时，全部默认开启屏蔽。
  const envEnabled = (key) => {
    const value = moduleEnv[key];
    if (value === undefined || value === null || value === "") return true;
    return !["false", "0", "off", "no"].includes(
      String(value).trim().toLowerCase()
    );
  };

  const settings = {
    homeAds: envEnabled("BLOCK_HOME_ADS"),
    homeLive: envEnabled("BLOCK_HOME_LIVE"),
    medicalPromotion: envEnabled("BLOCK_MEDICAL_PROMOTION"),
    splashAds: envEnabled("BLOCK_SPLASH_ADS"),
    adResources: envEnabled("BLOCK_AD_RESOURCES"),
    adEngage: envEnabled("BLOCK_AD_ENGAGE"),
  };

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

    // 部分首页卡片本身仍是普通 video/note，但作者头像处带有直播标记。
    // 2026-10-03 抓包确认：直播信息位于 item.user.live，活动状态为 2。
    const isActiveLiveInfo = (liveInfo) => {
      if (!liveInfo || typeof liveInfo !== "object") return false;

      const liveStatus = Number(
        liveInfo.live_status ?? liveInfo.status ?? liveInfo.room_status
      );
      if (
        liveStatus === 1 ||
        liveStatus === 2 ||
        (Boolean(liveInfo.room_id) &&
          (Boolean(liveInfo.live_link) ||
            Boolean(liveInfo.stream_url) ||
            Boolean(liveInfo.cover)))
      ) {
        return true;
      }
      return false;
    };

    const authorLiveCandidates = [
      item.user?.live,
      item.author?.live,
      item.note_card?.user?.live,
      item.note_card?.author?.live,
    ];

    if (authorLiveCandidates.some(isActiveLiveInfo)) return true;

    // 少数普通视频未携带 user.live，但推荐轨迹明确来自直播笔记池。
    // 仅匹配直播专用轨迹标记，避免用宽泛的 "live" 误伤普通视频。
    const liveTrack = [
      item.recommend?.track_id,
      item.track_id_mix_rank,
      item.track_info,
      item.rec_extra_info,
    ]
      .filter((value) => typeof value === "string")
      .join(" ");

    if (/livenote|living_note|live_dssm/i.test(liveTrack)) {
      return true;
    }

    return false;
  };

  const isMedicalPromotion = (item) => {
    if (!item || typeof item !== "object") return false;

    const nickname = String(
      item.user?.nickname || item.author?.nickname || ""
    );
    const contentText = [item.title, item.name, item.desc]
      .filter((value) => typeof value === "string")
      .join(" ");
    const allText = `${nickname} ${contentText}`;

    // 必须同时具备医美项目和商业账号/营销表达，避免仅凭单个关键词误删。
    const medicalService =
      /双眼皮|眼袋|开眼角|隆鼻|鼻修复|植发|发际线|正畸|牙贴面|牙套|口腔|下巴后缩|嘴凸|祛斑|祛痘|吸脂|脂肪填充|玻尿酸|肉毒素|热玛吉|超声炮|医美|整形|抗衰|微整/i;
    const commercialAccount =
      /医生|医师|博士|主任|院长|助理|团队|医院|诊所|机构|医美|整形|美容|植发|正畸|口腔|牙贴面|眼袋|双眼皮|抗衰|微整|皮肤科|眼科|修复/i;
    const marketingLanguage =
      /预约|面诊|案例|招募|限时|名额|排班|加号|到院|价格|低价|优惠|免费|咨询|方案|改善|效果|术后|恢复|变美|设计/i;

    let score = 0;
    if (commercialAccount.test(nickname)) score += 3;
    if (medicalService.test(contentText)) score += 2;
    if (marketingLanguage.test(allText)) score += 2;

    return score >= 5;
  };

  const filterBlockedCards = (items) => {
    if (!Array.isArray(items)) return items;

    let adsRemoved = 0;
    let liveRemoved = 0;
    let medicalPromotionRemoved = 0;

    const filtered = items.filter((item) => {
      if (settings.homeAds && isPromotedAd(item)) {
        adsRemoved += 1;
        return false;
      }
      if (settings.homeLive && isLiveCard(item)) {
        liveRemoved += 1;
        return false;
      }
      if (settings.medicalPromotion && isMedicalPromotion(item)) {
        medicalPromotionRemoved += 1;
        return false;
      }
      return true;
    });

    // 每批都输出，便于区分“规则未命中”与“小红书本地缓存/预加载”。
    console.log(
      `[小红书首页过滤 v8] 扫描 ${items.length} 条，广告 ${adsRemoved} 条，直播 ${liveRemoved} 条，疑似医美推广 ${medicalPromotionRemoved} 条，保留 ${filtered.length} 条`
    );

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

  const filterAdResources = () => {
    if (!Array.isArray(payload?.data)) return;

    const groups = payload.data.length;
    const resources = payload.data.reduce(
      (sum, group) =>
        sum + (Array.isArray(group?.resources) ? group.resources.length : 0),
      0
    );

    payload.data = [];
    console.log(
      `[小红书广告素材过滤] 清除 ${groups} 组、${resources} 个素材链接`
    );
  };

  const filterAdsEngage = () => {
    if (!payload?.data || typeof payload.data !== "object") return;

    const images = Array.isArray(payload.data.default_img_list)
      ? payload.data.default_img_list.length
      : 0;

    payload.data.type = -1;
    payload.data.forward = "";
    payload.data.keyword_list = [];
    payload.data.default_img_list = [];
    payload.data.landing_page_flag = 0;
    payload.data.forward_timing_flag = 0;
    payload.data.deeplink_forward_timing_flag = 0;

    console.log(`[小红书广告互动过滤] 清除默认图片 ${images} 张`);
  };

  if (requestUrl.includes("/system_service/splash_config")) {
    if (settings.splashAds) filterSplashConfig();
  } else if (
    requestUrl.includes("/system_service/splash_online_decision") ||
    requestUrl.includes("/system_service/splash_async_optimization")
  ) {
    if (settings.splashAds) rejectSplashDecision();
  } else if (requestUrl.includes("/api/sns/v1/ads/resource")) {
    if (settings.adResources) filterAdResources();
  } else if (requestUrl.includes("/api/sns/v1/tag/ads_engage")) {
    if (settings.adEngage) filterAdsEngage();
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
