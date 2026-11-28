# Cold Knowledge Bundle: chats-2026-11-part23


---
## FILE: `chats/Optimizing Two-Step LLM Routing.md` [Part 13/14]

function saveStateKey_(props, stateMap, key, prev) {
  const pLock = LockService.getScriptLock();
  pLock.waitLock(10000);
  try {
    let latest = {};
    const latestRaw = props.getProperty(key);
    if (latestRaw) { try { latest = JSON.parse(latestRaw); } catch (e) {} }
    const merged = Object.assign({}, latest, prev);
    if (!prev.kbP) delete merged.kbP;
    if (!prev.kbT) delete merged.kbT;
    if (!prev.kbTarget) delete merged.kbTarget;
    const serialized = JSON.stringify(merged);
    props.setProperty(key, serialized);
    stateMap[key] = serialized;
  } finally {
    pLock.releaseLock();
  }
}

function sanitizePathSlug_(name) {
  return String(name || '').toLowerCase().replace(/[^a-z0-9_-]+/g, '-').replace(/^-+|-+$/g, '') || 'general';
}

function resolveKbTarget_(file, baseName, rootId) {
  const rawName = file.getName();
  const isCoreTag = CONFIG.KB_CORE_TAG_REGEX.test(rawName);
  const isKbTag = CONFIG.KB_TAG_REGEX.test(rawName);

  const chain = [];
  let cur = file;
  for (let depth = 0; depth < 6; depth++) {
    const parents = cur.getParents();
    if (!parents.hasNext()) break;
    const parent = parents.next();
    if (rootId && parent.getId() === rootId) break;
    const pName = parent.getName();
    if (CONFIG.SOURCE_FOLDER_NAMES.some(n => n.toLowerCase() === pName.toLowerCase())) break;
    const segs = pName.split('/').map(s => s.trim()).filter(Boolean);
    for (let i = segs.length - 1; i >= 0; i--) {
      if (!CONFIG.SOURCE_FOLDER_NAMES.some(n => n.toLowerCase() === segs[i].toLowerCase())) {
        chain.unshift(segs[i]);
      }
    }
    cur = parent;
  }

  const kbIdx = chain.findIndex(n => n.toLowerCase() === CONFIG.KB_FOLDER_NAME.toLowerCase());
  const inKbFolder = kbIdx !== -1;
  if (!isCoreTag && !isKbTag && !inKbFolder) return null;

  const relFolders = inKbFolder ? chain.slice(kbIdx + 1) : chain;
  const cleanFile = baseName
    .replace(/\s*\[(kb|core)\]\s*/gi, ' ')
    .replace(/[#?%\\/:*|"<>]/g, '_')
    .replace(/\s+/g, ' ')
    .trim() || 'Untitled';

  if (isCoreTag || (relFolders.length > 0 && relFolders[0].toLowerCase() === 'core')) {
    return `core/${cleanFile}.md`;
  }
  if (relFolders.length > 0) {
    const folderPath = relFolders.map(sanitizePathSlug_).join('/');
    return `chats/${folderPath}/${cleanFile}.md`;
  }
  return `chats/${cleanFile}.md`;
}

function pushBatchToGitHubRepo_(owner, repo, branch, ops, commitMessage, token) {
  const baseApi = `https://api.github.com/repos/${owner}/${repo}`;
  const headers = { Authorization: `Bearer ${token}`, Accept: 'application/vnd.github+json' };

  const refResp = UrlFetchApp.fetch(`${baseApi}/git/ref/heads/${branch}`, { method: 'get', headers, muteHttpExceptions: true });
  if (refResp.getResponseCode() !== 200) {
    console.error(`KB ref fetch failed (${refResp.getResponseCode()}): ${refResp.getContentText()}`);
    return false;
  }
  const headSha = JSON.parse(refResp.getContentText()).object.sha;

  const commitResp = UrlFetchApp.fetch(`${baseApi}/git/commits/${headSha}`, { method: 'get', headers, muteHttpExceptions: true });
  if (commitResp.getResponseCode() !== 200) {
    console.error(`KB commit fetch failed (${commitResp.getResponseCode()}): ${commitResp.getContentText()}`);
    return false;
  }
  const baseTreeSha = JSON.parse(commitResp.getContentText()).tree.sha;

  const treeEntries = [];
  for (const op of ops) {
    if (op.content === null) {
      const chk = UrlFetchApp.fetch(`${baseApi}/contents/${encodeURI(op.path)}?ref=${branch}`, {
        method: 'get', headers, muteHttpExceptions: true
      });
      if (chk.getResponseCode() === 200) {
        treeEntries.push({ path: op.path, mode: '100644', type: 'blob', sha: null });
      }
      continue;
    }
    const blobResp = UrlFetchApp.fetch(`${baseApi}/git/blobs`, {
      method: 'post', contentType: 'application/json', headers,
      payload: JSON.stringify({ content: op.content, encoding: 'utf-8' }), muteHttpExceptions: true
    });
    if (blobResp.getResponseCode() !== 201) {
      console.error(`KB blob failed (${blobResp.getResponseCode()}): ${blobResp.getContentText()}`);
      return false;
    }
    const blobSha = JSON.parse(blobResp.getContentText()).sha;
    treeEntries.push({ path: op.path, mode: '100644', type: 'blob', sha: blobSha });
  }

  if (treeEntries.length === 0) return true;

  const treeResp = UrlFetchApp.fetch(`${baseApi}/git/trees`, {
    method: 'post', contentType: 'application/json', headers,
    payload: JSON.stringify({ base_tree: baseTreeSha, tree: treeEntries }), muteHttpExceptions: true
  });
  if (treeResp.getResponseCode() !== 201) {
    console.error(`KB tree failed (${treeResp.getResponseCode()}): ${treeResp.getContentText()}`);
    return false;
  }
  const newTreeSha = JSON.parse(treeResp.getContentText()).sha;

  const newCommitResp = UrlFetchApp.fetch(`${baseApi}/git/commits`, {
    method: 'post', contentType: 'application/json', headers,
    payload: JSON.stringify({ message: commitMessage, tree: newTreeSha, parents: [headSha] }), muteHttpExceptions: true
  });
  if (newCommitResp.getResponseCode() !== 201) {
    console.error(`KB commit create failed (${newCommitResp.getResponseCode()}): ${newCommitResp.getContentText()}`);
    return false;
  }
  const newCommitSha = JSON.parse(newCommitResp.getContentText()).sha;

  const patchResp = UrlFetchApp.fetch(`${baseApi}/git/refs/heads/${branch}`, {
    method: 'patch', contentType: 'application/json', headers,
    payload: JSON.stringify({ sha: newCommitSha }), muteHttpExceptions: true
  });
  if (patchResp.getResponseCode() !== 200) {
    console.error(`KB ref update failed (${patchResp.getResponseCode()}): ${patchResp.getContentText()}`);
    return false;
  }
  return true;
}

function collectAssets_(turns) {
  const assets = [];
  for (const turn of turns) {
    for (const item of turn.items) {
      if (item.type === 'image_b64' && item.data && item.data.length < 7000000) {
        assets.push({ mimeType: item.mimeType || 'image/png', dataB64: item.data });
      } else if (item.type === 'image_drive') {
        try {
          const blob = DriveApp.getFileById(item.fileId).getBlob();
          const bytes = blob.getBytes();
          if (bytes.length < 5 * 1024 * 1024) {
            assets.push({ mimeType: blob.getContentType() || 'image/png', dataB64: Utilities.base64Encode(bytes) });
          }
        } catch (e) {}
      }
    }
  }
  return assets;
}

function requeueAllPastChats() {
  const props = PropertiesService.getScriptProperties();
  props.deleteProperty(CONFIG.SCAN_STATE_KEY);
  props.deleteProperty(CONFIG.DISPATCH_STATE_KEY);
  props.deleteProperty(CONFIG.KB_DISPATCH_STATE_KEY);
  const all = props.getProperties();
  let resetCount = 0;

  for (const key of Object.keys(all)) {
    if (!key.startsWith(CONFIG.STATE_PREFIX)) continue;
    try {
      const st = JSON.parse(all[key]);
      delete st.t; delete st.pt; delete st.qt; delete st.qa;
      delete st.tc; delete st.th; delete st.part; delete st.partStartTc;
      delete st.kbT; delete st.kbP; delete st.kbTarget;
      props.setProperty(key, JSON.stringify(st));
      resetCount++;
    } catch (e) {}
  }
  console.log(`Reset ${resetCount} chat(s). Running full sync...`);
  syncCleanMarkdown_(true, true);
}

function doPost(e) {
  try {
    const { secret } = getSecrets_();
    const payload = JSON.parse(e.postData.contents);
    if (!payload || payload.secret !== secret) {
      return jsonResponse_({ ok: false, error: 'Unauthorized' });
    }

    if (payload.action === 'get_pdf') {
      const existing = DriveApp.getFileById(payload.fileId);
      if (existing.isTrashed()) {
        return jsonResponse_({ ok: false, error: 'Existing PDF is trashed' });
      }
      const bytes = existing.getBlob().getBytes();
      return jsonResponse_({ ok: true, pdfB64: Utilities.base64Encode(bytes) });
    }

    const lock = LockService.getScriptLock();
    lock.waitLock(30000);
    try {
      const pdfFolder = getOrCreateFolder_(CONFIG.PDF_FOLDER_NAME);
      const props = PropertiesService.getScriptProperties();
      const key = CONFIG.STATE_PREFIX + payload.sourceId;

      let prev = {};
      const raw = props.getProperty(key);
      if (raw) { try { prev = JSON.parse(raw); } catch (err) {} }

      if (payload.mode === 'append' && typeof payload.expectedTc === 'number' &&
          typeof prev.tc === 'number' && prev.tc !== payload.expectedTc) {
        return jsonResponse_({ ok: false, error: 'Stale delta: expectedTc mismatch' });
      }

      if (prev.p && payload.mode !== 'new_part') {
        try {
          const old = DriveApp.getFileById(prev.p);
          if (!old.isTrashed()) old.setTrashed(true);
        } catch (err) {}
      }
      const dupes = pdfFolder.getFilesByName(payload.pdfName);
      while (dupes.hasNext()) {
        const df = dupes.next();
        if (!df.isTrashed()) df.setTrashed(true);
      }

      const bytes = Utilities.base64Decode(payload.pdfB64);
      const blob = Utilities.newBlob(bytes, 'application/pdf', payload.pdfName);
      const created = pdfFolder.createFile(blob);

      prev.p = created.getId();
      prev.pt = payload.updatedMs;
      if (typeof payload.nextTc === 'number') prev.tc = payload.nextTc;
      if (payload.nextTh) prev.th = payload.nextTh;
      prev.part = payload.part || 1;
      prev.partStartTc = payload.partStartTc || 0;
      delete prev.qa;
      props.setProperty(key, JSON.stringify(prev));

      return jsonResponse_({ ok: true, pdfId: created.getId() });
    } finally {
      lock.releaseLock();
    }
  } catch (err) {
    return jsonResponse_({ ok: false, error: err.message });
  }
}

function jsonResponse_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

function pushJobToGitHub_(path, obj, token) {
  const url = `https://api.github.com/repos/${CONFIG.GITHUB_OWNER}/${CONFIG.GITHUB_REPO}/contents/${path}`;
  const headers = { Authorization: `Bearer ${token}`, Accept: 'application/vnd.github+json' };

  let sha = null;
  const getResp = UrlFetchApp.fetch(url, { method: 'get', headers, muteHttpExceptions: true });
  if (getResp.getResponseCode() === 200) {
    try { sha = JSON.parse(getResp.getContentText()).sha; } catch (e) {}
  }

  const body = {
    message: `Queue ${path}`,
    content: Utilities.base64Encode(JSON.stringify(obj), Utilities.Charset.UTF_8),
    branch: CONFIG.GITHUB_BRANCH
  };
  if (sha) body.sha = sha;

  const putResp = UrlFetchApp.fetch(url, {
    method: 'put', contentType: 'application/json', headers,
    payload: JSON.stringify(body), muteHttpExceptions: true
  });
  const code = putResp.getResponseCode();
  if (code !== 200 && code !== 201) {
    console.error(`GitHub PUT failed (${code}): ${putResp.getContentText()}`);
    return false;
  }
  return true;
}

function triggerGitHubWorkflow_(token) {
  const url = `https://api.github.com/repos/${CONFIG.GITHUB_OWNER}/${CONFIG.GITHUB_REPO}/actions/workflows/build-pdfs.yml/dispatches`;
  const resp = UrlFetchApp.fetch(url, {
    method: 'post', contentType: 'application/json',
    headers: { Authorization: `Bearer ${token}`, Accept: 'application/vnd.github+json' },
    payload: JSON.stringify({ ref: CONFIG.GITHUB_BRANCH }), muteHttpExceptions: true
  });
  const code = resp.getResponseCode();
  if (code !== 204 && code !== 200) {
    console.error(`GitHub workflow trigger failed (${code}): ${resp.getContentText()}`);
  }
}

/* ===== Text Cleaning & Extraction ===== */

function joinStreamText_(a, b) {
  if (!a) return b || '';
  if (!b) return a;
  if (/\s$/.test(a) || /^\s/.test(b)) return a + b;
  if (/^[,.;:!?)}\]'"*]/.test(b) || /[(\[{\"'*-]$/.test(a)) return a + b;
  return a + ' ' + b;
}

