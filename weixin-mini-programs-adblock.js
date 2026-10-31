/* 可莉公开模块全部12个脚本的 Egern 原生适配，保留各自处理逻辑。 */
export default async function(ctx) {
let original;
try {
if (!ctx.request || !ctx.response) return;
original = await ctx.response.text();
const $request = {url:ctx.request.url,headers:ctx.request.headers};
const $response = {body:original};
let result;
function $done(value) { result=value; }
if (new RegExp("^https://webapi\\.qmai\\.cn/web/catering/design/homePage-Config", "i").test($request.url)) {
// 企迈点单系统去广告; source https://raw.githubusercontent.com/ifflagged/Romeo/main/Modules/JavaScript/Kelee/WexinMiniPrograms_Remove_ads/kelee_kff.js
(function () {
let obj = JSON.parse($response.body);
obj.data.config = JSON.stringify(JSON.parse(obj.data.config).filter(item => !item.id.includes("13502ede-f5fd-4d5c-90f5-f2454a30fda0")));
obj.data.config = JSON.stringify(JSON.parse(obj.data.config).filter(item => !item.id.includes("c1caaf62-e91d-4040-b533-dab39c0fec13")));
obj.data.config = JSON.stringify(JSON.parse(obj.data.config).filter(item => !item.id.includes("cc9d17ec-3ac5-494b-b82e-8d3c72c243d4")));
obj.data.config = JSON.stringify(JSON.parse(obj.data.config).filter(item => !item.id.includes("7bef8fe9-0daf-46b3-a2b0-dd9fba49423f")));
obj.data.config = JSON.stringify(JSON.parse(obj.data.config).filter(item => !item.id.includes("ff7e1263-d8d2-4f09-9947-d8c43c77bb10")));
obj.data.config = JSON.stringify(JSON.parse(obj.data.config).filter(item => !item.id.includes("874197b4-fe93-4a80-a555-8df1bc7e8211")));
obj.data.config = JSON.stringify(JSON.parse(obj.data.config).filter(item => !item.id.includes("0ba6a615-b7e9-48aa-afe7-329635385f2c")));
obj.data.config = JSON.stringify(JSON.parse(obj.data.config).filter(item => !item.id.includes("a11b0e7d-a162-4802-ac71-21d98e8adddf")));
$done({body: JSON.stringify(obj)});
})();
return {body: typeof result?.body === "string" ? result.body : original};
}
if (new RegExp("^https://ump\\.ems\\.com\\.cn/new-generation-extend/redis/pageInfoByChannel", "i").test($request.url)) {
// EMS中国邮政物流速递去广告; source https://raw.githubusercontent.com/ifflagged/Romeo/main/Modules/JavaScript/Kelee/WexinMiniPrograms_Remove_ads/kelee_ems.js
(function () {
let obj = JSON.parse($response.body);
obj.info.moduleJson = JSON.stringify(JSON.parse(obj.info.moduleJson).filter(item => !item.moduleName.includes("广告")));
$done({body: JSON.stringify(obj)});
})();
return {body: typeof result?.body === "string" ? result.body : original};
}
if (new RegExp("^https://mapi\\.xiaotucc\\.com/(mall/main|main_page/index/getActivity)", "i").test($request.url)) {
// 小兔充充去广告; source https://raw.githubusercontent.com/ifflagged/Romeo/main/Modules/JavaScript/Kelee/WexinMiniPrograms_Remove_ads/kelee_xiaotucc.js
(function () {
if(-1!=$request.url.indexOf("main_page/index/getActivity")){
    let obj=JSON.parse($response.body);
    delete obj.data.p3;
    $done({body: JSON.stringify(obj)});
   }
   else if(-1!=$request.url.indexOf("mall/main")){
    let obj=JSON.parse($response.body);
    delete obj.data;
    $done({body: JSON.stringify(obj)});
   }
   else $done($response);
   
})();
return {body: typeof result?.body === "string" ? result.body : original};
}
if (new RegExp("^https://minifm\\.maxxipoint\\.com/banner/list", "i").test($request.url)) {
// 全家微会员去广告; source https://raw.githubusercontent.com/ifflagged/Romeo/main/Modules/JavaScript/Kelee/WexinMiniPrograms_Remove_ads/kelee_FamilyMart.js
(function () {
let obj=JSON.parse($response.body);
delete obj.data.topBanner ;
$done({body: JSON.stringify(obj)});
})();
return {body: typeof result?.body === "string" ? result.body : original};
}
if (new RegExp("^https://lawsonapi\\.yorentown\\.com/area/sh-lawson/app/v1/home", "i").test($request.url)) {
// 罗森点点去广告; source https://raw.githubusercontent.com/ifflagged/Romeo/main/Modules/JavaScript/Kelee/WexinMiniPrograms_Remove_ads/kelee_lawson.js
(function () {
let obj=JSON.parse($response.body);
delete obj.data.homeButtonList ;
delete obj.data.dysmorphismPictureList ;
$done({body: JSON.stringify(obj)});
})();
return {body: typeof result?.body === "string" ? result.body : original};
}
if (new RegExp("^https://miniapp\\.sexytea2013\\.com/cms/slot/queryByCodes\\?codes=INDEX_TOP_BANNER", "i").test($request.url)) {
// 茶颜悦色去广告; source https://raw.githubusercontent.com/ifflagged/Romeo/main/Modules/JavaScript/Kelee/WexinMiniPrograms_Remove_ads/kelee_chayanyuese_remove_ads.js
(function () {
let obj=JSON.parse($response.body);
delete obj.data.INDEX_SLOT_01;
delete obj.data.INDEX_SLOT_02;
obj.data?.INDEX_TOP_BANNER?.contents?.forEach(item => {
  delete item.bubble; 
  delete item.figure; 
  item.value = "https://raw.githubusercontent.com/huangkouping/egern/main/weixin-mini-programs-cyys1.jpg?v=ec412d4bc351";
});
$done({body: JSON.stringify(obj)});
})();
return {body: typeof result?.body === "string" ? result.body : original};
}
if (new RegExp("^https://coco-com\\.e\\.verystar\\.net/v1/home/info", "i").test($request.url)) {
// COCO点单去广告; source https://raw.githubusercontent.com/ifflagged/Romeo/main/Modules/JavaScript/Kelee/WexinMiniPrograms_Remove_ads/kelee_coco.js
(function () {
let obj=JSON.parse($response.body);
delete obj.data.top_background_url ;
delete obj.data.bottom_banner_list ;
$done({body: JSON.stringify(obj)});
})();
return {body: typeof result?.body === "string" ? result.body : original};
}
if (new RegExp("^https://htwkop\\.xiaojukeji\\.com/gateway\\?api=hm\\.fa\\.homeConfig", "i").test($request.url)) {
// 滴滴青桔去广告; source https://raw.githubusercontent.com/ifflagged/Romeo/main/Modules/JavaScript/Kelee/WexinMiniPrograms_Remove_ads/kelee_qingju.js
(function () {
let obj=JSON.parse($response.body);
delete obj.data.bannerInfoConfig ;
$done({body: JSON.stringify(obj)});
})();
return {body: typeof result?.body === "string" ? result.body : original};
}
if (new RegExp("^https://cappapi\\.alittle-tea\\.com/open\\?method=catering\\.set\\.ad", "i").test($request.url)) {
// 一点点+去广告; source https://raw.githubusercontent.com/ifflagged/Romeo/main/Modules/JavaScript/Kelee/WexinMiniPrograms_Remove_ads/kelee_alittle-tea.js
(function () {
let obj=JSON.parse($response.body);
delete obj.data;
$done({body: JSON.stringify(obj)});
})();
return {body: typeof result?.body === "string" ? result.body : original};
}
if (new RegExp("^https://api\\.prod\\.dj\\.mstand\\.cn/scrm/mini/app/index/info", "i").test($request.url)) {
// M Stand去广告; source https://raw.githubusercontent.com/ifflagged/Romeo/main/Modules/JavaScript/Kelee/WexinMiniPrograms_Remove_ads/kelee_M_Stand.js
(function () {
let obj=JSON.parse($response.body);
delete obj.data.homeNewsAdv.jumpValue ;
delete obj.data.homeDineInAdv ;
delete obj.data.homePickupAdv ;
delete obj.data.nearbyShopInfo ;
delete obj.data.homeEventThemesAdv ;
delete obj.data.eventThemes ;
delete obj.data.homeRootAdv ;
delete obj.data.homeTopAdv ;
delete obj.data.homeDialogAdv ;
delete obj.data.homeBannerAdv ;
delete obj.data.homeCouponAdv ;
delete obj.data.homeCompanyAdv ;
delete obj.data.homeDeliveryAdv ;
$done({body: JSON.stringify(obj)});

})();
return {body: typeof result?.body === "string" ? result.body : original};
}
if (new RegExp("^https://passenger\\.t3go\\.cn/(solution\\-|common\\-)?(passenger\\-)?(activity\\-|app\\-)?api/notoken/(trip/)?api/(home/|common/)?(v[1-3]/)?(ad/getNegativescreen|solution/passenger/open/getHomeMenu|leftmenu|getHomeInfoGlobal)", "i").test($request.url)) {
// T3出行去广告; source https://raw.githubusercontent.com/ifflagged/Romeo/main/Modules/JavaScript/Kelee/WexinMiniPrograms_Remove_ads/kelee_T3.js
(function () {
let obj = JSON.parse($response.body);
delete obj.data;
$done({body: JSON.stringify(obj)});

})();
return {body: typeof result?.body === "string" ? result.body : original};
}
if (new RegExp("^https://newton\\.gumingnc\\.com/newton-buyer/newton/buyer/(ump|touch|external/front)", "i").test($request.url)) {
// 古茗去广告; source https://raw.githubusercontent.com/ifflagged/Romeo/main/Modules/JavaScript/Kelee/WexinMiniPrograms_Remove_ads/kelee_ming.js
(function () {
let obj=JSON.parse($response.body);
obj.data=[];
$done({body: JSON.stringify(obj)});
})();
return {body: typeof result?.body === "string" ? result.body : original};
}

return {body:original};
} catch (_) { return original === undefined ? undefined : {body:original}; }
}
