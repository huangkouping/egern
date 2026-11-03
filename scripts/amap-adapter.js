/**
 * Egern Adapter Script for Amap (高德地图)
 * 专攻 AOCS 云控与 POI 详情页骨架清洗，其余交给 Egern 原生处理
 */

const POI_KEEP_MODULES = new Set([
  'baseInfo', 'poiDetailCommonConfig', 'navbarMore', 'backToTop',
  'poiDetailBottomBar', 'poiMapModule', 'anchor', 'reSortContentAndSimilar',
  'comprehensiveEditEntrance', 'functionZone', 'poiTipBar', 'floatTelButton',
  'footer_tel_button', 'footer_retain_button', 'attractGalleryInfo',
  'combineReviews', 'evaluateVO', 'reviews', 'inviteReview',
  'seriousPublicExperience', 'societyPublicExperience', 'poiDetailRankUpCard',
  'travelGuideAndQa', 'poiDetailAQModule', 'AIStreetTips', 'expertNote',
  'recommend_food', 'shopNews', 'mallNews', 'shopBaseCase', 'wikiInfo',
  'wikiInfoBelow', 'poiDetailNote', 'poiDetailWikiAndLOI', 'human_traffic',
  'floorGuideGbf', 'houseEvaluationInfo', 'residentialOwnersVO', 'realtorRealStep',
  'houseOfficeInfo', 'houseOfficeService', 'houseOfficeBrandIntroduction',
  'houseOfficeNotice', 'newHouseDetailInfo', 'house_apart_info', 'scenic_mustplay',
  'hotelGraphicDetail', 'homestayGraphicDetail', 'hotelFacilities', 'hotelMustRead',
  'shoppingMallEvent', 'enhanceIMQuestions', 'enhanceCustomerServicePoiModule',
  'aiAgentFooterBar', 'imBottomGuide', 'enhanceCustomerServiceFixedBottom',
  'shopBasePerson', 'shopServiceBffvo', 'service_process', 'shopCourseList',
  'poiDetailJobList', 'jobRec', 'shop_vip_card', 'shopStdActivity',
  'privateSphereChannel', 'kaShopService', 'ka_not_enter', 'company1688Info',
  'thirdparty_info', 'expressEntryCard', 'poi_intercept', 'aiAgentEntry',
  'commonAiAgent', 'poiCardAiAgentEntryV2', 'storeDirections', 'shopFindWayGuide',
  'shopQualifications', 'businessQualifications', 'legal_document',
  'home_legal_document', 'rec_legal_document', 'business_scope',
  'governmentInformation', 'official_account', 'merchantSettlement',
  'shop_settlement', 'scenic_ticket', 'movieBookingShelf', 'hotelRooms',
  'ktvBookingShelf', 'venueBookingShelfModule', 'reserveShelf', 'DinnerBottomBar',
  'poiDetailAppointmentRegister'
]);

const ENTRANCE_1_KEEP = new Set([7, 8, 10, 17, '7', '8', '10', '17']);
const ENTRANCE_2_KEEP = new Set([32, 4, 9, 16, 14, '32', '4', '9', '16', '14']);

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

    // 1. 云控配置清洗 (aocs)
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

        if (data.custom_consultdata?.widget_guide) {
          delete data.custom_consultdata.widget_guide;
          modified = true;
        }

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
            for (const ik of innerDrop) { delete inner[ik]; }
            data.amap_basemap_config.value = JSON.stringify(inner);
            modified = true;
          } catch (_) {}
        }
      }
    }

    // 2. 地点详情页清洗 (poi_detail)
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

    // 3. 个人中心清洗 (profile) —— 1:1 对齐原版
    else if (mode === 'profile') {
      const data = json.data;
      if (data && typeof data === 'object') {
        delete data.tipData;
        delete data.wallet;

        if (Array.isArray(data.cardList)) {
          // 只保留足迹卡与核心入口卡
          data.cardList = data.cardList.filter(
            card => card?.dataKey === 'MineNewFootprintCard' || card?.dataKey === 'MineNewBEntranceCardV4'
          );

          for (const card of data.cardList) {
            if (card?.dataKey === 'MineNewBEntranceCardV4') {
              const content = card.content || card.data;
              if (content && typeof content === 'object') {
                if (Array.isArray(content.entranceList_1)) {
                  content.entranceList_1 = content.entranceList_1.filter(item => ENTRANCE_1_KEEP.has(item?.id));
                }
                if (Array.isArray(content.entranceList_2)) {
                  content.entranceList_2 = content.entranceList_2.filter(item => ENTRANCE_2_KEEP.has(item?.id));
                }
              }
            }
          }
        }
        modified = true;
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