function cleanTextArtifacts_(raw) {
  let text = String(raw || '').replace(/\r\n/g, '\n').replace(/\f/g, '\n');
  if (((text.match(/^[ \t]*```/gm) || []).length % 2) === 1) text += '\n```';

  const code = [];
  text = text.replace(/```[\s\S]*?```|`[^`\n]+`/g, m => {
    const tok = `\u0000CD_${code.length}\u0000`;
    code.push(m);
    return tok;
  });

  const math = [];
  const stashMath = m => {
    const tok = `\u0000MT_${math.length}\u0000`;
    math.push(m);
    return tok;
  };
  text = text
    .replace(/(?<!\\)\$\$[\s\S]+?(?<!\\)\$\$/g, stashMath)
    .replace(/(?<!\\)\$(?!\s)(?:\\\$|[^$\n])+?(?<!\s)(?<!\\)\$(?!\d)/g, stashMath);

  text = text
    .replace(/!?\[([^\]]*)\]\((?:https?:\/\/|mailto:)[^)\s]+\)/gi, '$1')
    .replace(/<(?:https?:\/\/|mailto:)[^>\s]+>/gi, '')
    .replace(/\b(?:https?:\/\/|mailto:)[^\s)\]>"]+/gi, '')
    .replace(/【[^】]*】/g, '')
    .replace(/\[(?:cite_start|cite_end|cite:[^\]]*|source|citation needed)\]/gi, '')
    .replace(/\[(?:\d+(?:\s*[-–,]\s*\d+)*)\]/g, '')
    .replace(/\(\s*\)/g, '')
    .replace(/\*\*([^\n*]+?)\*\*/g, (_, inner) => {
      const lead = (/^\s+/.exec(inner) || [''])[0], trail = (/\s+$/.exec(inner) || [''])[0], core = inner.trim();
      return core ? `${lead}**${core}**${trail}` : '';
    })
    .replace(/([.!?,:;])[ \t]+\*(?=[.,;:!?)]|$)/g, '$1*')
    .replace(/([A-Za-z0-9.!?,:;])[ \t]+\*(?=[.,;:!?)]|$)/g, '$1*')
    .replace(/^[ \t]*(?:[-=]{2,}[ \t]*)?Page[ \t]+\d+(?:[ \t]+of[ \t]+\d+)?(?:[ \t]*[-=]{2,})?[ \t]*$/gim, '')
    .replace(/([A-Za-z]{2,})-\n([A-Za-z]{2,})/g, '$1$2');

  const lines = text.split('\n'), out = [];
  let tbl = [];
  const isSep = l => l.includes('|') && /^\|?\s*:?[-–—]{1,}:?\s*(\|\s*:?[-–—]{1,}:?\s*)+\|?$/.test(l.trim());
  const isStruct = l => {
    const t = l.trim();
    return !t || /^#{1,6}\s/.test(t) || /^[-*+]\s/.test(t) || /^\d+[.)]\s/.test(t) ||
           /^>\s?/.test(t) || /^(-{3,}|\*{3,}|_{3,})$/.test(t) || /^\u0000(?:CD|MT)_\d+\u0000$/.test(t);
  };
  const flushTbl = () => {
    if (!tbl.length) return;
    if (out.length && out[out.length - 1].trim() !== '') out.push('');
    const splitR = r => r.replace(/^\|/, '').replace(/(^|[^\\])\|$/, '$1').replace(/\\\|/g, '\u0000P\u0000')
      .split('|').map(c => c.replace(/\u0000P\u0000/g, '|').trim());
    const parsed = tbl.map(splitR);
    const cols = Math.max(...parsed.map(r => r.length));
    tbl.forEach((rawRow, idx) => {
      const cells = parsed[idx].slice(0, cols);
      while (cells.length < cols) cells.push('');
      if (isSep(rawRow)) {
        out.push('| ' + cells.map(c => (c.startsWith(':') && c.endsWith(':')) ? ':---:' : (c.startsWith(':') ? ':---' : (c.endsWith(':') ? '---:' : '---'))).join(' | ') + ' |');
      } else {
        out.push('| ' + cells.map(c => c.replace(/\|/g, '\\|')).join(' | ') + ' |');
      }
    });
    out.push('');
    tbl = [];
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i], t = line.trim();
    const isTbl = /^\|.*\|$/.test(t) || (t.includes('|') && (tbl.length > 0 || (i + 1 < lines.length && isSep(lines[i + 1]))));
    if (isTbl) { tbl.push(t); continue; }
    flushTbl();
    if (out.length && !isStruct(line) && !isStruct(out[out.length - 1]) && !/  $/.test(out[out.length - 1])) {
      out[out.length - 1] = out[out.length - 1].replace(/\s+$/, '') + ' ' + t;
    } else {
      out.push(line);
    }
  }
  flushTbl();

  return out.join('\n')
    .replace(/(\S) {2,}/g, '$1 ')
    .replace(/\u0000MT_(\d+)\u0000/g, (_, i) => math[Number(i)])
    .replace(/\u0000CD_(\d+)\u0000/g, (_, i) => code[Number(i)])
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

function extractCleanChat_(data, file) {
  const title = file.getName().replace(/\.(json|prompt|txt)$/i, '') || 'Untitled prompt';
  const model = data.runSettings?.model ? String(data.runSettings.model).replace(/^models\//, '') : 'unknown';
  const updatedIso = file.getLastUpdated().toISOString();
  const rawSys = data.systemInstruction
    ? (typeof data.systemInstruction === 'string'
        ? data.systemInstruction
        : (data.systemInstruction.text || (data.systemInstruction.parts || []).map(p => p.text || '').join('')))
    : '';
  const systemInstruction = rawSys ? cleanTextArtifacts_(rawSys) : '';

  const rawTurns = [];
  const appendItem = (role, item, joiner) => {
    const lastTurn = rawTurns[rawTurns.length - 1];
    if (lastTurn && lastTurn.role === role) {
      const lastItem = lastTurn.items[lastTurn.items.length - 1];
      if (lastItem && lastItem.type === item.type && (item.type === 'text' || item.type === 'thought')) {
        lastItem.text = joiner(lastItem.text, item.text);
        return;
      }
      lastTurn.items.push(item);
    } else {
      rawTurns.push({ role, items: [item] });
    }
  };

  const extractRawParts = (role, parts) => {
    for (const p of (parts || [])) {
      if (!p) continue;
      const th = Boolean(p.thought || p.isThought);
      if (th && !CONFIG.INCLUDE_THOUGHTS) continue;
      if (p.text) appendItem(role, { type: th ? 'thought' : 'text', text: String(p.text) }, (a, b) => a + b);
      else if (p.inlineData?.data && String(p.inlineData.mimeType || '').startsWith('image/')) {
        appendItem(role, { type: 'image_b64', mimeType: p.inlineData.mimeType, data: p.inlineData.data }, null);
      } else if (p.executableCode?.code) {
        appendItem(role, { type: 'text', text: `\n\`\`\`${(p.executableCode.language || 'python').toLowerCase()}\n${p.executableCode.code}\n\`\`\`\n` }, joinStreamText_);
      } else if (p.codeExecutionResult?.output) {
        appendItem(role, { type: 'text', text: `\n**Execution Output:**\n\`\`\`text\n${p.codeExecutionResult.output}\n\`\`\`\n` }, joinStreamText_);
      }
    }
  };

  if (Array.isArray(data.chunkedPrompt?.chunks)) {
    for (const c of data.chunkedPrompt.chunks) {
      const role = String(c.role || '').toLowerCase() === 'user' ? 'User' : (String(c.role || '').toLowerCase() === 'model' ? 'Model' : 'Other');
      if (Array.isArray(c.parts)) extractRawParts(role, c.parts);
      else {
        const th = Boolean(c.isThought || c.thought);
        if ((!th || CONFIG.INCLUDE_THOUGHTS) && c.text) appendItem(role, { type: th ? 'thought' : 'text', text: String(c.text) }, joinStreamText_);
        if (c.inlineImage?.data) appendItem(role, { type: 'image_b64', mimeType: c.inlineImage.mimeType || 'image/png', data: c.inlineImage.data }, null);
        if (c.driveImage?.id) appendItem(role, { type: 'image_drive', fileId: c.driveImage.id }, null);
      }
    }
  } else if (Array.isArray(data.contents)) {
    for (const c of data.contents) {
      extractRawParts(String(c.role || '').toLowerCase() === 'user' ? 'User' : 'Model', c.parts);
    }
  }

  const turns = [];
  for (const turn of rawTurns) {
    const cleanedItems = [];
    for (const item of turn.items) {
      if (item.type === 'text' || item.type === 'thought') {
        const clean = cleanTextArtifacts_(item.text);
        if (clean) cleanedItems.push({ type: item.type, text: clean });
      } else cleanedItems.push(item);
    }
    if (cleanedItems.length) turns.push({ role: turn.role, items: cleanedItems });
  }
  return { title, model, updatedIso, systemInstruction, turns };
}

