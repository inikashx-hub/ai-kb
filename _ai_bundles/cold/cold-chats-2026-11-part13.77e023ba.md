# Cold Knowledge Bundle: chats-2026-11-part13


---
## FILE: `chats/Optimizing Two-Step LLM Routing.md` [Part 15/17 — 4. Enforce Strict Router & Grounding Rules]

## [Chapter Context: 4. Enforce Strict Router & Grounding Rules]

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

---

### Quick Test to Verify End-to-End
1. Make sure your `GITHUB_TOKEN` (or a new `AI_KB_TOKEN` in Script Properties) has **Contents: Read & write** on `inikashx-hub/ai-kb`.
2. Add **`[kb]`** to the name of one chat JSON in Drive (or move one chat into `Google AI Studio/KB/Maths/`).
3. In Apps Script, select **`flushKbSyncNow`** and tap **Run**.
4. Within ~20 seconds, you’ll see that file land cleanly in `inikashx-hub/ai-kb`, trigger `build-kb.yml`, and automatically generate its 1-turn Subject Pack in `_ai_bundles/packs-list.txt` and Cold Bundle in `_ai_bundles/llms.txt`!

---

## User

I don't know how to edit the token

---

## Model

First, check which kind of token you already have—you might not even need to edit it!

### Step 1: Check Your Token Prefix in Apps Script
1. In Google Apps Script, tap **Project Settings (⚙️ gear icon)** on the left.
2. Scroll down to **Script Properties** and look at `GITHUB_TOKEN`:
   * If it starts with **`ghp_`** *(Classic token)* → **You don’t need to change anything!** It already works on both repos.
   * If it starts with **`github_pat_`** *(Fine-grained token)* → Follow Step 2 below.

---

### Step 2: Grant Access to `ai-kb` on GitHub
Open **`https://github.com/settings/personal-access-tokens`** in your phone browser *(or tap your **Profile picture → Settings → scroll down to Developer settings → Personal access tokens → Fine-grained tokens**)*.

From there, pick whichever is easier:

#### Easiest Way: Edit Your Existing Token *(No Apps Script Changes Needed)*
1. Tap the **name** of your existing token.
2. Scroll to **Repository access** → choose **Only select repositories**.
3. Make sure **BOTH `AI-Studio-pdf-worker` AND `ai-kb`** are checked! *(Double-check that `AI-Studio-pdf-worker` stays selected so your PDF builder doesn't lose access.)*
4. Under **Repository permissions**, confirm **Contents** is set to **Read and write** (keep **Actions** / **Workflows** as-is for your PDF worker).
5. Tap **Save** / **Update permissions** at the bottom. Done—your token string stays the same!

#### Alternative Way: Add a Separate `AI_KB_TOKEN` *(Zero Risk to PDF Worker)*
1. On the **Fine-grained tokens** page, tap **Generate new token**.
2. **Token name:** `ai-kb-sync` (pick any **Expiration** you prefer).
3. **Repository access:** **Only select repositories** → select **`ai-kb`**.
4. **Repository permissions → Contents:** **Read and write**.
5. Tap **Generate token** and copy the `github_pat_...` string.
6. Back in Apps Script → **Project Settings (⚙️) → Script Properties → Add script property**:
   * **Property:** `AI_KB_TOKEN`
   * **Value:** *(paste your new token)*
   * Tap **Save script properties**.

Once done, tag one chat in Drive with `[kb]` (or run **`flushKbSyncNow`** in Apps Script) to test the sync!

---

## Model

Your script pasted cleanly and ran with **zero errors**!

`MD: 0, PDF batch queued: 0, ai-kb synced: 0` just means your existing Drive files were already synced to Markdown, and **none of the source chats are marked for `ai-kb` yet**.

---

### How to Run Your First `ai-kb` Sync Test
1. **Go to your source AI Studio folder in Google Drive** (`Google AI Studio` or `AI Studio` — *not* `AI Studio Markdown`).
2. Pick one study chat (for example, inside `Maths/`) and either:
   * **Rename it** to include **`[kb]`** (e.g., `Percentages [kb]`), **OR**
   * Move it into a subfolder named **`KB`** inside `Google AI Studio` (e.g., `Google AI Studio/KB/Maths/`).
   *(Remember: `[core]` sends it to `core/` for Tier 1 instead.)*
3. Come back to Apps Script and tap **Run** on **`flushKbSyncNow`**.

---

### What to Look For in the Execution Log
* **Success:** You'll see `ai-kb synced: 1` (and the chat will appear inside `inikashx-hub/ai-kb/chats/...` within seconds).
* **If it logs a `403` or `404` error:** That just means the token needs `Contents: Read & write` access to `ai-kb`—share the exact log message if that happens and we'll sort it right away!

---

## User

I renamed it in drive. But, app script still shows 0 processed

---

## Model

Look at your Drive screenshot—that explains it immediately!

Look at **`Google AI Studio/KB/English` (Modified 8:02 pm)** in `My Drive`:
1. Unlike GitHub, **Google Drive does not create nested folders when you type `/`**—so it created one flat folder at the root of `My Drive` literally named `"Google AI Studio/KB/English"`.
2. Because that folder sits at `My Drive` root (outside `Google AI Studio`) and its literal name isn't `"KB"`, Apps Script skipped it. *(Also remember: always put `[kb]` or `KB/` on your **source AI Studio chat files**, not the `.md` copies inside `AI Studio Markdown`.)*

---

### Quick 2-Step Fix

#### 1. (Optional Tidy-Up in Drive)
You can either keep that folder as-is (the updated script below now handles `/` in Drive folder names too!), **or** organize cleanly as:
* `My Drive` → create folder **`KB`** → create **`English`**, **`Maths`**, etc. inside **`KB`** → move source chats in.
* **Or** leave chats inside `General Awareness` / `Google AI Studio` and just add **`[kb]`** to the chat filename.

#### 2. Update Apps Script (Now Scans `My Drive/KB`, Handles `/`, & Logs Counts)
Paste this updated complete code (adds `KB` root scanning, strips `My Drive` from paths, handles slash-named folders like `Google AI Studio/KB/English`, and prints `Scanned` + `KB tracked` counts in the log):

```javascript
/**
 * Syncs AI Studio chats -> Clean .md in Drive -> Batched Private PDFs + Selective Batched Public KB Sync (Choice A)
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
        if (!prev.t) continue;

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
