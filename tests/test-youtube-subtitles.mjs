import fs from "node:fs";
import assert from "node:assert/strict";
const dir=process.env.YT_SUBTITLES_DIR||new URL("../",import.meta.url);
const path=name=>typeof dir==="string"?dir+"/"+name:new URL(name,dir);
const load=async kind=>(await import("data:text/javascript;base64,"+Buffer.from(fs.readFileSync(path("youtube-subtitles-"+kind+".js"),"utf8")).toString("base64"))).default;
const request=await load("request"),response=await load("response"),composite=await load("composite"),translate=await load("translate");
const values=new Map(),storage={get:k=>values.get(k)??null,set:(k,v)=>values.set(k,v),delete:k=>values.delete(k)};
const oldLog=console.log;console.log=()=>{};
try{
 const req={url:"https://www.youtube.com/youtubei/v1/player?key=t",method:"POST",headers:new Headers({"content-type":"application/json"}),body:{},text:async()=>JSON.stringify({playbackContext:{contentPlaybackContext:{}}})};
 let out=await request({request:req,env:{},storage});assert.equal(JSON.parse(out.body).playbackContext.contentPlaybackContext.autoCaptionsDefaultOn,true);
 out=await request({request:req,env:{AutoCC:"false"},storage});assert.equal(JSON.parse(out.body).playbackContext.contentPlaybackContext.autoCaptionsDefaultOn,undefined);
 const timed={url:"https://www.youtube.com/api/timedtext?v=t&lang=en&tlang=zh",method:"GET",headers:new Headers()};
 out=await request({request:timed,env:{Type:"Translate"},storage});assert.match(out.url,/subtype=Translate/);assert.doesNotMatch(out.url,/tlang=/);
 out=await request({request:timed,env:{Type:"Official",ShowOnly:"false"},storage});assert.match(out.url,/subtype=Official/);
 out=await request({request:timed,env:{Type:"Official",ShowOnly:"true"},storage});assert.doesNotMatch(out.url,/subtype=Official/);
 const captions={captions:{playerCaptionsTracklistRenderer:{captionTracks:[{baseUrl:"https://www.youtube.com/api/timedtext?v=t&lang=en",languageCode:"en",name:{simpleText:"English"}}],audioTracks:[{captionTrackIndices:[0]}]}}};
 out=await response({request:req,response:{status:200,headers:new Headers({"content-type":"application/json"}),text:async()=>JSON.stringify(captions)},storage,env:{}});
 assert.equal(JSON.parse(out.body).captions.playerCaptionsTracklistRenderer.captionTracks[0].isTranslatable,true);
 const raw=new Uint8Array([0x98,0x06,0x01]);
 for(const endpoint of ["player","get_watch"]){
  out=await response({request:{url:"https://youtubei.googleapis.com/youtubei/v1/"+endpoint+"?key=t",method:"POST",headers:new Headers()},
   response:{status:200,headers:new Headers({"content-type":"application/x-protobuf"}),arrayBuffer:async()=>raw.buffer},storage});
  assert.deepEqual(out.body,raw);
 }
 const input={events:[{tStartMs:0,dDurationMs:1000,segs:[{utf8:"你好"}]}]},original={events:[{tStartMs:0,dDurationMs:1000,segs:[{utf8:"Hello"}]}]};
 let fetches=0;
 const ctx={request:{url:"https://www.youtube.com/api/timedtext?v=t&lang=en&tlang=zh&fmt=json3&subtype=Official",headers:new Headers()},
  response:{status:200,headers:new Headers({"content-type":"application/json"}),text:async()=>JSON.stringify(input)},storage,
  env:{ShowOnly:"false",Position:"Forward"},http:{get:async()=>{fetches++;return {status:200,headers:new Headers({"content-type":"application/json"}),text:async()=>JSON.stringify(original)}}}};
 out=await composite(ctx);let line=JSON.parse(out.body).events[0].segs[0].utf8;assert.match(line,/Hello/);assert.match(line,/你好/);assert.equal(fetches,1);
 out=await composite({...ctx,env:{ShowOnly:"true"}});line=JSON.parse(out.body).events[0].segs[0].utf8;assert.equal(line,"你好");assert.equal(fetches,1);
 const google=async url=>{assert.match(url,/translate\.googleapis\.com/);return {status:200,headers:new Headers({"content-type":"application/json"}),text:async()=>JSON.stringify([[["你好","Hello",null,null]],null,"en"])}};
 const translation={request:{url:"https://www.youtube.com/api/timedtext?v=t&lang=en&fmt=json3&subtype=Translate",headers:new Headers()},
  response:{status:200,headers:new Headers({"content-type":"application/json"}),text:async()=>JSON.stringify(original)},storage,env:{ShowOnly:"false",Position:"Forward"},http:{get:google,post:google}};
 out=await translate(translation);line=JSON.parse(out.body).events[0].segs[0].utf8;assert.ok(line.indexOf("Hello")<line.indexOf("你好"));
 out=await translate({...translation,env:{ShowOnly:"false",Position:"Reverse"}});line=JSON.parse(out.body).events[0].segs[0].utf8;assert.ok(line.indexOf("你好")<line.indexOf("Hello"));
 out=await translate({...translation,env:{ShowOnly:"true"}});assert.equal(JSON.parse(out.body).events[0].segs[0].utf8,"你好");
 const lyric={contents:{sectionListRenderer:{contents:[{musicDescriptionShelfRenderer:{description:{runs:[{text:"Hello"}]}}}]}}};
 out=await translate({...translation,request:{url:"https://music.youtube.com/youtubei/v1/browse?subtype=Translate",headers:new Headers()},response:{status:200,headers:new Headers({"content-type":"application/json"}),text:async()=>JSON.stringify(lyric)},env:{ShowOnly:"false"}});
 line=JSON.parse(out.body).contents.sectionListRenderer.contents[0].musicDescriptionShelfRenderer.description.runs[0].text;assert.match(line,/Hello/);assert.match(line,/你好/);
 const bad="{broken";out=await response({request:req,response:{status:200,headers:new Headers({"content-type":"application/json"}),text:async()=>bad},storage});assert.equal(out.body,bad);
}finally{console.log=oldLog;}
console.log("PASS: player JSON/Proto, caption routing, fresh-install settings, official bilingual merging, translation/position/ShowOnly, Music lyrics and malformed body passthrough");
