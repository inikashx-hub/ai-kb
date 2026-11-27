# Cold Knowledge Bundle: chats-2026-11-part11


---
## FILE: `chats/Optimizing Two-Step LLM Routing.md` [Part 13/17 — 4. Enforce Strict Router & Grounding Rules]

## [Chapter Context: 4. Enforce Strict Router & Grounding Rules]

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

      const pLock = LockService.getScriptLock();
      pLock.waitLock(10000);
      try {
        let latest = {};
        const latestRaw = props.getProperty(key);
        if (latestRaw) { try { latest = JSON.parse(latestRaw); } catch (e) {} }
        const merged = Object.assign({}, latest, prev);
        props.setProperty(key, JSON.stringify(merged));
        stateMap[key] = JSON.stringify(merged);
      } finally {
        pLock.releaseLock();
      }
    }

    if (!paused) {
      props.setProperty(CONFIG.SCAN_STATE_KEY, String(startTime));
    }

    // PHASE 2: Batched + Idle-Debounced PDF Queueing
    const lastDispatchMs = Number(props.getProperty(CONFIG.DISPATCH_STATE_KEY) || 0);
    const batchCooldownMs = CONFIG.PDF_BATCH_HOURS * 60 * 60 * 1000;
    const idleThresholdMs = CONFIG.PDF_IDLE_MINUTES * 60 * 1000;
    const canDispatchPdf = forceFlush || (Date.now() - lastDispatchMs >= batchCooldownMs);

    if (canDispatchPdf && !paused) {
      for (const key of Object.keys(stateMap)) {
        if (!key.startsWith(CONFIG.STATE_PREFIX)) continue;
        if (Date.now() - startTime > 220000) { paused = true; break; }

        let prev = {};
        try { prev = JSON.parse(stateMap[key]); } catch (e) { continue; }
        if (!prev.t) continue;

        const jobInFlight = prev.qa && (Date.now() - prev.qa < 20 * 60 * 1000);
        const needsPdf = (prev.pt !== prev.t || !prev.p) && !jobInFlight;
        if (!needsPdf) continue;

        if (!forceFlush && (Date.now() - prev.t < idleThresholdMs)) continue;

        const id = key.slice(CONFIG.STATE_PREFIX.length);
        let file;
        try { file = DriveApp.getFileById(id); } catch (e) { continue; }
        if (file.isTrashed() || file.getSize() > 15 * 1024 * 1024) continue;

        const updatedMs = file.getLastUpdated().getTime();
        if (!forceFlush && (Date.now() - updatedMs < idleThresholdMs)) continue;

        let data;
        try { data = JSON.parse(file.getBlob().getDataAsString('UTF-8')); } catch (e) { continue; }
        if (!data || (!data.chunkedPrompt && !data.contents && !data.runSettings)) continue;

        const chat = extractCleanChat_(data, file);
        const baseName = cleanName_(file.getName());
        const fullMdText = renderCleanMd_(chat);

        const fullTc = chat.turns.length;
        const fullTh = hashTurns_(chat.turns);
        let mode = 'full';
        let part = 1;
        let partStartTc = 0;
        let expectedTc = 0;
        let existingPdfId = null;
        let pdfName = `${baseName}.pdf`;
        let turnsForPdf = chat.turns;
        let jobMdText = fullMdText;
        let skipQueue = false;

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
                  mode = 'append';
                  part = curPart;
                  partStartTc = prev.partStartTc || 0;
                  expectedTc = prev.tc;
                  existingPdfId = prev.p;
                  pdfName = curPdfName;
                  turnsForPdf = chat.turns.slice(prev.tc);
                  jobMdText = renderContinuationMd_(chat, turnsForPdf, prev.tc, fullTc, null);
                } else {
                  mode = 'new_part';
                  part = curPart + 1;
                  partStartTc = prev.tc;
                  expectedTc = prev.tc;
                  existingPdfId = null;
                  pdfName = `${baseName} (Part ${part}).pdf`;
                  turnsForPdf = chat.turns.slice(prev.tc);
                  jobMdText = renderContinuationMd_(chat, turnsForPdf, prev.tc, fullTc, part);
                }
              }
            } catch (e) {}
          }
        }

        if (!skipQueue) {
          const assets = collectAssets_(turnsForPdf);
          const jobPayload = {
            sourceId: id,
            updatedMs,
            baseName,
            pdfName,
            mode,
            existingPdfId,
            expectedTc,
            nextTc: fullTc,
            nextTh: fullTh,
            part,
            partStartTc,
            mdText: jobMdText,
            assets
          };
          if (pushJobToGitHub_(`jobs/${id}.json`, jobPayload, token)) {
            prev.qt = updatedMs;
            prev.qa = Date.now();
            queuedCount++;
          }
        }

        const pLock = LockService.getScriptLock();
        pLock.waitLock(10000);
        try {
          let latest = {};
          const latestRaw = props.getProperty(key);
          if (latestRaw) { try { latest = JSON.parse(latestRaw); } catch (e) {} }
          props.setProperty(key, JSON.stringify(Object.assign({}, latest, prev)));
        } finally {
          pLock.releaseLock();
        }
      }

      if (queuedCount > 0) {
        triggerGitHubWorkflow_(token);
        if (!paused) {
          props.setProperty(CONFIG.DISPATCH_STATE_KEY, String(Date.now()));
        }
      }
    }

    console.log(paused
      ? `Paused at time guard. MD: ${mdCount}, Queued for PDF: ${queuedCount}. Run again to queue remaining.`
      : `Done! MD updated: ${mdCount}, Queued for GitHub PDF batch: ${queuedCount}`);
  } finally {
    cache.remove('gh_sync_running');
  }
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
  const all = props.getProperties();
  let resetCount = 0;

  for (const key of Object.keys(all)) {
    if (!key.startsWith(CONFIG.STATE_PREFIX)) continue;
    try {
      const st = JSON.parse(all[key]);
      delete st.t;
      delete st.pt;
      delete st.qt;
      delete st.qa;
      delete st.tc;
      delete st.th;
      delete st.part;
      delete st.partStartTc;
      props.setProperty(key, JSON.stringify(st));
      resetCount++;
    } catch (e) {}
  }
  console.log(`Reset ${resetCount} chat(s). Running flushPendingPdfsNow()...`);
  syncCleanMarkdown_(true);
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
  for (const n of CONFIG.SOURCE_FOLDER_NAMES) {
    const it = DriveApp.getFoldersByName(n);
    while (it.hasNext()) { const f = it.next(); if (!f.isTrashed()) out.push(f); }
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

### Quick Checklist After Pasting
1. **Save** the Apps Script (`Ctrl + S` / Save icon).
2. Make sure you also update **`.github/workflows/build-pdfs.yml`** in `AI-Studio-pdf-worker` with the `actions/cache@v4` version from the previous message.
3. Want to test it right away without waiting 4 hours? Select **`flushPendingPdfsNow`** from the Run dropdown in Apps Script and tap **Run**. *(Once the first cached GitHub run finishes, every run after that restores all packages from cache!)*

---

## User

Should I update version in apps script?

---

## Model

**No—you don't need to update the deployment version for this change**, and here is why:

* **Time-driven triggers (`syncCleanMarkdown`) and manual runs (`flushPendingPdfsNow`)** always execute your latest saved code automatically as soon as you hit Save.
* **Your Web App deployment (`doPost`)** only runs the pinned deployment version—**but we didn't change a single line of `doPost`**, `getSecrets_`, or `PDF_FOLDER_NAME`, so your existing `GAS_WEBHOOK_URL` will keep working identically as-is.

### If You Still Want to Sync the Version (Optional)
Just watch out for one classic Apps Script trap so you don't break your GitHub Secret:
* **Do NOT click `Deploy → New deployment`** (that generates a brand-new URL and breaks `GAS_WEBHOOK_URL` in GitHub).
* Instead, go to **`Deploy → Manage deployments → Edit (pencil icon ✏️) → Version: New version → Deploy`**. That updates your code version while keeping the **exact same Web App URL** [1.1.1, 1.1.2].

---

## User

Updated it

---

## Model

Awesome! Here is a quick verification tip, and then we’re ready for the **storage & `ai-kb` sync** step:

### 1. Quick Compute Check
* Run **`flushPendingPdfsNow`** once in Apps Script (if you have any un-built PDFs) and check the **Actions** tab in `AI-Studio-pdf-worker`.
* *Note:* The **first** run takes normal time while saving the cache; from the **second** run onward, it restores apt/pip/MathJax from cache and stays fast (and runs at most every 4 hours after 25 min idle).

---

### 2. Next Up: Storage & Connecting to `ai-kb` (at 50 Chats/Day)
Because your Apps Script **already** builds clean `.md` files in Drive every 15 minutes (using 0 GitHub minutes!) and can read your Drive folders (`Maths`, `Reasoning`, `General Awareness`, `English`), we can push `.md` files straight from Drive to `inikashx-hub/ai-kb` in batched commits.

Before writing that sync, decide how you want to handle the **50 chats/day (~67.5 MB/month)** volume inside `ai-kb` so your RAG packs don't overflow the 20-URL / 35 KB limits:

* **Choice A — Selective Sync (Simplest):**
  Keep all 50 chats/day in Drive (`AI Studio Markdown` + `AI Studio PDF`), and only auto-push **selected folders** or chats tagged **`[kb]`** into `ai-kb` (also keeps any `Private/` folder off your public repo).
* **Choice B — Auto-Distill Before Sync (Best Long-Term for URL Context):**
  Keep full 10k-token chats in Drive, and distill each chat into a **crisp 2–4 KB takeaway/cheat-sheet `.md`** before pushing to `ai-kb`—shrinking storage by **~15×** so 1-turn packs stay fast for months.
* **Choice C — Sync All 50 Raw Chats/Day (High-Volume Setup):**
  Push all study folders into `ai-kb` bucketed by **Subject + Month** (`chats/maths-2026-11/`), upgrade `build-kb.py` to a **2-level index (`llms.txt` → `llms-maths.txt`)**, and run `build-kb.yml` on a **6-hour schedule** instead of every commit so `.git` history doesn't bloat.

Which path (`A`, `B`, or `C`) fits your daily study style best?

---

## User

Compare the 3 choices across various parameters

---

## Model

Here is a head-to-head comparison of **Choice A**, **Choice B**, and **Choice C** tailored specifically to your **50 chats/day (10k tokens each)** Banking-exam workflow:

---

### Side-by-Side Comparison

| Parameter | **Choice A: Selective Sync** *(Tag / Folder Filter)* | **Choice B: Auto-Distill** *(10k → ~3 KB Notes)* | **Choice C: Full Raw 50/Day Sync** *(Monthly Shards + 2-Level Index)* |
| :--- | :--- | :--- | :--- |
| **Monthly `ai-kb` Growth** | **~5–15 MB / month** *(depends on how many you tag)* | **~4.5 MB / month** *(~15× smaller than raw)* | **~67.5 MB / month** raw + bundle churn |
| **Git History Bloat Risk** | **Very Low** | **Very Low** | **High** *(needs 6-hr `cron` rebuilds + annual repo rotation)* |
| **1-Turn Pack Compatibility** | **High** *(packs stay small for months)* | **Highest** *(hundreds of distilled chats fit in 1–3 URLs)* | **Low** *(subject packs overflow 20 URLs unless split by month)* |
| **Turns Needed at Scale** | **1 Turn** (for packs) / **2 Turns** (`llms.txt`) | **1 Turn** (for almost everything) | **2 Turns** (within a subject index) / **3 Turns** (cross-month search) |
| **Detail & Recall Accuracy** | **100% verbatim** on synced chats *(0% on unsynced)* | **High for concepts/tricks**, drops specific raw Q&As | **100% verbatim** across all 50 chats/day *(but noisy)* |
| **Privacy Risk (Public Repo)** | **Very Low** *(only approved folders/tags leave Drive)* | **Medium** *(automated summaries could leak private topics unless filtered)* | **Highest** *(all non-excluded chats go public)* |
| **Needs Gemini API Key?** | **No (100% No-API)** | **Yes** *(for automated background distilling)* — *or manual end-of-chat prompt* | **No (100% No-API)** |
| **Daily Manual Effort** | **Low** *(tag `[kb]` or drop into `KB/` folder)* | **Zero** *(if automated)* | **Zero** *(just organize folders or let auto-router sort)* |
| **Repo Lifespan Before Reset** | **1.5 – 3+ years** | **2 – 4+ years** | **~4 – 6 months** before rotating (`ai-kb-2026`, `ai-kb-2027`) |

---

### How They Compare on the 5 Things That Matter Most

#### 1. Exam-Prep Accuracy (`Maths / Reasoning` vs. `General Awareness`)
* **Choice B (Distill)** is **best for Maths, Reasoning & English rules**: In a 10k-token *Percentages* practice session, ~80% is trial-and-error chatter. Distilling keeps the **formulas, shortcuts, and mistakes you made**, giving Gemini super clean, noise-free context. *However*, it loses exact wording of individual GA MCQs or edge-case practice problems.
* **Choice C (Full Raw)** keeps **every single question and step verbatim**, which helps if you later want to re-find a specific practice problem—but that extra chatter fills up your 35 KB URL chunks fast.
* **Choice A (Selective)** gives you **full verbatim fidelity** on the chats that actually matter (concept sessions, GA compendiums, revision notes) while ignoring throwaway practice drills.

#### 2. The Hidden "No-API" Catch in Choice B
* Remember you originally wanted **no API usage**.
* **Automated** distillation of 50 chats/day requires calling an LLM API (like Gemini API free tier) inside Apps Script or GitHub Actions.
* **Zero-API workaround for Choice B:** Before ending a long study chat in AI Studio, you can ask `"Summarize all formulas, shortcuts, and traps from this chat into a clean cheat sheet"` and only sync *that*—or stick with Choice A / C for pure zero-API automation.

#### 3. 1-Turn Speed vs. Multi-Turn Search
* Because **Choice A and B** keep each subject small, your static **`packs/`** stay under ~5–8 URLs for months—keeping **true 1-Turn answers** alive.
* In **Choice C**, `Maths` alone grows by ~10–15 MB/month (~300–450 URL chunks/month!). You can’t load 300 URLs in 1 turn, so you must split into `maths-2026-11`, `maths-2026-12` and navigate via **`llms.txt` → `llms-maths.txt` → Cold Bundle** (2–3 turns).

#### 4. Privacy & Public Repo Safety
* **Choice A** is the safest: your private/personal chats stay in Google Drive by default, and **only** study folders or `[kb]`-tagged chats ever touch your public `ai-kb` repo.
* **Choice C** pushes almost everything by default unless you maintain a strict blocklist.

#### 5. Repo Maintenance Over 6–12 Months
* **Choice A & B** keep `ai-kb` compact and fast for years.
* **Choice C** forces two extra safeguards: switching `build-kb.yml` from `on: push` to a **6-hour `cron` schedule** (to avoid 50×/day `.git` bundle rewrites) and starting a fresh archive repo every ~6 months.

---

### Practical Recommendation for Your Setup
For Banking prep with **50 chats/day** and **zero APIs**, the sweet spot is **Choice A (Folder/Tag Selective Sync)** paired with your **Drive archive**:
1. Let your **Apps Script** keep converting **all 50 chats/day** into clean `.md` + `.pdf` privately inside Google Drive.
2. Auto-push **only** specific study folders (or chats with `[kb]` in the name, plus your GA compendiums) from Apps Script into `ai-kb` in **4-hour batches**—giving you **1-Turn speed**, **100% privacy control**, and **zero repo bloat**.
3. *(If you ever want to search one of your 10,000 raw non-`[kb]` practice sessions later, you already have all of them neatly archived as clean `.md` and `.pdf` in Drive—or batchable into NotebookLM anytime.)*

Which one (`A`, `B`, or `C`) do you want to implement?

---

## User

Choice A

---

## Model

Let's implement **Choice A (Selective Sync)**.

Every 15 minutes, Apps Script will continue building clean `.md` files privately in Google Drive for **all 50 chats/day**. Then, in **4-hour batches** (after 15 minutes of idle time), it will push **only** selected study chats into `inikashx-hub/ai-kb` in **one single batched Git commit** (so `build-kb.yml` only rebuilds once per batch, keeping `.git` history tiny).

---

### How You Control What Goes to `ai-kb`
Any chat stays **100% private in Google Drive** *unless* it matches one of these simple rules:
1. **Tag in filename:** Add **`[kb]`** anywhere in the chat title/filename (e.g., `Percentages Tricks [kb]`) → syncs to `chats/<your-subject-folder>/...` in `ai-kb` (the `[kb]` tag is automatically stripped from the GitHub filename).
2. **Core cheat sheets:** Add **`[core]`** in the filename (e.g., `Math Formulas [core]`) → syncs to `core/` in `ai-kb` (always loaded in Tier 1 `hot-core.md`).
3. **Or use a `KB` folder:** Put files inside a folder named **`KB`** inside your AI Studio folder (e.g., `Google AI Studio/KB/Maths/...` or `Google AI Studio/KB/core/...`) → auto-syncs everything inside `KB/` without needing `[kb]` in every filename.

---

### Step 1: Give Apps Script Write Access to `ai-kb` (Important!)
In Apps Script → **Project Settings → Script Properties**, check your `GITHUB_TOKEN`:
* If your `GITHUB_TOKEN` is a fine-grained token scoped **only** to `AI-Studio-pdf-worker`, either:
  * **Option 1:** Edit that token on GitHub to also grant **Contents: Read and write** on **`ai-kb`**, **OR**
  * **Option 2:** Create a second fine-grained token for `ai-kb` (**Contents: Read and write**) and add it to Script Properties as **`AI_KB_TOKEN`** (the script checks `AI_KB_TOKEN` first and falls back to `GITHUB_TOKEN`).

---

### Step 2: Replace Your Google Apps Script with This Complete Code
Select all, delete your old script, paste this in, and save (`syncCleanMarkdown` stays on your existing 15-minute trigger, and you get a new **`flushKbSyncNow()`** function if you ever want an immediate push to `ai-kb`!):