function formatTurnsMd_(turns) {
  const lines = [];
  for (const turn of turns) {
    const body = turn.items.filter(i => i.type === 'text' || i.type === 'thought')
      .map(i => i.type === 'thought' ? `<details>\n<summary>Thinking Process</summary>\n\n${i.text}\n\n</details>` : i.text)
      .join('\n\n');
    if (body.trim()) lines.push(`## ${turn.role}`, '', body, '', '---', '');
  }
  return lines;
}

function renderCleanMd_(chat) {
  const lines = [`# ${chat.title}`, ''];
  if (CONFIG.INCLUDE_METADATA) {
    lines.push(`> **Model:** ${chat.model} | **Updated:** ${chat.updatedIso.replace('T', ' ').slice(0, 16)} UTC`, '', '---', '');
  }
  if (chat.systemInstruction) lines.push('## System Instructions', '', chat.systemInstruction, '', '---', '');
  lines.push(...formatTurnsMd_(chat.turns));
  return lines.join('\n').trim() + '\n';
}

function renderContinuationMd_(chat, turns, startIdx, endIdx, partNum) {
  const lines = [];
  if (partNum) {
    lines.push(`# ${chat.title} (Part ${partNum})`, '');
  }
  const rangeLabel = `Turns ${startIdx + 1}–${endIdx}`;
  if (CONFIG.INCLUDE_METADATA) {
    lines.push(`> **Continuation (${rangeLabel})** | **Model:** ${chat.model} | **Updated:** ${chat.updatedIso.replace('T', ' ').slice(0, 16)} UTC`, '', '---', '');
  } else {
    lines.push(`> **Continuation (${rangeLabel})**`, '', '---', '');
  }
  lines.push(...formatTurnsMd_(turns));
  return lines.join('\n').trim() + '\n';
}

