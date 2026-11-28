# Subject Pack: miscellaneous (Part 8/24)


---
## FILE: `chats/Fixing GitHub Actions Workflow Errors.md` [Part 8/10]

5. **Let's check if the user wants us to explain how it works AND offer the ready-to-paste updated code (`Code.gs`, `render.py`, `build-pdfs.yml`) — or wait: should we give the clear explanation + ask if they want the updated files, OR give the clean solution right now?**
   Notice how the user asked:
   > *"Is there a way to render only new 10k tokens instead of 500k tokens every single time?"*
   They asked a direct "Is there a way...?" question (and earlier they liked complete copy-paste scripts when ready, though right now they haven't confirmed yet whether they prefer **Option A: One merged PDF (`pypdf` append)** vs **Option B: Separate continuation Part PDFs (`Part 2`, `Part 3`)**!). Wait: let's explain clearly:
   1. **Yes — it's very doable!** Explain the **2 ways** to do it cleanly in their exact setup:
      - **Approach 1 (Recommended — One Single PDF + Fast Incremental Render via `pypdf`):**
        - Apps Script stores the **turn count (`tc`)** and a **SHA-256 hash (`th`)** of all previously rendered turns in `PropertiesService`.
        - When you add 10k new tokens to a 500k session, Apps Script checks if the first `tc` turns are unchanged.
          - **If unchanged:** Apps Script sends **only the new 10k-token turns** (`~40 KB`) + the old PDF's Drive ID (`existingPdfId`) to GitHub.
          - GitHub Actions runs MathJax + WeasyPrint on **only those new 10k tokens** (~2–3 seconds!), downloads the existing PDF from Apps Script (`action: 'get_pdf'`), stitches `old.pdf + delta.pdf` in **< 0.5 seconds** using Python's `pypdf`, and sends the combined PDF back (or automatically rolls over to `(Part 2)` if the PDF ever exceeds ~15 MB).
          - **If you edited an earlier message in the middle:** The hash check automatically falls back to a full re-render so nothing gets out of sync.
        - **Catch to keep in mind:**
          - Because `old.pdf + delta.pdf` are merged as separate PDF pages, the new turns start at the **top of a new page** (like a new chapter/continuation) rather than mid-page at the bottom of Page 700, and page numbers work best as `Page 1, Page 2, ...` (or `Page 701...` without `"of N"`, since earlier pages already have baked-in footers unless stamped).
          - Also, sending the merged PDF back to `doPost` still hits Apps Script's ~20–35 MB transfer limit if a single PDF gets huge (unless you auto-rollover to `Part 2` above ~15 MB).
      - **Approach 2 (Simplest & Zero Merge Transfer — Separate Part PDFs):**
        - Same turn-count + hash check in Apps Script, but instead of fetching and re-uploading the huge 500k PDF, GitHub renders **only the 10k new tokens** into a tiny standalone `Chat Name (Part 2).pdf` (or updates `Part 2` as you keep adding turns until `Part 2` itself gets big). Zero large file transfers, zero `doPost` size limits, ~3-second renders!
   2. **Offer to generate the exact complete updated files (`Code.gs`, `render.py`, `build-pdfs.yml`)** as soon as they say which style they prefer:
      - **Approach 1** (one single merged PDF via `pypdf`, with automatic `Part 2` rollover only if > 15 MB), **or**
      - **Approach 2** (separate `Part 2` PDFs for new additions).

Let's double-check that every technical detail (hash check on `turns`, `pypdf` append [2.1.1], `WeasyPrint` `counter-reset: page` [1.2.1], Apps Script 50 MB `UrlFetchApp` / ~20–35 MB `doPost` memory limit, new turns starting on a fresh page) is 100% accurate and clearly explained without making anything up!

Let's write a crisp, practical, well-structured answer.Yes — you can avoid re-rendering the old 500k tokens completely by tracking **turn count + a prefix hash** in Apps Script and using **PDF appending (`pypdf`)** [2.1.1] on GitHub.

Here is how it works and the two ways you can set it up:

---

### Core idea (how Apps Script detects "only new turns")
In `Code.gs`, every chat is a list of turns (`chat.turns = [User, Model, User, Model, ...]`).
1. When a chat is rendered, Apps Script saves two extra fields in `PropertiesService`:
   * `tc`: how many turns were rendered (e.g., `84` turns)
   * `th`: a SHA-256 hash of `chat.turns[0..83]`
2. Later, when you add **10k new tokens** (turns `84..87`) to that 500k session:
   * Apps Script hashes `chat.turns[0..83]` and compares it to `th`.
   * **If it matches** (99% of the time when continuing a chat): Apps Script sends **only the new 10k-token turns** (`chat.turns.slice(84)`) + their images to GitHub (`~40 KB` JSON instead of `~5 MB`).
   * **If it doesn't match** (you edited or deleted an earlier message in the middle): it automatically falls back to a full re-render so your PDF never goes out of sync.

---

### Two ways to handle the PDF output

#### Option A: Keep ONE single merged PDF (`Chat Name.pdf`) — Recommended
1. `render.py` runs MathJax + WeasyPrint **only on the new 10k tokens** (takes **~2–3 seconds** instead of minutes!).
2. `render.py` fetches the existing `old.pdf` from Drive (via a small `get_pdf` action in Apps Script `doPost`), stitches `old.pdf + new_turns.pdf` together in **< 0.5 seconds** using Python's `pypdf` [2.1.1], and sends the combined PDF back.
3. **Safety rollover:** If `old.pdf` ever grows past ~15 MB (approaching Apps Script's ~20–35 MB `doPost` memory ceiling), it automatically starts `Chat Name (Part 2).pdf` instead of failing.

**Small visual trade-off:** The newly appended 10k-token section starts cleanly at the **top of a new page** (after the last page of `old.pdf`), and page footers work best as `"Page 701"` (using CSS `counter-reset: page` [1.2.1]) without `"of 715"` (since pages 1–700 already have their old `"Page X of 700"` text baked in).

---

#### Option B: Save new turns as a separate continuation PDF (`Chat Name (Part 2).pdf`)
1. Same turn-count + hash check, and GitHub renders **only the 10k new tokens** (~2–3 seconds).
2. Instead of downloading and re-uploading the huge 500k PDF every time, it simply saves/updates **`Chat Name (Part 2).pdf`** in Drive (and keeps appending future small updates into `Part 2` until `Part 2` itself gets large).
3. **Benefit:** Zero large file transfers through `doPost`, zero Apps Script size limits, even faster.

---

If you tell me which one you prefer (**Option A: one merged PDF** or **Option B: separate Part 2 continuation PDFs**), I can give you the complete, drop-in updated `Code.gs`, `render.py`, and `build-pdfs.yml` for it!

---

## User

Option A

---

## Model

**search** "WeasyPrint" "counter-reset: page" "first page" OR "off by one" OR "body" Look at `1.1.3` and `1.1.4` (`GitHub Kozea/WeasyPrint` issues/docs): Look carefully at `1.1.4`:
> *"It is not possible to change page counter directly on `@page`... `body { counter-reset: page 700; }`"*
AND notice in `1.1.3` & `1.1.4`: in WeasyPrint, `counter-reset: page <N>` on `body` resets the counter BEFORE the first page counter increment (`1`st page becomes `N + 1`? Or `N`? Wait: in WeasyPrint issue #1167 / #1694, `counter-reset: page 2` on `body` or first element sets page 1 to `2` or `3` depending on version — let's check `1.1.1` / `1.1.4` carefully!). Actually let's check if there is an even simpler, **zero-ambiguity** way OR check `counter-reset: page 2` in WeasyPrint 62+ (`1.1.4`)! Let's run one quick search on `WeasyPrint` `counter-reset: page` `page 2` `body`.**search** site:github.com/Kozea/WeasyPrint "counter-reset: page" "counter(page)" Look at `1.1.3` (`Kozea/WeasyPrint#1167`) and `1.2.1` (`Kozea/WeasyPrint` docs!):
- Look at `1.1.3`: `body { counter-reset: page 1; }` -> in CSS Paged Media / WeasyPrint, the root/page context increments `page` by 1 *at the start of each page*, so `body { counter-reset: page 700; }` makes the first page `701` (`700 + 1`) — OR in some CSS specs `counter-reset` on `body` sets page 1 to `700` if `body` starts *after* `@page` begins!
Wait: look at the **even cleaner**, 100% foolproof alternative:
- On `'full'` mode (non-incremental, e.g. 95% of chats rendered in one go): keep `"Page " counter(page) " of " counter(pages)`!
- On `'append'` mode (incremental delta chunk): use `body { counter-reset: page <old_page_count>; }` with `"Page " counter(page)`! Wait: what if WeasyPrint starts `counter-reset: page 700` on `body` at `700` vs `701`? Actually in WeasyPrint (`#1167` / `#1694`), `counter-reset: page N` on `body` sets `page` on the first page to `N` (Wait: why? Because `@page` starts Page 1 and increments `page` from 0→1 BEFORE `body` lays out, and THEN `body { counter-reset: page N; }` resets the already-incremented counter to `N` on page 1, and Page 2 increments to `N + 1`! Look at `1.1.3` where `counter-reset: page 1` on `body` didn't double-increment to 2 — wait: let's check `1.1.3` or avoid guessing!).
Wait — if we aren't 100% certain whether WeasyPrint 70 sets `body { counter-reset: page N }` to `N` or `N + 1`, we can ALSO label appended sections cleanly as `"Update · Page " counter(page)` (starting at 1 for each appended continuation, e.g. `Cont. p.1`, `Cont. p.2`, OR even better: **`pypdf` doesn't even need `counter-reset` to look super clean** if we write `"Cont. Page " counter(page)` or test/stamp!). WAIT — ACTUALLY, THINK ABOUT `Cont. Page 1` vs `Page 701`:
- Look: on Page 1–700 of `old.pdf`, the bottom-right footer ALREADY says **`Page 1 of 700` ... `Page 700 of 700`**!
- If Page 701 said `Page 701`, and Page 700 said `Page 700 of 700`, having `"Update (Turns 85–88) · p. 1"` (or `body { counter-reset: page <old_page_count + 1>; }`? No, don't risk off-by-one!) vs labeling the continuation clearly (`"Part 2 · Page 1"` or `"Update · Page " counter(page)`) is **NEVER off-by-one** and immediately tells you where the new update starts!
- Wait: OR if you WANT continuous numbering `701, 702...`, even `render.py` can check `len(PdfReader(...).pages)`? No, checking the rendered text of `delta` in Python takes 1 line with `pypdf` (`PdfReader(io.BytesIO(delta_bytes)).pages[0].extract_text()`)? No, don't do double renders! Putting **`"Cont. (Turns X–Y) · Page " counter(page) " of " counter(pages)`** (or `"Continued · Page " counter(page) " of " counter(pages)`) in `@bottom-right` on appended pages is **100% consistent, zero off-by-one risk, and works with `"of " counter(pages)` cleanly for that update section**!!
That's genuinely cleaner and more readable when skimming a 700-page PDF (`Page 700 of 700` → `Continued · Page 1 of 4` → `Continued · Page 2 of 4`)!

---

### Let's Double-Check Every Line of `Code.gs`, `render.py`, and `build-pdfs.yml`

#### Check `Code.gs` carefully:
1. Helper `hashTurns_(turns)`:
   ```javascript
   function hashTurns_(turns) {
     const raw = JSON.stringify(turns);
     const digest = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, raw, Utilities.Charset.UTF_8);
     return digest.map(b => ('0' + ((b & 0xff).toString(16))).slice(-2)).join('');
   }
   ```
   Wait: check `(b & 0xff).toString(16)` in Apps Script! In Google Apps Script, `computeDigest` returns signed bytes `-128..127`, so `(b & 0xff).toString(16)` gives exact unsigned hex `00..ff`! Zero issues, deterministic across runs!

2. Helper `renderTurnsMd_(chat, turns, opts)` (replaces/extends `renderCleanMd_`):
   - For the `.md` file in Google Drive (`AI Studio Markdown`): STILL calls `renderFullMd_(chat)` so the Drive `.md` file is always the complete full conversation!
   - For GitHub PDF job payload (`jobMdText`):
     - If `mode === 'full'`: `renderFullMd_(chat)` (same as before!)
     - If `mode === 'new_part'`: `renderContinuationMd_(chat, deltaTurns, startTurnIdx, part)` (with `# Title (Part N)` + `> Continued from Turn X | Model | Updated` + `deltaTurns`)
     - If `mode === 'append'`: `renderContinuationMd_(chat, deltaTurns, startTurnIdx, null)` (with `> Continued (Turns X–Y) | Model | Updated` + `deltaTurns`)
   - Wait: verify `startTurnIdx` is 1-based for display (`Turns ${startTurnIdx + 1}–${endTurnIdx}`)! If `prev.tc = 84` and `chat.turns.length = 88`, `Turns 85–88`! Nice!

3. Decision logic in `syncCleanMarkdown()` for `needsPdf`:
   Let's trace ALL cases when `needsPdf` is `true`!
   - Remember:
     ```javascript
     const needsMd = prev.t !== updatedMs || !prev.m;
     const jobInFlight = prev.qa && (Date.now() - prev.qa < 15 * 60 * 1000);
     const needsPdf = (prev.pt !== updatedMs || !prev.p) && !jobInFlight;
     ```
   - Inside `if (needsPdf)`:
     ```javascript
     const fullTc = chat.turns.length;
     const fullTh = hashTurns_(chat.turns);
     let mode = 'full';
     let part = 1;
     let partStartTc = 0;
     let expectedTc = 0;
     let existingPdfId = null;
     let targetPdfName = `${baseName}.pdf`;
     let turnsForPdf = chat.turns;

     if (prev.p && typeof prev.tc === 'number' && prev.tc > 0 && prev.tc <= fullTc && prev.th) {
       const prefixHash = hashTurns_(chat.turns.slice(0, prev.tc));
       if (prefixHash === prev.th) {
         if (fullTc === prev.tc) {
           // Only metadata/timestamp changed (no new turns in chat.turns) — skip or re-use
           // Wait: what if file was renamed or metadata edited without adding turns?
           // Safest: skip expensive PDF re-render if turns are 100% identical AND pdf still exists!
         }
       }
     }
     ```
     **HOLD ON! CHECK THAT EDGE CASE!!** What if `fullTc === prev.tc` AND `prefixHash === prev.th`?! Suppose Google Drive touched `updatedMs` (or someone opened AI Studio without adding a turn, OR added an empty/thought-only turn when `INCLUDE_THOUGHTS: false`)!
     - If `prev.p` still exists and isn't trashed, and `chat.turns` is **100% identical** (`fullTc === prev.tc && prefixHash === prev.th`), there are **ZERO new turns** to render!
     - We can simply update `prev.pt = updatedMs` without wasting a GitHub Actions run!
     - What if `fullTc > prev.tc` AND `prefixHash === prev.th`?
       Check `existingFile = DriveApp.getFileById(prev.p)`:
       - If `!existingFile.isTrashed()`:
         - Check `existingFile.getSize()`:
           - If `< 15 * 1024 * 1024` (under 15 MB):
             - `mode = 'append'`!
             - `part = prev.part || 1`
             - `partStartTc = prev.partStartTc || 0`
             - `expectedTc = prev.tc`
             - `existingPdfId = prev.p`
             - `targetPdfName = part > 1 ? `${baseName} (Part ${part}).pdf` : `${baseName}.pdf``
             - `turnsForPdf = chat.turns.slice(prev.tc)`
           - If `>= 15 * 1024 * 1024` (15 MB rollover!):
             - `mode = 'new_part'`!
             - `part = (prev.part || 1) + 1`
             - `partStartTc = prev.tc`
             - `expectedTc = prev.tc`
             - `existingPdfId = null`
             - `targetPdfName = `${baseName} (Part ${part}).pdf``
             - `turnsForPdf = chat.turns.slice(prev.tc)`
       - If `existingFile` WAS trashed / deleted by user:
         - Fall back cleanly to `mode = 'full'` (`part = 1, partStartTc = 0, expectedTc = 0, turnsForPdf = chat.turns`)!
     - What if `prefixHash !== prev.th` (user edited/deleted an earlier turn) OR `prev.tc` wasn't saved yet?
       - `mode = 'full'` (`part = 1, partStartTc = 0, expectedTc = 0, turnsForPdf = chat.turns`)!

   **WAIT — CHECK ONE DETAIL ON `doPost(e)` WHEN `mode === 'new_part'` vs `mode === 'append'` vs `mode === 'full'`!** Look at `doPost(e)` in their original script (lines 166–177):
   ```javascript
   if (prev.p) {
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
   ```
   **LOOK WHAT WOULD HAPPEN IF WE KEPT `if (prev.p) old.setTrashed(true)` WHEN `mode === 'new_part'`!!** IF `mode === 'new_part'` (rolling over to `Part 2` because `Part 1` exceeded 15 MB), `prev.p` IS `Part 1`! If `doPost` trashed `prev.p`, it would DELETE `Part 1`!! **WHAT A CATCH!!** Let's fix that cleanly:
   - In `doPost(e)`:
     - Only trash `prev.p` when `payload.mode !== 'new_part'`! (Wait: when `mode === 'new_part'`, we WANT to keep `Part 1` untouched in Drive, and only trash any pre-existing file named `payload.pdfName` i.e. `Part 2`!)
     - And when `mode === 'full'`, also clean up any old `(Part 2)`, `(Part 3)`? Actually trashing `prev.p` and `dupes` (by `payload.pdfName`) handles normal replacement, and if `mode === 'full'` and `prev.part > 1`, trashing `prev.p` + `dupes` handles it cleanly too (or even better: `getFilesByName(payload.pdfName)` cleans up `Chat Name.pdf`, and `prev.p` cleans up the previous active file).
     - And when `mode === 'append'`: check `if (typeof payload.expectedTc === 'number' && typeof prev.tc === 'number' && prev.tc !== payload.expectedTc)` → reject (`{ ok: false, error: 'Stale delta: expectedTc mismatch' }`) so out-of-order concurrent callbacks can NEVER duplicate turns!
     - On success in `doPost(e)`, save:
       ```javascript
       prev.p = created.getId();
       prev.pt = payload.updatedMs;
       prev.tc = payload.nextTc;
       prev.th = payload.nextTh;
       prev.part = payload.part || 1;
       prev.partStartTc = payload.partStartTc || 0;
       delete prev.qa;
       ```

4. **Check `requeueAllPastChats()` with the new fields!**
   In `requeueAllPastChats()`:
   ```javascript
   delete st.t;
   delete st.pt;
   delete st.qt;
   delete st.qa;
   delete st.tc;
   delete st.th;
   delete st.part;
   delete st.partStartTc;
   ```
   Wait: should `requeueAllPastChats()` clear `tc`/`th`/`part`/`partStartTc`? **YES!** Because `requeueAllPastChats()` is explicitly for doing a fresh full reset of all past chats! Clearing `tc`/`th`/`part`/`partStartTc` ensures every chat gets a clean full render from Turn 0 and records its baseline `tc`/`th`! (And for normal day-to-day runs, you do NOT run `requeueAllPastChats()` — only `syncCleanMarkdown` runs!)

5. **Check `render.py` with `mode == 'append'` vs `'full'` vs `'new_part'`:**
   Let's trace `render.py` step by step:
   - Read job JSON:
     ```python
     mode = job.get('mode', 'full')
     is_continuation = mode in ('append', 'new_part')
     footer_label = 'Continued · Page ' if is_continuation else 'Page '
     delta_bytes = build_pdf_bytes(job['mdText'], job.get('assets', []), footer_label=footer_label)
     ```
   - If `mode == 'append'` and `job.get('existingPdfId')`:
     1. Call `fetch_existing_pdf(job['existingPdfId'])` (with retry loop up to 4 attempts on timeout/network errors):
        ```python
        resp = requests.post(
            GAS_WEBHOOK_URL,
            json={'secret': GAS_SECRET, 'action': 'get_pdf', 'fileId': existing_pdf_id},
            timeout=120
        )
        ```
        Decode `base64.b64decode(res_json['pdfB64'])` → `old_bytes`.
     2. Merge with `pypdf`:
        ```python
        writer = PdfWriter()
        writer.append(io.BytesIO(old_bytes))
        writer.append(io.BytesIO(delta_bytes))
        buf = io.BytesIO()
        writer.write(buf)
        final_pdf_bytes = buf.getvalue()
        ```
     3. Backwards compatibility: if a job in `jobs/` was created by an *older* script (so `mode` isn't in `job`), `mode` defaults to `'full'`, `final_pdf_bytes = delta_bytes`, and everything works seamlessly!
   - When sending final PDF back to `GAS_WEBHOOK_URL`:
     ```python
     json={
         'secret': GAS_SECRET,
         'mode': mode,
         'sourceId': job['sourceId'],
         'updatedMs': job['updatedMs'],
         'pdfName': job.get('pdfName') or f"{job['baseName']}.pdf",
         'pdfB64': pdf_b64,
         'expectedTc': job.get('expectedTc', 0),
         'nextTc': job.get('nextTc'),
         'nextTh': job.get('nextTh'),
         'part': job.get('part', 1),
         'partStartTc': job.get('partStartTc', 0)
     }
     ```
     (Notice `timeout=180` for `requests.post` so even larger merged PDFs never hit a 90s timeout!)
   - Also keep the local `git rev-parse` `delete_github_job` fix so > 1 MB jobs always delete cleanly!

6. **WAIT — CHECK ONE SUBTLE EDGE CASE IN `Code.gs`!**
   Look at `Code.gs` lines 97–99 (`assets`): In the original `Code.gs`, `assets` looped over `chat.turns`. Now, for `turnsForPdf` (`chat.turns` in `full` mode, or `chat.turns.slice(prev.tc)` in `append`/`new_part` mode): We loop over **`turnsForPdf`** when collecting `assets`! Wait: what if `assets` has a `dataB64` image inside a new turn — does it render cleanly in `delta_bytes`? YES! And old images from previous turns are ALREADY baked into `old.pdf`, so they aren't re-uploaded or duplicated!

7. **WAIT — CHECK ONE MORE EDGE CASE IN `Code.gs`!**
   Look at `if (fullTc === prev.tc)` inside `needsPdf` when `prefixHash === prev.th`! Suppose `prev.p` exists and is NOT trashed, and `fullTc === prev.tc` and `prefixHash === prev.th`:
   - That means `updatedMs` changed on Drive (e.g. file touched/renamed or thought added when `INCLUDE_THOUGHTS: false`), **but the visible turns are 100% unchanged**!
   - If the user **renamed** the chat file in Drive (`file.getName()` changed, so `baseName` changed -> `targetPdfName !== existingFile.getName()`), we should handle that too!
   - Look how easy:
     ```javascript
     if (fullTc === prev.tc) {
       if (existingFile.getName() !== targetPdfName) existingFile.setName(targetPdfName);
       prev.pt = updatedMs;
       skipPdfQueue = true;
     }
     ```
     So if the user just renamed the file in Drive, Apps Script renames the existing PDF in Drive **in 0.1 seconds without even calling GitHub Actions!**

Let's review ALL THREE files one last time for syntax errors, missing imports, indentation, or missing edge cases:
- `build-pdfs.yml`: includes `pypdf` and `mathjax-full@3` ✅
- `render.py`: imports `io`, `PdfWriter` from `pypdf`, `fetch_existing_pdf`, `pypdf` merge, MathJax v3 SVG, `fix_inline_bullets`, `git rev-parse` `delete_github_job`, 4-attempt retry loop ✅
- `Code.gs`: `hashTurns_`, `renderContinuationMd_`, `CacheService` sync lock + brief `ScriptLock` per key, `get_pdf` action in `doPost(e)`, `expectedTc` guard, `mode === 'new_part'` preserves `Part 1`, 15 MB rollover threshold, `requeueAllPastChats()` ✅

Let's present the 3 complete, drop-in files cleanly with simple deployment steps!Here are all three complete, ready-to-paste files implementing **Option A** (incremental turn-only rendering + `pypdf` PDF merging [2.1.1], with automatic rollover to `(Part 2).pdf` if a single PDF ever exceeds 15 MB).

### How it behaves on your 500k + 10k scenario
* **First time a chat is processed (or if you edit an earlier message):** Full render, saving the turn count (`tc`) and SHA-256 prefix hash (`th`).
* **Next 10k-token follow-up:** Apps Script verifies the first `tc` turns match `th`, then sends **only the new 10k turns** (`~40 KB`) to GitHub. GitHub renders only those new pages (~2–3s), fetches the existing PDF from Drive, stitches them together with `pypdf` (< 0.5s), and saves the updated single PDF back to Drive.
* **Safety rollover:** If a single PDF ever crosses **15 MB**, it automatically preserves `Part 1` and starts `Chat Name (Part 2).pdf` so `doPost` never hits Apps Script's memory/upload cap.

---

### 1. GitHub: `.github/workflows/build-pdfs.yml`

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

      - name: Install WeasyPrint dependencies and Emoji/Symbol fonts
        run: |
          sudo apt-get update -qq
          sudo apt-get install -y -qq libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0 libharfbuzz-subset0 fontconfig fonts-noto-color-emoji fonts-noto-core fonts-symbola
          fc-cache -f

      - name: Install Python packages
        run: python3 -m pip install --break-system-packages -q weasyprint markdown-it-py pygments beautifulsoup4 requests pypdf

      - name: Install MathJax for LaTeX equations
        run: npm install --no-save --prefix /tmp/mj mathjax-full@3

      - name: Render PDFs and send back to Google Drive
        env:
          GAS_WEBHOOK_URL: ${{ secrets.GAS_WEBHOOK_URL }}
          GAS_SECRET: ${{ secrets.GAS_SECRET }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_REPO: ${{ github.repository }}
        run: python3 render.py
```

---

### 2. GitHub: `render.py`

```python
import os, io, re, json, base64, html, time, subprocess, requests
from bs4 import BeautifulSoup, NavigableString
from markdown_it import MarkdownIt
from pygments import highlight
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.formatters import HtmlFormatter
from pypdf import PdfWriter
from weasyprint import HTML

GAS_WEBHOOK_URL = os.environ['GAS_WEBHOOK_URL']
GAS_SECRET = os.environ['GAS_SECRET']
GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
GITHUB_REPO = os.environ['GITHUB_REPO']

formatter = HtmlFormatter(noclasses=True, style='friendly')

MJ_SCRIPT = r"""
const { mathjax } = require('/tmp/mj/node_modules/mathjax-full/js/mathjax.js');
const { TeX } = require('/tmp/mj/node_modules/mathjax-full/js/input/tex.js');
const { SVG } = require('/tmp/mj/node_modules/mathjax-full/js/output/svg.js');
const { liteAdaptor } = require('/tmp/mj/node_modules/mathjax-full/js/adaptors/liteAdaptor.js');
const { RegisterHTMLHandler } = require('/tmp/mj/node_modules/mathjax-full/js/handlers/html.js');
const { AllPackages } = require('/tmp/mj/node_modules/mathjax-full/js/input/tex/AllPackages.js');

const adaptor = liteAdaptor();
RegisterHTMLHandler(adaptor);
const tex = new TeX({ packages: AllPackages });
const svg = new SVG({ fontCache: 'none' });
const doc = mathjax.document('', { InputJax: tex, OutputJax: svg });

let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => { input += chunk; });
process.stdin.on('end', () => {
  const items = JSON.parse(input || '[]');
  const out = items.map(({ expr, display }) => {
    try {
      const node = doc.convert(expr, { display: !!display });
      return adaptor.innerHTML(node);
    } catch (e) {
      return null;
    }
  });
  process.stdout.write(JSON.stringify(out));
});
"""

def render_code(code, lang, attrs):
    lang_clean = (lang or '').strip().lower()
    if lang_clean == 'mermaid':
        try:
            b64 = base64.urlsafe_b64encode(code.strip().encode('utf-8')).decode('ascii').rstrip('=')
            r = requests.get(f'https://mermaid.ink/svg/{b64}?bgColor=white', timeout=15)
            if r.status_code == 200 and '<svg' in r.text:
                return f'<div class="diagram">{r.text}</div>'
        except Exception:
            pass
    try:
        lexer = get_lexer_by_name(lang_clean) if lang_clean else TextLexer()
    except Exception:
        lexer = TextLexer()
    highlighted = highlight(code, lexer, formatter)
    badge = f'<div class="code-lang">{lang_clean.upper()}</div>' if lang_clean else ''
    return f'<div class="code-card">{badge}{highlighted}</div>'

md = MarkdownIt('commonmark', {'html': False, 'linkify': False, 'highlight': render_code}).enable(['table', 'strikethrough'])

BASE_CSS = """
body {
  font-family: "Liberation Sans", "DejaVu Sans", "Noto Color Emoji", Arial, sans-serif;
  font-size: 10pt; line-height: 1.55; color: #1e293b;
}
h1 { font-size: 17pt; color: #0f172a; border-bottom: 2px solid #2563eb; padding-bottom: 6px; margin: 0 0 10px; break-after: avoid; }
h2 { font-size: 12pt; color: #1e40af; background: #eff6ff; padding: 4px 10px; border-radius: 5px; margin: 16px 0 8px; break-after: avoid; }
h3, h4 { color: #0f172a; margin: 12px 0 5px; break-after: avoid; }
p { margin: 0 0 8px; orphans: 3; widows: 3; }
blockquote { margin: 8px 0; padding: 6px 12px; border-left: 3px solid #94a3b8; background: #f8fafc; color: #475569; }
hr { border: none; border-top: 1px solid #e2e8f0; margin: 12px 0; }
ul, ol { margin: 4px 0 10px; padding-left: 20px; }
li { margin-bottom: 3px; }
code { font-family: "Liberation Mono", "DejaVu Sans Mono", "Courier New", monospace; font-size: 8.5pt; background: #f1f5f9; padding: 1px 4px; border-radius: 3px; }
.code-card { border: 1px solid #cbd5e1; border-radius: 6px; margin: 8px 0 12px; overflow: hidden; break-inside: avoid-page; }
.code-lang { font-size: 7.5pt; font-weight: bold; background: #e2e8f0; color: #475569; padding: 2px 8px; }
.code-card pre { margin: 0 !important; padding: 8px 10px !important; white-space: pre-wrap; word-break: break-word; font-size: 8pt; line-height: 1.4; }
.diagram { text-align: center; margin: 10px 0; break-inside: avoid; }
.diagram svg, img { max-width: 100%; max-height: 520px; height: auto; }
.math-inline { display: inline; }
.math-inline svg { display: inline; max-width: 100%; overflow: visible; color: inherit; }
.math-display { display: block; text-align: center; margin: 8px 0 10px; break-inside: avoid; }
.math-display svg { display: inline-block; max-width: 100%; overflow: visible; color: inherit; }
.math-fallback { font-family: "Liberation Mono", "DejaVu Sans Mono", monospace; font-size: 9pt; background: #f8fafc; padding: 1px 4px; border-radius: 3px; }
.wide-page { page: wide; }
table { width: 100%; table-layout: fixed; border-collapse: collapse; margin: 10px 0 14px; font-size: 8.8pt; line-height: 1.4; }
table.compact-tbl { font-size: 7.8pt; line-height: 1.32; }
thead { display: table-header-group; }
tr { break-inside: avoid; }
th, td { border: 1px solid #cbd5e1; padding: 6px 8px; text-align: left; vertical-align: top; overflow-wrap: break-word; word-wrap: break-word; }
th { background: #e2e8f0; color: #0f172a; font-weight: bold; }
tbody tr:nth-child(even) { background: #f8fafc; }
"""

def build_css(footer_prefix='Page '):
    page_css = f"""
@page {{
  size: A4 portrait;
  margin: 14mm 13mm;
  @bottom-right {{ content: "{footer_prefix}" counter(page) " of " counter(pages); font-size: 8pt; color: #64748b; }}
}}
@page wide {{
  size: A4 landscape;
  margin: 11mm 12mm;
  @bottom-right {{ content: "{footer_prefix}" counter(page) " of " counter(pages); font-size: 8pt; color: #64748b; }}
}}
"""
    return page_css + BASE_CSS

def fix_inline_bullets(text):
    out_lines = []
    for line in text.split('\n'):
        if not line.strip():
            out_lines.append(line)
            continue
        m_lead = re.match(r'^(\s*(?:[-*+]|\d+[.)])\s+)', line)
        pos = len(m_lead.group(1)) if m_lead else 0
        is_list_line = bool(m_lead)

        in_italic = False
        res = [line[:pos]]
        i = pos
        n = len(line)
        split_count = 0

        while i < n:
            if line[i] == '*':
                j = i
                while j < n and line[j] == '*':
                    j += 1
                if (j - i) == 1:
                    prev_ch = line[i - 1] if i > pos else ''
                    next_ch = line[i + 1] if i + 1 < n else ''
                    if not in_italic and prev_ch in (':', '.', ')') and next_ch == ' ':
                        res.append('\n\n* ' if (split_count == 0 and not is_list_line) else '\n* ')
                        split_count += 1
                        i += 2
                        continue
                    else:
                        in_italic = not in_italic
                res.append(line[i:j])
                i = j
                continue
            res.append(line[i])
            i += 1
        out_lines.append(''.join(res))
    return '\n'.join(out_lines)

def render_math_batch(math_items):
    if not math_items:
        return []
    try:
        proc = subprocess.run(
            ['node', '-e', MJ_SCRIPT],
            input=json.dumps(math_items),
            text=True,
            capture_output=True,
            timeout=120
        )
        if proc.returncode == 0 and proc.stdout:
            return json.loads(proc.stdout)
        print(f"MathJax error (code={proc.returncode}): {proc.stderr[:400]}")
    except Exception as e:
        print(f"MathJax exception: {e}")
    return [None] * len(math_items)

def prepare_markdown_and_math(md_text):
    code_store = []

    def stash_fenced(m):
        token = f'\uE000C{len(code_store)}\uE001'
        code_store.append(m.group(2))
        return m.group(1) + token

    def stash_inline_code(m):
        token = f'\uE000C{len(code_store)}\uE001'
        code_store.append(m.group(0))
        return token

    text = re.sub(r'(^|\n)([ \t]*(`{3,}|~{3,})[^\n]*\n[\s\S]*?\n[ \t]*\3[ \t]*(?=\n|$))', stash_fenced, md_text)
    text = re.sub(r'(`+)([^\n]*?)\1', stash_inline_code, text)

    math_items = []

    def stash_math(expr, display):
        token = f'\uE000M{len(math_items)}\uE001'
        math_items.append({'expr': expr.strip(), 'display': display})
        return token

    text = re.sub(r'(?<!\\)\$\$([\s\S]+?)(?<!\\)\$\$', lambda m: stash_math(m.group(1), True), text)
    text = re.sub(r'(?<!\\)\\\[([\s\S]+?)(?<!\\)\\\]', lambda m: stash_math(m.group(1), True), text)
    text = re.sub(r'(?<!\\)\\\((.+?)(?<!\\)\\\)', lambda m: stash_math(m.group(1), False), text)
    text = re.sub(r'(?<!\\)\$(?!\s)((?:\\\$|[^$\n])+?)(?<!\s)(?<!\\)\$(?!\d)', lambda m: stash_math(m.group(1), False), text)

    text = fix_inline_bullets(text)

    for idx, original_code in enumerate(code_store):
        text = text.replace(f'\uE000C{idx}\uE001', original_code)

    return text, math_items
