'use strict';
const yulinPending=new Map();let yulinRequestId=0;
window.yulinNativeResult=function(id,status,body){const p=yulinPending.get(id);if(!p)return;yulinPending.delete(id);p.cleanup();p.resolve(new Response(body,{status,headers:{'content-type':'application/json'}}))};
const originalFetch=window.fetch.bind(window);window.fetch=function(input,init={}){const url=typeof input==='string'?input:input.url;if(window.YulinNative&&(url.startsWith('/api/ai/')||url.startsWith('/api/library/')||url.startsWith('/api/cloud/')))return new Promise((resolve,reject)=>{const id=String(++yulinRequestId);const abort=()=>{YulinNative.cancel(id);yulinPending.delete(id);reject(new DOMException('Stopped','AbortError'))};if(init.signal?.aborted){abort();return}init.signal?.addEventListener('abort',abort,{once:true});yulinPending.set(id,{resolve,reject,progress:init.onProgress,cleanup:()=>init.signal?.removeEventListener('abort',abort)});YulinNative.request(id,url,init.body||'{}')});return originalFetch(input,init)};
function yulinSave(name,content,type){const blob=content instanceof Blob?content:new Blob([content],{type:type||'application/octet-stream'});if(blob.size>12*1024*1024){alert('导出文件超过12 MB，请减少笔迹或分次导出。');return}const r=new FileReader();r.onload=()=>YulinNative.saveFile(name,blob.type||type||'application/octet-stream',r.result.split(',')[1]);r.readAsDataURL(blob)}
window.yulinSettingsChanged=()=>{if(typeof refreshAIStatus==='function')refreshAIStatus()};

window.yulinCloudProgress=(id,done,total)=>{const p=yulinPending.get(id);if(p?.progress)p.progress(done,total)};