function getSourceFolders_() {
  const out = [];
  const targets = [...CONFIG.SOURCE_FOLDER_NAMES, CONFIG.KB_FOLDER_NAME];
  for (const n of targets) {
    const it = DriveApp.getFoldersByName(n);
    while (it.hasNext()) { const f = it.next(); if (!f.isTrashed()) out.push(f); }
  }
  // Also catch Drive folders containing "/KB" in their name
  const q = DriveApp.searchFolders(`title contains "/${CONFIG.KB_FOLDER_NAME}" and trashed = false`);
  while (q.hasNext()) { const f = q.next(); if (!f.isTrashed()) out.push(f); }
  return out;
}

function getOrCreateFolder_(name) {
  const it = DriveApp.getFoldersByName(name);
  while (it.hasNext()) { const f = it.next(); if (!f.isTrashed()) return f; }
  return DriveApp.createFolder(name);
}

function collectFiles_(folder, visited, out, sinceIso) {
  const id = folder.getId();
  if (visited.has(id)) return;
  visited.add(id);
  const fi = sinceIso
    ? folder.searchFiles(`trashed = false and modifiedDate > "${sinceIso}"`)
    : folder.getFiles();
  while (fi.hasNext()) out.push(fi.next());
  const si = folder.getFolders();
  while (si.hasNext()) {
    const s = si.next();
    if (!s.isTrashed()) collectFiles_(s, visited, out, sinceIso);
  }
}

