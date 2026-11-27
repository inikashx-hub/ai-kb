# Cold Knowledge Bundle: chats-2026-11-part10


---
## FILE: `chats/Optimizing Two-Step LLM Routing.md` [Part 12/17 — 4. Enforce Strict Router & Grounding Rules]

## [Chapter Context: 4. Enforce Strict Router & Grounding Rules]

prev.p = created.getId; prev.pt = payload.updatedMs; if (typeof payload.nextTc === 'number') prev.tc = payload.nextTc; if (payload.nextTh) prev.th = payload.nextTh; prev.part = payload.part || 1; prev.partStartTc = payload.partStartTc || 0; delete prev.qa; props.setProperty(key, JSON.stringify(prev));

      return jsonResponse_({ ok: true, pdfId: created.getId }); } finally { lock.releaseLock; } } catch (err) { return jsonResponse_({ ok: false, error: err.message }); } }

function jsonResponse_(obj) { return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON); }

function pushJobToGitHub_(path, obj, token) { const url = `https://api.github.com/repos/${CONFIG.GITHUB_OWNER}/${CONFIG.GITHUB_REPO}/contents/${path}`; const headers = { Authorization: `Bearer ${token}`, Accept: 'application/vnd.github+json' };

  let sha = null; const getResp = UrlFetchApp.fetch(url, { method: 'get', headers, muteHttpExceptions: true }); if (getResp.getResponseCode === 200) { try { sha = JSON.parse(getResp.getContentText).sha; } catch (e) {} }

  const body = { message: `Queue ${path}`, content: Utilities.base64Encode(JSON.stringify(obj), Utilities.Charset.UTF_8), branch: CONFIG.GITHUB_BRANCH }; if (sha) body.sha = sha;

  const putResp = UrlFetchApp.fetch(url, { method: 'put', contentType: 'application/json', headers, payload: JSON.stringify(body), muteHttpExceptions: true }); const code = putResp.getResponseCode; if (code !== 200 && code !== 201) { console.error(`GitHub PUT failed (${code}): ${putResp.getContentText()}`); return false; } return true; }

function triggerGitHubWorkflow_(token) { const url = `https://api.github.com/repos/${CONFIG.GITHUB_OWNER}/${CONFIG.GITHUB_REPO}/actions/workflows/build-pdfs.yml/dispatches`; const resp = UrlFetchApp.fetch(url, { method: 'post', contentType: 'application/json', headers: { Authorization: `Bearer ${token}`, Accept: 'application/vnd.github+json' }, payload: JSON.stringify({ ref: CONFIG.GITHUB_BRANCH }), muteHttpExceptions: true }); const code = resp.getResponseCode; if (code !== 204 && code !== 200) { console.error(`GitHub workflow trigger failed (${code}): ${resp.getContentText()}`); } }

/* ===== Text Cleaning & Extraction ===== */

function joinStreamText_(a, b) { if (!a) return b || ''; if (!b) return a; if (/\s$/.test(a) || /^\s/.test(b)) return a + b; if (/^[,.;:!?)}\]'"*]/.test(b) || /[(\[{\"'*-]$/.test(a)) return a + b; return a + ' ' + b; }

