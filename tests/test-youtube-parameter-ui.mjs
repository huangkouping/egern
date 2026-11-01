import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import assert from "node:assert/strict";
import {execFileSync} from "node:child_process";
const wrapperPath=process.argv[2]||new URL("../scripts/youtube-parameter-wrapper.js",import.meta.url);
const filename=fs.realpathSync(path.resolve(wrapperPath instanceof URL?wrapperPath.pathname:wrapperPath));
const wrapper=fs.readFileSync(filename,"utf8");
const python=[
"import sys,json,yaml","from pathlib import Path","sys.path.insert(0,sys.argv[1])",
"from youtube_parameter_ui import fields,schema_for","root=Path(sys.argv[1]).parent","result={}",
"for flavor,name in [('enhance','youtube-enhance.yaml'),('subtitles','youtube-subtitles-translation.yaml')]:",
" m=yaml.safe_load((root/name).read_text());defaults,items=fields(flavor,m)",
" result[flavor]={'defaults':defaults,'fields':items,'format':'json' if flavor=='enhance' else 'query','schema':schema_for(items)}",
"print(json.dumps(result,ensure_ascii=False))"].join("\n");
const specs=JSON.parse(execFileSync("python",["-c",python,path.dirname(filename)],{encoding:"utf8"}));
const parse=(raw,format)=>format==="json"?JSON.parse(raw):Object.fromEntries(new URLSearchParams(raw));
let checks=0;
for(const [flavor,spec] of Object.entries(specs)){
 function run(env,initial) {
  let result;
  const code=wrapper.replace("UI_SPEC",()=>JSON.stringify(spec)).replace("SOURCE_CODE",()=>'$done({plain:$argument,global:globalThis.$argument});globalThis.$argument={changed:true};');
  const ctx=vm.createContext({ctx:{env},$argument:initial,$done:v=>result=v,console});
  vm.runInContext(code,ctx);
  assert.equal(result.plain,result.global);assert.equal(ctx.$argument,initial);
  return parse(result.plain,spec.format);
 }
 const baseline=run({},undefined);
 for(const [key,item] of Object.entries(spec.fields)){
  const schema=spec.schema[key];assert.equal(schema.name,item.name);assert.ok(schema.description.length>0);
  if(item.type==="boolean"){
   assert.deepEqual(schema.options,["true","false"]);
   for(const value of ["true","false"]){const out=run({[key]:value},undefined);assert.equal(String(out[key]),value);checks++;}
  }else{
   for(const [label,expected] of Object.entries(item.values)){
    assert.ok(schema.options.includes(label));const out=run({[key]:label},undefined);assert.equal(String(out[key]),String(expected));checks++;
   }
  }
 }
 const inherited=spec.format==="json"?'{"customLanguage":"fr","blockUpload":true}':"NewOfficialOption=keep&Storage=PersistentStore";
 const preserved=run({},inherited);assert.equal(preserved.customLanguage??preserved.NewOfficialOption,flavor==="enhance"?"fr":"keep");
 if(flavor==="enhance"){
  assert.equal(String(run({blockUpload:"false"},inherited).blockUpload),"false");
  assert.equal(run({captionLang:"简体中文"},undefined).captionLang,"zh-Hans");
 }else{
  assert.equal(baseline.Storage,"Argument");
  assert.equal(run({Storage:"官方在线设置优先"},undefined).Storage,"PersistentStore");
  assert.equal(run({ShowOnly:"false"},undefined).ShowOnly,"false");
 }
}
console.log("PASS: "+checks+" Chinese options mapped to runtime arguments; false values, upstream extras, settings priority and isolated global argument preserved");