function cleanName_(raw) {
  return raw.replace(/\.(json|prompt|txt)$/i, '').replace(/[\\/:*?"<>|]/g, '_').trim() || 'Untitled prompt';
}
```

Save and run **`flushKbSyncNow`** once more—check the **`Scanned:`**, **`KB tracked:`**, and **`ai-kb synced:`** numbers in the Execution log!

---

## User

Still no

---

## Model

Aha—I see **`English[KB]`** right there in your Drive screenshot!

That actually makes a great workflow (putting `[KB]` on a **folder** name instead of renaming every file inside it), **and** it explains why `KB tracked: 0` happened: our script was only checking `[kb]` on **filenames**, not on **folder names** like `English[KB]`.

I updated the script so **`[kb]` / `[core]` works on BOTH folder names (like `English[KB]`, `Maths[KB]`, `Formulas[core]`) AND file names**, plus it even handles plain `.md`/`.txt` files if you drop any into a `[KB]` folder.

---

### Replace Your Code in `Untitled 2.gs` with This Complete Version

```javascript
/**
 * Syncs AI Studio chats -> Clean .md in Drive -> Batched Private PDFs + Selective Batched Public KB Sync (Choice A)
 * Supports [kb] / [core] on BOTH folder names (e.g. "English[KB]") and file names, OR a folder named "KB".
 * Reads GITHUB_TOKEN, CALLBACK_SECRET, and optional AI_KB_TOKEN from Project Settings -> Script Properties.
 */
const CONFIG = {
  SOURCE_FOLDER_NAMES: ['Google AI Studio', 'AI Studio'],
  MD_FOLDER_NAME: 'AI Studio Markdown',
  PDF_FOLDER_NAME: 'AI Studio PDF',

  // Private PDF Worker Repo
  GITHUB_OWNER: 'inikashx-hub',
  GITHUB_REPO: 'AI-Studio-pdf-worker',
  GITHUB_BRANCH: 'main',

  // Public Selective Knowledge Base Repo (Choice A)
  KB_GITHUB_OWNER: 'inikashx-hub',
  KB_GITHUB_REPO: 'ai-kb',
  KB_GITHUB_BRANCH: 'main',
  KB_FOLDER_NAME: 'KB',
  KB_TAG_REGEX: /\[kb\]/i,
  KB_CORE_TAG_REGEX: /\[core\]/i,
  KB_IDLE_MINUTES: 15,        // Wait 15 min idle before pushing to ai-kb
  KB_BATCH_HOURS: 4,          // Push batched commit to ai-kb at most every 4 hours
  KB_MAX_BATCH_FILES: 25,

  INCLUDE_THOUGHTS: false,
  INCLUDE_METADATA: true,
  STATE_PREFIX: 'gh_sync_',
  SCAN_STATE_KEY: 'gh_last_scan_ms',
  DISPATCH_STATE_KEY: 'gh_last_pdf_dispatch_ms',
  KB_DISPATCH_STATE_KEY: 'gh_last_kb_dispatch_ms',

  PDF_IDLE_MINUTES: 25,       // Only build PDF after chat has been idle for 25 min
  PDF_BATCH_HOURS: 4,         // Trigger GitHub PDF batch at most every 4 hours (max 6x/day)
  MAX_SINGLE_PDF_BYTES: 15 * 1024 * 1024
};

function getSecrets_() {
  const props = PropertiesService.getScriptProperties();
  const token = (props.getProperty('GITHUB_TOKEN') || '').trim();
  const kbToken = (props.getProperty('AI_KB_TOKEN') || token).trim();
  const secret = (props.getProperty('CALLBACK_SECRET') || '').trim();
  if (!token || !secret) {
    throw new Error('Missing GITHUB_TOKEN or CALLBACK_SECRET in Project Settings -> Script Properties.');
  }
  return { token, kbToken, secret };
}

function hashTurns_(turns) {
  const raw = JSON.stringify(turns);
  const digest = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, raw, Utilities.Charset.UTF_8);
  return digest.map(b => ('0' + ((b & 0xff).toString(16))).slice(-2)).join('');
}

function syncCleanMarkdown() {
  syncCleanMarkdown_(false, false);
}

// Run manually anytime you want pending PDFs built immediately
function flushPendingPdfsNow() {
  syncCleanMarkdown_(true, false);
}

// Run manually anytime you want [kb] / [core] chats pushed to ai-kb immediately
function flushKbSyncNow() {
  syncCleanMarkdown_(false, true);
}

function syncCleanMarkdown_(forcePdfFlush, forceKbFlush) {
  const cache = CacheService.getScriptCache();
  if (cache.get('gh_sync_running')) return;
  cache.put('gh_sync_running', '1', 300);

  const startTime = Date.now();
  const fullScan = forcePdfFlush || forceKbFlush;

  try {
    const { token, kbToken } = getSecrets_();
    const mdFolder = getOrCreateFolder_(CONFIG.MD_FOLDER_NAME);
    const pdfFolder = getOrCreateFolder_(CONFIG.PDF_FOLDER_NAME);
    const rootId = DriveApp.getRootFolder().getId();
    const visited = new Set([mdFolder.getId(), pdfFolder.getId()]);

    const props = PropertiesService.getScriptProperties();
    const lastScanMs = Number(props.getProperty(CONFIG.SCAN_STATE_KEY) || 0);
    const sinceIso = (!fullScan && lastScanMs > 0)
      ? new Date(lastScanMs - 5 * 60 * 1000).toISOString()
      : '';

    const files = [];
    for (const f of getSourceFolders_()) collectFiles_(f, visited, files, sinceIso);

    const seen = new Set(files.map(f => f.getId()));
    try {
      const baseQ = 'mimeType = "application/vnd.google-makersuite.prompt" and trashed = false';
      const fullQ = sinceIso ? `${baseQ} and modifiedDate > "${sinceIso}"` : baseQ;
      const q = DriveApp.searchFiles(fullQ);
      while (q.hasNext()) {
        const pf = q.next();
        if (!seen.has(pf.getId())) { seen.add(pf.getId()); files.push(pf); }
      }
    } catch (e) {}

    const stateMap = props.getProperties();
    let mdCount = 0, queuedPdfCount = 0, kbSyncedCount = 0, paused = false;

    // PHASE 1: Fast Markdown sync in Drive (0 GitHub minutes)
    for (const file of files) {
      if (Date.now() - startTime > 120000) { paused = true; break; }
      if (file.isTrashed()) continue;
      const mime = file.getMimeType();
      if (mime.startsWith('application/vnd.google-apps.') || mime.startsWith('image/') ||
          mime.startsWith('video/') || mime.startsWith('audio/') || mime === 'application/pdf') continue;
      if (file.getSize() > 15 * 1024 * 1024) continue;

      const id = file.getId();
      const updatedMs = file.getLastUpdated().getTime();
      const key = CONFIG.STATE_PREFIX + id;
      let prev = {};
      if (stateMap[key]) { try { prev = JSON.parse(stateMap[key]); } catch (e) {} }

      const targetKbPath = resolveKbTarget_(file, cleanName_(file.getName()), rootId);
      const needsMd = prev.t !== updatedMs || !prev.m;
      const needsKbPathSync = (targetKbPath || '') !== (prev.kbTarget || '') || (targetKbPath || '') !== (prev.kbP || '');
      if (!needsMd && !needsKbPathSync) continue;

      if (needsMd) {
        let data = null;
        try { data = JSON.parse(file.getBlob().getDataAsString('UTF-8')); } catch (e) {}

        if (data && (data.chunkedPrompt || data.contents || data.runSettings)) {
          const chat = extractCleanChat_(data, file);
          const baseName = cleanName_(file.getName());
          const mdName = `${baseName}.md`;
          const fullMdText = renderCleanMd_(chat);

          let mdId = prev.m || null;
          if (!mdId) {
            const byName = mdFolder.getFilesByName(mdName);
            while (byName.hasNext()) {
              const ef = byName.next();
              if (!ef.isTrashed()) { mdId = ef.getId(); break; }
            }
          }
          let updated = false;
          if (mdId) {
            try {
              const ex = DriveApp.getFileById(mdId);
              if (!ex.isTrashed()) {
                ex.setContent(fullMdText);
                if (ex.getName() !== mdName) ex.setName(mdName);
                updated = true;
              }
            } catch (e) {}
          }
          if (!updated) mdId = mdFolder.createFile(Utilities.newBlob(fullMdText, 'text/markdown', mdName)).getId();

          prev.t = updatedMs;
          prev.m = mdId;
          mdCount++;
        } else if (targetKbPath && /\.(md|txt)$/i.test(file.getName())) {
          // Also allow direct .md / .txt files placed inside [KB] / KB folders
          prev.t = updatedMs;
          prev.m = id;
          prev.isPlainText = true;
        } else {
          continue;
        }
      }

      if (targetKbPath) prev.kbTarget = targetKbPath;
      else delete prev.kbTarget;

      saveStateKey_(props, stateMap, key, prev);
    }

    if (!paused) {
      props.setProperty(CONFIG.SCAN_STATE_KEY, String(startTime));
    }

    // PHASE 2: Batched + Idle-Debounced Private PDF Queueing
    const lastPdfMs = Number(props.getProperty(CONFIG.DISPATCH_STATE_KEY) || 0);
    const canDispatchPdf = forcePdfFlush || (Date.now() - lastPdfMs >= CONFIG.PDF_BATCH_HOURS * 60 * 60 * 1000);
    const pdfIdleMs = CONFIG.PDF_IDLE_MINUTES * 60 * 1000;

    if (canDispatchPdf && !paused) {
      for (const key of Object.keys(stateMap)) {
        if (!key.startsWith(CONFIG.STATE_PREFIX)) continue;
        if (Date.now() - startTime > 190000) { paused = true; break; }

        let prev = {};
        try { prev = JSON.parse(stateMap[key]); } catch (e) { continue; }
        if (!prev.t || prev.isPlainText) continue;

        const jobInFlight = prev.qa && (Date.now() - prev.qa < 20 * 60 * 1000);
        const needsPdf = (prev.pt !== prev.t || !prev.p) && !jobInFlight;
        if (!needsPdf) continue;
        if (!forcePdfFlush && (Date.now() - prev.t < pdfIdleMs)) continue;

        const id = key.slice(CONFIG.STATE_PREFIX.length);
        let file;
        try { file = DriveApp.getFileById(id); } catch (e) { continue; }
        if (file.isTrashed() || file.getSize() > 15 * 1024 * 1024) continue;

        const updatedMs = file.getLastUpdated().getTime();
        if (!forcePdfFlush && (Date.now() - updatedMs < pdfIdleMs)) continue;

        let data;
        try { data = JSON.parse(file.getBlob().getDataAsString('UTF-8')); } catch (e) { continue; }
        if (!data || (!data.chunkedPrompt && !data.contents && !data.runSettings)) continue;

        const chat = extractCleanChat_(data, file);
        const baseName = cleanName_(file.getName());
        const fullMdText = renderCleanMd_(chat);

        const fullTc = chat.turns.length;
        const fullTh = hashTurns_(chat.turns);
        let mode = 'full', part = 1, partStartTc = 0, expectedTc = 0, existingPdfId = null;
        let pdfName = `${baseName}.pdf`, turnsForPdf = chat.turns, jobMdText = fullMdText, skipQueue = false;

        if (prev.p && typeof prev.tc === 'number' && prev.tc > 0 && prev.tc <= fullTc && prev.th) {
          const prefixHash = hashTurns_(chat.turns.slice(0, prev.tc));
          if (prefixHash === prev.th) {
            try {
              const existingPdf = DriveApp.getFileById(prev.p);
              if (!existingPdf.isTrashed()) {
                const curPart = prev.part || 1;
                const curPdfName = curPart > 1 ? `${baseName} (Part ${curPart}).pdf` : `${baseName}.pdf`;
                if (fullTc === prev.tc) {
                  if (existingPdf.getName() !== curPdfName) existingPdf.setName(curPdfName);
                  prev.pt = updatedMs;
                  skipQueue = true;
                } else if (existingPdf.getSize() < CONFIG.MAX_SINGLE_PDF_BYTES) {
                  mode = 'append'; part = curPart; partStartTc = prev.partStartTc || 0;
                  expectedTc = prev.tc; existingPdfId = prev.p; pdfName = curPdfName;
                  turnsForPdf = chat.turns.slice(prev.tc);
                  jobMdText = renderContinuationMd_(chat, turnsForPdf, prev.tc, fullTc, null);
                } else {
                  mode = 'new_part'; part = curPart + 1; partStartTc = prev.tc;
                  expectedTc = prev.tc; existingPdfId = null; pdfName = `${baseName} (Part ${part}).pdf`;
                  turnsForPdf = chat.turns.slice(prev.tc);
                  jobMdText = renderContinuationMd_(chat, turnsForPdf, prev.tc, fullTc, part);
                }
              }
            } catch (e) {}
          }
        }
