# Subject Pack: ch04-enforce-strict-router-grounding (Part 8/14)


---
## FILE: `chats/Optimizing Two-Step LLM Routing.md` [Part 11/17 — 4. Enforce Strict Router & Grounding Rules]

## [Chapter Context: 4. Enforce Strict Router & Grounding Rules]

recent_candidates.sort(key=lambda x: x, reverse=True) selected_recent, recent_bytes = [], 0 for _, blk, b_size in recent_candidates: if selected_recent and (recent_bytes + b_size > MAX_RECENT_TOTAL_BYTES): break selected_recent.append(blk) recent_bytes += b_size

    recent_text = ( f"# Tier 1: Recent Compact Chats (Last {RECENT_DAYS} Days)\n" + "".join(selected_recent) if selected_recent else f"# Tier 1: Recent Changes\nNo compact chats updated in the last {RECENT_DAYS} days." ) (OUT_DIR / "hot-recent.md").write_text(recent_text, encoding="utf-8")

    # Apply optional user-defined packs.json (wildcard rules over auto-packs & core)
    all_pack_sources = dict(auto_packs) if hot_core_items: all_pack_sources["core"] = hot_core_items

    custom_packs: dict[str, list[dict]] = {} if PACKS_CONFIG.exists: cfg = json.loads(PACKS_CONFIG.read_text(encoding="utf-8")) for custom_name, patterns in cfg.items: matched_items = [] for src_name, src_items in sorted(all_pack_sources.items): if any(fnmatch(src_name, pat) for pat in patterns): matched_items.extend(src_items) if matched_items: custom_packs[f"custom-{sanitize_slug(custom_name)}"] = matched_items

    combined_packs = {**auto_packs,** custom_packs} pack_urls = write_static_packs(combined_packs)

    pack_lines = [ "# 1-Turn Dynamic Packs (Auto-generated from folders, chapters, and optional packs.json)", "# Mix and match any URLs below in Turn 1, or define your own combos in packs.json.", "", ] for pname, urls in pack_urls.items: pack_lines.append(f"## PACK: {pname} ({len(urls)} URLs)") for u in urls: pack_lines.append(u) pack_lines.append("Read every URL above via URL context and answer my question with exact FILE citations.") pack_lines.append("") (OUT_DIR / "packs-list.txt").write_text("\n".join(pack_lines), encoding="utf-8")

    index_entries = [] for group_name, items in sorted(cold_groups.items): index_entries.extend(write_cold_chunks(group_name, items))

    lines = [ "# Knowledge Base Index (Tier 2 Cold Bundles)", "# Use static pack URLs from packs-list.txt for 1-turn, or llms.txt for 2-turn discovery.", "", ] for entry in index_entries: lines.append(f"- URL: {entry['url']}") lines.append(f" Topic Group: {entry['group']}") lines.append(f" Files/Parts: {' | '.join(entry['titles'])}") if entry["prompts"]: lines.append(f" User Questions: {' | '.join(entry['prompts'])}") if entry["sections"]: lines.append(f" Topics/Chapters: {' | '.join(entry['sections'])}") if entry["preview"]: lines.append(f" Preview: {entry['preview']}") lines.append("")

    (OUT_DIR / "llms.txt").write_text("\n".join(lines), encoding="utf-8") print(f"Built {len(pack_urls)} pack(s) and {len(index_entries)} cold bundle(s).")

if __name__ == "__main__": main ```

*(Also add `"packs.json"` under `paths:` in `.github/workflows/build-kb.yml` if you later create a `packs.json` so editing `packs.json` auto-triggers a rebuild!)*

---

### Step 2: How You Control Packs Yourself (`packs.json` — Optional)
Without `packs.json`, `_ai_bundles/packs-list.txt` automatically gives you separate static URLs for every folder and every chapter (`ch01-...`, `ch04-...`, `ch13-...`, `study-chats`).

Whenever *you* want to merge any topics into your own custom 1-turn pack, just create **`packs.json`** at the root of `ai-kb`:
```json { "my-schemes-and-budget": ["ch03-*", "ch04-*"], "daily-revision": ["core", "study-chats", "ch13-*"] } ```
It builds `custom-my-schemes-and-budget-p1..pN.md` and `custom-daily-revision-p1..pN.md` automatically, completely under your control.

---

### Step 3: Universal System Instructions (Handles Both 1-Turn & 2-Turn)
Use this single System Instruction in Google AI Studio:

```markdown You are a strict, retrieval-grounded assistant for my knowledge base.