function cleanTextArtifacts_(raw) { let text = String(raw || '').replace(/\r\n/g, '\n').replace(/\f/g, '\n'); if (((text.match(/^[ \t]*```/gm) || []).length % 2) === 1) text += '\n```';

  const code = []; text = text.replace(/```[\s\S]*?```|`[^`\n]+`/g, m => { const tok = `\u0000CD_${code.length}\u0000`; code.push(m); return tok; });

  const math = []; const stashMath = m => { const tok = `\u0000MT_${math.length}\u0000`; math.push(m); return tok; }; text = text .replace(/(?<!\\)\$\$[\s\S]+?(?<!\\)\$\$/g, stashMath) .replace(/(?<!\\)\$(?!\s)(?:\\\$|[^$\n])+?(?<!\s)(?<!\\)\$(?!\d)/g, stashMath);

  text = text .replace(/!?\[([^\]]*)\]\((?:https?:\/\/|mailto:)[^)\s]+\)/gi, '$1') .replace(/<(?:https?:\/\/|mailto:)[^>\s]+>/gi, '') .replace(/\b(?:https?:\/\/|mailto:)[^\s)\]>"]+/gi, '') .replace(/]*】/g, '') .replace(/\[(?:cite_start|cite_end|cite:[^\]]*|source|citation needed)\]/gi, '') .replace(/\[(?:\d+(?:\s*[-–,]\s*\d+)*)\]/g, '') .replace(/\(\s*\)/g, '') .replace(/\*\*([^\n*]+?)\*\*/g, (_, inner) => { const lead = (/^\s+/.exec(inner) || ['']), trail = (/\s+$/.exec(inner) || ['']), core = inner.trim; return core ? `${lead}**${core}**${trail}` : ''; }) .replace(/([.!?,:;])[ \t]+\*(?=[.,;:!?)]|$)/g, '$1*') .replace(/([A-Za-z0-9.!?,:;])[ \t]+\*(?=[.,;:!?)]|$)/g, '$1*') .replace(/^[ \t]*(?:[-=]{2,}[ \t]*)?Page[ \t]+\d+(?:[ \t]+of[ \t]+\d+)?(?:[ \t]*[-=]{2,})?[ \t]*$/gim, '') .replace(/([A-Za-z]{2,})-\n([A-Za-z]{2,})/g, '$1$2');

  const lines = text.split('\n'), out = []; let tbl = []; const isSep = l => l.includes('|') && /^\|?\s*:?[-–—]{1,}:?\s*(\|\s*:?[-–—]{1,}:?\s*)+\|?$/.test(l.trim); const isStruct = l => { const t = l.trim; return !t || /^#{1,6}\s/.test(t) || /^[-*+]\s/.test(t) || /^\d+[.)]\s/.test(t) || /^>\s?/.test(t) || /^(-{3,}|\*{3,}|_{3,})$/.test(t) || /^\u0000(?:CD|MT)_\d+\u0000$/.test(t); }; const flushTbl = => { if (!tbl.length) return; if (out.length && out[out.length - 1].trim !== '') out.push(''); const splitR = r => r.replace(/^\|/, '').replace(/(^|[^\\])\|$/, '$1').replace(/\\\|/g, '\u0000P\u0000') .split('|').map(c => c.replace(/\u0000P\u0000/g, '|').trim); const parsed = tbl.map(splitR); const cols = Math.max(...parsed.map(r => r.length)); tbl.forEach((rawRow, idx) => { const cells = parsed[idx].slice(0, cols); while (cells.length < cols) cells.push(''); if (isSep(rawRow)) { out.push('| ' + cells.map(c => (c.startsWith(':') && c.endsWith(':')) ? ':---:' : (c.startsWith(':') ? ':---' : (c.endsWith(':') ? '---:' : '---'))).join(' | ') + ' |'); } else { out.push('| ' + cells.map(c => c.replace(/\|/g, '\\|')).join(' | ') + ' |'); } }); out.push(''); tbl = []; };

  for (let i = 0; i < lines.length; i++) { const line = lines[i], t = line.trim; const isTbl = /^\|.*\|$/.test(t) || (t.includes('|') && (tbl.length > 0 || (i + 1 < lines.length && isSep(lines[i + 1])))); if (isTbl) { tbl.push(t); continue; } flushTbl; if (out.length && !isStruct(line) && !isStruct(out[out.length - 1]) && !/ $/.test(out[out.length - 1])) { out[out.length - 1] = out[out.length - 1].replace(/\s+$/, '') + ' ' + t; } else { out.push(line); } } flushTbl;

  return out.join('\n') .replace(/(\S) {2,}/g, '$1 ') .replace(/\u0000MT_(\d+)\u0000/g, (_, i) => math[Number(i)]) .replace(/\u0000CD_(\d+)\u0000/g, (_, i) => code[Number(i)]) .replace(/\n{3,}/g, '\n\n') .trim; }

function extractCleanChat_(data, file) { const title = file.getName.replace(/\.(json|prompt|txt)$/i, '') || 'Untitled prompt'; const model = data.runSettings?.model ? String(data.runSettings.model).replace(/^models\//, '') : 'unknown'; const updatedIso = file.getLastUpdated.toISOString; const rawSys = data.systemInstruction ? (typeof data.systemInstruction === 'string' ? data.systemInstruction : (data.systemInstruction.text || (data.systemInstruction.parts || []).map(p => p.text || '').join(''))) : ''; const systemInstruction = rawSys ? cleanTextArtifacts_(rawSys) : '';

  const rawTurns = []; const appendItem = (role, item, joiner) => { const lastTurn = rawTurns[rawTurns.length - 1]; if (lastTurn && lastTurn.role === role) { const lastItem = lastTurn.items[lastTurn.items.length - 1]; if (lastItem && lastItem.type === item.type && (item.type === 'text' || item.type === 'thought')) { lastItem.text = joiner(lastItem.text, item.text); return; } lastTurn.items.push(item); } else { rawTurns.push({ role, items: [item] }); } };

  const extractRawParts = (role, parts) => { for (const p of (parts || [])) { if (!p) continue; const th = Boolean(p.thought || p.isThought); if (th && !CONFIG.INCLUDE_THOUGHTS) continue; if (p.text) appendItem(role, { type: th ? 'thought' : 'text', text: String(p.text) }, (a, b) => a + b); else if (p.inlineData?.data && String(p.inlineData.mimeType || '').startsWith('image/')) { appendItem(role, { type: 'image_b64', mimeType: p.inlineData.mimeType, data: p.inlineData.data }, null); } else if (p.executableCode?.code) { appendItem(role, { type: 'text', text: `\n\`\`\`${(p.executableCode.language || 'python').toLowerCase()}\n${p.executableCode.code}\n\`\`\`\n` }, joinStreamText_); } else if (p.codeExecutionResult?.output) { appendItem(role, { type: 'text', text: `\n**Execution Output:**\n\`\`\`text\n${p.codeExecutionResult.output}\n\`\`\`\n` }, joinStreamText_); } } };

  if (Array.isArray(data.chunkedPrompt?.chunks)) { for (const c of data.chunkedPrompt.chunks) { const role = String(c.role || '').toLowerCase === 'user' ? 'User' : (String(c.role || '').toLowerCase === 'model' ? 'Model' : 'Other'); if (Array.isArray(c.parts)) extractRawParts(role, c.parts); else { const th = Boolean(c.isThought || c.thought); if ((!th || CONFIG.INCLUDE_THOUGHTS) && c.text) appendItem(role, { type: th ? 'thought' : 'text', text: String(c.text) }, joinStreamText_); if (c.inlineImage?.data) appendItem(role, { type: 'image_b64', mimeType: c.inlineImage.mimeType || 'image/png', data: c.inlineImage.data }, null); if (c.driveImage?.id) appendItem(role, { type: 'image_drive', fileId: c.driveImage.id }, null); } } } else if (Array.isArray(data.contents)) { for (const c of data.contents) { extractRawParts(String(c.role || '').toLowerCase === 'user' ? 'User' : 'Model', c.parts); } }

  const turns = []; for (const turn of rawTurns) { const cleanedItems = []; for (const item of turn.items) { if (item.type === 'text' || item.type === 'thought') { const clean = cleanTextArtifacts_(item.text); if (clean) cleanedItems.push({ type: item.type, text: clean }); } else cleanedItems.push(item); } if (cleanedItems.length) turns.push({ role: turn.role, items: cleanedItems }); } return { title, model, updatedIso, systemInstruction, turns }; }

