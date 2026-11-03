/**
 * Egern Adapter Script for Amap (高德地图)
 * ES Module specification
 * 
 * 1. aocs: 顶层 40+ 键彻底剔除，嵌套 JSON 字符串全量清洗
 * 2. poi_detail: 采用 94 个模块白名单骨架过滤机制
 * 3. profile: 1:1 严格对齐原版 JQ（剔除 tipData/wallet，仅保留 FootprintCard 与 BEntranceCardV4，并精准过滤 entranceList_1/2）
 * 4. scene_rec: 兼容原版逻辑清洗推荐与气泡
 * 5. hitch_passenger: 仅剔除顺风车横幅，保全发单功能
 */

// POI 详情页保留白名单 (94 个完整骨架与专属数据)
const POI_KEEP_MODULES = new Set([
  // 1. 基础骨架
  'baseInfo', 'poiDetailCommonConfig', 'navbarMore', 'backToTop',
  'poiDetailBottomBar', 'poiMapModule', 'anchor', 'reSortContentAndSimilar',
  'comprehensiveEditEntrance', 'functionZone', 'poiTipBar', 'floatTelButton',
  'footer_tel_button', 'footer_retain_button',

  // 2. UGC、评价与图集
  'attractGalleryInfo', 'combineReviews', 'evaluateVO', 'reviews',
  'inviteReview', 'seriousPublicExperience', 'societyPublicExperience',
  'poiDetailRankUpCard', 'travelGuideAndQa', 'poiDetailAQModule',
  'AIStreetTips', 'expertNote', 'recommend_food', 'shopNews', 'mallNews', 'shopBaseCase',

  // 3. 介绍与百科
  'wikiInfo', 'wikiInfoBelow', 'poiDetailNote', 'poiDetailWikiAndLOI',

  // 4. 本地点专属业务数据
  'human_traffic', 'floorGuideGbf', 'houseEvaluationInfo', 'residentialOwnersVO',
  'realtorRealStep', 'houseOfficeInfo', 'houseOfficeService', 'houseOfficeBrandIntroduction',
  'houseOfficeNotice', 'newHouseDetailInfo', 'house_apart_info', 'scenic_mustplay',
  'hotelGraphicDetail', 'homestayGraphicDetail', 'hotelFacilities', 'hotelMustRead', 'shoppingMallEvent',

  // 5. 本店服务与自营通道
  'enhanceIMQuestions', 'enhanceCustomerServicePoiModule', 'aiAgentFooterBar', 'imBottomGuide',
  'enhanceCustomerServiceFixedBottom', 'shopBasePerson', 'shopServiceBffvo', 'service_process',
  'shopCourseList', 'poiDetailJobList', 'jobRec', 'shop_vip_card', 'shopStdActivity',
  'privateSphereChannel', 'kaShopService', 'ka_not_enter', 'company1688Info', 'thirdparty_info',
  'expressEntryCard', 'poi_intercept', 'aiAgentEntry', 'commonAiAgent', 'poiCardAiAgentEntryV2',

  // 6. 指引与位置
  'storeDirections', 'shopFindWayGuide',

  // 7. 资质与合规公示
  'shopQualifications', 'businessQualifications', 'legal_document', 'home_legal_document',
  'rec_legal_document', 'business_scope', 'governmentInformation', 'official_account',
  'merchantSettlement', 'shop_settlement',

  // 8. 本地点自有预订库存
  'scenic_ticket', 'movieBookingShelf', 'hotelRooms', 'ktvBookingShelf',
  'venueBookingShelfModule', 'reserveShelf', 'DinnerBottomBar', 'poiDetailAppointmentRegister'
]);