### Rules
1. Read EVERY URL provided in the user prompt via URL context before answering.
2. If the provided URLs are Subject/Chapter/Chat packs (not `llms.txt` alone), answer the user's question immediately in the same turn using ONLY facts found in those files, citing exact `FILE:` paths.
3. If `llms.txt` is provided and the answer is not in the other loaded files, DO NOT guess—output a single `text` code block with the 1 to 8 most relevant Cold Bundle URLs from `llms.txt` plus:
   `Read every URL above via URL context and answer my previous question with exact FILE citations.`
4. Never fabricate or extrapolate beyond retrieved content.
```

Now **you** decide on every query: paste 1 chapter pack, mix 3 chapters together, define custom combos in `packs.json`, or drop `llms.txt` when you want Gemini to discover across the whole repo!

---

## User

How to create custom packs.json?

---

## Model

Here is the step-by-step guide to creating and using **`packs.json`** in your `inikashx-hub/ai-kb` repository.

---

### Step 1: Check Your Exact Auto-Pack Names First
1. Open **`_ai_bundles/packs-list.txt`** → tap **Raw** in your repo.
2. Look at the `## PACK: ...` names (for example: `ch01-rbi-monetary-policy`, `ch03-indian-economy-union-budget`, `ch04-government-schemes-initiatives`, `ch13-important-days-themes`, `study-chats`, etc.).

You can match those exact names **or** use `*` wildcards (like `"ch04-*"`).

---

### Step 2: Create `packs.json` at the Repo Root
1. Go to the **main root page** of `ai-kb` (same level as `README.md` and `build-kb.py`).
2. Tap **Add file** → **Create new file**.
3. Name the file **`packs.json`**.
4. Paste your custom groups using valid JSON (here is a starter example you can customize):

```json
{
  "economy-and-schemes": [
    "ch01-*",
    "ch03-*",
    "ch04-*"
  ],
  "static-quick": [
    "ch11-*",
    "ch12-*",
    "ch13-*"
  ],
  "math-and-core": [
    "core",
    "study-chats"
  ]
}
```

#### Rules to Remember Inside `packs.json`:
* **Strict JSON syntax:** Use double quotes `"..."`, put commas between items, and **no trailing comma** after the last item or last bracket (and no `#` or `//` comments).
* **Wildcards supported:**
  * `"ch04-*"` → matches Chapter 4 automatically
  * `"study-chats"` → matches standalone chats
  * `"core"` → matches files inside `core/` (if you add any)
* **Stay under 20 URLs per pack:** Keep each custom pack focused (around 2–5 chapters/folders, so it stays around ~3–12 URLs of 35 KB each—well within AI Studio’s 20-URL limit).

5. Tap **Commit changes...**.

---

### Step 3: Make `packs.json` Auto-Rebuild on Edit
Right now, `.github/workflows/build-kb.yml` only triggers when `chats/**`, `core/**`, or `build-kb.py` changes. Add `"packs.json"` so editing `packs.json` triggers a rebuild automatically:

1. Open **`.github/workflows/build-kb.yml`** → tap the **pencil icon (✏️)**.
2. Add `- "packs.json"` under `paths:`:
```yaml
    paths:
      - "chats/**"
      - "core/**"
      - "build-kb.py"
      - "packs.json"
```
3. Tap **Commit changes...**.

---

### Step 4: Grab Your Custom Pack URLs
1. Wait ~15 seconds for the GitHub Action to turn green ✅ (under **More ▾ → Actions**).
2. Open **`_ai_bundles/packs-list.txt`** → **Raw**.
3. Scroll down to see your new **`## PACK: custom-economy-and-schemes`**, **`custom-static-quick`**, and **`custom-math-and-core`** URL blocks—copy whichever ones you use most and pin them in Gboard Clipboard for instant 1-turn chats!

---

## User

My knowledge base is going to include many files in the future. How can I work about it?

---

## Model

GitHub itself won’t be your bottleneck—even **3,000 Markdown chats** only take ~40–50 MB of text.

The **only two real scaling ceilings** are inside Google AI Studio Playground:
1. **The 20-URL per-request cap** (a single 1-turn pack becomes unusable once it grows past ~10–15 URLs).
2. **The ~35–40 KB browse snippet limit** (if `llms.txt` itself grows past ~35 KB, Playground will truncate the bottom of your index!).

Here is the exact playbook to scale this architecture cleanly to **hundreds or thousands of files**:

---