function formatTurnsMd_(turns) { const lines = []; for (const turn of turns) { const body = turn.items.filter(i => i.type === 'text' || i.type === 'thought') .map(i => i.type === 'thought' ? `<details>\n<summary>Thinking Process</summary>\n\n${i.text}\n\n</details>` : i.text) .join('\n\n'); if (body.trim) lines.push(`## ${turn.role}`, '', body, '', '---', ''); } return lines; }

function renderCleanMd_(chat) { const lines = [`# ${chat.title}`, '']; if (CONFIG.INCLUDE_METADATA) { lines.push(`> **Model:** ${chat.model} | **Updated:** ${chat.updatedIso.replace('T', ' ').slice(0, 16)} UTC`, '', '---', ''); } if (chat.systemInstruction) lines.push('## System Instructions', '', chat.systemInstruction, '', '---', ''); lines.push(...formatTurnsMd_(chat.turns)); return lines.join('\n').trim + '\n'; }

function renderContinuationMd_(chat, turns, startIdx, endIdx, partNum) { const lines = []; if (partNum) { lines.push(`# ${chat.title} (Part ${partNum})`, ''); } const rangeLabel = `Turns ${startIdx + 1}–${endIdx}`; if (CONFIG.INCLUDE_METADATA) { lines.push(`> **Continuation (${rangeLabel})** | **Model:** ${chat.model} | **Updated:** ${chat.updatedIso.replace('T', ' ').slice(0, 16)} UTC`, '', '---', ''); } else { lines.push(`> **Continuation (${rangeLabel})**`, '', '---', ''); } lines.push(...formatTurnsMd_(turns)); return lines.join('\n').trim + '\n'; }

