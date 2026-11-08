/* 小红书关注页过滤 🅗：直播卡片与顶部动态头像条 */
(function(){
 if(typeof $response==="undefined"||!$response.body)return $done({});
 const url=String(typeof $request!=="undefined"&&$request.url||"");
 if(!/\/api\/sns\/(?:v\d+|web\/v\d+)\/(?:follow|followfeed|feed\/follow|note\/follow)/i.test(url))return $done({});
 let p;try{p=JSON.parse($response.body)}catch(_){return $done({})}
 const env=typeof ctx!=="undefined"&&ctx&&ctx.env||{};
 const on=k=>!["false","0","off","no"].includes(String(env[k]??"true").toLowerCase());
 const live=v=>{if(!v||typeof v!=="object")return false;const s=Number(v.live_status??v.status??v.room_status);return s===1||s===2||!!(v.room_id&&(v.live_link||v.stream_url||v.cover))};
 const isLive=x=>{
  if(!x||typeof x!=="object")return false;
  return [x,x.note_card,x.card,x.note,x.content].filter(Boolean).some(v=>{
   const t=String(v.model_type||v.type||v.card_type||"").toLowerCase();
   return /^(live|live[_-].*|.*[_-]live)$/.test(t)||!!v.live_card_info||live(v.live_info)||live(v.live)||live(v.user?.live)||live(v.author?.live)||live(v.note_card?.user?.live);
  });
 };
 let removed=0,rows=0;
 const filter=a=>{if(!Array.isArray(a))return;const b=a.filter(x=>{if(isLive(x)){removed++;return false}return true});a.splice(0,a.length,...b)};
 const d=p?.data;
 if(d&&typeof d==="object"){
  if(on("BLOCK_FOLLOW_LIVE")){
   for(const key of ["items","feeds","notes","list","note_list","follow_feeds"])filter(d[key]);
   if(Array.isArray(d))filter(d);
   if(d.result&&typeof d.result==="object")for(const key of ["items","feeds","notes","list"])filter(d.result[key]);
  }
  if(on("HIDE_FOLLOW_STORIES")){
   // Only clear explicitly identified top-of-follow activity/avatar strips; do not remove followed accounts elsewhere.
   for(const key of ["follow_user_list","follow_users","user_stories","story_list","stories","follow_story_list","live_users","living_users","avatar_list","user_updates"]){
    if(Array.isArray(d[key])){rows+=d[key].length;d[key]=[]}
   }
   if(d.result&&typeof d.result==="object")for(const key of ["user_stories","story_list","stories","live_users","living_users"]){
    if(Array.isArray(d.result[key])){rows+=d.result[key].length;d.result[key]=[]}
   }
  }
 }
 console.log("[小红书关注页] 过滤直播 "+removed+"，顶部动态 "+rows);
 return removed+rows?$done({body:JSON.stringify(p)}):$done({});
})();