### 1. Keep Every Folder / Pack Under ~250 KB (~7 URLs Max)
Right now, standalone files without a subfolder go into `study-chats`. Once you have 50–100 chats, `study-chats` would blow past 20 URLs and break 1-turn mode.
* **The Fix:** Never dump everything flat into `chats/`. Always group into focused subfolders—and split big folders by sub-topic or year if one gets too large:
  ```text
  chats/
  ├── quant/
  ├── reasoning/
  ├── english/
  ├── ga-compendium/
  ├── coding/
  └── archive-2025/
  ```
* Because `build-kb.py` automatically turns every subfolder into its own pack, each pack stays compact (**2–7 URLs**), fast, and 100% 1-turn compatible.

---

### 2. Protect `llms.txt` from Crossing 35 KB (Use a "2-Level Index" Later)
Right now your `llms.txt` (with 23 Cold parts) is around **~12 KB**—plenty of headroom.
* Up to about **60–80 Cold Bundles (~2.5 MB of text)**, one single `llms.txt` works cleanly as long as you keep entries concise (skip long `Preview:` lines once you have many bundles).
* **Once `llms.txt` nears ~30 KB (100+ bundles):** Switch `build-kb.py` to a **2-Level Index**:
  * **`llms.txt`** (<10 KB) becomes a tiny **Master Directory** listing only folder/topic indexes (`llms-quant.txt`, `llms-ga.txt`, `llms-coding.txt`).
  * Each **`llms-<topic>.txt`** (<35 KB) lists the Cold Bundles for that topic.
  * When you know the subject (e.g., Quant), paste **`llms-quant.txt`** + your question for **2-turn** lookup across hundreds of Quant files.

---

### 3. Automate Sorting in Your 15-Minute Sync Pipeline
You shouldn't sort hundreds of chats into folders manually on your phone.
* In your **private repo’s 15-minute sync script**, add simple **title/keyword rules** (or read a tag like `#quant` / `#coding` / `#ga` in your prompt) to automatically save synced `.md` files into the right subfolder (`chats/quant/`, `chats/ga/`, etc.) inside `ai-kb`.
* Anything without a matched keyword can fall back to `chats/misc-YYYY-MM/` so no single folder ever balloons uncontrollably.

---

### 4. Keep Tier 1 (`core/` and `hot-recent.md`) Strictly Lean
* **`core/` (`hot-core.md`):** Treat this like RAM—keep **only** master cheat sheets, formula lists, and key rules here (**stay under ~30–35 KB total** so it never gets truncated).
* **`hot-recent.md`:** Our script already caps this at 40 KB (last 14 days, compact files only). Older chats automatically roll out into `cold/` and their topic packs, so Tier 1 stays fast forever.

---

### 5. Use the 80/20 Daily Workflow + NotebookLM for Static Archives
As your library grows large:
* **Daily Active Topics (1-Turn):** Keep only your **3–5 most-used Subject Packs** (or custom `packs.json` bundles) pinned in Gboard Clipboard.
* **Long-Tail / Older Files (2-Turn):** Use `llms.txt` (or `llms-<topic>.txt`) so you don't have to manage 30 clipboard pins.
* **Massive Static Books / Archives (Bonus Trick):** If you ever accumulate **dozens of huge static PDFs/compendiums** (10+ MB), **NotebookLM (Gemini Notebook)** lets you upload **50 sources per notebook** (up to 500,000 words each) on the free tier—so you can bundle 30–50 static `.md` files per consolidated `.md` and keep giant static archives there, while keeping your **live, 15-minute-updated AI Studio chats** in this GitHub hybrid.

---

Whenever you're ready to **wire up your private repo's 15-minute Apps Script pipeline** with automatic keyword-to-folder routing (or add the 2-level `llms-<topic>.txt` index), just let me know!

---

## User

Before automate the pipeline, I just want to know any compute or storage obstacles for the free tier since I make atleast 50 chats(10000 tokens each) per day

---

## Model

Good thing you checked first—at **50 chats/day × 10,000 tokens**, your pipeline produces roughly:
* **~500,000 tokens/day** ≈ **~2.25 MB/day** of `.md` text (plus **10–25 MB/day** if you also keep `.pdf`s)
* **~1,500 files/month** ≈ **~67.5 MB/month** of `.md` text
* **~18,250 files/year** ≈ **~820 MB/year** of `.md` text

At that velocity, **three free-tier ceilings and one RAG limit will break** unless you adjust how the pipeline batches and stores data:

---