function getSourceFolders_ { const out = []; for (const n of CONFIG.SOURCE_FOLDER_NAMES) { const it = DriveApp.getFoldersByName(n); while (it.hasNext) { const f = it.next; if (!f.isTrashed) out.push(f); } } return out; } function getOrCreateFolder_(name) { const it = DriveApp.getFoldersByName(name); while (it.hasNext) { const f = it.next; if (!f.isTrashed) return f; } return DriveApp.createFolder(name); } function collectFiles_(folder, visited, out) { const id = folder.getId; if (visited.has(id)) return; visited.add(id); const fi = folder.getFiles; while (fi.hasNext) out.push(fi.next); const si = folder.getFolders; while (si.hasNext) { const s = si.next; if (!s.isTrashed) collectFiles_(s, visited, out); } } function cleanName_(raw) { return raw.replace(/\.(json|prompt|txt)$/i, '').replace(/[\\/:*?"<>|]/g, '_').trim || 'Untitled prompt'; } YAML: name: Build AI Studio PDFs

on: workflow_dispatch:

permissions: contents: write

concurrency: group: ai-studio-pdf-renderer cancel-in-progress: false

jobs: render: runs-on: ubuntu-latest timeout-minutes: 30 steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Install WeasyPrint dependencies and Emoji/Symbol fonts
        run: | sudo apt-get update -qq sudo apt-get install -y -qq libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0 libharfbuzz-subset0 fontconfig fonts-noto-color-emoji fonts-noto-core fonts-symbola fc-cache -f

      - name: Install Python packages
        run: python3 -m pip install --break-system-packages -q weasyprint markdown-it-py pygments beautifulsoup4 requests pypdf

      - name: Install MathJax for LaTeX equations
        run: npm install --no-save --prefix /tmp/mj mathjax-full@3

      - name: Render PDFs and send back to Google Drive
        env: GAS_WEBHOOK_URL: ${{ secrets.GAS_WEBHOOK_URL }} GAS_SECRET: ${{ secrets.GAS_SECRET }} GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }} GITHUB_REPO: ${{ github.repository }} run: python3 render.py

---

## Model

Look at `build-pdfs.yml` and your Apps Script—your incremental `append` + `prefixHash` logic is already super smart, so we don't need to rewrite it from scratch.

Right now you have **three specific compute leaks**:
1. **`build-pdfs.yml` setup penalty (~90–130s per run):** Re-downloading Noto fonts (`apt-get`), `weasyprint` (`pip`), and `mathjax-full` (`npm`) from scratch on *every* run—costing **2–3 billed minutes before `render.py` even starts**.
2. **Every-15-minute PDF triggers:** While you study a topic, every 15-minute save triggers a fresh GitHub VM boot (`~50 runs/day × 2–3 min` = **3,000+ min/month**, blowing past the 2,000-min cap).
3. **Full Drive folder scan every 15 minutes:** `collectFiles_` calls `getLastUpdated()` on every file in Drive (`1,500 files × 96 runs/day`), which will eventually hit Apps Script's **90 min/day** trigger limit.

Here is the clean fix—dropping GitHub compute from **~3,000+ min/mo → ~180–300 min/mo** and cutting Apps Script runtime to **~2 seconds per run**.

---

### Fix 1: Cache Dependencies in `build-pdfs.yml` (Private Repo)
Replace your **`.github/workflows/build-pdfs.yml`** with this version. It caches `/tmp/apt-cache` (`.deb` fonts), `~/.cache/pip`, and `/tmp/mj` (`mathjax-full`), cutting setup time by ~75%:

```yaml
name: Build AI Studio PDFs

on:
  workflow_dispatch:

permissions:
  contents: write

concurrency:
  group: ai-studio-pdf-renderer
  cancel-in-progress: false

jobs:
  render:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Cache apt packages, pip wheels, and MathJax
        uses: actions/cache@v4
        with:
          path: |
            /tmp/apt-cache
            ~/.cache/pip
            /tmp/mj/node_modules
          key: pdf-deps-${{ runner.os }}-v1

      - name: Install WeasyPrint dependencies and Emoji/Symbol fonts
        run: |
          sudo mkdir -p /tmp/apt-cache
          sudo apt-get update -qq
          sudo apt-get -o Dir::Cache::Archives=/tmp/apt-cache install -y -qq \
            libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0 libharfbuzz-subset0 \
            fontconfig fonts-noto-color-emoji fonts-noto-core fonts-symbola
          fc-cache -f

      - name: Install Python packages
        run: python3 -m pip install --break-system-packages -q weasyprint markdown-it-py pygments beautifulsoup4 requests pypdf

      - name: Install MathJax for LaTeX equations (only on cache miss)
        run: |
          if [ ! -d "/tmp/mj/node_modules/mathjax-full" ]; then
            npm install --no-save --prefix /tmp/mj mathjax-full@3
          fi

      - name: Render PDFs and send back to Google Drive
        env:
          GAS_WEBHOOK_URL: ${{ secrets.GAS_WEBHOOK_URL }}
          GAS_SECRET: ${{ secrets.GAS_SECRET }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_REPO: ${{ github.repository }}
        run: python3 render.py
```

---

### Fix 2: Batch + Idle-Debounce + Incremental Scan in Google Apps Script
Keep **`.md` syncing every 15 minutes** (0 GitHub minutes), while:
* Scanning **only files modified since the last run** (`modifiedDate > sinceIso`).
* Waiting **25 minutes of idle time** before rendering a PDF (stops re-rendering mid-study).
* Dispatching GitHub PDF builds in **4-hour batches** (max 6 runs/day, with a manual `flushPendingPdfsNow()` function if you ever want a PDF immediately).

#### A. Replace lines `1` through `194` (from `const CONFIG` down to the end of `syncCleanMarkdown`) with this:

```javascript
const CONFIG = {
  SOURCE_FOLDER_NAMES: ['Google AI Studio', 'AI Studio'],
  MD_FOLDER_NAME: 'AI Studio Markdown',
  PDF_FOLDER_NAME: 'AI Studio PDF',

  GITHUB_OWNER: 'inikashx-hub',
  GITHUB_REPO: 'AI-Studio-pdf-worker',
  GITHUB_BRANCH: 'main',

  INCLUDE_THOUGHTS: false,
  INCLUDE_METADATA: true,
  STATE_PREFIX: 'gh_sync_',
  SCAN_STATE_KEY: 'gh_last_scan_ms',
  DISPATCH_STATE_KEY: 'gh_last_pdf_dispatch_ms',

  PDF_IDLE_MINUTES: 25,       // Only build PDF after chat has been idle for 25 min
  PDF_BATCH_HOURS: 4,         // Trigger GitHub PDF batch at most every 4 hours (max 6x/day)
  MAX_SINGLE_PDF_BYTES: 15 * 1024 * 1024
};

function getSecrets_() {
  const props = PropertiesService.getScriptProperties();
  const token = (props.getProperty('GITHUB_TOKEN') || '').trim();
  const secret = (props.getProperty('CALLBACK_SECRET') || '').trim();
  if (!token || !secret) {
    throw new Error('Missing GITHUB_TOKEN or CALLBACK_SECRET in Project Settings -> Script Properties.');
  }
  return { token, secret };
}

function hashTurns_(turns) {
  const raw = JSON.stringify(turns);
  const digest = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, raw, Utilities.Charset.UTF_8);
  return digest.map(b => ('0' + ((b & 0xff).toString(16))).slice(-2)).join('');
}

function syncCleanMarkdown() {
  syncCleanMarkdown_(false);
}

// Run this manually from the Apps Script editor anytime you want PDFs built immediately
function flushPendingPdfsNow() {
  syncCleanMarkdown_(true);
}

function syncCleanMarkdown_(forceFlush) {
  const cache = CacheService.getScriptCache();
  if (cache.get('gh_sync_running')) return;
  cache.put('gh_sync_running', '1', 300);

  const startTime = Date.now();

  try {
    const { token } = getSecrets_();
    const mdFolder = getOrCreateFolder_(CONFIG.MD_FOLDER_NAME);
    const pdfFolder = getOrCreateFolder_(CONFIG.PDF_FOLDER_NAME);
    const visited = new Set([mdFolder.getId(), pdfFolder.getId()]);

    const props = PropertiesService.getScriptProperties();
    const lastScanMs = Number(props.getProperty(CONFIG.SCAN_STATE_KEY) || 0);
    // 5-minute overlap prevents missing files during Drive index lag
    const sinceIso = (!forceFlush && lastScanMs > 0)
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
    let mdCount = 0, queuedCount = 0, paused = false;

    // PHASE 1: Fast Markdown sync in Drive (uses 0 GitHub minutes)
    for (const file of files) {
      if (Date.now() - startTime > 150000) { paused = true; break; }
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

      if (prev.t === updatedMs && prev.m) continue;

      let data;
      try { data = JSON.parse(file.getBlob().getDataAsString('UTF-8')); } catch (e) { continue; }
      if (!data || (!data.chunkedPrompt && !data.contents && !data.runSettings)) continue;

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
            sourceId: id, updatedMs, baseName, pdfName, mode, existingPdfId,
            expectedTc, nextTc: fullTc, nextTh: fullTh, part, partStartTc,
            mdText: jobMdText, assets
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
      ? `Paused at time guard. MD: ${mdCount}, Queued for PDF: ${queuedCount}.`
      : `Done! MD updated: ${mdCount}, Queued for GitHub PDF batch: ${queuedCount}`);
  } finally {
    cache.remove('gh_sync_running');
  }
}
```

#### B. Update `requeueAllPastChats()` and `collectFiles_()` (Keep everything else untouched!):
Replace `requeueAllPastChats()` with:
```javascript
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
      delete st.t; delete st.pt; delete st.qt; delete st.qa;
      delete st.tc; delete st.th; delete st.part; delete st.partStartTc;
      props.setProperty(key, JSON.stringify(st));
      resetCount++;
    } catch (e) {}
  }
  console.log(`Reset ${resetCount} chat(s). Running flushPendingPdfsNow()...`);
  syncCleanMarkdown_(true);
}
```

And replace `collectFiles_` at the very bottom with:
```javascript
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
```

---

### Expected Compute After This Patch
* **Apps Script:** ~1–3 seconds per 15-minute check (~3–5 min/day vs. 90-min limit).
* **Private GitHub Actions:** Max ~6 batched PDF runs/day, ~1 min each with cache = **~180–250 min/month** (out of your 2,000-minute free quota).
* **One future note:** Apps Script `ScriptProperties` has a **500 KB** total storage limit—at ~230 bytes per chat state record, you're completely fine up to ~2,000 chats (later you can archive old `gh_sync_` entries or move them to a Google Sheet).

Once you test `flushPendingPdfsNow()` and see the cached `build-pdfs.yml` finish cleanly, we’re ready to tackle **storage & smart filtering into `ai-kb`**!

---

## User

Give me the complete updated javascript code; so that, I can paste and delete the old one

---

## Model

Here is the **complete, ready-to-paste Google Apps Script code**. You can select all, delete your old script, paste this in, and save—your existing 15-minute trigger (`syncCleanMarkdown`) and `ScriptProperties` secrets will continue working without needing any reconfiguration.

```javascript
/**
 * Syncs AI Studio chats -> Clean .md in Drive -> Batched & Idle-Debounced Private GitHub Actions -> Incremental PDFs via doPost()
 * Reads GITHUB_TOKEN and CALLBACK_SECRET safely from Project Settings -> Script Properties.
 */
const CONFIG = {
  SOURCE_FOLDER_NAMES: ['Google AI Studio', 'AI Studio'],
  MD_FOLDER_NAME: 'AI Studio Markdown',
  PDF_FOLDER_NAME: 'AI Studio PDF',

  GITHUB_OWNER: 'inikashx-hub',
  GITHUB_REPO: 'AI-Studio-pdf-worker',
  GITHUB_BRANCH: 'main',

  INCLUDE_THOUGHTS: false,
  INCLUDE_METADATA: true,
  STATE_PREFIX: 'gh_sync_',
  SCAN_STATE_KEY: 'gh_last_scan_ms',
  DISPATCH_STATE_KEY: 'gh_last_pdf_dispatch_ms',

  PDF_IDLE_MINUTES: 25,       // Only build PDF after chat has been idle for 25 min
  PDF_BATCH_HOURS: 4,         // Trigger GitHub PDF batch at most every 4 hours (max 6x/day)
  MAX_SINGLE_PDF_BYTES: 15 * 1024 * 1024
};

function getSecrets_() {
  const props = PropertiesService.getScriptProperties();
  const token = (props.getProperty('GITHUB_TOKEN') || '').trim();
  const secret = (props.getProperty('CALLBACK_SECRET') || '').trim();
  if (!token || !secret) {
    throw new Error('Missing GITHUB_TOKEN or CALLBACK_SECRET in Project Settings -> Script Properties.');
  }
  return { token, secret };
}

function hashTurns_(turns) {
  const raw = JSON.stringify(turns);
  const digest = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, raw, Utilities.Charset.UTF_8);
  return digest.map(b => ('0' + ((b & 0xff).toString(16))).slice(-2)).join('');
}

function syncCleanMarkdown() {
  syncCleanMarkdown_(false);
}

// Run this manually from the Apps Script editor anytime you want pending PDFs built immediately
function flushPendingPdfsNow() {
  syncCleanMarkdown_(true);
}

function syncCleanMarkdown_(forceFlush) {
  const cache = CacheService.getScriptCache();
  if (cache.get('gh_sync_running')) return;
  cache.put('gh_sync_running', '1', 300);

  const startTime = Date.now();

  try {
    const { token } = getSecrets_();
    const mdFolder = getOrCreateFolder_(CONFIG.MD_FOLDER_NAME);
    const pdfFolder = getOrCreateFolder_(CONFIG.PDF_FOLDER_NAME);
    const visited = new Set([mdFolder.getId(), pdfFolder.getId()]);

    const props = PropertiesService.getScriptProperties();
    const lastScanMs = Number(props.getProperty(CONFIG.SCAN_STATE_KEY) || 0);
    // 5-minute overlap prevents missing files during Drive index lag
    const sinceIso = (!forceFlush && lastScanMs > 0)
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
    let mdCount = 0, queuedCount = 0, paused = false;

    // PHASE 1: Fast Markdown sync in Drive (uses 0 GitHub minutes)
    for (const file of files) {
      if (Date.now() - startTime > 150000) { paused = true; break; }
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

      if (prev.t === updatedMs && prev.m) continue;

      let data;
      try { data = JSON.parse(file.getBlob().getDataAsString('UTF-8')); } catch (e) { continue; }
      if (!data || (!data.chunkedPrompt && !data.contents && !data.runSettings)) continue;

      const chat = extractCleanChat_(data, file);
      const baseName = cleanName_(file.getName());
      const mdName = `${baseName}.md`;
      const fullMdText = renderCleanMd_(chat);
