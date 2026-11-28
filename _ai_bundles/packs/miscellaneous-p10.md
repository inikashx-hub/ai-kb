# Subject Pack: miscellaneous (Part 10/24)


---
## FILE: `chats/Fixing GitHub Actions Workflow Errors.md` [Part 10/10]

1. **GitHub Free Tier Minutes (2,000 min/month limit):**
   - **Fixed setup per triggered run:** `~25–35s` (`~0.5 min`) — same as before (installs WeasyPrint deps, Python packages, and MathJax).
   - **On a 500k-token session + 10k new tokens (the biggest win!):**
     - **Before:** Re-rendering all 510k tokens (~700–1,000+ pages) in MathJax + WeasyPrint takes roughly **2 to 8+ minutes** per follow-up update (plus high risk of timeout/retry burning even more minutes). Five 10k-token follow-ups across a day = **~12 to 40+ minutes** for just *one* chat.
     - **Now (Option A):** MathJax + WeasyPrint renders *only* the new 10k tokens (**~2–4s**), `get_pdf` fetches the old PDF (**~2–5s**), `pypdf` merges them (**< 0.5s**), and `doPost` saves it (**~2–5s**) — roughly **8–15 seconds** of actual work per update + ~30s setup (**~40–45s total = ~0.7 min**). Five separate follow-ups = **~3.5 minutes** total (or **~1.5 min** if batched in one 15-min cycle!).
     - **Net GitHub minutes saved on long chats:** **~75% to 90%+ fewer minutes per update** (and **~95%+ reduction in render CPU time** once the VM boots).
   - **On tiny/short chats (< ~10 pages):**
     - Adding `get_pdf` adds one extra ~2s HTTP round-trip (~3s full vs ~5s incremental), so short chats use virtually the same minutes (~0.05 min difference), while **any chat over ~30k–50k+ tokens** starts saving significantly.
   - **On timestamp-only / no-new-turn updates:**
     - `skipQueue` handles renames or non-visible edits inside Apps Script with **0 GitHub minutes** (100% saved).

2. **GitHub Repository Storage / Git History Bloat (1 GB recommended / 5 GB limit):**
   - **Before:** Every 10k follow-up on a 500k session pushed another **~2.5–6 MB** `jobs/{id}.json` commit permanently into `.git` history (10 follow-ups = ~25–60 MB of permanent Git bloat for a single chat!).
   - **Now:** Apps Script pushes **only the new 10k turns** (**~40–60 KB** JSON, and skips old images completely!).
   - **Savings:** **~98% smaller Git commits** (roughly **50×–100× less repo bloat** over time!).

