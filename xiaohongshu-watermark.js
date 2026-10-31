/*
 * 小红书保存去水印补充，仅处理媒体接口。
 * 参考 ddgksf2013 redbook_json.js V1.0.27 (2025-08-17) 的水印标记及源地址缓存思路。
 * 来源：https://github.com/Moli-X/Resources/blob/main/QuantumultX/Rewrite/Script/redbook_json.js
 * 评论区参考 fmz200/wool_scripts/Scripts/xiaohongshu/xiaohongshu.js（2026-06-05）。
 * 仅适配水印：保留广告、直播、商品、菜单及保存权限逻辑。
 * 缓存仅保存在客户端，不发起额外网络请求；未命中时保留原响应。
 */
(function () {
  const finish = (value) => $done(value);
  if (typeof $response === "undefined" || typeof $response.body !== "string") return finish({});
  const request = typeof $request === "undefined" ? {} : $request;
  const url = String(request.url || "");
  const endpoint = url.match(/^https?:\/\/[a-zA-Z0-9.-]+\.xiaohongshu\.com\/api\/sns\/v\d+\/(note\/comment\/(?:list|sub_comments)|interaction\/comment\/video\/download|note\/(?:tabfeed|redtube|videofeed|feed|imagefeed|video\/save|live_photo\/save)|system_service\/config)(?:\?|$)/);
  if (!endpoint) return finish({});
  let payload;
  try { payload = JSON.parse($response.body); } catch (_) { return finish({}); }
  const object = v => v !== null && typeof v === "object" && !Array.isArray(v);
  if (!object(payload)) return finish({});
  const original = JSON.stringify(payload);
  const store = typeof $persistentStore !== "undefined" ? $persistentStore : null;
  const cacheKey = "huangkouping.xhs.watermark.v1";
  let cache = {videos: [], photos: [], comments: []};
  try {
    const saved = store && JSON.parse(store.read(cacheKey) || "null");
    if (object(saved)) {
      cache.videos = Array.isArray(saved.videos) ? saved.videos.filter(object) : [];
      cache.photos = Array.isArray(saved.photos) ? saved.photos.filter(object) : [];
      cache.comments = Array.isArray(saved.comments) ? saved.comments.filter(object) : [];
    }
  } catch (_) {}
  let cacheChanged = false;
  const put = (kind, value, id) => {
    cache[kind] = cache[kind].filter(v => String(v[id]) !== String(value[id]));
    cache[kind].push(value);
    cache[kind] = cache[kind].slice(-100);
    cacheChanged = true;
  };
  const mediaUrl = media => {
    const streams = media && media.stream;
    // 与上游一样优先使用 h265 播放源；兼容仅有 h264 的响应。
    for (const codec of ["h265", "h264"]) {
      const list = streams && streams[codec];
      if (!Array.isArray(list)) continue;
      for (const stream of list) {
        if (object(stream) && typeof stream.master_url === "string" && /^https?:\/\//.test(stream.master_url)) return stream.master_url;
      }
    }
    return "";
  };
  const watermark = node => {
    if (object(node.media_save_config)) node.media_save_config.disable_watermark = true;
  };
  const visitNote = (node, inheritedId) => {
    if (!object(node)) return;
    const id = node.id || node.note_id || inheritedId;
    watermark(node);
    const media = node.video_info_v2 && node.video_info_v2.media;
    const video = mediaUrl(media);
    if (id && video) put("videos", {note_id: String(id), download_url: video}, "note_id");
    if (Array.isArray(node.images_list)) {
      for (const image of node.images_list) {
        if (!object(image)) continue;
        const live = image.live_photo && image.live_photo.media;
        const liveUrl = mediaUrl(live);
        if (live && live.video_id && image.live_photo_file_id && liveUrl) {
          put("photos", {video_id: String(live.video_id), file_id: String(image.live_photo_file_id), url: liveUrl, note_id: id ? String(id) : ""}, "file_id");
        }
      }
    }
    // 原脚本在图文 note_list 内添加此标记；不更改 disable_save。
    if (Array.isArray(node.note_list)) for (const note of node.note_list) {
      if (object(note) && !Object.prototype.hasOwnProperty.call(note, "media_save_config")) note.media_save_config = {disable_watermark: true};
      visitNote(note, id);
    }
  };
  const requestNoteId = () => {
    const query = url.match(/[?&]note_id=([^&#]+)/);
    if (query) { try { return decodeURIComponent(query[1]); } catch (_) {} }
    if (typeof request.body === "string") {
      try { const data = JSON.parse(request.body); if (data.note_id) return String(data.note_id); } catch (_) {}
      const form = request.body.match(/(?:^|&)note_id=([^&]+)/);
      if (form) { try { return decodeURIComponent(form[1]); } catch (_) {} }
    }
    return "";
  };
  // 仅处理评论媒体和水印身份字段；不修改账号 user_id、昵称、正文或点赞。
  const processComments = data => {
    const process = comment => {
      if (!object(comment)) return;
      const pictures = Array.isArray(comment.pictures) ? comment.pictures : [];
      const videos = Array.isArray(comment.videos) ? comment.videos : [];
      if (pictures.length || videos.length) {
        if (object(comment.user)) delete comment.user.red_id;
        if (pictures.length && comment.comment_type === 3) comment.comment_type = 2;
        if (comment.media_source_type === 1) comment.media_source_type = 0;
        watermark(comment);
      }
      for (const picture of pictures) {
        if (!object(picture)) continue;
        const originalImage = picture.meme_package && picture.meme_package.image_url;
        if (typeof originalImage === "string" && /^https?:\/\//.test(originalImage)) {
          picture.url = originalImage;
          picture.origin_url = originalImage;
        }
      }
      for (const media of pictures.concat(videos)) {
        if (!object(media) || !media.video_id) continue;
        let info = media.video_info;
        if (typeof info === "string") {
          try { info = JSON.parse(info); } catch (_) { continue; }
        }
        if (!object(info)) continue;
        const originalUrl = mediaUrl(info);
        if (originalUrl) put("comments", {video_id: String(media.video_id), url: originalUrl}, "video_id");
      }
      if (Array.isArray(comment.sub_comments)) comment.sub_comments.forEach(process);
    };
    if (object(data) && Array.isArray(data.comments)) data.comments.forEach(process);
  };
  try {
    const path = endpoint[1];
    if (path === "note/comment/list" || path === "note/comment/sub_comments") {
      processComments(payload.data);
    } else if (path === "interaction/comment/video/download") {
      const video = object(payload.data) && payload.data.video;
      if (object(video) && video.video_id) {
        const found = cache.comments.find(v => v.video_id === String(video.video_id));
        if (found) video.video_url = found.url;
      }
    } else if (path === "system_service/config") {
      if (object(payload.data)) delete payload.data.watermark_pic_path;
    } else if (path === "note/video/save") {
      if (object(payload.data)) {
        const id = payload.data.note_id || requestNoteId();
        const found = id && cache.videos.find(v => v.note_id === String(id));
        if (found) payload.data.download_url = found.download_url;
      }
    } else if (path === "note/live_photo/save") {
      if (object(payload.data)) {
        const id = requestNoteId();
        if (Array.isArray(payload.data.datas) && payload.data.datas.length) {
          payload.data.datas = payload.data.datas.map(item => {
            if (!object(item)) return item;
            // 只替换明确匹配的视频/文件，不返回其他笔记的缓存。
            const found = cache.photos.find(v =>
              (item.file_id && String(item.file_id) === v.file_id ||
               item.video_id && String(item.video_id) === v.video_id) &&
              (!id || !v.note_id || v.note_id === id));
            return found ? {...item, url: found.url} : item;
          });
        } else if (id && (payload.data.datas === undefined || Array.isArray(payload.data.datas))) {
          const selected = cache.photos.filter(v => v.note_id === id);
          if (selected.length) payload.data.datas = selected.map(({video_id,file_id,url}) => ({video_id,file_id,url}));
        }
      }
    } else {
      const data = payload.data;
      const notes = Array.isArray(data) ? data : object(data) && Array.isArray(data.items) ? data.items : [];
      for (const note of notes) visitNote(note);
    }
    if (cacheChanged && store) {
      try { store.write(JSON.stringify(cache), cacheKey); } catch (_) {}
    }
    if (JSON.stringify(payload) === original) return finish({});
    console.log("[小红书保存去水印] 已处理 " + path);
    return finish({body: JSON.stringify(payload)});
  } catch (_) {
    return finish({});
  }
})();
