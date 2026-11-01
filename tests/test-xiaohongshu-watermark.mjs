import assert from "node:assert/strict";
import fs from "node:fs";
const filename = process.env.XHS_SCRIPT || new URL("../xiaohongshu-watermark.js", import.meta.url);
const code = fs.readFileSync(filename, "utf8");
const {default:run} = await import("data:text/javascript;base64,"+Buffer.from(code).toString("base64"));
const values = new Map();
const storage = {getJSON:key=>values.get(key),setJSON:(key,v)=>values.set(key,structuredClone(v))};
let checks=0;
const call = async (path,data,env={},body) => {
  const original = typeof data==="string" ? data : JSON.stringify(data);
  const result=await run({request:{url:"https://edith.xiaohongshu.com/api/sns/"+path,body},
    response:{text:async()=>original},storage,env});
  return result?.body ? JSON.parse(result.body) : data;
};
const note={id:"n1",model_type:"note",media_save_config:{disable_save:true,disable_watermark:false,disable_weibo_cover:false},
 function_switch:[{enable:false,reason:"restricted"}],share_info:{function_entries:[{type:"share"},{type:"video_download"},{type:"video_download"}]},
 video_info_v2:{media:{stream:{h265:[{master_url:"https://media.test/original.mp4?sig=keep"}]}}},
 images_list:[{live_photo_file_id:"f1",live_photo:{media:{video_id:"p1",stream:{h264:[{master_url:"https://media.test/live.mp4"}]}}}}]};
const feed=await call("v4/note/videofeed",{data:[note,{id:"normal",title:"保留正文",ad:{keep:true}}]});
assert.equal(feed.data.length,2);assert.equal(feed.data[1].ad.keep,true);
assert.deepEqual(feed.data[0].media_save_config,{disable_save:false,disable_watermark:true,disable_weibo_cover:true});
assert.equal(feed.data[0].function_switch[0].enable,true);
assert.equal(feed.data[0].share_info.function_entries[0].type,"video_download");
assert.equal(feed.data[0].share_info.function_entries.filter(v=>v.type==="video_download").length,1);checks++;
const saved=await call("v10/note/video/save",{code:-1,success:false,data:{note_id:"n1",disable:true,msg:"禁止保存",download_url:"watermarked"}});
assert.equal(saved.data.download_url,"https://media.test/original.mp4?sig=keep");assert.equal(saved.code,0);assert.equal(saved.data.disable,undefined);checks++;
const unknown={code:-1,data:{note_id:"other",disable:true,download_url:"unchanged"}};
assert.deepEqual(await call("v10/note/video/save",unknown),unknown);checks++;
const live=await call("v1/note/live_photo/save?note_id=n1",{data:{datas:[{file_id:"f1",url:"watermarked"}]}});
assert.equal(live.data.datas[0].url,"https://media.test/live.mp4");
const wrong=await call("v1/note/live_photo/save?note_id=other",{data:{datas:[{file_id:"f1",url:"unchanged"}]}});
assert.equal(wrong.data.datas[0].url,"unchanged");
const recovered=await call("v1/note/live_photo/save",{code:-1,data:{datas:[]}}, {}, JSON.stringify({note_id:"n1"}));
assert.equal(recovered.data.datas[0].file_id,"f1");assert.equal(recovered.success,true);
const missingData=await call("v1/note/live_photo/save?note_id=n1",{code:-1});assert.equal(missingData.data.datas[0].file_id,"f1");
assert.deepEqual(await call("v1/note/live_photo/save",{data:{datas:[]}}),{data:{datas:[]}});checks++;
const input={data:{red_id:"top",comments:[{user:{user_id:"u1",red_id:"red",nickname:"昵称"},comment_type:3,media_source_type:1,
 pictures:[{red_id:"picture",meme_package:{image_url:"https://img.test/original.jpg"}}],
 sub_comments:[{comment_type:3,media_source_type:1,user:{red_id:"sub"},pictures:[{video_id:"c1",video_info:JSON.stringify({stream:{h265:[{master_url:"https://video.test/comment.mp4"}]}})}]}]}]}};
const comment=await call("v5/note/comment/list",input);
const walk=v=>{if(v&&typeof v==="object"){assert.equal(Object.hasOwn(v,"red_id"),false);Object.values(v).forEach(walk)}};
walk(comment.data);assert.equal(comment.data.comments[0].user.user_id,"u1");assert.equal(comment.data.comments[0].user.nickname,"昵称");
assert.equal(comment.data.comments[0].sub_comments[0].comment_type,2);assert.equal(comment.data.comments[0].sub_comments[0].media_source_type,0);
assert.equal(comment.data.comments[0].pictures[0].url,"https://img.test/original.jpg");checks++;
const downloaded=await call("v1/interaction/comment/video/download",{data:{video:{video_id:"c1",video_url:"watermarked"}}});
assert.equal(downloaded.data.video.video_url,"https://video.test/comment.mp4");checks++;
const replies=await call("v2/note/comment/sub_comments",{data:{sub_comments:[{user:{red_id:"reply"},pictures:[{video_id:"c2",video_info:"malformed"}]}]}});
assert.equal(replies.data.sub_comments[0].user.red_id,undefined);checks++;
assert.deepEqual(await call("v5/note/comment/list",input,{REMOVE_COMMENT_WATERMARK:"false"}),input);
assert.deepEqual(await call("v4/note/videofeed",{data:[note]},{REMOVE_MEDIA_WATERMARK:"false",ENABLE_MEDIA_SAVE:"false"}),{data:[note]});
const permission=await call("v4/note/videofeed",{data:[note]},{ENABLE_MEDIA_SAVE:"false"});
assert.equal(permission.data[0].media_save_config.disable_save,true);assert.equal(permission.data[0].function_switch[0].enable,false);checks++;
const malformed="{ broken";const result=await run({request:{url:"https://edith.xiaohongshu.com/api/sns/v5/note/comment/list"},response:{text:async()=>malformed},storage});
assert.equal(result.body,malformed);checks++;
let consumed=false;assert.equal(await run({request:{url:"https://example.com/"},response:{text:async()=>{consumed=true;return "{}"}}}),undefined);assert.equal(consumed,false);checks++;
values.set("huangkouping.xhs.watermark.v2",{videos:[{note_id:"expired",download_url:"https://x.test/old",at:Date.now()-8*86400000}]});
const expired={data:{note_id:"expired",download_url:"unchanged"}};assert.deepEqual(await call("v10/note/video/save",expired),expired);checks++;
const batch=Array.from({length:310},(_,i)=>({...note,id:"bounded"+i}));
await call("v4/note/videofeed",{data:batch});
assert.equal(values.get("huangkouping.xhs.watermark.v2").videos.length,300);checks++;
console.log("PASS: "+checks+" groups (watermark flags, menus, keyed video/live save, recursive comments, reply media, toggles, malformed JSON, scope, TTL and cache bounds)");