3. **GitHub API Rate Limits & Apps Script Free Tier Quotas:**
   - **Apps Script `UrlFetchApp` (20,000 calls/day [1.1.1], 50 MB max payload, 6 min/execution, 90 min/day trigger runtime [1.1.1]):**
     - Uploading ~50 KB instead of ~5 MB per job to GitHub cuts `UrlFetchApp` upload time and prevents hitting Apps Script's **50 MB payload cap** / V8 memory limits on long sessions with images (plus the 15 MB rollover protects `doPost`!).
     - Note: Each `append` job adds **1 extra `get_pdf` call** to Apps Script (`doPost`), which takes ~2–5s out of your Web App budget (doesn't count against your 90 min/day *trigger* runtime, only synchronous Web App time, and is tiny vs 20,000 URL Fetch calls/day).

4. **Bottom-line monthly projection on GitHub's 2,000 free minutes:**
   - Even if you actively maintain **multiple 500k-token sessions** with **10+ follow-up turns per day**, your monthly GitHub Actions usage stays around **~150–250 minutes/month (~8%–12% of the 2,000-minute Free tier)** — whereas re-rendering 500k tokens every turn could easily burn **1,000–2,000+ minutes/month** and risk hitting the cap or timing out!

Everything is accurate, transparent about trade-offs on tiny chats vs huge chats, and grounded in exact numbers from their scripts and verified documentation. Let's write it cleanly!Here is the realistic breakdown of what **Option A** saves you compared to full re-rendering, especially for GitHub's **2,000 free minutes/month** and repo storage limits:

---

### 1. GitHub Actions Free Tier Minutes (2,000 min/month)

Every triggered run still has a fixed **~25–35 second (`~0.5 min`) startup cost** (installing WeasyPrint dependencies, Python packages, and MathJax). The big difference is what happens **after** setup:

#### On a 500k-token session + 10k new tokens

| Metric | Previous (Full Re-render) | Option A (Incremental + `pypdf`) | Savings |
| :--- | :--- | :--- | :--- |
| **MathJax + WeasyPrint render** | **~2 to 8+ mins** *(700–1,000+ pages)* | **~2 to 4 sec** *(~10–15 new pages)* | **~95%+ render time** |
| **Fetch + Merge + Save (`get_pdf` + `pypdf`)** | `~5–15 sec` *(upload only)* | `~5–10 sec` | — |
| **Total per single update (incl. ~30s boot)** | **~2.5 to 9 mins** | **~40–45 sec (`~0.7 min`)** | **~75%–90% fewer minutes** |
| **5 follow-ups (10k each, separate runs)** | **~13 to 45 mins** | **~3.5 mins** *(~1.5m if batched)* | **~75%–92% saved** |

* **Monthly impact:** Even if you actively continue **huge 500k-token sessions 10 times every day** (300 updates/month), Option A uses roughly **~200 minutes/month (~10% of your 2,000 free minutes)**, whereas full re-renders could easily burn **1,000–2,000+ minutes/month** (and frequently waste extra minutes on timeouts/retries).
* **No-new-turn edits / renames:** If `updatedMs` changes without adding visible turns, `skipQueue` updates the name/timestamp right inside Apps Script using **0 GitHub minutes (100% saved)**.
* **Honest trade-off on very short chats (< 10 pages):** For tiny chats, fetching `old.pdf` (`get_pdf`) adds one ~2-second HTTP round-trip, so a tiny update takes ~5s instead of ~3s (~0.03 min difference — negligible). The payoff kicks in heavily once chats pass ~30k–50k+ tokens.

---

### 2. GitHub Repository Size & Git History Bloat (Private Repo)
Because `jobs/*.json` is committed and deleted via Git, GitHub retains old deleted blobs inside `.git` history permanently (GitHub recommends keeping repos under ~1 GB).
* **Previous:** Every 10k follow-up on a 500k-token session committed another **~2.5–6+ MB** `jobs/{id}.json` permanently into Git history (10 follow-ups = ~25–60 MB of bloat for one chat, plus much more if the earlier turns had images).
* **Option A:** Apps Script pushes **only the new 10k turns** (**~40–60 KB** JSON) and skips all old images.
* **Savings:** **~98% smaller Git commits (~50×–100× less permanent repo bloat)**.

---

### 3. Google Apps Script Quotas & Reliability
Consumer `@gmail.com` Apps Script limits include **90 minutes/day** of trigger runtime, **6 minutes max per execution**, **20,000 URL Fetch calls/day**, and a **50 MB** `UrlFetchApp` payload limit [1.1.1, 2.1.2].
* **Smaller GitHub uploads:** Uploading ~50 KB instead of ~5 MB per update keeps `syncCleanMarkdown` fast inside its 220-second window and well clear of the 50 MB `UrlFetchApp` cap.
* **No giant timeouts:** Rendering 10k tokens avoids MathJax/WeasyPrint timeouts on 1,000-page HTML documents, and the **15 MB PDF rollover (`Part 2`)** protects `doPost` from hitting Apps Script's memory/Drive blob limits.

---

### Summary
* **On small chats:** Virtually the same minutes (~0.5 min per batch run).
* **On 500k-token mega-sessions:** You save **~75%–90%+ of your GitHub Actions minutes** per follow-up and **~98% of your Git repository history growth**, while eliminating almost all timeout/memory failures.

---