### 1. Private Repo Compute: GitHub Actions 2,000-Minute Cap *(Will Hit Mid-Month!)*
* **Public `ai-kb` repo:** Standard Linux runners are **free with no minute limit**, so `build-kb.py` in `ai-kb` costs you zero quota.
* **Private converter repo:** GitHub Free gives private repos **$12/month of compute (~2,000 Linux minutes/month)**, and **every job rounds up to the nearest full minute**.
  * **The Trap:** Running 50 separate jobs/day = `50 × 1 min × 30 = 1,500 min/month` (and if PDF generation makes jobs take 65 seconds, GitHub bills **2 minutes/job = 3,000 min/month**, locking your private repo mid-month!).
  * **The Fix:** **Batch instead of running 1 job per chat.** Have Apps Script queue new chats and trigger the private Action **once every 3–4 hours** (6–8 batch runs/day instead of 50+ runs/day). That drops usage to ~200–400 min/month.

---

### 2. `ai-kb` Storage & Git History Bloat *(Silent Repo Killer!)*
* **GitHub Limits:** GitHub recommends keeping total repo size **under 1 GB** (and strongly under 5 GB).
* **The Trap:** Every time `build-kb.py` commits new hashed `cold/*.md` and `packs/*.md` bundles, **Git keeps every old version forever inside `.git` history**. If you rebuild and commit 5–20 MB of bundles **50 times a day**, `.git` history can balloon by **several GB per month**, making clones slow and risking GitHub size warnings.
* **The Fix:**
  1. **Batch pushes to `ai-kb` (2–4×/day)**—or set `build-kb.yml` to run on a **`cron` schedule every 6 hours** instead of on every file push.
  2. **Never push `.pdf` files to GitHub** (keep only `.md`).
  3. **Start a fresh archive repo (or squash old history)** every 6–12 months.

---

### 3. Google Apps Script Quotas *(90 Min/Day Trigger Limit)*
* **Consumer Gmail Limits:** **90 minutes/day** total trigger runtime (6 minutes max per run), **20,000 `UrlFetch` calls/day**, and **2,000 file conversions/day**.
* **The Trap:** A 15-minute trigger runs **96 times/day**, leaving an average of **56 seconds per run** before hitting the 90-minute daily cap. Once your Drive folder holds 1,000+ files, scanning the whole folder every 15 minutes will blow past 56 seconds and fail.
* **The Fix:** Store already-processed chat IDs in **`PropertiesService`** (or move processed chats into monthly subfolders) so each 15-minute check finishes in **2–4 seconds**. *(Also watch your 15 GB Google account storage if generating 50 PDFs/day—that’s ~4–9 GB/year in PDFs alone.)*

---

### 4. The Biggest Obstacle: Your **AI Studio URL Context Index** Breaks at 50 Chats/Day!
Look at the math inside AI Studio Playground:
* One 10,000-token chat (**~45 KB**) is already larger than `MAX_PART_BYTES = 35 KB`—meaning **50 chats/day = ~65 new Cold parts per DAY (~2,000 parts/month)**.
* **`hot-recent.md`** (40 KB cap) won't fit even **one** full raw 10k-token chat.
* **`llms.txt`** overflows its **~35–40 KB browse truncation ceiling in just 2 days**, and static packs would multiply into hundreds of packs.

---

### How to Design Around This Before Automating
Pick whichever matches how you actually use those 50 daily chats:

#### Path 1: **Distill or Filter Before Pushing to `ai-kb`** *(Best to Keep GitHub + AI Studio Hybrid Working)*
Most 10,000-token chats are ~80% pasted prompts, trial-and-error, and verbose chatter, with ~20% reusable takeaways.
* **Auto-summarize/filter:** Have your pipeline either push **only** chats tagged for your KB (e.g., 5–10/day) **or** distill each 10k-token chat into a **crisp 2–5 KB `.md` takeaway/cheat sheet** before pushing to `ai-kb` (while keeping the full 10k-token raw archive privately in Google Drive).
* **Result:** ~3–6 MB/month instead of 67.5 MB/month—your `hot-recent.md`, topic packs, and `llms.txt` stay fast, clean, and workable for months.

