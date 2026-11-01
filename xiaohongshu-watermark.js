/*
 * 小红书保存去水印，Egern 原生响应脚本。
 * 水印开关、播放源缓存及保存响应参考 ddgksf2013 / RuCu6 / fmz200 公开实现。
 * 不请求外部服务，不修改广告/直播过滤；媒体缓存仅存客户端。
 */
const ENDPOINT = /^https?:\/\/[a-zA-Z0-9.-]+\.xiaohongshu\.com\/api\/sns\/v\d+\/(note\/comment\/(?:list|sub_comments)|interaction\/comment\/video\/download|note\/(?:tabfeed|redtube|videofeed|feed|imagefeed|video\/save|live_photo\/save)|system_service\/config)(?:\?|$)/;
const KEY = "huangkouping.xhs.watermark.v2";
const LEGACY_KEY = "huangkouping.xhs.watermark.v1";
const TTL = 7 * 86400000, LIMIT = 300;
const object = v => v !== null && typeof v === "object" && !Array.isArray(v);
const http = v => typeof v === "string" && /^https?:\/\//i.test(v);
const enabled = (env, key) => !["false", "0", "off", "no"].includes(String(env?.[key] ?? "true").trim().toLowerCase());
function mediaUrl(media) {
  for (const codec of ["h265", "h264"]) {
    const streams = media?.stream?.[codec];
    if (!Array.isArray(streams)) continue;
    for (const stream of streams) {
      if (http(stream?.master_url)) return stream.master_url;
      if (Array.isArray(stream?.backup_urls)) {
        const backup = stream.backup_urls.find(http);
        if (backup) return backup;
      }
    }
  }
  return "";
}
export default async function(ctx) {
  let original;
  try {
    const url = String(ctx.request?.url || ""), endpoint = url.match(ENDPOINT);
    if (!endpoint || !ctx.response) return;
    const path = endpoint[1], env = ctx.env || {};
    const wm = enabled(env, "REMOVE_MEDIA_WATERMARK");
    const save = enabled(env, "ENABLE_MEDIA_SAVE");
    const comments = wm && enabled(env, "REMOVE_COMMENT_WATERMARK");
    if (!wm && !save) return;
    original = await ctx.response.text();
    let payload;
    try { payload = JSON.parse(original); } catch (_) { return {body:original}; }
    if (!object(payload)) return {body:original};
    const before = JSON.stringify(payload), now = Date.now();
    let stored;
    const storage = ctx.storage;
    try {
      stored = storage?.getJSON ? storage.getJSON(KEY) : JSON.parse(storage?.get?.(KEY) || "null");
      if (!object(stored)) stored = storage?.getJSON ? storage.getJSON(LEGACY_KEY) : JSON.parse(storage?.get?.(LEGACY_KEY) || "null");
    } catch (_) {}
    const cache = {videos:[], photos:[], comments:[]};
    for (const kind of Object.keys(cache)) {
      if (Array.isArray(stored?.[kind])) {
        cache[kind] = stored[kind].filter(object).map(v => ({...v, at:Number(v.at) || now}))
          .filter(v => v.at <= now && now-v.at < TTL).slice(-LIMIT);
      }
    }
    let dirty = false, hits = 0;
    const put = (kind, entry, id) => {
      cache[kind] = cache[kind].filter(v => String(v[id]) !== String(entry[id]));
      cache[kind].push({...entry, at:now}); cache[kind] = cache[kind].slice(-LIMIT); dirty = true;
    };
    const find = (kind, predicate) => [...cache[kind]].reverse().find(predicate);
    const configure = (node, isVideo=false) => {
      if (!object(node)) return;
      if (wm || save) {
        if (!object(node.media_save_config)) node.media_save_config = {};
        if (wm) {
          node.media_save_config.disable_watermark = true;
          node.media_save_config.disable_weibo_cover = true;
        }
        if (save) node.media_save_config.disable_save = false;
      }
      if (save && Array.isArray(node.function_switch)) {
        for (const item of node.function_switch) if (object(item) && item.enable === false) { item.enable = true; item.reason = ""; }
      }
      if (save && isVideo && object(node.share_info)) {
        const entries = node.share_info.function_entries;
        if (Array.isArray(entries)) {
          const index = entries.findIndex(v => v?.type === "video_download");
          const entry = index < 0 ? {type:"video_download"} : entries.splice(index,1)[0];
          node.share_info.function_entries = [entry, ...entries.filter(v => v?.type !== "video_download")];
        }
      }
    };
    const visitNote = (node, inheritedId="") => {
      if (!object(node)) return;
      const id = node.note_id || node.id || inheritedId;
      const media = node.video_info_v2?.media || node.video_info?.media || node.video?.media;
      const video = mediaUrl(media), images = Array.isArray(node.images_list) ? node.images_list : Array.isArray(node.image_list) ? node.image_list : [];
      const isNote = Boolean(id && (video || images.length || node.model_type === "note" || node.type === "video"));
      if (isNote || object(node.media_save_config)) configure(node, Boolean(video || node.type === "video"));
      if (wm && id && video) put("videos", {note_id:String(id),download_url:video}, "note_id");
      if (wm) for (const image of images) {
        if (!object(image)) continue;
        const live = image.live_photo?.media, source = mediaUrl(live);
        if (source && live?.video_id && image.live_photo_file_id) put("photos",
          {note_id:id ? String(id) : "", file_id:String(image.live_photo_file_id),video_id:String(live.video_id),url:source}, "file_id");
      }
      for (const key of ["note_list","items","feeds","notes"]) {
        if (Array.isArray(node[key])) for (const child of node[key]) visitNote(child,id);
      }
      if (object(node.note_card)) visitNote(node.note_card,id);
    };
    const clearRedId = node => {
      if (Array.isArray(node)) { for (const child of node) clearRedId(child); }
      else if (object(node)) {
        if (Object.prototype.hasOwnProperty.call(node,"red_id")) {
          node.fmz200 = node.red_id; delete node.red_id;
        }
        for (const child of Object.values(node)) clearRedId(child);
      }
    };
    const processComment = comment => {
      if (!object(comment)) return;
      const pictures = Array.isArray(comment.pictures) ? comment.pictures : [];
      const videos = Array.isArray(comment.videos) ? comment.videos : [];
      if (pictures.length || videos.length) {
        if (comment.comment_type === 3) comment.comment_type = 2;
        if (comment.media_source_type === 1) comment.media_source_type = 0;
        if (object(comment.media_save_config)) configure(comment);
      }
      for (const picture of pictures) {
        if (!object(picture)) continue;
        const source = picture.meme_package?.image_url;
        if (http(source)) { picture.url = source; picture.origin_url = source; }
      }
      for (const item of [...pictures,...videos]) {
        if (!object(item) || !item.video_id) continue;
        let info = item.video_info;
        if (typeof info === "string") { try { info = JSON.parse(info); } catch (_) { continue; } }
        const source = mediaUrl(info) || mediaUrl(info?.media);
        if (source) put("comments",{video_id:String(item.video_id),url:source},"video_id");
      }
      if (Array.isArray(comment.sub_comments)) comment.sub_comments.forEach(processComment);
    };
    let requestData = {};
    if (path.endsWith("/save") || path === "interaction/comment/video/download") {
      try {
        const req = ctx.request;
        const text = typeof req.body === "string" ? req.body :
          req.body && typeof req.text === "function" ? await req.text() : "";
        if (text) {
          try { requestData = JSON.parse(text); } catch (_) { requestData = Object.fromEntries(new URLSearchParams(text)); }
          if (!object(requestData)) requestData = {};
        }
      } catch (_) {}
    }
    const params = new URL(url).searchParams;
    const noteId = String(payload.data?.note_id || requestData.note_id || params.get("note_id") || "");
    if (path === "note/comment/list" || path === "note/comment/sub_comments") {
      if (comments) {
        clearRedId(payload.data);
        const data = payload.data;
        const list = Array.isArray(data) ? data : Array.isArray(data?.comments) ? data.comments :
          Array.isArray(data?.sub_comments) ? data.sub_comments : [];
        list.forEach(processComment);
      }
    } else if (path === "interaction/comment/video/download") {
      if (comments && object(payload.data?.video)) {
        const video = payload.data.video, id = video.video_id || requestData.video_id || params.get("video_id");
        const found = id && find("comments",v=>v.video_id===String(id));
        if (found && http(found.url)) { video.video_url = found.url; hits++; }
      }
    } else if (path === "system_service/config") {
      if (wm && object(payload.data)) delete payload.data.watermark_pic_path;
    } else if (path === "note/video/save") {
      const found = wm && noteId && find("videos",v=>v.note_id===noteId && http(v.download_url));
      if (found) {
        if (!object(payload.data)) payload.data = {};
        payload.data.download_url = found.download_url; hits++;
        if (save) {
          delete payload.data.disable; delete payload.data.msg;
          payload.data.status = 2; payload.data.note_id = noteId;
          if (payload.code !== undefined) payload.code = 0;
          if (payload.success !== undefined) payload.success = true;
        }
      }
    } else if (path === "note/live_photo/save") {
      if (wm && save && noteId && !object(payload.data) && cache.photos.some(v => v.note_id===noteId && http(v.url))) payload.data = {};
      if (wm && object(payload.data)) {
        const list = payload.data.datas;
        if (Array.isArray(list) && list.length) {
          payload.data.datas = list.map(item => {
            if (!object(item)) return item;
            const found = find("photos",v =>
              ((item.file_id && String(item.file_id)===v.file_id) || (item.video_id && String(item.video_id)===v.video_id)) &&
              (!noteId || !v.note_id || v.note_id===noteId) && http(v.url));
            if (!found) return item;
            hits++; return {...item,url:found.url};
          });
        } else if (save && noteId && (list === undefined || Array.isArray(list))) {
          const selected = cache.photos.filter(v=>v.note_id===noteId && http(v.url));
          if (selected.length) {
            payload.data.datas = selected.map(({file_id,video_id,url})=>({file_id,video_id,url}));
            payload.code = 0; payload.success = true; payload.msg = "成功"; hits += selected.length;
          }
        }
      }
    } else {
      const data = payload.data;
      if (Array.isArray(data)) data.forEach(v=>visitNote(v));
      else if (object(data)) visitNote(data);
    }
    if (dirty && storage) {
      try {
        if (storage.setJSON) storage.setJSON(KEY,cache); else storage.set?.(KEY,JSON.stringify(cache));
      } catch (_) {}
    }
    const result = JSON.stringify(payload);
    if (result === before) return {body:original};
    console.log("[小红书保存去水印] "+path+"，原始媒体命中 "+hits+"，缓存 "+cache.videos.length+"/"+cache.photos.length+"/"+cache.comments.length);
    return {body:result};
  } catch (_) {
    return original === undefined ? undefined : {body:original};
  }
}
