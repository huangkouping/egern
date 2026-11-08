/* 小红书搜索结果广告与直播过滤 · 复用首页精准判定逻辑 · 2026-11-08 */
(function () {
  if (typeof $response === "undefined" || !$response.body) return $done({});
  const url = String(typeof $request !== "undefined" ? ($request.url || "") : "");
  if (!/\/search\//i.test(url)) return $done({});
  let payload;
  try { payload = JSON.parse($response.body); } catch (_) { return $done({}); }
  const env = typeof ctx !== "undefined" && ctx && ctx.env ? ctx.env : {};
  const enabled = (key) => !["false","0","off","no"].includes(String(env[key] ?? "true").toLowerCase());
  const blockAds = enabled("BLOCK_SEARCH_ADS");
  const blockLive = enabled("BLOCK_SEARCH_LIVE");
  const blockMedical = enabled("BLOCK_MEDICAL_PROMOTION");
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


  // 搜索结果的外层包装与首页不同，逐层检查卡片本身及 note_card。
  const searchCard = (item) => {
    if (!item || typeof item !== "object") return null;
    const nodes = [item, item.note_card, item.card, item.content, item.note, item.note_info].filter(x => x && typeof x === "object");
    if (blockAds && nodes.some(isPromotedAd)) return "广告";
    if (blockLive && nodes.some(isLiveCard)) return "直播";
    if (blockMedical && nodes.some(isMedicalPromotion)) return "医美";
    return null;
  };
  let scanned = 0, ads = 0, live = 0, medical = 0;
  const filter = (arr) => {
    if (!Array.isArray(arr)) return;
    scanned += arr.length;
    const kept = arr.filter(item => {
      const kind = searchCard(item);
      if (kind === "广告") ads++;
      else if (kind === "直播") live++;
      else if (kind === "医美") medical++;
      return !kind;
    });
    arr.splice(0, arr.length, ...kept);
  };
  const data = payload?.data;
  if (Array.isArray(data)) filter(data);
  else if (data && typeof data === "object") {
    for (const key of ["items","notes","feeds","results","list","note_list","search_results"]) filter(data[key]);
    for (const group of ["result","search_result"]) {
      if (data[group] && typeof data[group] === "object")
        for (const key of ["items","notes","feeds","list"]) filter(data[group][key]);
    }
  }
  console.log("[小红书搜索测试] 扫描 " + scanned + "，广告 " + ads + "，直播 " + live + "，医美 " + medical);
  return ads + live + medical ? $done({body:JSON.stringify(payload)}) : $done({});
})();
