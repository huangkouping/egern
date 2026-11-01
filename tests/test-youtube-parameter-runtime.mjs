import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import assert from "node:assert/strict";
const [flavor,dir]=process.argv.slice(2);
if(flavor==="enhance"){
 const code=fs.readFileSync(path.join(dir,"youtube-enhance-ui-response.js"),"utf8"),parsed=[];
 vm.runInNewContext(code,{
  ctx:{env:{blockUpload:"false",blockShorts:"true",captionLang:"简体中文"}},$argument:"{}",
  $request:{url:"https://youtubei.googleapis.com/youtubei/v1/player",headers:{"user-agent":"com.google.ios.youtube/21"}},
  $response:{body:new Uint8Array([255]),headers:{}},$persistentStore:{read:()=>null,write:()=>true},
  $notification:{post:()=>{}},$done:()=>{},Uint8Array,TextEncoder,TextDecoder,URL,console:{log:()=>{}},
  JSON:{parse:s=>{const obj=JSON.parse(s);if(obj&&typeof obj==="object")parsed.push(obj);return obj;},stringify:JSON.stringify}
 },{timeout:5000});
 assert.ok(parsed.some(p=>p.blockUpload===false&&p.blockShorts===true&&p.captionLang==="zh-Hans"));
}else{
 const code=fs.readFileSync(path.join(dir,"youtube-subtitles-ui-request.js"),"utf8");
 for(const enabled of ["true","false"]){
  let complete,timer;const completion=new Promise(resolve=>complete=resolve);
  const body=JSON.stringify({playbackContext:{contentPlaybackContext:{}}});
  const context=vm.createContext({
   ctx:{env:{AutoCC:enabled,Type:"官方字幕（双语合成）",Storage:"模块设置优先"}},Egern:{},
   $argument:"Type=Official&AutoCC=true&Storage=Argument&LogLevel=OFF",
   $request:{url:"https://www.youtube.com/youtubei/v1/player?key=t",method:"POST",headers:{"content-type":"application/json"},body},
   $response:{headers:{},body:""},$persistentStore:{read:()=>null,write:()=>true},$done:complete,
   $script:{startTime:Date.now()/1000},URL,TextEncoder,TextDecoder,Uint8Array,ArrayBuffer,console:{log:()=>{}}
  });
  vm.runInContext(code,context,{timeout:5000});
  let out;
  try{out=await Promise.race([completion,new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error("timeout")),3000)})]);}
  finally{clearTimeout(timer);}
  const setting=JSON.parse(out.body).playbackContext.contentPlaybackContext.autoCaptionsDefaultOn;
  assert.equal(setting,enabled==="true"?true:undefined);
  if(enabled==="false")assert.equal(out.body,body);
 }
}
console.log("PASS: actual "+flavor+" upstream script receives native controls and preserves disabled state");
