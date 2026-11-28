# Subject Pack: miscellaneous (Part 11/14)


---
## FILE: `chats/Optimizing Two-Step LLM Routing.md` [Part 11/14]

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

      const targetKbPath = resolveKbTarget_(file, cleanName_(file.getName()));
      const needsMd = prev.t !== updatedMs || !prev.m;
      const needsKbPathSync = (targetKbPath || '') !== (prev.kbP || '');
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

    // PHASE 3: Batched Selective Sync to Public ai-kb Repo (1 single commit for all changed [kb]/[core] files)
    const lastKbMs = Number(props.getProperty(CONFIG.KB_DISPATCH_STATE_KEY) || 0);
    const canDispatchKb = forceKbFlush || (Date.now() - lastKbMs >= CONFIG.KB_BATCH_HOURS * 60 * 60 * 1000);
    const kbIdleMs = CONFIG.KB_IDLE_MINUTES * 60 * 1000;

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
        if (!targetPath && !oldPath) continue;
        if (targetPath && prev.kbT === prev.t && oldPath === targetPath) continue;
        if (!forceKbFlush && (Date.now() - prev.t < kbIdleMs)) continue;

        const id = key.slice(CONFIG.STATE_PREFIX.length);
        let srcFile;
        try { srcFile = DriveApp.getFileById(id); } catch (e) { continue; }

        // If source file was trashed or [kb] tag removed, delete old file from ai-kb
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
      ? `Paused at time guard. MD: ${mdCount}, PDF queued: ${queuedPdfCount}, KB synced: ${kbSyncedCount}.`
      : `Done! MD: ${mdCount}, PDF batch queued: ${queuedPdfCount}, ai-kb synced: ${kbSyncedCount}`);
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

function resolveKbTarget_(file, baseName) {
  const rawName = file.getName();
  const isCoreTag = CONFIG.KB_CORE_TAG_REGEX.test(rawName);
  const isKbTag = CONFIG.KB_TAG_REGEX.test(rawName);

  const chain = [];
  let cur = file;
  for (let depth = 0; depth < 6; depth++) {
    const parents = cur.getParents();
    if (!parents.hasNext()) break;
    const parent = parents.next();
    const pName = parent.getName();
    if (CONFIG.SOURCE_FOLDER_NAMES.some(n => n.toLowerCase() === pName.toLowerCase())) break;
    chain.unshift(pName);
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
      // Only delete if path actually exists on remote branch
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
