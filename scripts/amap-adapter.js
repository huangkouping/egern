/**
 * Egern Adapter Script for Amap (高德地图)
 * ES Module specification
 * 
 * 严格对齐正式版核心逻辑：
 * 1. aocs: 顶层 40+ 键彻底剔除，嵌套 JSON 字符串全量清洗
 * 2. poi_detail: 采用与正式版一致的白名单机制，非基础骨架与经营模块一律剔除
 * 3. profile: 剔除钱包/提示，并精准过滤 cardList 运营卡片
 */

// POI 详情页保留白名单（与正式版 keep_module 核心集合对齐）
const POI_KEEP_MODULES = new Set([
  // 基础骨架
  'baseInfo', 'poiDetailCommonConfig', 'navbarMore', 'backToTop',
  'poiDetailBottomBar', 'poiMapModule', 'anchor', 'reSortContentAndSimilar',
  'comprehensiveEditEntrance', 'functionZone', 'poiTipBar', 'floatTelButton',
  'footer_tel_button', 'footer_retain_button',
  // UGC、评价与图集
  'attractGalleryInfo', 'combineReviews', 'evaluateVO', 'reviews',
  'inviteReview', 'seriousPublicExperience', 'societyPublicExperience',
  'poiDetailRankUpCard', 'travelGuideAndQa', 'poiDetailAQModule',
  'AIStreetTips', 'expertNote', 'recommend_food', 'shopNews', 'mallNews', 'shopBaseCase',
  // 本地点介绍、百科与专属数据
  'wikiInfo', 'wikiInfoBelow', 'poiDetailNote', 'poiDetailWikiAndLOI',
  'human_traffic', 'floorGuideGbf', 'houseEvaluationInfo', 'scenic_mustplay',
  'hotelGraphicDetail', 'homestayGraphicDetail', 'hotelFacilities', 'hotelMustRead',
  // 本店服务、指引与自有预订
  'enhanceIMQuestions', 'shopBasePerson', 'shopServiceBffvo', 'service_process',
  'storeDirections', 'shopFindWayGuide', 'shopQualifications', 'businessQualifications',
  'scenic_ticket', 'movieBookingShelf', 'hotelRooms', 'ktvBookingShelf',
  'venueBookingShelfModule', 'reserveShelf', 'DinnerBottomBar', 'poiDetailAppointmentRegister'
]);

