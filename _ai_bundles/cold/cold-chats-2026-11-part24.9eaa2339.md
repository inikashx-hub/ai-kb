# Cold Knowledge Bundle: chats-2026-11-part24


---
## FILE: `chats/Optimizing Two-Step LLM Routing.md` [Part 14/14]

if (!skipQueue) {
          const assets = collectAssets_(turnsForPdf);
          const jobPayload = {
            sourceId: id, updatedMs, baseName, pdfName, mode, existingPdfId,
            expectedTc, nextTc: fullTc, nextTh: fullTh, part, partStartTc,
            mdText: jobMdText, assets
          };
          if (pushJobToGitHub_(`jobs/${id}.json`, jobPayload, token)) {
            prev.qt = updatedMs;
            prev.qa = Date.now();
            queuedPdfCount++;
          }
        }
        saveStateKey_(props, stateMap, key, prev);
      }

      if (queuedPdfCount > 0) {
        triggerGitHubWorkflow_(token);
        if (!paused) props.setProperty(CONFIG.DISPATCH_STATE_KEY, String(Date.now()));
      }
    }

    // PHASE 3: Batched Selective Sync to Public ai-kb Repo
    const lastKbMs = Number(props.getProperty(CONFIG.KB_DISPATCH_STATE_KEY) || 0);
    const canDispatchKb = forceKbFlush || (Date.now() - lastKbMs >= CONFIG.KB_BATCH_HOURS * 60 * 60 * 1000);
    const kbIdleMs = CONFIG.KB_IDLE_MINUTES * 60 * 1000;
    let kbTrackedCount = 0;

    if (canDispatchKb && !paused) {
      const kbOps = [];
      const pendingStateUpdates = [];

      for (const key of Object.keys(stateMap)) {
        if (!key.startsWith(CONFIG.STATE_PREFIX)) continue;
        if (kbOps.length >= CONFIG.KB_MAX_BATCH_FILES) break;
        if (Date.now() - startTime > 240000) { paused = true; break; }

        let prev = {};
        try { prev = JSON.parse(stateMap[key]); } catch (e) { continue; }
        if (!prev.t || !prev.m) continue;

        const targetPath = prev.kbTarget || null;
        const oldPath = prev.kbP || null;
        if (targetPath) kbTrackedCount++;
        if (!targetPath && !oldPath) continue;
        if (targetPath && prev.kbT === prev.t && oldPath === targetPath) continue;
        if (!forceKbFlush && (Date.now() - prev.t < kbIdleMs)) continue;

        const id = key.slice(CONFIG.STATE_PREFIX.length);
        let srcFile;
        try { srcFile = DriveApp.getFileById(id); } catch (e) { continue; }

        if (srcFile.isTrashed() || !targetPath) {
          if (oldPath) {
            kbOps.push({ path: oldPath, content: null });
            delete prev.kbP; delete prev.kbT; delete prev.kbTarget;
            pendingStateUpdates.push({ key, prev });
          }
          continue;
        }

        const updatedMs = srcFile.getLastUpdated().getTime();
        if (!forceKbFlush && (Date.now() - updatedMs < kbIdleMs)) continue;

        let mdText = '';
        try {
          const mdFile = DriveApp.getFileById(prev.m);
          if (mdFile.isTrashed()) continue;
          mdText = mdFile.getBlob().getDataAsString('UTF-8');
        } catch (e) { continue; }

        if (oldPath && oldPath !== targetPath) {
          kbOps.push({ path: oldPath, content: null });
        }
        kbOps.push({ path: targetPath, content: mdText });
        prev.kbP = targetPath;
        prev.kbT = prev.t;
        pendingStateUpdates.push({ key, prev });
      }

      if (kbOps.length > 0) {
        const pushed = pushBatchToGitHubRepo_(
          CONFIG.KB_GITHUB_OWNER,
          CONFIG.KB_GITHUB_REPO,
          CONFIG.KB_GITHUB_BRANCH,
          kbOps,
          `sync: batch update ${kbOps.length} KB file(s) from Drive`,
          kbToken
        );
        if (pushed) {
          kbSyncedCount = pendingStateUpdates.length;
          for (const item of pendingStateUpdates) {
            saveStateKey_(props, stateMap, item.key, item.prev);
          }
          if (!paused) props.setProperty(CONFIG.KB_DISPATCH_STATE_KEY, String(Date.now()));
        }
      }
    }

    console.log(paused
      ? `Paused at time guard. Scanned: ${files.length}, MD: ${mdCount}, KB tracked: ${kbTrackedCount}, PDF queued: ${queuedPdfCount}, ai-kb synced: ${kbSyncedCount}.`
      : `Done! Scanned: ${files.length}, MD: ${mdCount}, KB tracked: ${kbTrackedCount}, PDF queued: ${queuedPdfCount}, ai-kb synced: ${kbSyncedCount}`);
  } finally {
    cache.remove('gh_sync_running');
  }
}

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
  let isCoreTag = CONFIG.KB_CORE_TAG_REGEX.test(rawName);
  let isKbTag = CONFIG.KB_TAG_REGEX.test(rawName);

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
        if (CONFIG.KB_CORE_TAG_REGEX.test(segs[i])) isCoreTag = true;
        if (CONFIG.KB_TAG_REGEX.test(segs[i])) isKbTag = true;
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

  const cleanFolders = relFolders
    .map(f => sanitizePathSlug_(f.replace(/\s*\[(kb|core)\]\s*/gi, ' ')))
    .filter(Boolean);

  if (isCoreTag || (cleanFolders.length > 0 && cleanFolders[0] === 'core')) {
    return `core/${cleanFile}.md`;
  }
  if (cleanFolders.length > 0) {
    return `chats/${cleanFolders.join('/')}/${cleanFile}.md`;
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
      delete st.kbT; delete st.kbP; delete st.kbTarget; delete st.isPlainText;
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
  const seenIds = new Set();
  const addFolder = f => {
    if (f && !f.isTrashed() && !seenIds.has(f.getId())) {
      seenIds.add(f.getId());
      out.push(f);
    }
  };
  for (const n of [...CONFIG.SOURCE_FOLDER_NAMES, CONFIG.KB_FOLDER_NAME]) {
    const it = DriveApp.getFoldersByName(n);
    while (it.hasNext()) addFolder(it.next());
  }
  const queries = [
    `title contains '${CONFIG.KB_FOLDER_NAME}' and trashed = false`,
    `title contains 'core' and trashed = false`
  ];
  for (const qStr of queries) {
    try {
      const q = DriveApp.searchFolders(qStr);
      while (q.hasNext()) {
        const f = q.next();
        const name = f.getName().trim();
        if (/^kb$/i.test(name) || /\[(kb|core)\]/i.test(name) || /\/kb(\/|$)/i.test(name)) {
          addFolder(f);
        }
      }
    } catch (e) {}
  }
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

Save and run **`flushKbSyncNow`**—any valid chats inside **`English[KB]`** will now push cleanly to `chats/english/...` in `inikashx-hub/ai-kb`! *(Note: Make sure the files inside `English[KB]` are your AI Studio JSON/chat files or `.md`/`.txt` files, not PDFs or Google Docs.)*

---