#### Path 2: **Keep All 50 Raw 10k-Token Chats/Day Searchable** *(Graduate from URL Context)*
If you truly want **every raw 10,000-token chat** searchable without summarizing:
* **Free Batching into NotebookLM (Gemini Notebook):** Have your pipeline merge each day’s 50 chats (~375,000 words, which fits under NotebookLM's **500,000 words/source** limit) into **1 daily `.md` file** in Google Drive, and load **50 days (~2,500 full raw chats)** per free notebook.
* **True Vector RAG:** At 1,500+ raw long docs/month, a vector store (like the **Gemini API File Search tool**, or a local vector DB) handles unlimited document counts natively without needing manual packs or `llms.txt`.

---

## User

Let's resolve compute issue first.

---

## Model

To stay safely under GitHub’s **2,000 minutes/month** private-repo limit (and Apps Script’s **90 min/day** trigger limit) at **50 chats/day**, you need to eliminate **per-chat job overhead** and **mid-chat re-runs**.

Here is the exact **4-step compute optimization plan**—followed by how we can patch your specific setup:

---

### The Compute Math: Why You Burn Minutes Today
GitHub Actions **rounds every job UP to the nearest full minute** on private repos:
* **1 job per chat (50×/day):** `50 runs × 1–2 min × 30 days` = **1,500 to 3,000+ min/month** *(even if actual conversion only takes 5 seconds, booting the VM + installing tools bills 1–2 full minutes every time!)*.
* **6 batched jobs/day (every 4 hours):** `6 runs × 1–2 min × 30 days` = **180 to 360 min/month** *(80%+ of your free quota left untouched!)*.

---

### The 4 Fixes to Cut Compute by ~85%

#### 1. Batch Queueing (50 Triggers/Day → 4–6 Runs/Day)
Instead of firing a GitHub Action every time a single chat updates:
* Let Apps Script check Drive every 15 minutes (just logging changed file IDs into a queue in `PropertiesService`—takes <2 seconds).
* Trigger your private GitHub Action **only once every 3–4 hours** (and **skip firing** if the queue is empty), passing **all queued chats in one batch** so GitHub boots **one VM** and loops through ~8–12 chats in one pass.

#### 2. Add a 20-Minute "Idle Debounce" (Stops Mid-Chat Waste)
If you talk in one AI Studio chat for 45 minutes, a 15-minute trigger converts the *same* chat 3 times while you're still typing.
* **The Fix:** In Apps Script, only queue a chat for conversion once its `lastUpdated` timestamp is **at least 20–30 minutes old** (meaning you finished the conversation). That alone cuts wasted conversions by **30–50%**.

#### 3. Separate Fast `.md` vs. Heavy `.pdf` (or Cache PDF Tools)
Converting `.md` takes **<1 second** in Python/Node. What makes jobs cross the 60-second line (`1 min → 2 min` billing!) is installing or running PDF renderers (`pandoc`/`texlive`/`playwright`/`weasyprint`) on every boot.
* **Cache dependencies with `actions/cache`** (or use a pre-built image on `ghcr.io`) so your GitHub Action doesn't re-download packages on every run—dropping boot+setup from ~60s down to ~10s.
* **Even faster:** Only generate `.pdf` once daily (or only on idle/finalized chats), while `.md` updates in batches every 4 hours.

#### 4. Incremental Scan in Apps Script (Protect the 90-Min/Day Quota)
Instead of scanning every file in your Google Drive folder every 15 minutes (which gets slower once you have 1,000+ chats):
* Query Drive with **`modifiedDate > lastSyncTime`** (or track processed timestamps in **`PropertiesService`**), so each 15-minute check finishes in **1–3 seconds** instead of timing out.

---

### Let's Patch Your Exact Pipeline Next
To write the exact batching + debounce patch for your private repo and Apps Script:
1. **How does your Apps Script send jobs to your private repo right now?** (`workflow_dispatch`, `repository_dispatch`, or pushing raw files via GitHub API?)
2. **What does your private repo’s workflow use to convert `.md` and `.pdf`?** *(If you paste your private `.yml` workflow and Apps Script—making sure to **remove any PAT/tokens first**—I'll rewrite both with batching, debounce, and dependency caching!)*

---

## User

The reason for creating Google AI Studio - Google drive- Google apps script- GitHub pipeline through private repository earlier is as follows: I want to study maths, reasoning, general awareness and English for banking examinations through long chat sessions per topic. For example; If I study percentages topic in maths subject, I dedicate a chat session that will be saved as JSON in Google drive and move it to maths folder. I faced two hurdles. First, I can't open JSON files in drive to study without friction; so, I create a pipeline to convert the chat sessions into .md files for lightweight processing for the LLMs and .pdf files for me. Second, once a chat session grows big(300-400k tokens), drive takes too long to save the already saved session for just one new chat and google has also put limitations on September 29 that affect long chat sessions disproportionately especially for the free tier. So, I needed to optimise the context window as much as possible with the help of some external source

---

## Model

That explains everything—especially why you want **short, fast AI Studio sessions** instead of dragging a 300–400k token JSON around (which both slows down Google Drive saves and burns through AI Studio's free-tier limits much faster).

Breaking each topic (like *Percentages*) into **short 10k–30k token mini-sessions** (`Percentages - Part 1`, `Part 2`, etc.) actually solves **both** problems at once:
1. Drive saves become instant again (tiny JSONs instead of multi-MB ones), and your AI Studio quota goes much further.
2. Your private converter doesn't have to keep re-rendering a giant 150-page PDF every time you send one new prompt!

---

### How to Cut Your Private Repo Compute by ~85–90%

Right now, your biggest compute leak is **spinning up a full GitHub Action VM + PDF engine for individual/active chats every 15 minutes**. Here is the exact architecture fix:

#### 1. Separate Fast `.md` Conversion from Heavy `.pdf` Rendering
* **`.md` conversion (`JSON → .md`)** is pure text parsing—converting 25 AI Studio JSONs in one Python batch takes **< 2 seconds** (or can even run directly inside Google Apps Script using `JSON.parse()` for **0 GitHub minutes**!).
* **`.pdf` conversion** (especially if you render math/LaTeX formulas) is the heavy step that pushes jobs past the 60-second line (`1 min → 2 min` billing).
* **The Fix:** You don't need a rebuilt `.pdf` every 15 minutes while you are actively studying. Run **`.pdf` rendering in 1–2 batches per day** (or only every 4–6 hours on **finished/idle** chats), while `.md` can update much more often at virtually zero cost.

#### 2. Add a 20–30 Minute "Idle Debounce" + Batch Queue
* Let Apps Script run on its 15-minute check using **`modifiedDate > lastSyncTime`** (takes ~1–2 seconds, protecting your 90 min/day Apps Script quota).
* **Debounce rule:** Do **not** queue an active JSON while you are still studying in it! Only queue a JSON once its Drive `lastUpdated` timestamp is **at least 20–30 minutes old** (idle/finished).
* **Batch dispatch:** Trigger your private GitHub Action **once every 4 hours** (max 6 runs/day, and **skip completely** if nothing changed). Inside that single VM boot, loop through **all queued JSONs in one pass** (starting your PDF engine *once* instead of 50 times).
* **New Compute Math:** `4–6 batch runs/day × 1–2 min × 30 days` = **~120–360 min/month** (comfortably inside your **2,000 min/month** free quota, even at 50 chats/day!).

#### 3. Cache Your PDF Tools (`actions/cache`)
If your private workflow installs `pandoc`/`texlive`, `weasyprint`, or `playwright`/Chromium on every run, that wastes 45–90 seconds per job before converting a single file. Adding `actions/cache` (or a pre-built container) drops setup down to ~5–10 seconds.

---

### Ready to Patch Your Private Pipeline?
Paste your **private repo’s `.github/workflows/*.yml`** and your **Google Apps Script code** here (**make sure to delete/mask any GitHub tokens or Drive folder IDs first!**).

I’ll inspect how it currently triggers and converts, and give you the exact **batch + idle-debounce + cache** update to slash your GitHub Actions minutes first—before we connect the `.md` output into `ai-kb`.

---

## User

Apps script code: /**
 * Syncs AI Studio chats -> Clean .md in Drive -> Private GitHub Actions -> Incremental PDFs via doPost
 * Reads GITHUB_TOKEN and CALLBACK_SECRET safely from Project Settings -> Script Properties.
 */ const CONFIG = { SOURCE_FOLDER_NAMES: ['Google AI Studio', 'AI Studio'], MD_FOLDER_NAME: 'AI Studio Markdown', PDF_FOLDER_NAME: 'AI Studio PDF',

  GITHUB_OWNER: 'inikashx-hub', GITHUB_REPO: 'AI-Studio-pdf-worker', GITHUB_BRANCH: 'main',

  INCLUDE_THOUGHTS: false, INCLUDE_METADATA: true, STATE_PREFIX: 'gh_sync_', MAX_SINGLE_PDF_BYTES: 15 * 1024 * 1024 };

function getSecrets_ { const props = PropertiesService.getScriptProperties; const token = (props.getProperty('GITHUB_TOKEN') || '').trim; const secret = (props.getProperty('CALLBACK_SECRET') || '').trim; if (!token || !secret) { throw new Error('Missing GITHUB_TOKEN or CALLBACK_SECRET in Project Settings -> Script Properties.'); } return { token, secret }; }

function hashTurns_(turns) { const raw = JSON.stringify(turns); const digest = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, raw, Utilities.Charset.UTF_8); return digest.map(b => ('0' + ((b & 0xff).toString(16))).slice(-2)).join(''); }

function syncCleanMarkdown { const cache = CacheService.getScriptCache; if (cache.get('gh_sync_running')) return; cache.put('gh_sync_running', '1', 300);

  const startTime = Date.now;

  try { const { token } = getSecrets_; const mdFolder = getOrCreateFolder_(CONFIG.MD_FOLDER_NAME); const pdfFolder = getOrCreateFolder_(CONFIG.PDF_FOLDER_NAME); const visited = new Set([mdFolder.getId, pdfFolder.getId]);

    const files = []; for (const f of getSourceFolders_) collectFiles_(f, visited, files);

    const seen = new Set(files.map(f => f.getId)); try { const q = DriveApp.searchFiles('mimeType = "application/vnd.google-makersuite.prompt" and trashed = false'); while (q.hasNext) { const pf = q.next; if (!seen.has(pf.getId)) { seen.add(pf.getId); files.push(pf); } } } catch (e) {}

    const props = PropertiesService.getScriptProperties; const stateMap = props.getProperties; let mdCount = 0, queuedCount = 0, paused = false;

    for (const file of files) { if (Date.now - startTime > 220000) { paused = true; break; } if (file.isTrashed) continue; const mime = file.getMimeType; if (mime.startsWith('application/vnd.google-apps.') || mime.startsWith('image/') || mime.startsWith('video/') || mime.startsWith('audio/') || mime === 'application/pdf') continue;

      const id = file.getId; const updatedMs = file.getLastUpdated.getTime; const key = CONFIG.STATE_PREFIX + id; let prev = {}; if (stateMap[key]) { try { prev = JSON.parse(stateMap[key]); } catch (e) {} }

      const needsMd = prev.t !== updatedMs || !prev.m; const jobInFlight = prev.qa && (Date.now - prev.qa < 15 * 60 * 1000); const needsPdf = (prev.pt !== updatedMs || !prev.p) && !jobInFlight;

      if (!needsMd && !needsPdf) continue; if (file.getSize > 15 * 1024 * 1024) continue;

      let data; try { data = JSON.parse(file.getBlob.getDataAsString('UTF-8')); } catch (e) { continue; } if (!data || (!data.chunkedPrompt && !data.contents && !data.runSettings)) continue;

      const chat = extractCleanChat_(data, file); const baseName = cleanName_(file.getName); const mdName = `${baseName}.md`; const fullMdText = renderCleanMd_(chat);

      let mdId = prev.m || null; if (needsMd) { if (!mdId) { const byName = mdFolder.getFilesByName(mdName); while (byName.hasNext) { const ef = byName.next; if (!ef.isTrashed) { mdId = ef.getId; break; } } } let updated = false; if (mdId) { try { const ex = DriveApp.getFileById(mdId); if (!ex.isTrashed) { ex.setContent(fullMdText); if (ex.getName !== mdName) ex.setName(mdName); updated = true; } } catch (e) {} } if (!updated) mdId = mdFolder.createFile(Utilities.newBlob(fullMdText, 'text/markdown', mdName)).getId; prev.t = updatedMs; prev.m = mdId; mdCount++; }

      if (needsPdf) { const fullTc = chat.turns.length; const fullTh = hashTurns_(chat.turns); let mode = 'full'; let part = 1; let partStartTc = 0; let expectedTc = 0; let existingPdfId = null; let pdfName = `${baseName}.pdf`; let turnsForPdf = chat.turns; let jobMdText = fullMdText; let skipQueue = false;

        if (prev.p && typeof prev.tc === 'number' && prev.tc > 0 && prev.tc <= fullTc && prev.th) { const prefixHash = hashTurns_(chat.turns.slice(0, prev.tc)); if (prefixHash === prev.th) { try { const existingPdf = DriveApp.getFileById(prev.p); if (!existingPdf.isTrashed) { const curPart = prev.part || 1; const curPdfName = curPart > 1 ? `${baseName} (Part ${curPart}).pdf` : `${baseName}.pdf`;

                if (fullTc === prev.tc) { if (existingPdf.getName !== curPdfName) existingPdf.setName(curPdfName); prev.pt = updatedMs; skipQueue = true; } else if (existingPdf.getSize < CONFIG.MAX_SINGLE_PDF_BYTES) { mode = 'append'; part = curPart; partStartTc = prev.partStartTc || 0; expectedTc = prev.tc; existingPdfId = prev.p; pdfName = curPdfName; turnsForPdf = chat.turns.slice(prev.tc); jobMdText = renderContinuationMd_(chat, turnsForPdf, prev.tc, fullTc, null); } else { mode = 'new_part'; part = curPart + 1; partStartTc = prev.tc; expectedTc = prev.tc; existingPdfId = null; pdfName = `${baseName} (Part ${part}).pdf`; turnsForPdf = chat.turns.slice(prev.tc); jobMdText = renderContinuationMd_(chat, turnsForPdf, prev.tc, fullTc, part); } } } catch (e) {} } }

        if (!skipQueue) { const assets = collectAssets_(turnsForPdf); const jobPayload = { sourceId: id, updatedMs, baseName, pdfName, mode, existingPdfId, expectedTc, nextTc: fullTc, nextTh: fullTh, part, partStartTc, mdText: jobMdText, assets }; if (pushJobToGitHub_(`jobs/${id}.json`, jobPayload, token)) { prev.qt = updatedMs; prev.qa = Date.now; queuedCount++; } } }

      const pLock = LockService.getScriptLock; pLock.waitLock(10000); try { let latest = {}; const latestRaw = props.getProperty(key); if (latestRaw) { try { latest = JSON.parse(latestRaw); } catch (e) {} } props.setProperty(key, JSON.stringify(Object.assign({}, latest, prev))); } finally { pLock.releaseLock; } }

    if (queuedCount > 0) { triggerGitHubWorkflow_(token); }

    console.log(paused ? `Paused at time guard. MD: ${mdCount}, Queued for PDF: ${queuedCount}. Run again to queue remaining.` : `Done! MD updated: ${mdCount}, Queued for GitHub PDF build: ${queuedCount}`); } finally { cache.remove('gh_sync_running'); } }

function collectAssets_(turns) { const assets = []; for (const turn of turns) { for (const item of turn.items) { if (item.type === 'image_b64' && item.data && item.data.length < 7000000) { assets.push({ mimeType: item.mimeType || 'image/png', dataB64: item.data }); } else if (item.type === 'image_drive') { try { const blob = DriveApp.getFileById(item.fileId).getBlob; const bytes = blob.getBytes; if (bytes.length < 5 * 1024 * 1024) { assets.push({ mimeType: blob.getContentType || 'image/png', dataB64: Utilities.base64Encode(bytes) }); } } catch (e) {} } } } return assets; }

function requeueAllPastChats { const props = PropertiesService.getScriptProperties; const all = props.getProperties; let resetCount = 0;

  for (const key of Object.keys(all)) { if (!key.startsWith(CONFIG.STATE_PREFIX)) continue; try { const st = JSON.parse(all[key]); delete st.t; delete st.pt; delete st.qt; delete st.qa; delete st.tc; delete st.th; delete st.part; delete st.partStartTc; props.setProperty(key, JSON.stringify(st)); resetCount++; } catch (e) {} } console.log(`Reset ${resetCount} chat(s). Running syncCleanMarkdown() now...`); syncCleanMarkdown; }

function doPost(e) { try { const { secret } = getSecrets_; const payload = JSON.parse(e.postData.contents); if (!payload || payload.secret !== secret) { return jsonResponse_({ ok: false, error: 'Unauthorized' }); }

    if (payload.action === 'get_pdf') { const existing = DriveApp.getFileById(payload.fileId); if (existing.isTrashed) { return jsonResponse_({ ok: false, error: 'Existing PDF is trashed' }); } const bytes = existing.getBlob.getBytes; return jsonResponse_({ ok: true, pdfB64: Utilities.base64Encode(bytes) }); }

    const lock = LockService.getScriptLock; lock.waitLock(30000); try { const pdfFolder = getOrCreateFolder_(CONFIG.PDF_FOLDER_NAME); const props = PropertiesService.getScriptProperties; const key = CONFIG.STATE_PREFIX + payload.sourceId;

      let prev = {}; const raw = props.getProperty(key); if (raw) { try { prev = JSON.parse(raw); } catch (err) {} }

      if (payload.mode === 'append' && typeof payload.expectedTc === 'number' && typeof prev.tc === 'number' && prev.tc !== payload.expectedTc) { return jsonResponse_({ ok: false, error: 'Stale delta: expectedTc mismatch' }); }

      if (prev.p && payload.mode !== 'new_part') { try { const old = DriveApp.getFileById(prev.p); if (!old.isTrashed) old.setTrashed(true); } catch (err) {} } const dupes = pdfFolder.getFilesByName(payload.pdfName); while (dupes.hasNext) { const df = dupes.next; if (!df.isTrashed) df.setTrashed(true); }

      const bytes = Utilities.base64Decode(payload.pdfB64); const blob = Utilities.newBlob(bytes, 'application/pdf', payload.pdfName); const created = pdfFolder.createFile(blob);
