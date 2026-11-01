import fs from "node:fs";
import vm from "node:vm";
import assert from "node:assert/strict";
const dir=process.env.YOUTUBE_ENHANCE_DIR||new URL("../input/",import.meta.url);
const file=name=>typeof dir==="string"?dir+"/"+name:new URL(name,dir);
function execute(kind,url,headers={},bytes=new Uint8Array()){
 let output;const request={url,method:"POST",headers:{"user-agent":"com.google.ios.youtube/21",...headers},body:bytes};
 vm.runInNewContext(fs.readFileSync(file("youtube."+kind+".js"),"utf8"),{
  $request:request,$response:{status:200,headers:{"content-type":"application/x-protobuf"},body:bytes},
  $persistentStore:{read:()=>null,write:()=>true},$notification:{post:()=>{}},
  $done:value=>output=value,URL,Uint8Array,ArrayBuffer,TextEncoder,TextDecoder,console:{log:()=>{}}
 },{timeout:5000});
 return output;
}
let out=execute("request","https://r1.googlevideo.com/initplayback?x=1&ack=1");
assert.equal(out.response.status,200);assert.equal(out.response.body.length,0);
out=execute("request","https://youtubei.googleapis.com/youtubei/v1/log_event",{"content-encoding":"gzip","x-other":"keep"});
assert.equal(out.headers["content-encoding"],undefined);assert.equal(out.headers["x-other"],"keep");
out=execute("response","https://youtubei.googleapis.com/youtubei/v1/player",{},new Uint8Array([255]));
assert.equal(Object.keys(out).length,0);
console.log("PASS: original request fallback, log_event header handling and invalid Protobuf passthrough");