export default async function (ctx) {
  const { response, env } = ctx ?? {};
  const mode = env?.MODE;

  if (!response?.body || !mode) return undefined;

  try {
    const rawText = typeof response.body === 'string'
      ? response.body
      : new TextDecoder('utf-8').decode(response.body);

    const json = JSON.parse(rawText);
    if (!json || typeof json !== 'object') return undefined;

    let modified = false;

    // ==========================================
    // 1. 云控配置全量深度清洗 (aocs/updatable/1)
    // ==========================================
    if (mode === 'aocs') {
      const data = json.data;
      if (data && typeof data === 'object') {
        const dropKeys = [
          'adStatementConfig', 'adCustomerRetainArchitecture', 'adImEntryConfig',
          'adVenueConfig', 'adPerfSwitch', 'EndNaviC3AdCard', 'infoCpcReport',
          'hotsaleConfig', 'marketing_resource_config', 'coupon_risk_asac',
          'commonCouponSceneLog', 'sug_coupon_opt', 'giftEntryConfig',
          'splashscreen', 'SplashScreenControl', 'splashview_config',
          'feedback_banner', 'TrainOrderBanner', 'nearby_business_popup',
          'shortcut_popup_frequency', 'tel_retention_popup', 'hotel_activity',
          'taxi_activity', 'hotel_privilege', 'sportsActivityConfig',
          'activity_qingke_contry_control', '920bestwishes', 'free_ride',
          'homepage_resource_config', 'home_message_guide', 'hotel_tipsicon',
          'sur_bar', 'nearby_map_entry_guide', 'comment_info', 'small_biz_index',
          'small_biz_fun', 'setpagesearch', 'wallet'
        ];
        for (const k of dropKeys) {
          if (k in data) { delete data[k]; modified = true; }
        }

        if (data.custom_consultdata && typeof data.custom_consultdata === 'object') {
          if ('widget_guide' in data.custom_consultdata) {
            delete data.custom_consultdata.widget_guide;
            modified = true;
          }
        }

        // 嵌套 1: amap_basemap_config 内部广告与活动
        if (typeof data.amap_basemap_config?.value === 'string') {
          try {
            const inner = JSON.parse(data.amap_basemap_config.value);
            const innerDrop = [
              'splash', 'ai_splash', 'ipSquare_window_video_config',
              'usercenter_lottery_switch', 'coins_lottery', 'coins_wish',
              'newYearLotteryTips', 'mileage_coin_scene', 'licheng_coin_mine_entry',
              'member_grabbing', 'vip_checkout_welfare_dialog_config',
              'task_poi_card_coupon_switch', 'jay_act', 'pointExchangeCenter',
              'pointExchangeGoCommentUrl', 'batchCheckIn', 'batchCheckIn_new',
              'fireworks', 'fireworkFeatureCodes', 'setFireworksNightMode',
              'fireworks_click_change_night', '2024greetingTofireworks',
              'greeting_widget_switch', 'newYearSystemScreenRecordListenSwitch',
              'ugcActivityH5', 'study_create_url', 'asset_space_pilot',
              'ipSquare_goods_tab_desc', 'vip_member_config', 'recently_activity',
              'business_position', 'carLogos', 'voiceLogos', 'increase_product_name_account',
              'invite_poi_share_pic', 'block_increase_product_detail_share_button',
              'mainIcon', 'mainBubble', 'blueBar', 'presetWord', 'homepage_tabguide',
              'suit_set_popup', 'pop_selection', 'ipsqure_free_pop_hours',
              'desk_card_footprint_check_in', 'desk_card_searchtool', 'arLayerDialogConfig',
              'geochoBackConfirmDialogConfig', 'followGuidePopupConfig',
              'growth_bubble_guide_config', 'bottom_login_guide_config',
              'frequent_location_login_guide_config', 'login_guide_show_rules',
              'show_landmark_exploration_card', 'reachFrequency', 'reachTaskFrequency',
              'msgbox_show_popwindow', 'aiqs_pull_up_guide', 'new_aiqs_pull_up_guide',
              'full_screen_guide_video_config', 'ai_guideo_video_map', 'feature_guide_switch',
              'geoechoGuideLottieConfig', 'level_page_slide', 'level_page_tips',
              'garage_top_button', 'ThemeSquareSwiperCanJumpUrlList'
            ];
            let innerMod = false;
            for (const ik of innerDrop) {
              if (ik in inner) { delete inner[ik]; innerMod = true; }
            }
            if (innerMod) {
              data.amap_basemap_config.value = JSON.stringify(inner);
              modified = true;
            }
          } catch (_) {}
        }

        // 嵌套 2: 引擎渲染广告开关 (engine_render)
        if (typeof data.engine_render?.value === 'string') {
          try {
            const inner = JSON.parse(data.engine_render.value);
            if (inner && typeof inner === 'object') {
              delete inner.can_show_advert;
              delete inner.advert_note_num;
              data.engine_render.value = JSON.stringify(inner);
              modified = true;
            }
          } catch (_) {}
        }

        // 嵌套 3: 搜索历史与热词 (his_input_tip)
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

        // 嵌套 4: 详情页货架吸顶优化 (detail_config)
        if (typeof data.detail_config?.value === 'string') {
          try {
            const inner = JSON.parse(data.detail_config.value);
            if (inner && typeof inner === 'object') {
              delete inner.shelf_coupon_refresh;
              inner.isGoodsShelfPerfV2 = 0;
              inner.NearbySearchOptimization = 0;
              if (inner.poiDetailScreenCacheConfig) inner.poiDetailScreenCacheConfig.secondScreenAnchorModule = '';
              if (inner.poiDetailScreenCacheOtherConfig) inner.poiDetailScreenCacheOtherConfig.secondScreenAnchorModule = '';
              data.detail_config.value = JSON.stringify(inner);
              modified = true;
            }
          } catch (_) {}
        }

        // 嵌套 5: 导航结束运营按钮 (navi_end)
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

    // ==========================================
    // 2. 地点详情页清洗 (search/poi/detail)
    // ==========================================
    else if (mode === 'poi_detail') {
      const data = json.data;
      if (data && typeof data === 'object') {
        if (data.modules && typeof data.modules === 'object') {
          for (const mk of Object.keys(data.modules)) {
            if (!POI_KEEP_MODULES.has(mk)) {
              delete data.modules[mk];
              modified = true;
            }
          }
        }
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

    // ==========================================
    // 3. 个人中心清洗 (dsp/profile/index/nodefaasv3) —— 1:1 对齐原版 JQ
    // ==========================================
    else if (mode === 'profile') {
      const data = json.data;
      if (data && typeof data === 'object') {
        // 1. del(.data.tipData, .data.wallet)
        if ('tipData' in data) { delete data.tipData; modified = true; }
        if ('wallet' in data) { delete data.wallet; modified = true; }

        // 2. cardList 仅保留 MineNewFootprintCard 与 MineNewBEntranceCardV4
        if (Array.isArray(data.cardList)) {
          const keepCardKeys = new Set(['MineNewFootprintCard', 'MineNewBEntranceCardV4']);
          const origLen = data.cardList.length;
          data.cardList = data.cardList.filter(card => keepCardKeys.has(card?.dataKey));
          if (data.cardList.length !== origLen) modified = true;

          // 3. 精准过滤 entranceList_1 (7,8,10,17) 与 entranceList_2 (32,4,9,16,14)
          const keep1 = new Set([7, 8, 10, 17, '7', '8', '10', '17']);
          const keep2 = new Set([32, 4, 9, 16, 14, '32', '4', '9', '16', '14']);

          for (const card of data.cardList) {
            if (card?.dataKey === 'MineNewBEntranceCardV4') {
              const container = card.content || card.data;
              if (container && typeof container === 'object') {
                if (Array.isArray(container.entranceList_1)) {
                  container.entranceList_1 = container.entranceList_1.filter(item => keep1.has(item?.id));
                  modified = true;
                }
                if (Array.isArray(container.entranceList_2)) {
                  container.entranceList_2 = container.entranceList_2.filter(item => keep2.has(item?.id));
                  modified = true;
                }
              }
            }
          }
        }
      }
    }

    // ==========================================
    // 4. 搜索/推荐栏目清洗 (scene/recommend)
    // ==========================================
    else if (mode === 'scene_rec') {
      const data = json.data;
      if (data && typeof data === 'object') {
        const defTools = data.toolsRecommend?.data?.default;
        if (Array.isArray(defTools)) {
          const keepTools = new Set([102, 103, 106, 151]);
          const beforeLen = defTools.length;
          data.toolsRecommend.data.default = defTools.filter(t => keepTools.has(Number(t?.id)));
          if (data.toolsRecommend.data.default.length !== beforeLen) modified = true;
        }

        const swData = data.shadingWords?.data;
        if (swData && typeof swData === 'object') {
          if (Array.isArray(swData.regions?.content)) {
            const keepRegions = new Set(['quickLink', 'history', 'searchFind']);
            swData.regions.content = swData.regions.content.filter(r => keepRegions.has(r));
            modified = true;
          }
          if (swData.modules && typeof swData.modules === 'object') {
            for (const k of Object.keys(swData.modules)) {
              if (k !== 'searchFind' && k !== 'quickLink') {
                delete swData.modules[k];
                modified = true;
              }
            }
          }
        }
      }
    }

    // ==========================================
    // 5. 顺风车乘客页 (hitch/passenger/content_info)
    // ==========================================
    else if (mode === 'hitch_passenger') {
      const luban = json.data?.lubanData;
      if (luban && typeof luban === 'object') {
        if ('banner' in luban) {
          delete luban.banner;
          return { body: JSON.stringify(json) };
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