export default async function (ctx) {
  const { response, env } = ctx ?? {};
  const mode = env?.MODE;

  if (!response?.body || !mode) {
    return undefined;
  }

  try {
    const rawText = typeof response.body === 'string'
      ? response.body
      : new TextDecoder('utf-8').decode(response.body);

    const json = JSON.parse(rawText);
    if (!json || typeof json !== 'object') return undefined;

    let modified = false;

    // 1. 云控配置全量深度清洗 (aocs/updatable/1)
    if (mode === 'aocs') {
      const data = json.data;
      if (data && typeof data === 'object') {
        // 对齐正式版 40+ 个顶层冗余/推广键
        const dropKeys = [
          'adStatementConfig', 'adCustomerRetainArchitecture', 'adImEntryConfig',
          'adVenueConfig', 'adPerfSwitch', 'EndNaviC3AdCard', 'infoCpcReport',
          'hotsaleConfig', 'marketing_resource_config', 'coupon_risk_asac',
          'commonCouponSceneLog', 'sug_coupon_opt', 'giftEntryConfig',
          'splashscreen', 'SplashScreenControl', 'splashview_config',
          'feedback_banner', 'TrainOrderBanner', 'nearby_business_popup',
          'shortcut_popup_frequency', 'tel_retention_popup', 'hotel_activity',
          'taxi_activity', 'hotel_privilege', 'sportsActivityConfig',
          'activity_qingke_contry_control', '920bestwishes', 'custom_consultdata',
          'free_ride', 'homepage_resource_config', 'home_message_guide',
          'hotel_tipsicon', 'sur_bar', 'nearby_map_entry_guide', 'comment_info',
          'small_biz_index', 'small_biz_fun', 'setpagesearch', 'wallet'
        ];
        for (const k of dropKeys) {
          if (k in data) {
            delete data[k];
            modified = true;
          }
        }

        // 嵌套配置 1: amap_basemap_config 内部广告与活动全量切除
        if (typeof data.amap_basemap_config?.value === 'string') {
          try {
            const inner = JSON.parse(data.amap_basemap_config.value);
            const innerDrop = [
              'splash', 'ai_splash', 'ipSquare_window_video_config',
              'usercenter_lottery_switch', 'coins_lottery', 'coins_wish',
              'newYearLotteryTips', 'mileage_coin_scene', 'licheng_coin_mine_entry',
              'member_grabbing', 'vip_checkout_welfare_dialog_config',
              'task_poi_card_coupon_switch', 'jay_act', 'pointExchangeCenter',
              'batchCheckIn', 'batchCheckIn_new', 'fireworks', 'mainIcon',
              'mainBubble', 'blueBar', 'presetWord', 'homepage_tabguide',
              'suit_set_popup', 'pop_selection', 'ThemeSquareSwiperCanJumpUrlList'
            ];
            let innerMod = false;
            for (const ik of innerDrop) {
              if (ik in inner) {
                delete inner[ik];
                innerMod = true;
              }
            }
            if (innerMod) {
              data.amap_basemap_config.value = JSON.stringify(inner);
              modified = true;
            }
          } catch (_) {}
        }

        // 嵌套配置 2: 搜索历史推荐与附近热词 (his_input_tip)
        if (typeof data.his_input_tip?.value === 'string') {
          try {
            const inner = JSON.parse(data.his_input_tip.value);
            if (inner && typeof inner === 'object') {
              delete inner.channel_zhitiao;
              inner.his_recommend_bangdan = 0;
              if (inner.nearby_hotword) inner.nearby_hotword.search_detail = 0;
              data.his_input_tip.value = JSON.stringify(inner);
              modified = true;
            }
          } catch (_) {}
        }

        // 嵌套配置 3: 导航结束运营按钮 (navi_end)
        if (typeof data.navi_end?.value === 'string') {
          try {
            const inner = JSON.parse(data.navi_end.value);
            if (inner && typeof inner === 'object' && 'operator_btns' in inner) {
              delete inner.operator_btns;
              data.navi_end.value = JSON.stringify(inner);
              modified = true;
            }
          } catch (_) {}
        }
      }
    }

    // 2. 地点详情页清洗 (search/poi/detail) —— 采用原生白名单过滤
    else if (mode === 'poi_detail') {
      const data = json.data;
      if (data && typeof data === 'object') {
        // 清洗 modules：只保留白名单以内的核心功能/UGC模块
        if (data.modules && typeof data.modules === 'object') {
          const modKeys = Object.keys(data.modules);
          for (const mk of modKeys) {
            if (!POI_KEEP_MODULES.has(mk)) {
              delete data.modules[mk];
              modified = true;
            }
          }
        }
        // 清洗 regions 引用：同步滤除非白名单模块
        if (data.regions && typeof data.regions === 'object') {
          for (const rk of Object.keys(data.regions)) {
            if (Array.isArray(data.regions[rk])) {
              data.regions[rk] = data.regions[rk].filter(
                item => typeof item !== 'string' || POI_KEEP_MODULES.has(item)
              );
              modified = true;
            }
          }
        }
      }
    }

    // 3. 个人中心清洗 (dsp/profile/index/nodefaasv3)
    else if (mode === 'profile') {
      const data = json.data;
      if (data && typeof data === 'object') {
        if ('tipData' in data) { delete data.tipData; modified = true; }
        if ('wallet' in data) { delete data.wallet; modified = true; }
        // 过滤 cardList 仅保留合法的基础卡片
        if (Array.isArray(data.cardList)) {
          const beforeLen = data.cardList.length;
          data.cardList = data.cardList.filter(
            card => card?.dataKey === 'MineNewFootprintCard' || card?.dataKey === 'MineNewBEntranceCardV4'
          );
          if (data.cardList.length !== beforeLen) modified = true;
        }
      }
    }

    if (modified) {
      return { body: JSON.stringify(json) };
    }
    return undefined;
  } catch (_) {
    return undefined;
  }
}
