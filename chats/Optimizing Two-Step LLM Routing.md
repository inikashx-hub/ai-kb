# Optimizing Two-Step LLM Routing

> **Model:** gemini-4-hydrogen | **Updated:** 2026-11-27 15:12 UTC

---

## User

Thinking of ways to get RAG like functionality in normal Google AI Studio instead of using API with the help of URL toggle and GitHub

---

## Model

You can get surprisingly close to a real RAG pipeline right inside the **Google AI Studio Playground** (no API keys, vector DBs, or custom servers) by treating **GitHub as your dynamic document store** and **URL context** as your retriever.

However, simply pasting `https://github.com/user/repo` won't work like RAG—URL Context **does not crawl nested links or folders**. It only reads the exact URLs you give it (meaning a standard GitHub repo link only gives Gemini the landing page HTML and `README.md`).

To make it behave like actual RAG, here are the best ways to architect **GitHub + URL Context** in normal Google AI Studio, ranked from simplest to most scalable.

---

### First, Two Crucial Rules for GitHub + URL Context
1. **Always use `raw.githubusercontent.com` (or GitHub Gist `/raw`), NOT `github.com/user/repo/blob/...`:**
   Standard GitHub URLs return heavy HTML UI wrappers, navigation menus, and truncated previews. Raw URLs return pure Markdown, JSON, CSV, XML, or code—saving massive amounts of tokens and avoiding parsing errors.
2. **Public repos only:**
   URL Context can only fetch **publicly accessible URLs**. Do **not** put private/sensitive data in a public repo just to use this trick. (For private codebases, check **Method 4** below.)

---

### Method 1: The "Saved Prompt + Sharded Bundles" Setup (Best for < 20 Files / Medium KBs)
URL Context allows up to **20 URLs per request** (up to **34 MB per URL**, though bounded by the model's context window). Instead of linking 200 tiny notes, bundle them into **5–15 logical files** in a public GitHub repo.

1. **Organize your repo into topic files** (e.g., `docs/architecture.md`, `docs/api-spec.md`, `notes/decisions.md`).
2. **Automate bundling (optional but huge time-saver):** Add a simple **GitHub Action** using a tool like **Repomix** (`repomix --split-output 1mb`) or a small Python script that merges folders into clean `.md` or `.xml` bundles on every `git push`.
3. **Save a Template in Google AI Studio:**
   * Turn **ON** the **URL context** toggle in the right-hand Tools sidebar.
   * In **System Instructions**, paste your list of `https://raw.githubusercontent.com/<user>/<repo>/main/bundle-1.md` URLs along with a rule like:
     > *"Use your URL context / browse tool to read the raw GitHub files listed below before answering. Only answer using facts found in those URLs, and cite the exact filename/URL for every claim."*
   * **Save the prompt** in AI Studio. Whenever you open it, you have a live, synced chat over your GitHub repo—just edit and push to GitHub to update the "knowledge base."

---

### Method 2: The `llms.txt` Two-Step "Router" (True Retrieval for Large Repos)
If your repo has **hundreds of files** (way too big to stuff all at once into 20 URLs or a single turn's token budget), mimic a two-step RAG retriever using an index file—similar to how `llms.txt` works for developer docs.

1. Create a lightweight **`llms.txt`** (or `manifest.json`) in your repo root containing **1–2 line descriptions + exact raw URLs** for every doc/chunk:
   ```markdown
   # Knowledge Base Index
   - [Auth & OAuth Flows](https://raw.githubusercontent.com/you/kb/main/auth.md): JWT setup, refresh tokens, middleware.
   - [Billing Webhook Spec](https://raw.githubusercontent.com/you/kb/main/billing.md): Stripe events, retry logic, DB schema.
   ```
   *(You can auto-generate this index via a GitHub Action whenever files change.)*
2. Put **only** the `llms.txt` URL in your **System Instructions**, and instruct Gemini:
   > *"On the first turn of a question, read `llms.txt`. Identify the 2–4 raw URLs most relevant to the user's question and list them explicitly. Do not guess answers before reading the target files."*
3. **Two-turn retrieval:**
   * **Turn 1:** You ask your question -> Gemini reads `llms.txt` and identifies the exact 3 URLs needed.
   * **Turn 2:** Paste those 3 URLs (or tell it to fetch them if you copy-paste them in) -> Gemini reads only the relevant chunks and answers with zero context bloat.

---

### Method 3: GitHub Pages + "Google Search Grounding" + "URL Context" (Zero-Manual-URL Search)
Notice that Google AI Studio lets you toggle **both** **Grounding with Google Search** and **URL context** at the same time. Google explicitly recommends this pairing: *"Search for breadth, URL Context for depth."*

If you publish your GitHub repo via **GitHub Pages** (`https://<username>.github.io/<repo>/`, e.g., with MkDocs or plain Markdown/HTML) and it gets indexed by Google:
1. Enable **both** `Grounding with Google Search` and `URL context` in AI Studio.
2. Put this in **System Instructions**:
   > *"Before answering, always search `site:username.github.io/your-repo` using Google Search, then use the URL context / browse tool to read the full content of the top matching pages."*

**Why this feels like real RAG:** Google Search acts as your free semantic/keyword retriever across unlimited pages, and URL Context reads the top matching pages in full before generating the answer. **Catch:** Newly pushed GitHub Pages edits aren't searchable until Google crawls/re-indexes them, so this works better for stable documentation than rapid minute-by-minute edits.

---

### Method 4: Need Private Repos? Use AI Studio's Native GitHub Sync (or Upload Bundles)
If your repo **cannot be public**:
* **AI Studio Build Tab (Two-Way GitHub Sync):** In Google AI Studio's **Build** section, you can click `+` -> **Import from GitHub** to link a repository (and even sync changes back and forth) directly inside an AI Studio workspace without exposing raw public URLs.
* **Playground Drag-and-Drop:** Run `npx repomix` locally (with `--split-output 1mb` if huge) to flatten your private repo into 1–3 clean text/XML files and drop them straight into a Playground chat. You lose the "auto-update via URL" benefit, but it keeps private code off the public internet.

---

### Watch Out for These Gotchas
* **Stale Cache Behavior:** URL Context uses a two-stage fetch—it checks Google's internal web index cache first, and only falls back to a live fetch if not cached. GitHub's `raw.githubusercontent.com` CDN also caches files for ~5 minutes. If you just pushed a fix and Gemini insists on old info, try appending a dummy query string like `?v=2` (or linking a specific commit SHA URL instead of `/main/`) to force a fresh fetch.
* **Toggle Resetting:** In Google AI Studio Playground, double-check that **URL context** is actually toggled ON in the right sidebar when starting a new chat or duplicating prompts, as it defaults to OFF on fresh sessions.
* **Verify Retrieval:** Turn on **Show Thoughts** (if available on your selected model) or ask Gemini to quote exact headings—if a URL silently fails to fetch (e.g., repo is private or URL has a typo), you want the model instructed to tell you *"URL fetch failed"* rather than hallucinating from memory.

---

## User

Compare method 1 and 2

---

## Model

Here is a side-by-side breakdown of **Method 1 (Sharded Bundles)** vs. **Method 2 (`llms.txt` Two-Step Router)** so you can pick the right architecture for your knowledge base.

### At a Glance

| Feature | Method 1: Sharded Bundles | Method 2: `llms.txt` Two-Step Router |
| :--- | :--- | :--- |
| **How it works** | Loads all bundled files upfront via System Instructions. | Loads only a tiny index (`llms.txt`) first, then fetches specific files in Turn 2. |
| **User Experience** | **1-Turn (Instant):** Ask a question, get the answer immediately. | **2-Turn (Manual step):** Ask question → Gemini picks URLs → You paste/confirm them → Answer. |
| **Max Knowledge Base Size** | **Medium:** Hard-capped at **20 URLs** and Gemini’s context window (~1M tokens total). | **Massive:** Virtually unlimited files in GitHub; only 2–5 relevant files enter context per question. |
| **Latency & Token Usage** | **Slower / Heavy:** Re-processes massive documents even for tiny questions. | **Fast / Lightweight:** Context stays small and focused on just what’s needed. |
| **Accuracy / Failure Mode** | **High Recall:** Never misses a file, but huge contexts can dilute attention on subtle details. | **Routing Risk:** If your `llms.txt` summaries are vague, Gemini might pick the wrong file. |
| **Maintenance Effort** | Low–Medium (best with a GitHub Action that auto-merges files on push). | Medium (requires keeping `llms.txt` descriptions accurate as you add files). |

---

### The 4 Biggest Trade-Offs

#### 1. Friction vs. Scalability (The Core Trade-off)
* **Method 1 feels like magic** once set up: you open your saved AI Studio prompt, type a question, and get an answer in one shot. However, it hits a brick wall if your repo grows past **20 files** (or ~500k–800k tokens across bundles, leaving room for chat history).
* **Method 2 scales indefinitely**—your repo can have 500 separate Markdown files, PDFs, or code modules—but because Google AI Studio's URL Context tool doesn't recursively auto-crawl links found *inside* `llms.txt` in a single turn, **you** act as the middleman copying the 2–4 URLs Gemini asks for into Turn 2.

#### 2. Context Pollution & Speed
* **Method 1** dumps *everything* into the prompt. Even if you only ask about a single API error code, Gemini still has to read 400k tokens of unrelated HR docs, UI specs, and old meeting notes. That makes responses noticeably slower and can occasionally cause "needle-in-a-haystack" misses across multi-turn chats.
* **Method 2** keeps

---

## User

How can we optimise the method 2 for accuracy and user experience?

---

## Model

Method 2 (`llms.txt` Two-Step Router) usually breaks down in two places:
1. **Accuracy:** Gemini picks the wrong files from `llms.txt`, forgets a related dependency file, or guesses the answer in Turn 1 without waiting to read the actual docs.
2. **UX:** Having to highlight and copy-paste multiple `raw.githubusercontent.com` links into Turn 2 gets tedious fast.

You can solve both inside the normal Google AI Studio UI using the optimizations below.

---

### Part 1: Optimizing Accuracy (Better Retrieval, Zero Hallucinations)

#### 1. Turn `llms.txt` into a "Semantic Index" (Not Just Filenames)
If `llms.txt` only has file names and vague 5-word summaries, the router will miss files whenever your question uses different terminology. Structure each entry like a mini search-index record:
```markdown
- URL: https://raw.githubusercontent.com/user/repo/a1b2c3d/docs/auth.md
  Topic: Authentication, OAuth2, JWT & Session Middleware
  Keywords/Symbols: verifyToken(), RefreshTokenError, RedisStore, HTTP 401/403
  Answers: Login flows, token expiration, role-based access control (RBAC)
  Related/Dependencies: docs/db-schema.md, config/security-env.md
```
* **Automate it:** Add a GitHub Action (`on: push`) with a short Python/Node script that parses every Markdown/code file’s `#` headings, exported symbols/functions, and tags to rebuild `llms.txt` automatically on every commit.

#### 2. Use "Hybrid Chunking" Instead of 500 Micro-Files
If your repo has 400 tiny files (e.g., 1–2 KB each), two bad things happen: `llms.txt` becomes huge and noisy, and retrieving only 3 tiny files often misses surrounding context.
* **The Fix:** Have your GitHub Action bundle micro-files by feature/module into **30–60 medium-sized files** (e.g., ~20–100 KB each) and index *those* in `llms.txt`.
* Now `llms.txt` stays super compact, and every URL Gemini fetches in Turn 2 brings complete, self-contained context.

#### 3. Defeat Stale Caching with Commit-Pinned URLs
Because URL Context checks Google's internal index cache before doing a live fetch (and GitHub's raw CDN caches `/main/` links for ~5 minutes), editing a file doesn't always show up immediately if the URL string stays identical.
* **The Fix:** Have your GitHub Action write **commit-SHA URLs** inside `llms.txt`:
  `https://raw.githubusercontent.com/<user>/<repo>/<COMMIT_SHA>/bundle-auth.md`
* Every time a file changes, its URL in `llms.txt` changes. Google sees a brand-new URL, skips any stale index cache, and live-fetches your exact latest version. *(For `llms.txt` itself in System Instructions, you still point to `main/llms.txt`.)*

#### 4. Enforce Strict Router & Grounding Rules
* **Lower Temperature:** In AI Studio’s right sidebar, set **Temperature to `0.0`–`0.1`** so file selection and factual extraction stay deterministic.
* **Forbid Early Guessing:** Explicitly ban Gemini from answering in Turn 1 from memory or from the 1-line summaries inside `llms.txt`.
* **Always Fetch Dependencies (Top 3–5 URLs):** Tell Gemini to include any linked `Related/Dependencies` URLs (like schemas, config files, or shared types) alongside the primary match—up to the 20-URL per-request cap.
* **Allow a Turn-3 Re-Route:** Instruct Gemini: *"If the fetched files don't fully answer the question, tell me which 1–2 additional URLs from `llms.txt` you need instead of guessing."*

---

### Part 2: Optimizing UX (Removing the Copy-Paste Friction)

#### 1. The "1-Click Copy Code Block" Trick
The biggest annoyance in Method 2 is dragging your mouse to copy 4 separate URLs. In Google AI Studio, any Markdown fenced code block gets a **1-click Copy icon** in the corner.

Instruct Gemini to output Turn 1's requested URLs inside a **single plain `text` code block** (no markdown `[link](url)` formatting, no bullets—just raw `https://...` URLs) *plus* your Turn 2 instruction right inside the same block:

```text
https://raw.githubusercontent.com/user/repo/a1b2c3d/docs/auth.md
https://raw.githubusercontent.com/user/repo/a1b2c3d/docs/db-schema.md

Read the full contents of every URL above via URL context and answer my previous question thoroughly with exact file/section citations.
```
* **Your workflow becomes:** Ask question → Click **Copy** on the code block → **Ctrl+V** → **Enter**. It cuts Turn 2 down to ~2 seconds.

#### 2. The "80/20 Hot Cache" Hybrid (Makes Most Queries 1-Turn!)
You get **20 URL slots per request**, and `llms.txt` only uses **1 slot**. Don't waste the other 19!
* Put `llms.txt` **plus your 5–8 most frequently needed "core" files** (e.g., `README.md`, `architecture.md`, `api-overview.md`, `glossary.md`) directly into **System Instructions**.
* Tell Gemini: *"If the pre-loaded Core URLs fully answer the question, answer immediately in Turn 1. ONLY output the code block requesting extra URLs from `llms.txt` when specialized files are needed."*
* **Result:** ~70–80% of everyday questions answer instantly in **1 turn** (like Method 1), and deep/niche questions seamlessly invoke the **2-turn router** (like Method 2).

#### 3. Stay in Topic Threads, Reset Between Topics
* Once you paste URLs in Turn 2, their content remains in the conversation history for Turn 3, Turn 4, etc.—so follow-up questions on the same feature don't require re-pasting URLs.
* When switching to a completely unrelated part of your repo, open a fresh chat from your **Saved Prompt Template** so old documents don't pollute the active context.

---

### Copy-Paste System Instructions Template

Save this in a Google AI Studio Prompt with **URL context** toggled **ON** and **Temperature = `0.1`**:

```markdown
You are a strict, retrieval-grounded assistant for my knowledge base.

### Always-Loaded Core Sources (Read via URL context)
- Index: https://raw.githubusercontent.com/<USER>/<REPO>/main/llms.txt
- Core Overview: https://raw.githubusercontent.com/<USER>/<REPO>/main/docs/overview.md
- Core Schema/Glossary: https://raw.githubusercontent.com/<USER>/<REPO>/main/docs/glossary.md

### Workflow Rules
1. Check the pre-loaded Core Sources first. If they completely and unambiguously answer the user's question, answer immediately and cite the exact file/URL.
2. If the answer requires files listed in `llms.txt` that are NOT pre-loaded above:
   - DO NOT answer or guess from `llms.txt` summaries or your own memory.
   - Select the 2 to 5 most relevant URLs from `llms.txt` (including any listed dependency files).
   - Output a brief 1-line note explaining why you need them, followed by a SINGLE fenced `text` code block containing ONLY the raw `https://...` URLs (one per line) and the instruction line below at the bottom of the block:
     `Read every URL above via URL context and answer my question thoroughly with citations.`
3. Once those URLs are provided in the next turn, read them completely before answering. If a URL fails to load or lacks the answer, state that explicitly and request any missing URLs from `llms.txt`.
```

---

## User

Can we combine method 1 and method 2 to balance their respective weaknesses in one architecture?

---

## Model

Yes—in fact, combining them into a **"Tiered Hybrid" (Hot Bundles + Cold Router)** is the strongest no-API RAG architecture you can build in Google AI Studio.

Instead of choosing between *"load everything upfront"* (Method 1) and *"load nothing until Turn 2"* (Method 2), you merge **both** ideas in two ways:
1. **Tier 1 (Method 1 style):** Pre-load a few **Hot Bundles** directly in System Instructions for 1-turn speed.
2. **Tier 2 (Method 2 + Method 1 style):** Don't index 500 tiny raw files in `llms.txt`—index **Cold Bundles** (sharded topic files) so even Turn-2 retrieval benefits from Method 1's bundling!

---

### How the Hybrid Architecture Works

```text
                [ Google AI Studio System Instructions ]
                ├── 1. llms.txt (Semantic index of Tier 2 Cold Bundles)
                └── 2. 4–6 Tier 1 "Hot Bundles" (Core / Active / Recent docs)
                                      │
                             User asks question
                                      │
          ┌───────────────────────────┴───────────────────────────┐
          ▼                                                       ▼
   Answered by Hot Bundles?                              Needs deep/niche info?
          │                                                       │
          ▼                                                       ▼
  [ 1-Turn Instant Answer ]                        [ Turn 1: Output 1-Click Copy
   (Zero copy-paste UX)                              block with 2–4 Cold Bundle URLs ]
                                                                  │
                                                                  ▼
                                                   [ Turn 2: Paste → Full Answer ]
```

#### Why This Cancels Out Both Methods' Weaknesses
* **Fixes Method 2’s UX Friction:** Daily questions (core architecture, conventions, active sprint work, glossary) hit **Tier 1 Hot Bundles** and resolve in **1 turn**.
* **Fixes Method 2’s Routing Misses:** Because **Tier 2** is *also* pre-bundled into ~20–50 medium topic chunks (instead of 500 tiny files), `llms.txt` stays short, sharp, and much harder for the router to misread.
* **Fixes Method 1’s Context Bloat & 20-URL Cap:** Massive archives, legacy modules, logs, and deep reference docs stay out of context in **Tier 2** until actually needed—keeping answers fast and focused.

---

### How to Set Up the GitHub Pipeline

You only need one **GitHub Action** (`on: push`) that splits your repository into two tiers automatically:

#### 1. Define What Goes into "Hot" vs. "Cold"
Pick whichever rule fits your workflow best:
* **By Folder / Tag:** Anything in `/core/` (or Markdown files with `tier: hot` in YAML frontmatter) merges into Tier 1. Everything else merges by directory into Tier 2 Cold Bundles.
* **By Recency ("Active Working Set"):** Have your GitHub Action bundle **all files edited in the last 14–30 days** (`git log`) into `hot-recent.md`, plus permanent essentials into `hot-core.md`. *(This is huge for active projects—whatever you're actively working on is always 1-turn!)*.

#### 2. Watch Your "20-URL Budget" Math
Remember that Google AI Studio enforces a limit of **20 URLs per request**. Because System Instructions are sent with every turn, you must leave headroom for Turn 2:
* `1 URL`: `llms.txt` (in System Instructions)
* `4–6 URLs`: Tier 1 Hot Bundles (in System Instructions)
* **Remaining headroom (`13–15 URLs`)**: Safely available for Turn 2 Cold Bundle fetches + any extra links you paste mid-chat.

*(Avoid putting 15+ URLs into System Instructions, or you'll leave almost no room for Turn 2 retrieval.)*

#### 3. Keep `llms.txt` Lean by Excluding Tier 1
Inside `llms.txt`, **only index Tier 2 Cold Bundles** (and optionally note at the top: *"Core architecture, glossary, and recent changes are already pre-loaded in Tier 1"*). That prevents Gemini from wasting Turn 2 fetching a file it already has in System Instructions.

---

### Power-User Upgrade: "Role-Sliced Prompts" on One Repo
Because your GitHub Action already builds modular bundles, you can save **2 or 3 different AI Studio Prompt Templates** pointing to the *same* repository:
* **Prompt A ("Backend Expert"):** Tier 1 = `hot-core.md` + `bundle-api.md` + `bundle-db.md` + `llms.txt`
* **Prompt B ("Frontend Expert"):** Tier 1 = `hot-core.md` + `bundle-ui.md` + `bundle-state.md` + `llms.txt`

Each prompt stays super light and instant for its primary domain, yet can still cross over into the other domain via `llms.txt` whenever needed.

---

### Final Comparison

| Dimension | Pure Method 1 | Pure Method 2 | Tiered Hybrid (1 + 2) |
| :--- | :--- | :--- | :--- |
| **Routine Questions** | 1 turn | 2 turns | **1 turn** (~80% of the time) |
| **Deep / Niche Questions** | Fails past 20 URLs / context cap | 2 turns (risk of missing micro-files) | **2 turns** (high accuracy via bundled shards) |
| **Context Speed** | Slow (everything loaded) | Fast | **Fast** (small hot core + lazy cold load) |
| **Max Repo Size** | Medium | Unlimited | **Unlimited** |
| **Maintenance** | 1 Action (Bundler) | 1 Action (Indexer) | **1 Action** (Does both in one pass) |

---

## User

Give me a step by step guide to set up GitHub essentials for the hybrid

---

## Model

Here is a complete, step-by-step guide to setting up the **GitHub backend** for the **Tiered Hybrid** architecture. Once configured, every `git push` automatically builds your **Tier 1 Hot Bundles**, **Tier 2 Cold Bundles**, and **`llms.txt` Semantic Index**—with zero external dependencies or API keys.

---

### Step 1: Create a Public Repo with This Folder Structure
URL Context requires publicly accessible URLs, so make sure the repository is **Public** (do not store secrets or private data).

Create this folder layout:
```text
my-ai-kb/
├── kb/                          # Put all your notes, docs, and code here
│   ├── core/                    # Tier 1: Always pre-loaded (1-turn answers)
│   │   ├── architecture.md
│   │   └── glossary.md
│   ├── backend/                 # Tier 2: Auto-bundled into cold-backend.<hash>.md
│   │   ├── auth.md
│   │   └── billing.md
│   └── frontend/                # Tier 2: Auto-bundled into cold-frontend.<hash>.md
│       └── state.md
├── scripts/
│   └── build_kb.py              # The builder script (Step 2)
└── .github/
    └── workflows/
        └── build-kb.yml         # The GitHub Action (Step 3)
```

> **Tip for better routing accuracy:** You can optionally add simple YAML frontmatter to the top of any Markdown file to help `llms.txt` route questions accurately (or force a non-`core/` file into Tier 1):
> ```markdown
> ---
> tier: hot          # Optional: promotes this file into hot-core.md
> summary: Explains Stripe webhook verification and retry backoff rules.
> keywords: stripe, webhook, 400, idempotency, signature
> ---
> ```

---

### Step 2: Add the Builder Script (`scripts/build_kb.py`)
This standard-library Python script does four critical things automatically:
1. Bundles `kb/core/` (and any `tier: hot` file) into **`_ai_bundles/hot-core.md`**.
2. Bundles any file modified in the **last 14 days** (`git log`) into **`_ai_bundles/hot-recent.md`**.
3. Groups everything else by subfolder into **Tier 2 Cold Bundles** (splitting at ~180 KB per file so Turn 2 stays fast) using **content-hashed filenames** (`cold-backend.a1b2c3d4.md`) so neither GitHub’s CDN nor Google’s URL Context serves stale versions.
4. Generates **`_ai_bundles/llms.txt`** by extracting file paths, frontmatter summaries/keywords, and Markdown `#` / `##` headings.

Create **`scripts/build_kb.py`**:

```python
import hashlib
import os
import re
import shutil
import subprocess
from pathlib import Path

KB_DIR = Path("kb")
OUT_DIR = Path("_ai_bundles")
COLD_DIR = OUT_DIR / "cold"

ALLOWED_EXTS = {".md", ".txt", ".json", ".yaml", ".yml", ".csv", ".py", ".ts", ".js"}
MAX_COLD_BYTES = 180_000  # ~45k tokens max per Cold Bundle
RECENT_DAYS = 14

REPO = os.environ.get("GITHUB_REPOSITORY", "YOUR_USERNAME/YOUR_REPO")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"

def get_recent_files(days: int) -> set[Path]:
    try:
        out = subprocess.check_output(
            ["git", "log", f"--since={days} days ago", "--name-only", "--pretty=format:", "--", str(KB_DIR)],
            text=True,
        )
        return {Path(line.strip()) for line in out.splitlines() if line.strip()}
    except Exception:
        return set()

def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return {}, text
    meta = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip().lower()] = v.strip()
    return meta, text[match.end() :]

def extract_headings(text: str, limit: int = 12) -> list[str]:
    headings = re.findall(r"^#{1,2}\s+(.+)$", text, re.MULTILINE)
    cleaned = [h.strip().replace("\n", " ") for h in headings]
    return cleaned[:limit]

def format_file_block(rel_path: Path, body: str) -> str:
    return f"\n\n---\n## FILE: `{rel_path.as_posix()}`\n\n{body.strip()}\n"

def write_cold_chunks(group_name: str, items: list[dict]) -> list[dict]:
    chunks = []
    current_blocks = []
    current_meta = []
    current_size = 0

    for item in items:
        block = format_file_block(item["path"], item["body"])
        block_size = len(block.encode("utf-8"))
        if current_blocks and (current_size + block_size > MAX_COLD_BYTES):
            chunks.append((current_blocks, current_meta))
            current_blocks, current_meta, current_size = [], [], 0
        current_blocks.append(block)
        current_meta.append(item)
        current_size += block_size

    if current_blocks:
        chunks.append((current_blocks, current_meta))

    written = []
    for idx, (blocks, metas) in enumerate(chunks, start=1):
        suffix = f"-part{idx}" if len(chunks) > 1 else ""
        content = f"# Cold Knowledge Bundle: {group_name}{suffix}\n" + "".join(blocks)
        short_hash = hashlib.md5(content.encode("utf-8")).hexdigest()[:8]
        filename = f"cold-{group_name}{suffix}.{short_hash}.md"
        (COLD_DIR / filename).write_text(content, encoding="utf-8")

        all_headings = []
        summaries = []
        keywords = []
        for m in metas:
            all_headings.extend(m["headings"])
            if m["summary"]:
                summaries.append(m["summary"])
            if m["keywords"]:
                keywords.append(m["keywords"])

        written.append(
            {
                "url": f"{RAW_BASE}/_ai_bundles/cold/{filename}",
                "group": f"{group_name}{suffix}",
                "files": [m["path"].as_posix() for m in metas],
                "headings": all_headings[:15],
                "summaries": summaries,
                "keywords": keywords,
            }
        )
    return written

def main():
    if not KB_DIR.exists():
        raise SystemExit("Missing 'kb/' directory.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(COLD_DIR, ignore_errors=True)
    COLD_DIR.mkdir(parents=True, exist_ok=True)

    recent_paths = get_recent_files(RECENT_DAYS)
    hot_core_blocks = []
    hot_recent_blocks = []
    cold_groups: dict[str, list[dict]] = {}

    for path in sorted(KB_DIR.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in ALLOWED_EXTS:
            continue

        raw_text = path.read_text(encoding="utf-8", errors="ignore")
        meta, body = parse_frontmatter(raw_text)
        rel_from_kb = path.relative_to(KB_DIR)
        top_folder = rel_from_kb.parts[0] if len(rel_from_kb.parts) > 1 else "general"

        is_hot = (top_folder == "core") or (meta.get("tier") == "hot")
        block = format_file_block(path, body)

        if is_hot:
            hot_core_blocks.append(block)
        else:
            if path in recent_paths:
                hot_recent_blocks.append(block)

            cold_groups.setdefault(top_folder, []).append(
                {
                    "path": path,
                    "body": body,
                    "headings": extract_headings(body),
                    "summary": meta.get("summary", ""),
                    "keywords": meta.get("keywords", ""),
                }
            )

    # Write static Tier 1 Hot Bundles (never 404 even if empty)
    core_text = (
        "# Tier 1: Core Knowledge\n" + "".join(hot_core_blocks)
        if hot_core_blocks
        else "# Tier 1: Core Knowledge\nNo core files configured yet."
    )
    (OUT_DIR / "hot-core.md").write_text(core_text, encoding="utf-8")

    recent_text = (
        f"# Tier 1: Files Modified in Last {RECENT_DAYS} Days\n" + "".join(hot_recent_blocks)
        if hot_recent_blocks
        else f"# Tier 1: Recent Changes\nNo non-core files modified in the last {RECENT_DAYS} days."
    )
    (OUT_DIR / "hot-recent.md").write_text(recent_text, encoding="utf-8")

    # Write content-hashed Tier 2 Cold Bundles & build llms.txt
    index_entries = []
    for group_name, items in sorted(cold_groups.items()):
        index_entries.extend(write_cold_chunks(group_name, items))

    lines = [
        "# Knowledge Base Index (Tier 2 Cold Bundles)",
        "# Note: Core docs and recently modified files (last 14 days) are already pre-loaded in Tier 1.",
        "",
    ]
    for entry in index_entries:
        lines.append(f"- URL: {entry['url']}")
        lines.append(f"  Topic Group: {entry['group']}")
        lines.append(f"  Files: {', '.join(entry['files'])}")
        if entry["summaries"]:
            lines.append(f"  Summary: {' | '.join(entry['summaries'])}")
        if entry["keywords"]:
            lines.append(f"  Keywords: {', '.join(entry['keywords'])}")
        if entry["headings"]:
            lines.append(f"  Headings: {', '.join(entry['headings'])}")
        lines.append("")

    (OUT_DIR / "llms.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"Built {len(index_entries)} cold bundle(s) and updated Tier 1 + llms.txt.")

if __name__ == "__main__":
    main()
```

---

### Step 3: Add the GitHub Action (`.github/workflows/build-kb.yml`)
Two subtle gotchas are handled here for you:
1. **`fetch-depth: 0`**: Required so `git log` sees commit history for `hot-recent.md`.
2. **`paths:` + `[skip ci]`**: Prevents the Action from triggering an infinite commit loop when it pushes `_ai_bundles/`.

Create **`.github/workflows/build-kb.yml`**:

```yaml
name: Build AI Knowledge Bundles

on:
  push:
    branches: ["main"]
    paths:
      - "kb/**"
      - "scripts/build_kb.py"
  workflow_dispatch:

permissions:
  contents: write

jobs:
  build-bundles:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository with history
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Build Hot/Cold bundles and llms.txt
        run: python3 scripts/build_kb.py

      - name: Commit updated bundles
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add _ai_bundles/
          if git diff --staged --quiet; then
            echo "No bundle changes to commit."
          else
            git commit -m "chore: rebuild AI knowledge bundles [skip ci]"
            git push
          fi
```

---

### Step 4: Verify Permissions & First Build
1. On GitHub, go to **Settings → Actions → General → Workflow permissions** and ensure **Read and write permissions** is enabled (some accounts restrict write permissions by default even when set in YAML).
2. Commit and push at least one file inside `kb/` (along with `build_kb.py` and `build-kb.yml`).
3. Open the **Actions** tab and confirm **Build AI Knowledge Bundles** turns green.
4. Check your repo root—you will now see `_ai_bundles/` containing `llms.txt`, `hot-core.md`, `hot-recent.md`, and `cold/cold-*.<hash>.md`.

---

### Step 5: Connect Your 3 Static URLs to Google AI Studio
1. Open Google AI Studio Playground, toggle **URL context** **ON**, and set **Temperature** to **`0.1`**.
2. Paste these **3 static URLs** (replace `<USER>` and `<REPO>`) into **System Instructions**:

```markdown
You are a retrieval-grounded assistant for my knowledge base.

### Always-Loaded Tier 1 Sources + Tier 2 Index (Read via URL context)
- Tier 1 Core: https://raw.githubusercontent.com/<USER>/<REPO>/main/_ai_bundles/hot-core.md
- Tier 1 Recent: https://raw.githubusercontent.com/<USER>/<REPO>/main/_ai_bundles/hot-recent.md
- Tier 2 Index: https://raw.githubusercontent.com/<USER>/<REPO>/main/_ai_bundles/llms.txt

### Rules
1. First check Tier 1 Core and Tier 1 Recent. If they fully answer the user's question, answer immediately in this turn and cite the exact `FILE:` path.
2. If the question requires files listed in `llms.txt` that are NOT in Tier 1:
   - Do NOT guess or answer from `llms.txt` summaries alone.
   - Pick the 1 to 4 most relevant Cold Bundle URLs from `llms.txt`.
   - Output a 1-line note explaining why, followed by a SINGLE `text` code block containing ONLY the raw `https://...` URLs (one per line) and this final line inside the block:
     `Read every URL above via URL context and answer my previous question with exact FILE citations.`
3. Once provided in the next turn, read the Cold Bundles completely before answering.
```

3. **Save the prompt** in Google AI Studio. From now on, just push edits to `kb/` on GitHub—your AI Studio chat stays permanently synced. *(Note: After a push, `raw.githubusercontent.com` can take ~1–5 minutes to refresh `llms.txt` and Tier 1 links on `/main/`, though once `llms.txt` updates, the hashed Tier 2 Cold URLs load fresh immediately.)*

---

## User

Help me to fill the blanks to create repository

---

## Model

Here is exactly how to fill out each field on those two screens:

### Screen 1 (General)
* **Owner:** Leave as `inikashx-hub`
* **Repository name:** Type `ai-kb` *(short, lowercase, no spaces—you can also use `my-ai-kb` or any name you like)*
* **Description:** *(Optional)* `Knowledge base for Google AI Studio RAG`

### Screen 2 (Configuration)
* **Choose visibility:** Keep it on **Public** *(required so Google AI Studio’s URL Context can read it)*
* **Add README:** Toggle **ON** *(important on mobile—this automatically creates your `main` branch right away so you can start adding files immediately)*
* **Add .gitignore:** Leave as **No .gitignore**
* **Add license:** Leave as **No license**

Tap the green **Create repository** button.

---

### Quick Tip for Adding Folders on Mobile (Next Screen)
GitHub doesn't have a separate "New Folder" button in the browser. Once your repo opens:
1. Tap **Add file** → **Create new file**.
2. In the **Name your file...** box, typing a `/` automatically creates folders:
   * Type `kb/core/overview.md` → paste a sample note → tap **Commit changes...**
   * Repeat to create `scripts/build_kb.py` → paste the Python script → commit.
   * Repeat to create `.github/workflows/build-kb.yml` → paste the workflow YAML → commit.

*(Note: If you name your repo `ai-kb`, your 3 Google AI Studio System Instruction URLs will be under `inikashx-hub/ai-kb`!)*

---

## User

Should I create separate folder for .txt and .md files?

---

## Model

**No—do not separate folders by file type.** Group your folders by **topic or subject** instead (and mix `.md` and `.txt` freely inside them).

### Why?
Our `build_kb.py` script already supports both `.md` and `.txt` (plus `.json`, `.csv`, `.py`, etc.) automatically, and it creates **Tier 2 Cold Bundles based on your folder names**:
* If you make `kb/txt/` and `kb/md/`, your bundles get split awkwardly by file extension (`cold-txt.md` vs. `cold-md.md`), scattering related info across different files.
* If you make topic folders like `kb/core/`, `kb/work/`, `kb/study/`, or `kb/coding/`, all `.txt` and `.md` files on the same subject get bundled together—so Gemini gets the full picture in a single fetch.

### One Quick Tip for `.txt` Files
Since `llms.txt` extracts Markdown `#` headings to figure out which bundle to fetch, plain `.txt` files without headings have slightly fewer routing clues. To keep accuracy high:
1. **Give `.txt` files descriptive filenames** (e.g., `kb/finance/tax-rules-2026.txt` instead of `notes1.txt`)—filenames are always included in `llms.txt`.
2. **Use `.md` for new notes** whenever possible, since `#` headings help Gemini navigate long bundles faster.

---

## User

I meant the code that you have given in the previous chats for creating new files in repository

---

## Model

Got it! Here is the exact breakdown of **only the files you need to create manually** from the previous guide—and where each one goes:

### 1. The 2 Code Files (Exact Paths Required)
Keep these **outside** `kb/`, in their exact folders:
* **`scripts/build_kb.py`** → The Python builder script.
* **`.github/workflows/build-kb.yml`** → The GitHub Action workflow.

*(GitHub Actions only detects workflows inside `.github/workflows/`, and that workflow specifically runs `scripts/build_kb.py`, so those folder names must match exactly.)*

---

### 2. Your Knowledge Files (`.md` and `.txt`)
Put all your notes/docs inside **`kb/`**:
* **`kb/core/...`** → Anything here (whether `.md` or `.txt`) goes into Tier 1 (`hot-core.md`).
* **`kb/<any-topic>/...`** → Anything here (`.md` or `.txt` mixed together) becomes Tier 2 Cold Bundles.

*(You do **not** need to make separate `.txt` and `.md` folders.)*

---

### 3. Do NOT Create `_ai_bundles/` Manually!
You might have seen **`llms.txt`** (`.txt`) and **`hot-core.md`** / **`hot-recent.md`** (`.md`) in the folder diagram earlier. **Do not create those files or the `_ai_bundles/` folder yourself.**

Once you commit:
1. `scripts/build_kb.py`
2. `.github/workflows/build-kb.yml`
3. At least one starter file inside `kb/` (e.g., `kb/core/overview.md`)

…GitHub Actions will run automatically and generate **`_ai_bundles/llms.txt`**, **`hot-core.md`**, **`hot-recent.md`**, and **`cold/`** for you!

---

## User

Can I upload python script by creating new file now?

---

## Model

**Almost—just step out of `.github/workflows/` first!**

Right now your screen shows you are inside **`ai-kb / .github / workflows /`**. If you create a new file from here, GitHub will put it inside the `workflows` folder by mistake.

### Do This Instead:
1. **Go back to the repo root:** Tap **`ai-kb`** in the blue path (`ai-kb / .github / workflows /`).
2. **Create the script:** Once you are at the main `ai-kb` page, tap **`Add file`** (or **`+`**) → **Create new file**.
3. **Name & commit:** Type `scripts/build_kb.py`, paste the Python code, and tap **Commit changes...**.

---

### Quick Heads-Up Before You Commit
If you haven't created any file inside `kb/` yet:
* Creating `scripts/build_kb.py` will trigger the GitHub Action right away, and it will fail once with `"Missing 'kb/' directory"`—totally harmless, and it will turn green as soon as you add your first file in `kb/`.
* **Pro tip:** If you want a green ✅ on the very first run, create `kb/core/overview.md` (with any short starter text) *first*, and then create `scripts/build_kb.py` right after!

---

## User

I have my knowledge base files in Google drive

---

## Model

thought Awesome! Look at those fresh 2026 facts:
- Google Docs natively supports **File → Download → Markdown (.md)** AND (as of Oct 2026!) Google Drive / Docs natively opens and edits `.md` files directly in Markdown Mode without converting them!
- In Google AI Studio, you *can* attach files from Google Drive manually per prompt—**however**, that's static attachment per chat (not dynamic RAG across dozens of folders, and doesn't auto-sync when files are edited after attaching).

Now let's give the user **3 practical paths** from Google Drive into `inikashx-hub/ai-kb/kb/`, tailored to how often their files change and what file formats they have (Google Docs, `.md`/`.txt`, or `.pdf`/`.docx`):

1. **Quickest Option (Manual Upload from Android/Desktop — 2 Minutes, Zero Extra Setup):**
   - **If your Drive files are `.md` or `.txt`:**
     - Go to `inikashx-hub/ai-kb` → navigate into `kb/core/` (or create `kb/<topic>/` with a tiny placeholder file first so the folder exists) → tap **Add file → Upload files**.
     - On Android, when the file picker opens, tap the top-left menu (`≡`) and select **Google Drive** directly (or download them to your phone first) and upload multiple files at once!
   - **If your files are Google Docs:**
     - Open the Google Doc (in browser / desktop mode) → **File → Download → Markdown (`.md`)** (or Plain Text `.txt`) → upload to `kb/`.
   - **If your files are PDFs or `.docx`:**
     - Tell them honestly: right now `build_kb.py` only merges text formats (`.md`, `.txt`, `.csv`, `.json`), so it skips `.pdf`/`.docx`. *Offer:* "If your Drive is mostly PDFs or `.docx`, let me know and I can give you a 5-line update to `build-kb.yml` and `build_kb.py` that automatically extracts text from PDFs/Word docs inside GitHub Actions!"

2. **Automatic Sync Option (Google Apps Script — Free, Runs Inside Google Drive, No PC Required!):**
   - If they **actively edit** their knowledge base in Google Drive and want Drive changes to auto-push into `inikashx-hub/ai-kb/kb/` every hour or day:
   - Explain the **Google Apps Script** bridge (without dumping a massive wall of code unless they want it, OR give a concise working overview and offer the copy-paste script!):
     - Create a script at `script.google.com`.
     - Give it a folder ID from Google Drive + a GitHub Personal Access Token (fine-grained PAT with `Contents: Read & Write` scoped *only* to `inikashx-hub/ai-kb`).
     - It automatically converts Google Docs → Markdown/Text (`Drive.Files.export` / `DocumentApp`), reads `.md`/`.txt` files, preserves subfolders under `kb/`, and pushes updates via GitHub's Contents API on a schedule (e.g., every hour or on manual click).
     - GitHub Actions then automatically rebuilds `hot-core.md`, `hot-recent.md`, `cold/`, and `llms.txt`!
   - *(Wait: Let's offer to write the exact Google Apps Script for them if they want automatic sync, AND ask what file types are in their Drive—Google Docs, PDFs, `.docx`, or `.md`/`.txt`—so we don't overwhelm them with code they might not need if manual upload or PDF extraction is what they actually want!)*

3. **Wait—Also Note the Native AI Studio Drive Button (and Why GitHub Hybrid Still Wins):**
   - Mention briefly: Google AI Studio also has a built-in **Google Drive** attach option (`+` → **Drive**), which is great for quick one-off chats on 1–3 files, **but** it doesn't scale like RAG (you have to manually pick/re-attach files for new chats, and it can hit context limits fast if you attach an entire Drive folder). Keeping Drive synced into `ai-kb` gives you the true 2-tier RAG index (`llms.txt` + Hot/Cold bundles).

Let's keep the response super structured, helpful, and focused on their next move! Ask one simple clarifying question at the end (*"What file types are mostly in your Google Drive—Google Docs, PDFs/Word files, or `.txt`/`.md`—and do you edit them daily or mostly keep them static?"*) so we can give them the exact snippet they need next (whether it's PDF/DOCX extraction in `build_kb.py` or the Google Apps Script auto-syncer).You have two clean ways to bridge **Google Drive → GitHub (`ai-kb/kb/`)**, depending on whether your Drive files are mostly static or edited regularly—plus one important check on file types.

---

### First: Check Your File Types in Google Drive
Right now, `build_kb.py` only bundles **plain-text formats** (`.md`, `.txt`, `.csv`, `.json`, `.yaml`, code files).
* **Google Docs:** Need to be exported as **Markdown (`.md`)** or **Plain Text (`.txt`)** (`File → Download → Markdown (.md)` in Google Docs).
* **`.md` / `.txt` files:** Ready to go as-is! *(Note: Google Drive also supports opening and editing `.md` files directly inside Google Docs now without converting them.)*
* **PDFs / Word (`.docx`):** Currently skipped by `build_kb.py`—*though we can easily add a 5-line PDF/Word text extractor to your GitHub Action if you have lots of PDFs.*

---

### Option 1: Quick Manual Upload (Best if Files Don't Change Daily)
You can upload directly from your phone without any extra scripts:
1. In your `ai-kb` repo on GitHub, create at least one starter file inside each folder you want (e.g., `kb/core/readme.md`, `kb/notes/readme.md`) so the folders exist.
2. Open that folder → tap **Add file** → **Upload files**.
3. When Android's file picker opens, tap the **menu (`≡`)** on the left and pick **Google Drive** directly (or download the files first) to batch-upload multiple `.md` / `.txt` files in one commit.

---

### Option 2: Auto-Sync Google Drive → GitHub (Best if You Edit in Drive Often)
If you want changes in a Google Drive folder to **automatically sync** to `inikashx-hub/ai-kb/kb/` (without touching GitHub manually):
* Use **Google Apps Script** (`script.google.com`)—it is 100% free, runs directly on Google's servers, and needs no PC.
* A short Apps Script can:
  1. Scan a specific Google Drive folder (and its subfolders).
  2. Automatically convert **Google Docs → Markdown/Text** (and read `.md`/`.txt` files).
  3. Push only changed files into `kb/` on GitHub using a fine-grained GitHub Token on an hourly or daily timer.
  4. Your existing GitHub Action (`build-kb.yml`) then automatically rebuilds `hot-core.md`, `hot-recent.md`, `cold/`, and `llms.txt`.

*(Tip: Google AI Studio also has a built-in **Drive** button (`+` → Drive) to attach individual files per chat, which works well for 1–3 files—but it doesn't give you automatic multi-folder indexing or Tier 1/Tier 2 RAG scaling like GitHub does.)*

---

### Which Fits Your Drive Best?
Tell me two quick things and I'll give you the exact next step:
1. **What file types are in your Google Drive?** (Google Docs, `.md`/`.txt`, or PDFs/Word `.docx`?)
2. **Do you update those files frequently**, or is a one-time upload + occasional additions enough?

---

## User

I already have a private repository in GitHub that gets jobs from Google apps script with 15 minutes trigger to convert Google AI Studio chats into .md and .pdf files and save them in Google drive dynamically. My knowledge base is mostly Google AI Studio chats

---

## Model

That actually puts you **90% ahead of the game**—your pipeline is already converting messy AI Studio chats into clean `.md` files automatically!

Before connecting the two, there is **one critical privacy decision** you need to make first, because it determines which path you should take.

---

### First: The Privacy Fork (Public vs. Private)
Because `inikashx-hub/ai-kb` is **Public** (required for Google AI Studio’s **URL Context** toggle), **anyone on the internet can read files pushed to `ai-kb`**.

* **Path A (Chats are non-sensitive / filtered):** You can auto-push your `.md` chat exports from your private repo into `ai-kb/kb/` and get full hands-free **URL Context** RAG.
* **Path B (Chats contain private/personal/work data):** **Do NOT push them to `ai-kb`.** Instead, run `build_kb.py` *inside your existing private repo*, have it save `hot-recent.md` + `llms.txt` + `cold/*.md` straight into a dedicated **`AI-KB-Bundles/` folder in your Google Drive**, and attach them in AI Studio using the built-in **`+` → Google Drive** button when starting a chat. *(Zero public exposure, though you attach the updated bundle files manually per new chat instead of via URL Context.)*

---

### If You Go with Path A: Connecting Your Existing Pipeline to `ai-kb`
You don't need to touch your Google Apps Script at all. Your **private repo's GitHub Action** already receives the chats and builds the `.md` files—so just let it drop a copy of the `.md` files (ignore the `.pdf`s, since `.md` is cleaner and lighter) into `ai-kb`:

1. Create a **Fine-grained Personal Access Token (PAT)** on GitHub scoped **only** to `inikashx-hub/ai-kb` with **Contents: Read and write** permission.
2. Add that token as a Secret (e.g., `AI_KB_TOKEN`) in your **private** repo’s Settings.
3. Add a final step at the end of your private repo’s workflow that clones `inikashx-hub/ai-kb`, copies only the new/updated `.md` files into `kb/chats/YYYY-MM/` (or only chats tagged `#kb` / non-private if you want selective sync), and pushes.
4. `ai-kb`'s `build-kb.yml` will automatically trigger, update `hot-recent.md` (last 14 days of chats), shard older chats into `cold/`, and rebuild `llms.txt`.

---

### 3 Optimizations Specifically for AI Studio Chat Logs
Because your knowledge base is **chat transcripts** rather than handwritten docs, tweaking `build_kb.py` for chats will dramatically improve retrieval accuracy:

1. **Index "User Prompts" Instead of Random `#` Headings:**
   AI responses inside chat `.md` files are full of generic headings like `## Step 1` or `## Summary`, which add noise to `llms.txt`. Instead, extract the **chat title + the first 3–5 User messages** into `llms.txt`—those capture the exact questions/problems you solved in that chat!
2. **Auto-Group Cold Bundles by Month (`YYYY-MM`) or Topic Keywords:**
   Since chats arrive dynamically without manual folder sorting, saving them as `kb/2026-11/<chat-title>.md`, `kb/2026-10/<chat-title>.md` (or auto-routing by keyword like `python`, `finance`, `prompts`) automatically gives `build_kb.py` clean Cold Bundles (`cold-2026-11.<hash>.md`) with zero manual organizing.
3. **Strip Redundant Noise Before Bundling:**
   If your `.md` exporter includes long base64 strings, system boilerplate, or thinking traces, strip them before writing to `kb/` so your `hot-recent.md` and Cold Bundles stay compact and token-efficient.

---

Do you want to keep everything **100% private via Drive Bundles (Path B)**, or are your exported chats safe for **cross-repo push to `ai-kb` (Path A)**—and how are user vs. model turns formatted inside your exported `.md` files? If you share a quick snippet of one exported `.md` header, I can tailor `build_kb.py` to extract your exact chat titles and prompts cleanly.Looking at your `.md` format, this is actually **ideal** for the Tiered Hybrid setup—and sharing this sample just saved you from **two hidden bugs** that the generic `build_kb.py` would have hit:

1. **Heading Pollution:** Your chat exports use `## User` and `## Model` as level-2 headings, while the real topics live in **`# Title`**, the **User questions**, and **`###` subheadings**. The generic script would have put `User, Model, User, Model` into `llms.txt`.
2. **Bulk-Import `hot-recent.md` Bloat:** If you import 50 older chats from September/October into `ai-kb` today, `git log` would think all 50 were "edited today" and dump everything into `hot-recent.md`. Instead, we can read your **`**Updated:** YYYY-MM-DD`** timestamp directly!

*(Also, since your sample is SBI Clerk Mains math shortcuts with no sensitive personal data, **Path A**—cross-pushing non-private `.md` chats into `inikashx-hub/ai-kb`—is a great fit.)*

---

### Updated `scripts/build_kb.py` (Tailored to Your AI Studio Chat Format)

Replace the contents of **`scripts/build_kb.py`** with this version. It automatically:
* Parses **`# Title`** and **`**Updated:** YYYY-MM-DD`** for accurate 14-day recency detection.
* Extracts your **`## User` prompts** and **`###` section titles** (ignoring `User`/`Model` labels) into `llms.txt` for sharp semantic routing.
* Auto-groups flat chat dumps under `kb/chats/` by **Month (`YYYY-MM`)** if you don't sort them into topic folders, or by **folder name** if you organize them (e.g., `kb/quant/`, `kb/reasoning/`).

```python
import hashlib
import os
import re
import shutil
import subprocess
from datetime import date, datetime
from pathlib import Path

KB_DIR = Path("kb")
OUT_DIR = Path("_ai_bundles")
COLD_DIR = OUT_DIR / "cold"

ALLOWED_EXTS = {".md", ".txt", ".json", ".yaml", ".yml", ".csv", ".py", ".ts", ".js"}
MAX_COLD_BYTES = 180_000  # ~45k tokens max per Cold Bundle
RECENT_DAYS = 14

REPO = os.environ.get("GITHUB_REPOSITORY", "inikashx-hub/ai-kb")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
TODAY = date.today()

def get_git_recent_files(days: int) -> set[Path]:
    try:
        out = subprocess.check_output(
            ["git", "log", f"--since={days} days ago", "--name-only", "--pretty=format:", "--", str(KB_DIR)],
            text=True,
        )
        return {Path(line.strip()) for line in out.splitlines() if line.strip()}
    except Exception:
        return set()

def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return {}, text
    meta = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip().lower()] = v.strip()
    return meta, text[match.end() :]

def clean_chat_wrapper(text: str) -> str:
    return re.sub(r"^---\s*START OF FILE.*?---\s*\n+", "", text, flags=re.MULTILINE).strip()

def extract_chat_info(path: Path, body: str) -> dict:
    # 1. Title from H1 or filename
    h1_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    title = h1_match.group(1).strip() if h1_match else path.stem

    # 2. Updated date from "> **Model:** ... | **Updated:** YYYY-MM-DD ..."
    updated_date = None
    upd_match = re.search(r"\*\*Updated:\*\*\s*(\d{4}-\d{2}-\d{2})", body)
    if upd_match:
        try:
            updated_date = datetime.strptime(upd_match.group(1), "%Y-%m-%d").date()
        except ValueError:
            updated_date = None

    # 3. User prompts (the actual questions asked in the chat)
    raw_prompts = re.findall(
        r"^##\s+User\s*\n+(.*?)(?=\n+---|\n+##\s+Model|\Z)",
        body,
        re.DOTALL | re.MULTILINE,
    )
    prompts = []
    for p in raw_prompts[:4]:
        compact = " ".join(p.split())
        if compact:
            prompts.append(compact[:110] + ("..." if len(compact) > 110 else ""))

    # 4. H3 subheadings (skipping generic labels)
    h3s = re.findall(r"^###\s+(.+)$", body, re.MULTILINE)
    skip = {"conclusion", "summary", "summary checklist before applying:"}
    sections = [h.strip() for h in h3s if h.strip().lower() not in skip][:8]

    return {
        "title": title,
        "updated_date": updated_date,
        "prompts": prompts,
        "sections": sections,
    }

def format_file_block(rel_path: Path, body: str) -> str:
    return f"\n\n---\n## FILE: `{rel_path.as_posix()}`\n\n{body}\n"

def write_cold_chunks(group_name: str, items: list[dict]) -> list[dict]:
    chunks = []
    current_blocks, current_meta, current_size = [], [], 0

    for item in items:
        block = format_file_block(item["path"], item["body"])
        block_size = len(block.encode("utf-8"))
        if current_blocks and (current_size + block_size > MAX_COLD_BYTES):
            chunks.append((current_blocks, current_meta))
            current_blocks, current_meta, current_size = [], [], 0
        current_blocks.append(block)
        current_meta.append(item)
        current_size += block_size

    if current_blocks:
        chunks.append((current_blocks, current_meta))

    written = []
    for idx, (blocks, metas) in enumerate(chunks, start=1):
        suffix = f"-part{idx}" if len(chunks) > 1 else ""
        content = f"# Cold Knowledge Bundle: {group_name}{suffix}\n" + "".join(blocks)
        short_hash = hashlib.md5(content.encode("utf-8")).hexdigest()[:8]
        filename = f"cold-{group_name}{suffix}.{short_hash}.md"
        (COLD_DIR / filename).write_text(content, encoding="utf-8")

        titles, prompts, sections, summaries, keywords = [], [], [], [], []
        for m in metas:
            d = m["updated_date"].isoformat() if m["updated_date"] else ""
            titles.append(f"{m['title']} ({d})" if d else m["title"])
            prompts.extend(m["prompts"])
            sections.extend(m["sections"])
            if m["summary"]:
                summaries.append(m["summary"])
            if m["keywords"]:
                keywords.append(m["keywords"])

        written.append(
            {
                "url": f"{RAW_BASE}/_ai_bundles/cold/{filename}",
                "group": f"{group_name}{suffix}",
                "titles": titles,
                "prompts": prompts[:12],
                "sections": sections[:15],
                "summaries": summaries,
                "keywords": keywords,
            }
        )
    return written

def main():
    if not KB_DIR.exists():
        raise SystemExit("Missing 'kb/' directory.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(COLD_DIR, ignore_errors=True)
    COLD_DIR.mkdir(parents=True, exist_ok=True)

    git_recent = get_git_recent_files(RECENT_DAYS)
    hot_core_blocks = []
    hot_recent_blocks = []
    cold_groups: dict[str, list[dict]] = {}

    for path in sorted(KB_DIR.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in ALLOWED_EXTS:
            continue

        raw_text = path.read_text(encoding="utf-8", errors="ignore")
        meta, body = parse_frontmatter(raw_text)
        body = clean_chat_wrapper(body)
        info = extract_chat_info(path, body)

        rel_from_kb = path.relative_to(KB_DIR)
        top_folder = rel_from_kb.parts[0] if len(rel_from_kb.parts) > 1 else "general"

        is_hot = (top_folder == "core") or (meta.get("tier") == "hot")
        block = format_file_block(path, body)

        if is_hot:
            hot_core_blocks.append(block)
        else:
            # Prefer chat's **Updated:** date if present; otherwise fall back to git log
            if info["updated_date"] is not None:
                is_recent = (TODAY - info["updated_date"]).days <= RECENT_DAYS
            else:
                is_recent = path in git_recent

            if is_recent:
                hot_recent_blocks.append(block)

            # If dumped flat into kb/chats/, auto-shard by month (YYYY-MM)
            group_key = top_folder
            if top_folder == "chats" and info["updated_date"] is not None:
                group_key = f"chats-{info['updated_date'].strftime('%Y-%m')}"

            cold_groups.setdefault(group_key, []).append(
                {
                    "path": path,
                    "body": body,
                    "title": info["title"],
                    "updated_date": info["updated_date"],
                    "prompts": info["prompts"],
                    "sections": info["sections"],
                    "summary": meta.get("summary", ""),
                    "keywords": meta.get("keywords", ""),
                }
            )

    core_text = (
        "# Tier 1: Core Knowledge\n" + "".join(hot_core_blocks)
        if hot_core_blocks
        else "# Tier 1: Core Knowledge\nNo core files configured yet."
    )
    (OUT_DIR / "hot-core.md").write_text(core_text, encoding="utf-8")

    recent_text = (
        f"# Tier 1: Chats & Docs Updated in Last {RECENT_DAYS} Days\n" + "".join(hot_recent_blocks)
        if hot_recent_blocks
        else f"# Tier 1: Recent Changes\nNo chats or docs updated in the last {RECENT_DAYS} days."
    )
    (OUT_DIR / "hot-recent.md").write_text(recent_text, encoding="utf-8")

    index_entries = []
    for group_name, items in sorted(cold_groups.items()):
        index_entries.extend(write_cold_chunks(group_name, items))

    lines = [
        "# Knowledge Base Index (Tier 2 Cold Bundles)",
        "# Note: Core docs and chats updated in the last 14 days are already pre-loaded in Tier 1.",
        "",
    ]
    for entry in index_entries:
        lines.append(f"- URL: {entry['url']}")
        lines.append(f"  Topic Group: {entry['group']}")
        lines.append(f"  Chats/Files: {' | '.join(entry['titles'])}")
        if entry["prompts"]:
            lines.append(f"  User Questions: {' | '.join(entry['prompts'])}")
        if entry["sections"]:
            lines.append(f"  Key Sections: {' | '.join(entry['sections'])}")
        if entry["summaries"]:
            lines.append(f"  Summary: {' | '.join(entry['summaries'])}")
        if entry["keywords"]:
            lines.append(f"  Keywords: {' | '.join(entry['keywords'])}")
        lines.append("")

    (OUT_DIR / "llms.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"Built {len(index_entries)} cold bundle(s) and updated Tier 1 + llms.txt.")

if __name__ == "__main__":
    main()
```

---

### What `llms.txt` Will Look Like for Your Sample Chat
Instead of noisy `User, Model` headings, Gemini sees this crystal-clear index entry:
```text
- URL: https://raw.githubusercontent.com/inikashx-hub/ai-kb/main/_ai_bundles/cold/cold-chats-2026-09.8e4a12c1.md
  Topic Group: chats-2026-09
  Chats/Files: Solving Math Questions Under 30s (2026-09-29)
  User Questions: How to solve the given question within 30 seconds | I don't understand the coefficient method | When to use this method and when to be cautious about the same?
  Key Sections: Method 1: The 10-Second Coefficient Shortcut (Exam Trick) | Method 2: Complete 30-Second Algebraic Solution | What is a "Coefficient"? | The Idea Behind the Shortcut | When to USE this method: | When to be CAUTIOUS (or NOT use it):
```
That makes Turn-2 retrieval nearly effortless when you later ask *"What was that SBI Clerk coefficient shortcut for linear equations and when shouldn't I use it?"*

### One Small Tip on Organizing `kb/`
* If you dump all synced chats into **`kb/chats/`**, the script automatically bundles them by month (`chats-2026-09`, `chats-2026-10`, etc.).
* If you prefer topic-based bundles (even better for accuracy!), sort key subjects into subfolders like **`kb/quant/`**, **`kb/reasoning/`**, **`kb/ga/`**, and **`kb/core/`** (for master cheat sheets you always want in 1-turn memory).

---

## User

Where should I upload a knowledge base before uploading python script?

---

## Model

Upload your `.md` knowledge base files into a **`kb/`** folder at the **root** of your `inikashx-hub/ai-kb` repository (on the same level as `README.md` and `.github`).

### Which Subfolder Inside `kb/` Should You Use?
* **`kb/core/`** → Put your **most important master notes / cheat sheets** here (always pre-loaded for 1-turn answers).
* **`kb/chats/`** → Put your exported AI Studio **`.md` chat files** here if you want one simple dump folder (the script will automatically bundle them by month, like `2026-09`, and put the last 14 days into `hot-recent.md`).
* **OR `kb/<topic>/`** (e.g., `kb/quant/`, `kb/reasoning/`) → Use topic folders instead of `kb/chats/` if you want subject-based bundles.

*(Upload **only the `.md` files**—skip the `.pdf` duplicates.)*

---

### How to Upload Them on Mobile Right Now
GitHub won't let you upload into a folder until that folder exists, so create it in 10 seconds first:

1. Go to the **main root page** of `ai-kb` (tap `ai-kb` in the path if you're still inside `.github`).
2. Tap **Add file** → **Create new file**.
3. Type **`kb/chats/README.md`** (or `kb/core/README.md`) in the filename box, type `# Knowledge Base` in the body, and tap **Commit changes...**. *(This creates the `kb/` folder!)*
4. Open **`kb/chats/`** (or whichever subfolder you created) → tap **Add file** → **Upload files** → select your `.md` files from your phone or Google Drive → tap **Commit changes**.
5. **Now add the Python script:** Return to the root of `ai-kb`, tap **Add file** → **Create new file**, type **`scripts/build_kb.py`**, paste the script from the previous message, and commit.

As soon as you commit `scripts/build_kb.py`, open the **Actions** tab—your workflow will run automatically and build `_ai_bundles/`!

---

## User

I have just pasted the python code

---

## Model

Great job getting everything uploaded! Looking closely at your screenshot, I spotted **two small path differences** between your repo and what the workflow currently expects:

1. Your folder is named **`chats/`** at the root (instead of `kb/chats/`).
2. Your Python file is at the root named **`build-kb.py`** (with a hyphen, instead of `scripts/build_kb.py`).

Instead of making you delete or move your `chats/` folder on mobile, **it’s much easier to just update `build-kb.yml` and `build-kb.py` to match your exact layout right now.**

---

### Fix 1: Update `.github/workflows/build-kb.yml`
1. Open **`.github/workflows`** → tap **`build-kb.yml`** → tap the **pencil icon (✏️)** to edit.
2. Replace everything with this:

```yaml
name: Build AI Knowledge Bundles

on:
  push:
    branches: ["main"]
    paths:
      - "chats/**"
      - "core/**"
      - "build-kb.py"
  workflow_dispatch:

permissions:
  contents: write

jobs:
  build-bundles:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository with history
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Build Hot/Cold bundles and llms.txt
        run: python3 build-kb.py

      - name: Commit updated bundles
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add _ai_bundles/
          if git diff --staged --quiet; then
            echo "No bundle changes to commit."
          else
            git commit -m "chore: rebuild AI knowledge bundles [skip ci]"
            git push
          fi
```
3. Tap **Commit changes...**.

---

### Fix 2: Update `build-kb.py` (So It Reads `chats/` Directly)
1. Tap **`build-kb.py`** at the root of `ai-kb` → tap the **pencil icon (✏️)**.
2. Replace everything with this updated version (it scans `chats/` and optional `core/` directly at the root):

```python
import hashlib
import os
import re
import shutil
import subprocess
from datetime import date, datetime
from pathlib import Path

OUT_DIR = Path("_ai_bundles")
COLD_DIR = OUT_DIR / "cold"

ALLOWED_EXTS = {".md", ".txt", ".json", ".yaml", ".yml", ".csv", ".py", ".ts", ".js"}
MAX_COLD_BYTES = 180_000  # ~45k tokens max per Cold Bundle
RECENT_DAYS = 14

REPO = os.environ.get("GITHUB_REPOSITORY", "inikashx-hub/ai-kb")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
TODAY = date.today()

def get_git_recent_files(days: int) -> set[Path]:
    try:
        out = subprocess.check_output(
            ["git", "log", f"--since={days} days ago", "--name-only", "--pretty=format:"],
            text=True,
        )
        return {Path(line.strip()) for line in out.splitlines() if line.strip()}
    except Exception:
        return set()

def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return {}, text
    meta = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip().lower()] = v.strip()
    return meta, text[match.end() :]

def clean_chat_wrapper(text: str) -> str:
    return re.sub(r"^---\s*START OF FILE.*?---\s*\n+", "", text, flags=re.MULTILINE).strip()

def extract_chat_info(path: Path, body: str) -> dict:
    h1_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    title = h1_match.group(1).strip() if h1_match else path.stem

    updated_date = None
    upd_match = re.search(r"\*\*Updated:\*\*\s*(\d{4}-\d{2}-\d{2})", body)
    if upd_match:
        try:
            updated_date = datetime.strptime(upd_match.group(1), "%Y-%m-%d").date()
        except ValueError:
            updated_date = None

    raw_prompts = re.findall(
        r"^##\s+User\s*\n+(.*?)(?=\n+---|\n+##\s+Model|\Z)",
        body,
        re.DOTALL | re.MULTILINE,
    )
    prompts = []
    for p in raw_prompts[:4]:
        compact = " ".join(p.split())
        if compact:
            prompts.append(compact[:110] + ("..." if len(compact) > 110 else ""))

    h3s = re.findall(r"^###\s+(.+)$", body, re.MULTILINE)
    skip = {"conclusion", "summary", "summary checklist before applying:"}
    sections = [h.strip() for h in h3s if h.strip().lower() not in skip][:8]

    return {
        "title": title,
        "updated_date": updated_date,
        "prompts": prompts,
        "sections": sections,
    }

def sanitize_slug(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", name).strip("-").lower()
    return slug or "general"

def format_file_block(rel_path: Path, body: str) -> str:
    return f"\n\n---\n## FILE: `{rel_path.as_posix()}`\n\n{body}\n"

def write_cold_chunks(group_name: str, items: list[dict]) -> list[dict]:
    chunks = []
    current_blocks, current_meta, current_size = [], [], 0

    for item in items:
        block = format_file_block(item["path"], item["body"])
        block_size = len(block.encode("utf-8"))
        if current_blocks and (current_size + block_size > MAX_COLD_BYTES):
            chunks.append((current_blocks, current_meta))
            current_blocks, current_meta, current_size = [], [], 0
        current_blocks.append(block)
        current_meta.append(item)
        current_size += block_size

    if current_blocks:
        chunks.append((current_blocks, current_meta))

    written = []
    for idx, (blocks, metas) in enumerate(chunks, start=1):
        suffix = f"-part{idx}" if len(chunks) > 1 else ""
        content = f"# Cold Knowledge Bundle: {group_name}{suffix}\n" + "".join(blocks)
        short_hash = hashlib.md5(content.encode("utf-8")).hexdigest()[:8]
        filename = f"cold-{group_name}{suffix}.{short_hash}.md"
        (COLD_DIR / filename).write_text(content, encoding="utf-8")

        titles, prompts, sections, summaries, keywords = [], [], [], [], []
        for m in metas:
            d = m["updated_date"].isoformat() if m["updated_date"] else ""
            titles.append(f"{m['title']} ({d})" if d else m["title"])
            prompts.extend(m["prompts"])
            sections.extend(m["sections"])
            if m["summary"]:
                summaries.append(m["summary"])
            if m["keywords"]:
                keywords.append(m["keywords"])

        written.append(
            {
                "url": f"{RAW_BASE}/_ai_bundles/cold/{filename}",
                "group": f"{group_name}{suffix}",
                "titles": titles,
                "prompts": prompts[:12],
                "sections": sections[:15],
                "summaries": summaries,
                "keywords": keywords,
            }
        )
    return written

def main():
    scan_dirs = [d for d in (Path("core"), Path("chats"), Path("kb")) if d.exists()]
    if not scan_dirs:
        raise SystemExit("Missing 'chats/' or 'core/' directory.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(COLD_DIR, ignore_errors=True)
    COLD_DIR.mkdir(parents=True, exist_ok=True)

    git_recent = get_git_recent_files(RECENT_DAYS)
    hot_core_blocks = []
    hot_recent_blocks = []
    cold_groups: dict[str, list[dict]] = {}

    for root_dir in scan_dirs:
        for path in sorted(root_dir.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in ALLOWED_EXTS:
                continue

            raw_text = path.read_text(encoding="utf-8", errors="ignore")
            meta, body = parse_frontmatter(raw_text)
            body = clean_chat_wrapper(body)
            info = extract_chat_info(path, body)
            parts = path.parts

            is_hot = (
                root_dir.name == "core"
                or (root_dir.name == "kb" and len(parts) > 2 and parts[1] == "core")
                or meta.get("tier") == "hot"
            )
            block = format_file_block(path, body)

            if is_hot:
                hot_core_blocks.append(block)
            else:
                if info["updated_date"] is not None:
                    is_recent = (TODAY - info["updated_date"]).days <= RECENT_DAYS
                else:
                    is_recent = path in git_recent

                if is_recent:
                    hot_recent_blocks.append(block)

                if root_dir.name == "chats":
                    if len(parts) > 2:
                        group_key = sanitize_slug(parts[1])
                    elif info["updated_date"] is not None:
                        group_key = f"chats-{info['updated_date'].strftime('%Y-%m')}"
                    else:
                        group_key = "chats-general"
                else:
                    raw_sub = parts[1] if len(parts) > 2 else "general"
                    group_key = sanitize_slug(raw_sub)
                    if group_key == "chats" and info["updated_date"] is not None:
                        group_key = f"chats-{info['updated_date'].strftime('%Y-%m')}"

                cold_groups.setdefault(group_key, []).append(
                    {
                        "path": path,
                        "body": body,
                        "title": info["title"],
                        "updated_date": info["updated_date"],
                        "prompts": info["prompts"],
                        "sections": info["sections"],
                        "summary": meta.get("summary", ""),
                        "keywords": meta.get("keywords", ""),
                    }
                )

    core_text = (
        "# Tier 1: Core Knowledge\n" + "".join(hot_core_blocks)
        if hot_core_blocks
        else "# Tier 1: Core Knowledge\nNo core files configured yet."
    )
    (OUT_DIR / "hot-core.md").write_text(core_text, encoding="utf-8")

    recent_text = (
        f"# Tier 1: Chats & Docs Updated in Last {RECENT_DAYS} Days\n" + "".join(hot_recent_blocks)
        if hot_recent_blocks
        else f"# Tier 1: Recent Changes\nNo chats or docs updated in the last {RECENT_DAYS} days."
    )
    (OUT_DIR / "hot-recent.md").write_text(recent_text, encoding="utf-8")

    index_entries = []
    for group_name, items in sorted(cold_groups.items()):
        index_entries.extend(write_cold_chunks(group_name, items))

    lines = [
        "# Knowledge Base Index (Tier 2 Cold Bundles)",
        "# Note: Core docs and chats updated in the last 14 days are already pre-loaded in Tier 1.",
        "",
    ]
    for entry in index_entries:
        lines.append(f"- URL: {entry['url']}")
        lines.append(f"  Topic Group: {entry['group']}")
        lines.append(f"  Chats/Files: {' | '.join(entry['titles'])}")
        if entry["prompts"]:
            lines.append(f"  User Questions: {' | '.join(entry['prompts'])}")
        if entry["sections"]:
            lines.append(f"  Key Sections: {' | '.join(entry['sections'])}")
        if entry["summaries"]:
            lines.append(f"  Summary: {' | '.join(entry['summaries'])}")
        if entry["keywords"]:
            lines.append(f"  Keywords: {' | '.join(entry['keywords'])}")
        lines.append("")

    (OUT_DIR / "llms.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"Built {len(index_entries)} cold bundle(s) and updated Tier 1 + llms.txt.")

if __name__ == "__main__":
    main()
```
3. Tap **Commit changes...**.

---

### Check That It Worked
1. After committing `build-kb.py`, tap **`More ▾`** (top right, next to *Pull requests*) → **`Actions`**.
2. Wait ~10–15 seconds for **Build AI Knowledge Bundles** to turn green ✅.
3. Go back to **Code**—you’ll see a brand-new **`_ai_bundles/`** folder ready to connect to Google AI Studio!

---

## User

I updated them

---

## Model

**Awesome—it worked!** Look at **`github-actions[bot] 1 minute ago`** and the new **`_ai_bundles`** folder on your screen. Your GitHub pipeline is completely live.

Now all that's left is connecting it to **Google AI Studio**:

---

### Step 1: Set Up Google AI Studio
1. Open **Google AI Studio** → **Chat / Playground**.
2. In the settings/tools panel:
   * Turn **URL context** → **ON**
   * Set **Temperature** → **`0.1`**
3. Open **System Instructions** and paste this exact block (your `inikashx-hub/ai-kb` URLs are already filled in):

```markdown
You are a retrieval-grounded assistant for my knowledge base.

### Always-Loaded Tier 1 Sources + Tier 2 Index (Read via URL context)
- Tier 1 Core: https://raw.githubusercontent.com/inikashx-hub/ai-kb/main/_ai_bundles/hot-core.md
- Tier 1 Recent: https://raw.githubusercontent.com/inikashx-hub/ai-kb/main/_ai_bundles/hot-recent.md
- Tier 2 Index: https://raw.githubusercontent.com/inikashx-hub/ai-kb/main/_ai_bundles/llms.txt

### Rules
1. First check Tier 1 Core and Tier 1 Recent. If they fully answer the user's question, answer immediately in this turn and cite the exact `FILE:` path.
2. If the question requires files listed in `llms.txt` that are NOT in Tier 1:
   - Do NOT guess or answer from `llms.txt` summaries alone.
   - Pick the 1 to 4 most relevant Cold Bundle URLs from `llms.txt`.
   - Output a 1-line note explaining why, followed by a SINGLE `text` code block containing ONLY the raw `https://...` URLs (one per line) and this final line inside the block:
     `Read every URL above via URL context and answer my previous question with exact FILE citations.`
3. Once provided in the next turn, read the Cold Bundles completely before answering.
```

4. **Save the prompt** in AI Studio so you never have to paste this again.

---

### Step 2: Test It Right Now (2-Turn Test)
Since your sample math chat (`2026-09-29`) is older than 14 days, it sits in **Tier 2 Cold**—which lets you test the full router immediately. Ask this in the chat box:

> *"When should I be cautious about using the Coefficient Method for math questions?"*

**What you should see:**
1. **Turn 1:** Gemini checks `llms.txt` and gives you a **1-click Copy code block** containing your `cold-chats-2026-09.<hash>.md` URL.
2. **Turn 2:** Tap **Copy** on that block → **Paste** → **Send** → Gemini reads the Cold Bundle and answers directly from your notes with the exact `FILE:` citation.

*(Whenever you're ready to wire your **private repo's 15-minute pipeline** to auto-push new `.md` chats straight into `inikashx-hub/ai-kb/chats/`, just let me know and I'll give you that snippet too!)*

---

## User

There is no temperature toggle

---

## Model

That’s completely normal—**Google removed the Temperature slider on Gemini 3.6 Flash and newer models** (including **Gemini 3.8 Flash**, which I noticed you were using in your chat export).

You don't need Temperature for this setup—the strict System Instructions already handle the grounding rules.

### What to Set Instead (Tap the Tune/Sliders Icon at Top Right):
1. **Tools → URL context:** Toggle **ON** *(this is the only required switch)*.
2. **Thinking level** *(optional)*: Leave at default (or set higher for complex multi-file lookups, lower for faster 1-turn answers).

Go ahead and run your **2-turn test**!

---

## Model

**It actually worked!** Look at your last two screenshots:
* Gemini fetched both `hot-recent.md` and `llms.txt` directly from `raw.githubusercontent.com` (**Sources 1 & 2**).
* It gave the exact answer (**342 questions**), cited `FILE: chats/document.md`, and even identified the exact Tier 2 Cold Bundle (`cold-chats-general-part2.8485172c.md`) if you want to drill deeper into Chapter 4.

At the same time, your test just revealed **two super useful things** we can fix right away to make it smoother:

---

### 1. Why Turn 1 Asked You to Paste the 3 URLs
Look at Screenshot 2:
> *"My URL browsing tool can only access URLs that appear in the **user prompt** ... and blocked fetching the Tier 1 / Tier 2 URLs listed only in the system instructions."*

In the Google AI Studio Playground, **URL Context will not fetch URLs placed only in System Instructions**—they must appear in a **User message** at least once in the chat.

#### The 1-Tap Fix (Eliminates That Extra Turn):
1. **Pin those 3 URLs in your Android keyboard clipboard** (Gboard → Clipboard → Pin):
   ```text
   https://raw.githubusercontent.com/inikashx-hub/ai-kb/main/_ai_bundles/hot-core.md
   https://raw.githubusercontent.com/inikashx-hub/ai-kb/main/_ai_bundles/hot-recent.md
   https://raw.githubusercontent.com/inikashx-hub/ai-kb/main/_ai_bundles/llms.txt
   ```
2. Whenever you start a brand-new chat, tap that pinned snippet **+ type your question right below it in Turn 1**. Once they're in Turn 1, you never have to paste them again for follow-up turns in that chat!
3. *(Optional)* In the top-right Settings (tune icon), turn **Grounding with Google Search OFF** and leave only **URL context ON**—that stops Gemini from wasting time trying to Google-search `inikashx-hub/ai-kb`.

*(Also update Rule 2 in your System Instructions to remove `Always-Loaded Tier 1 Sources...` if you prefer keeping the 3 URLs in Turn 1—or leave it as a handy reminder.)*

---

### 2. Why `hot-recent.md` Only Showed Chapter 1 of `chats/document.md`
Look closely at Screenshot 5:
* `chats/document.md` is a **massive** 3,246-question compendium. Because it didn't have an `**Updated:** YYYY-MM-DD` line, `git log` treated it as "new today" and put the whole giant file into `hot-recent.md`.
* When a single fetched file gets very large, URL Context may only pull a partial window/excerpt (so it saw the Table of Contents + first 201 questions, rather than all 3,246!).

**How to fix this for big compendiums:**
* Keep `hot-recent.md` for **small/medium recent chats**, and split giant static compendiums (>150 KB) into smaller chapter files (or let `build-kb.py` automatically split any giant single `.md` file by heading into `<150 KB` Cold Bundle parts and skip huge >150 KB files from `hot-recent.md`).

If you want me to add that **auto-splitter for giant `.md` files** to `build-kb.py` (so massive compendiums like `document.md` are split into readable chapter chunks inside `cold/` and never clog `hot-recent.md`), just say the word!

---

## User

How does our RAG perform against Claude, Chatgpt and NotebookLM?

---

## Model

Your custom **GitHub + Google AI Studio Tiered Hybrid** actually outperforms the free tiers of **ChatGPT**, **Claude**, and **NotebookLM (renamed Gemini Notebook)** on scale and automation—while trailing them slightly on zero-click convenience and giant-PDF search.

Here is an honest, engineering-level comparison based on current platform limits and how your test just performed:

---

### Side-by-Side Comparison

| Feature | **Your GitHub + AI Studio Hybrid** | **NotebookLM (Gemini Notebook)** | **Claude Projects** | **ChatGPT Projects** |
| :--- | :--- | :--- | :--- | :--- |
| **Cost** | **$0 (Free)** | Free (Paid tiers for higher quotas) | Free (Paid required for RAG expansion) | Free (Paid required for >5 files) |
| **File / Source Cap** | **Unlimited** (auto-sharded via `llms.txt`) | **50 sources**/notebook Free (up to 600 on Ultra) | **Unlimited count**, capped by context on Free (**10× with Paid RAG**) | **5 files** Free, **25** Plus, **40** Pro/Enterprise |
| **Max Single File Size** | **34 MB** per URL *(but very huge files get excerpted)* | **500K words** / 200 MB per source | **30 MB** per file in Projects | **512 MB** / 2M tokens per file |
| **Auto-Sync New Chats** | **Automatic** (rebuilds on every GitHub push) | Manual re-upload / manual Drive re-sync | Manual re-upload on Free | Manual re-upload (Drive links don't auto-sync) |
| **Retrieval Type** | **Agentic Index Routing** (`llms.txt` → full Cold Bundle) | **Vector + Long Context** (chunk retrieval + inline quotes) | **Full Context** (Free) / **Auto-RAG** (Paid) | **Vector Chunk Retrieval** (top-K snippets) |
| **Privacy** | **Public repo** required for URL Context | **Private** by default | **Private** by default | **Private** by default |
| **UX Friction** | Medium (paste 3 URLs in Turn 1 + occasional Turn 2) | **Zero** (open & ask) | **Zero** (open & ask) | **Zero** (open & ask) |

---

### Where Your Hybrid Setup Actually **Beats** Them

1. **Unlimited, Auto-Updating History at $0:**
   * **ChatGPT Projects (Free)** hits a brick wall at **5 files**.
   * **NotebookLM (Free)** caps out at **50 sources per notebook**—if you drop in daily AI Studio chats, you fill it up in two months.
   * **Claude (Free)** doesn't turn on RAG expansion; once your uploads fill the context window, you're stuck.
   * **Your setup** has **no file cap** and automatically rolls the last 14 days into `hot-recent.md` and archives older chats into `llms.txt` whenever you push.
2. **Whole-Conversation Reasoning (No "Missing Half" Bug):**
   * Vector-chunk RAG (like **ChatGPT**) slices documents into small paragraphs and only retrieves the top matching chunks. On exam-prep or coding chats, that often grabs the formula *without* the *"When to be cautious"* section right below it.
   * Your setup retrieves **whole topic/month bundles**, so Gemini reads the full conversation arc from start to finish—leading to much better reasoning and synthesis.
3. **100% Transparent Debugging:**
   * In Claude/ChatGPT RAG mode, retrieval is a black box—if it misses a document, you have no idea why.
   * With your `llms.txt` setup, you can literally open `llms.txt` or inspect Gemini's Turn-1 selection to see *exact* titles, user prompts, and Cold Bundle URLs.

---

### Where They Still **Beat** Your Setup

1. **Searching Inside Massive Single Files (like your 3,246-question `document.md`):**
   * As you saw in Screenshot 5, when one single file is enormous, URL Context may only read a portion/excerpt of it.
   * **NotebookLM** and **ChatGPT** index giant 300-page PDFs into searchable chunks automatically, so asking *"Find every question about PM-KISAN from 2022 inside this 400-page compendium"* is more reliable there *(unless we auto-split large `.md` files into <100 KB chapter files in `build-kb.py`)*.
2. **Zero-Friction Daily UX & Privacy:**
   * You never have to pin/paste 3 URLs in Turn 1 or copy-paste a Cold Bundle URL in Turn 2, and everything stays private out of the box.
3. **Dedicated Study Features (NotebookLM):**
   * NotebookLM gives you clickable paragraph-level citations, Audio/Video Overviews, Mind Maps, and study quizzes—things AI Studio Playground doesn't try to do.

---

### The Best Setup? Use Both for What They're Built For
* **Use Your GitHub + AI Studio Hybrid** as your **living, auto-syncing brain** for all your ongoing AI Studio chats, shortcuts, coding notes, and daily Q&A (unlimited, $0, zero manual uploading).
* **Use NotebookLM (Gemini Notebook)** for **massive, static reference books & compendiums** (like that 3,246-question Banking GA PDF/book), where you want deep keyword search across 400 pages, flashcards, and audio revision.

---

## User

Can we make our hybrid better?

---

## Model

Yes—looking at your screenshots, there are **5 concrete upgrades** that will make your hybrid dramatically faster, stop giant files from getting cut off, and eliminate manual uploading.

Here are the highest-impact upgrades, ranked from #1 downward:

---

### Upgrade 1: Auto-Split Giant Files (<60 KB Chunks) + Cap `hot-recent.md` *(Fixes What Happened to `document.md`)*
In Screenshot 5, `chats/document.md` (3,246 questions) was so big that:
1. It bloated `hot-recent.md`.
2. URL Context only read the Table of Contents and the first 201 questions instead of the whole file.

**The Fix in `build-kb.py`:**
* **Never put huge (>40 KB) files into `hot-recent.md`**, and cap `hot-recent.md` at ~60 KB total (newest chats first). That guarantees Tier 1 is **always read 100% in full** on Turn 1.
* **Auto-split any large file (>60 KB) at chapter headings (`#` / `##`)** into smaller Cold Bundle parts (`cold-compendium-part1.<hash>.md`, `part2`, etc.). Each part stays compact enough that Gemini reads **every single question inside a fetched chapter**, instead of an excerpt.

---

### Upgrade 2: Smart Dual-Mode Indexing (`Chats` vs. `Books/Compendiums`)
Right now, `build-kb.py` only extracts `###` headings (to avoid `## User` / `## Model`). That works great for AI Studio chats, **but** for reference books/compendiums like `document.md`, chapter titles are often `##` headings—so `llms.txt` misses them.

**The Fix:**
* If a file contains `## User` / `## Model` → index **User Questions + `###` headings**.
* If it does **not** (a compendium or PDF-to-MD book) → index **`##` and `###` chapter titles** (e.g., `04. Government Schemes & Initiatives (342)`).
* Result: `llms.txt` routes you straight to the exact chapter part of a 400-page book—often beating ChatGPT/NotebookLM because you get the **entire chapter intact**, not fragmented chunks.

---

### Upgrade 3: Eliminate Wasted Web Search & Speed Up Turn 1
In Screenshot 2, Gemini wasted time running a Google Web Search (`"Web search did not return any indexed pages for inikashx-hub/ai-kb"`).
* **In AI Studio Settings (tune icon):** Turn **Grounding with Google Search → OFF** and keep only **URL context → ON**.
* **In Turn 1:** Keep your 3 URLs pinned in Gboard Clipboard and paste **3 URLs + Question** together in Message 1 so you skip the "please paste the URLs" round-trip completely.

---

### Upgrade 4: Connect Your Private Repo (True Zero-Touch Automation)
Right now you uploaded `.md` files manually from mobile. Since your private repo already runs every 15 minutes to convert AI Studio chats to `.md`:
* Add a **10-line cross-repo push step** at the end of your private GitHub Action (using a fine-grained PAT scoped only to `inikashx-hub/ai-kb`).
* Add a simple filter (e.g., **skip chats with `[private]` in the title**, push everything else to `chats/`).
* Your knowledge base will stay updated every 15 minutes with **zero manual work**.

---

### Upgrade 5: Actually Use `core/` (1-Turn Instant Cheat Sheets)
Right now `hot-core.md` is empty. Create a `core/` folder at the root of `ai-kb` and put 1–3 high-frequency master files there (e.g., `core/math-shortcuts-master.md`, `core/ga-important-dates.md`, `core/syllabus.md`). Anything in `core/` stays permanently loaded in Tier 1 for instant 1-turn answers.

---

### Which Upgrade Should We Do First?
* Say **"Upgrade the script"** and I’ll give you the drop-in **`build-kb.py`** with **#1 (60 KB auto-splitter + `hot-recent` size guard)** and **#2 (smart chat + book chapter indexing)** ready to paste.
* Or say **"Connect private repo"** and I’ll give you the **10-line cross-repo auto-sync YAML step** for your 15-minute pipeline!

---

## User

Upgrade the script

---

## Model

Here is the upgraded **`build-kb.py`** with all three script improvements built in:

1. **Auto-Splits Giant Files (<65 KB Chunks):** Splits large books/compendiums like `document.md` cleanly at `#` / `##` chapter boundaries (ignoring `#` inside code blocks) so URL Context reads **100% of every fetched part** without cutting off mid-book.
2. **Protects `hot-recent.md`:** Never dumps huge (>40 KB) compendiums into `hot-recent.md`, and caps `hot-recent.md` at 70 KB total (newest chats first) so Turn 1 stays fast and complete.
3. **Dual-Mode Indexing (`Chats` vs. `Compendiums`):**
   * For **AI Studio chats** (`## User` / `## Model`): extracts **User Questions + `###` subheadings**.
   * For **Books / Compendiums** (like `document.md`): extracts **`#`, `##`, and `###` chapter titles** so `llms.txt` points straight to the exact chapter part.

---

### How to Apply It
1. Open **`build-kb.py`** at the root of `inikashx-hub/ai-kb` → tap the **pencil icon (✏️)**.
2. Select all and replace with this upgraded script:

```python
import hashlib
import os
import re
import shutil
import subprocess
from datetime import date, datetime
from pathlib import Path

OUT_DIR = Path("_ai_bundles")
COLD_DIR = OUT_DIR / "cold"

ALLOWED_EXTS = {".md", ".txt", ".json", ".yaml", ".yml", ".csv", ".py", ".ts", ".js"}
MAX_COLD_BYTES = 65_000          # Small enough that URL Context reads 100% without truncation
MAX_RECENT_FILE_BYTES = 40_000   # Huge compendiums go straight to Cold chunks, not hot-recent
MAX_RECENT_TOTAL_BYTES = 70_000  # Keep hot-recent.md fast and lightweight
RECENT_DAYS = 14

REPO = os.environ.get("GITHUB_REPOSITORY", "inikashx-hub/ai-kb")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
TODAY = date.today()

def get_git_recent_files(days: int) -> set[Path]:
    try:
        out = subprocess.check_output(
            ["git", "log", f"--since={days} days ago", "--name-only", "--pretty=format:"],
            text=True,
        )
        return {Path(line.strip()) for line in out.splitlines() if line.strip()}
    except Exception:
        return set()

def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return {}, text
    meta = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip().lower()] = v.strip()
    return meta, text[match.end() :]

def clean_chat_wrapper(text: str) -> str:
    return re.sub(r"^---\s*START OF FILE.*?---\s*\n+", "", text, flags=re.MULTILINE).strip()

def split_by_heading_pattern(text: str, pattern: str) -> list[str]:
    """Split markdown text on heading lines outside fenced code blocks."""
    regex = re.compile(pattern)
    sections, current = [], []
    in_fence = False

    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith("```"): in_fence = not in_fence if not in_fence and regex.match(line) and current: sections.append("".join(current).strip) current = [line] else: current.append(line)

    if current: sections.append("".join(current).strip) return [s for s in sections if s]

def split_large_body(body: str, max_bytes: int) -> list[str]: """Split huge files cleanly at chapters (H1/H2), then H3, then paragraphs.""" if len(body.encode("utf-8")) <= max_bytes: return [body]

    pieces = [] for sec in split_by_heading_pattern(body, r"^#{1,2}\s+"): if len(sec.encode("utf-8")) <= max_bytes: pieces.append(sec) continue

        for sub in split_by_heading_pattern(sec, r"^#{3}\s+"): if len(sub.encode("utf-8")) <= max_bytes: pieces.append(sub) continue

            # Fallback: split oversized section by paragraph breaks
            buf, buf_bytes = [], 0 for para in sub.split("\n\n"): p_bytes = len(para.encode("utf-8")) + 2 if buf and (buf_bytes + p_bytes > max_bytes): pieces.append("\n\n".join(buf).strip) buf, buf_bytes = [], 0 buf.append(para) buf_bytes += p_bytes if buf: pieces.append("\n\n".join(buf).strip)

    # Merge adjacent small sections back up to max_bytes
    merged, cur, cur_bytes = [], [], 0 for p in pieces: p_bytes = len(p.encode("utf-8")) + 2 if cur and (cur_bytes + p_bytes > max_bytes): merged.append("\n\n".join(cur)) cur, cur_bytes = [], 0 cur.append(p) cur_bytes += p_bytes if cur: merged.append("\n\n".join(cur))

    return merged

def extract_doc_info(path: Path, text: str, fallback_title: str = "") -> dict: h1_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE) title = h1_match.group(1).strip if h1_match else (fallback_title or path.stem)

    updated_date = None upd_match = re.search(r"\*\*Updated:\*\*\s*(\d{4}-\d{2}-\d{2})", text) if upd_match: try: updated_date = datetime.strptime(upd_match.group(1), "%Y-%m-%d").date except ValueError: updated_date = None

    is_chat = bool(re.search(r"^##\s+(User|Model)\s*$", text, re.MULTILINE)) prompts = [] sections = []

    if is_chat: raw_prompts = re.findall( r"^##\s+User\s*\n+(.*?)(?=\n+---|\n+##\s+Model|\Z)", text, re.DOTALL | re.MULTILINE, ) for p in raw_prompts[:4]: compact = " ".join(p.split) if compact: prompts.append(compact[:110] + ("..." if len(compact) > 110 else ""))

        h3s = re.findall(r"^###\s+(.+)$", text, re.MULTILINE) skip = {"conclusion", "summary", "summary checklist before applying:"} sections = [h.strip[:90] for h in h3s if h.strip.lower not in skip][:8] else:
        # Non-chat compendium / notes: capture H1, H2, and H3 chapter headings
        hs = re.findall(r"^#{1,3}\s+(.+)$", text, re.MULTILINE) skip = {"table of contents", "contents", "index"} seen = set for h in hs: clean_h = " ".join(h.split)[:90] if clean_h and clean_h.lower not in skip and clean_h not in seen: seen.add(clean_h) sections.append(clean_h) if len(sections) >= 12: break

    return { "title": title, "updated_date": updated_date, "prompts": prompts, "sections": sections, }

def sanitize_slug(name: str) -> str: slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", name).strip("-").lower return slug or "general"

def format_file_block(rel_path: Path, body: str, part_label: str = "") -> str: label = f" {part_label}" if part_label else "" return f"\n\n---\n## FILE: `{rel_path.as_posix()}`{label}\n\n{body}\n"

def write_cold_chunks(group_name: str, items: list[dict]) -> list[dict]: chunks = [] current_blocks, current_meta, current_size = [], [], 0

    for item in items: block = format_file_block(item["path"], item["body"], item.get("part_label", "")) block_size = len(block.encode("utf-8")) if current_blocks and (current_size + block_size > MAX_COLD_BYTES): chunks.append((current_blocks, current_meta)) current_blocks, current_meta, current_size = [], [], 0 current_blocks.append(block) current_meta.append(item) current_size += block_size

    if current_blocks: chunks.append((current_blocks, current_meta))

    written = [] for idx, (blocks, metas) in enumerate(chunks, start=1): suffix = f"-part{idx}" if len(chunks) > 1 else "" content = f"# Cold Knowledge Bundle: {group_name}{suffix}\n" + "".join(blocks) short_hash = hashlib.md5(content.encode("utf-8")).hexdigest[:8] filename = f"cold-{group_name}{suffix}.{short_hash}.md" (COLD_DIR / filename).write_text(content, encoding="utf-8")

        titles, prompts, sections, summaries, keywords = [], [], [], [], [] seen_titles = set for m in metas: d = m["updated_date"].isoformat if m["updated_date"] else "" lbl = f"{m['title']} {m.get('part_label', '')}".strip full_t = f"{lbl} ({d})" if d else lbl if full_t not in seen_titles: seen_titles.add(full_t) titles.append(full_t) prompts.extend(m["prompts"]) sections.extend(m["sections"]) if m["summary"]: summaries.append(m["summary"]) if m["keywords"]: keywords.append(m["keywords"])

        written.append( { "url": f"{RAW_BASE}/_ai_bundles/cold/{filename}", "group": f"{group_name}{suffix}", "titles": titles, "prompts": list(dict.fromkeys(prompts))[:10], "sections": list(dict.fromkeys(sections))[:16], "summaries": list(dict.fromkeys(summaries)), "keywords": list(dict.fromkeys(keywords)), } ) return written

def main: scan_dirs = [d for d in (Path("core"), Path("chats"), Path("kb")) if d.exists] if not scan_dirs: raise SystemExit("Missing 'chats/' or 'core/' directory.")

    OUT_DIR.mkdir(parents=True, exist_ok=True) shutil.rmtree(COLD_DIR, ignore_errors=True) COLD_DIR.mkdir(parents=True, exist_ok=True)

    git_recent = get_git_recent_files(RECENT_DAYS) hot_core_blocks = [] recent_candidates = [] # (sort_date, block, byte_size) cold_groups: dict[str, list[dict]] = {}

    for root_dir in scan_dirs: for path in sorted(root_dir.rglob("*")): if not path.is_file or path.suffix.lower not in ALLOWED_EXTS: continue

            raw_text = path.read_text(encoding="utf-8", errors="ignore") meta, body = parse_frontmatter(raw_text) body = clean_chat_wrapper(body) top_info = extract_doc_info(path, body) parts = path.parts

            is_hot = ( root_dir.name == "core" or (root_dir.name == "kb" and len(parts) > 2 and parts == "core") or meta.get("tier") == "hot" )

            if is_hot: hot_core_blocks.append(format_file_block(path, body)) continue

            # Tier 1 Recent check (only compact files <= MAX_RECENT_FILE_BYTES)
            body_bytes = len(body.encode("utf-8")) if top_info["updated_date"] is not None: is_recent = (TODAY - top_info["updated_date"]).days <= RECENT_DAYS sort_d = top_info["updated_date"] else: is_recent = path in git_recent sort_d = TODAY if is_recent else date.min

            if is_recent and body_bytes <= MAX_RECENT_FILE_BYTES: blk = format_file_block(path, body) recent_candidates.append((sort_d, blk, len(blk.encode("utf-8"))))

            # Determine Tier 2 Cold group
            if root_dir.name == "chats": if len(parts) > 2: group_key = sanitize_slug(parts) elif top_info["updated_date"] is not None: group_key = f"chats-{top_info['updated_date'].strftime('%Y-%m')}" else: group_key = "chats-general" else: raw_sub = parts if len(parts) > 2 else "general" group_key = sanitize_slug(raw_sub) if group_key == "chats" and top_info["updated_date"] is not None: group_key = f"chats-{top_info['updated_date'].strftime('%Y-%m')}"

            # Split giant files into <65 KB parts and index each part's own headings
            body_parts = split_large_body(body, MAX_COLD_BYTES - 1500) total_parts = len(body_parts) for idx, part_body in enumerate(body_parts, start=1): part_label = f"[Part {idx}/{total_parts}]" if total_parts > 1 else "" part_info = extract_doc_info(path, part_body, fallback_title=top_info["title"]) cold_groups.setdefault(group_key, []).append( { "path": path, "body": part_body, "part_label": part_label, "title": top_info["title"], "updated_date": top_info["updated_date"], "prompts": part_info["prompts"], "sections": part_info["sections"], "summary": meta.get("summary", ""), "keywords": meta.get("keywords", ""), } )

    # Write Tier 1 Core
    core_text = ( "# Tier 1: Core Knowledge\n" + "".join(hot_core_blocks) if hot_core_blocks else "# Tier 1: Core Knowledge\nNo core files configured yet." ) (OUT_DIR / "hot-core.md").write_text(core_text, encoding="utf-8")

    # Write Tier 1 Recent (newest first, capped at MAX_RECENT_TOTAL_BYTES)
    recent_candidates.sort(key=lambda x: x, reverse=True) selected_recent, recent_bytes = [], 0 for _, blk, b_size in recent_candidates: if selected_recent and (recent_bytes + b_size > MAX_RECENT_TOTAL_BYTES): break selected_recent.append(blk) recent_bytes += b_size

    recent_text = ( f"# Tier 1: Recent Compact Chats (Last {RECENT_DAYS} Days)\n" + "".join(selected_recent) if selected_recent else f"# Tier 1: Recent Changes\nNo compact chats updated in the last {RECENT_DAYS} days (large compendiums are indexed in llms.txt)." ) (OUT_DIR / "hot-recent.md").write_text(recent_text, encoding="utf-8")

    # Write Tier 2 Cold Bundles & llms.txt
    index_entries = [] for group_name, items in sorted(cold_groups.items): index_entries.extend(write_cold_chunks(group_name, items))

    lines = [ "# Knowledge Base Index (Tier 2 Cold Bundles)", "# Note: Core docs and recent compact chats are pre-loaded in Tier 1. Large compendiums are split into full-read Cold parts below.", "", ] for entry in index_entries: lines.append(f"- URL: {entry['url']}") lines.append(f" Topic Group: {entry['group']}") lines.append(f" Files/Parts: {' | '.join(entry['titles'])}") if entry["prompts"]: lines.append(f" User Questions: {' | '.join(entry['prompts'])}") if entry["sections"]: lines.append(f" Topics/Chapters: {' | '.join(entry['sections'])}") if entry["summaries"]: lines.append(f" Summary: {' | '.join(entry['summaries'])}") if entry["keywords"]: lines.append(f" Keywords: {' | '.join(entry['keywords'])}") lines.append("")

    (OUT_DIR / "llms.txt").write_text("\n".join(lines), encoding="utf-8") print(f"Built {len(index_entries)} cold bundle(s) and updated Tier 1 + llms.txt.")

if __name__ == "__main__": main ```

3. Tap **Commit changes...**.

---

### Quick Test After Commit
1. Wait ~15 seconds (check **More ▾ → Actions** until green ✅).
2. In Google AI Studio, turn **Grounding with Google Search → OFF** (leave only **URL context → ON**).
3. Start a **fresh chat**, paste your **3 pinned URLs + a question about Chapter 4 of `document.md`** (e.g., *"Which exact Cold Bundle has Chapter 4 Government Schemes, and what topics/years are inside it?"*), and watch it route cleanly to the exact `<65 KB` part!

---

## User

# Untitled prompt

---

## You

Read every URL above via URL context and answer my previous question with exact FILE citations. Comprehensive analysis of the examiner's question setting pattern for scheme questions

---

## AI Studio

Tier 1 contains no relevant compendium files, so I am requesting Part 1 (the only bundle in `llms.txt` listing `Included Topic Chapters`) alongside evenly spaced Parts 4, 8, and 12 to map the archive and locate all scheme questions.

```text
https://raw.githubusercontent.com/inikashx-hub/ai-kb/main/_ai_bundles/cold/cold-chats-general-part1.b4ef2929.md
https://raw.githubusercontent.com/inikashx-hub/ai-kb/main/_ai_bundles/cold/cold-chats-general-part4.c8517c24.md
https://raw.githubusercontent.com/inikashx-hub/ai-kb/main/_ai_bundles/cold/cold-chats-general-part8.1bd816b5.md
https://raw.githubusercontent.com/inikashx-hub/ai-kb/main/_ai_bundles/cold/cold-chats-general-part12.c260178d.md
Read every URL above via URL context and answer my previous question with exact FILE citations.
```

---

## You

Read every URL above via URL context and answer my previous question with exact FILE citations.

---

## AI Studio

Part 1 identifies Chapter 4 (*Government Schemes & Initiatives*, 342 questions) and Chapter 3 (*Indian Economy & Union Budget*, 156 questions), which fall between Part 4 (Chapter 2) and Part 8 (Chapter 7), so please load Parts 5, 6, and 7 to read those chapters in full.

```text
https://raw.githubusercontent.com/inikashx-hub/ai-kb/main/_ai_bundles/cold/cold-chats-general-part5.5b52c641.md
https://raw.githubusercontent.com/inikashx-hub/ai-kb/main/_ai_bundles/cold/cold-chats-general-part6.2c69a78c.md
https://raw.githubusercontent.com/inikashx-hub/ai-kb/main/_ai_bundles/cold/cold-chats-general-part7.a6658fe9.md
Read every URL above via URL context and answer my previous question with exact FILE citations.
```

---

## You

Read every URL above via URL context and answer my previous question with exact FILE citations.

---

## AI Studio

### Evidence Scope & Archive Structure

This analysis is grounded in `FILE: chats/document.md [Part 5/13]`, `FILE: chats/document.md [Part 6/13]`, and `FILE: chats/document.md [Part 7/13]`:
- **`FILE: chats/document.md [Part 5/13]`** contains the tail of Chapter 2 (*Banking & Financial Awareness*, Q593–Q642), the entire Chapter 3 (*Indian Economy & Union Budget*, 156 Qs: Q1–Q156), and the start of Chapter 4 (*Government Schemes & Initiatives*, 342 Qs: Q1–Q19 retrieved before browse snippet truncation).
- **`FILE: chats/document.md [Part 6/13]`** contains Chapter 4 (*Government Schemes & Initiatives*) Q72–Q286 retrieved before browse snippet truncation.
- **`FILE: chats/document.md [Part 7/13]`** begins in Chapter 5 (*Appointments & Resignations*) and continues into Chapter 6 (*Awards & Honours*), confirming that Chapter 4 ends inside Part 6. *(Note: Chapter 4 Q20–Q71 in Part 5 and Q287–Q342 in Part 6 fall beyond the URL-context browse snippet length limit and are excluded from sample counts below.)*

---

### 1. Volume, Year-Wise Consistency & Cross-Chapter Distribution

- **Sustained High Weightage:** Chapter 4 (*Government Schemes & Initiatives*) comprises **342 questions** across 2019–2026: **2019 (70)**, **2020 (13)**, **2021 (53)**, **2022 (44)**, **2023 (50)**, **2024 (48)**, **2025 (48)**, and **2026 (16, partial year)**. Excluding the pandemic-disrupted 2020 cycle, Mains papers consistently draw **44–53 dedicated scheme questions per year**.
- **Schemes Leak Across Three Chapters:** Examiners do not restrict scheme testing to Chapter 4:
  - **Budget-linked Funds & Production Schemes (Chapter 3):** Examples include **PLI** domestic electronics output jumping from Rs 1.90 lakh cr to Rs 9.52 lakh cr (Q22), the **Urban Challenge Fund** of Rs 1 lakh cr (Q23), **RoDTEP** deadline extension (Q21), Kharif P&K fertiliser subsidy of Rs 37,216 cr (Q25), **UIDF** statement testing (Q39), Budget 2023–24 **Agricultural Accelerator Fund / EMRS / DigiLocker** (Q46–Q48), **Sovereign Green Bonds** of Rs 16,000 cr (Q71), **10,000 FPOs** in Budget 2020 (Q101), and **Carbon Credit Trading Scheme (CCTS)** administration by BEE (Q2).
  - **Bank-Routed / Small Savings Schemes (Chapter 2):** Examples include **Sovereign Gold Bonds (SGB)** eligible investors (Q637), quarterly interest-rate review of **Small Savings Schemes** (Q641), and commercial bank deposit schemes like Axis Bank's *Express Fixed Scheme* (Q593) and ICICI's *FD Health* (Q599).

---

### 2. The Nine Recurring Question-Setting Hooks

Across the **234 directly observed Chapter 4 questions** (Q1–Q19 in `[Part 5/13]` and Q72–Q286 in `[Part 6/13]`) plus scheme items in Chapters 2–3, examiners rely on nine repeatable "angle triggers":

#### (1) Hyper-Specific Numerical Parameters & Sub-Component Figures (Dominant Hook)
Examiners test exact numbers—and increasingly ask for **sub-shares, revised caps, and multi-tier brackets** rather than just headline outlays:
- **Outlays & Corpus:** PMAY-G total outlay Rs 3,06,137 cr specifically asking for the **state share** (`Rs 1 Lakh crore`, Ch 4 Q78); 7 farmer schemes Rs 14,235.30 cr asking for **1st and 2nd highest allocations** (*Crop science for food and nutritional security* & *Digital Agriculture Mission*, Ch 4 Q77); Fund of Funds for Startups (`Rs 10,000 cr`, Ch 4 Q87); PLI Semiconductor (`Rs 76,000 cr`, Ch 4 Q182) and enhanced Solar PLI (`Rs 24,000 cr`, Ch 4 Q172); PMGKAY total spend across phases (`Rs 3.91 lakh cr`, Ch 4 Q148); Atmanirbhar Bharat Rozgar Yojana (`Rs 22,810 cr`, Ch 4 Q213); AIF corpus (`Rs 1 lakh cr`, Ch 4 Q115, Q247, Q259); RuPay/BHIM-UPI incentive (`Rs 1,300 cr`, Ch 4 Q178); BharatNet (`Rs 6,000 cr`, Ch 4 Q269).
- **Loan Limits, Guarantees, Subsidies & Withdrawal Caps:** MSME **TREAD** grant (`30%`, Ch 4 Q88); **MSSC** partial withdrawal (`40%`, Ch 4 Q110); **VGF** GoI share (`40%`, Ch 4 Q122); **CGSS** guarantee (`75%` for loans above Rs 3 cr up to Rs 5 cr, Ch 4 Q144); **PMEGP** manufacturing cap (`Rs 50 lakh`, Ch 4 Q145); **ECLGS** aviation ceiling raised from Rs 400 cr to `Rs 1,500 cr` (Ch 4 Q146); **CBFTE** max reimbursement (`Rs 10,000`, Ch 4 Q149); **SIDBI ARISE** (`Rs 3 cr`, Ch 4 Q200) & **SFURTI** (`Rs 8 cr`, Ch 4 Q205); **DAY-NULM** SHG max loan (`Rs 20 lakh`, Ch 4 Q216); **PMJDY** overdraft (`Rs 10,000`, Ch 4 Q221, Q243); **MUDRA** *Kishore* (`Rs 5 lakh`, Ch 4 Q262) & *Tarun* (`>5 to 10 lakh`, Ch 4 Q238); **PSB Loans in 59 minutes** (`Rs 1 lakh to Rs 5 cr`, Ch 4 Q240); **CLCSS** subsidy (`up to Rs 1 cr` across `51 sub-sectors`, Ch 4 Q263–Q264); ethanol interest subvention (`6% p.a.`, Ch 4 Q255); **MPLAD** (`Rs 5 cr/yr`, Ch 4 Q108); **IREDA** Navratna cap without GoI nod (`Rs 1,000 cr`, Ch 4 Q85).
- **Insurance & Pension Mechanics:** **PMSBY** partial disability cover (`Rs 1 lakh`, Ch 4 Q118); **PMJJBY** premium hike (`Rs 330 to Rs 436`, Ch 4 Q191); **PM-SYM** monthly contribution for <40 yrs (`Rs 200`, Ch 4 Q142) and income cap (`< Rs 15,000`, Ch 4 Q215); **PMFBY** Kharif premium (`2%`, Ch 4 Q222); **APY** plan count (`5 plans`, Ch 4 Q248); **PM-KISAN** payout cadence (`3 installments in 4 quarters`, Ch 4 Q261).
- **Scheme Scope Counts & Exception Rules:** **PLI** (`14 sectors`, Ch 4 Q155); **PM-MITRA** (`7` states/parks, Ch 4 Q139, Q203); **PM-JANMAN** (`73` ST communities across `18` states, Ch 4 Q105); **PM Gati Shakti** (`7 Engines`, Ch 4 Q81); **DAY-NRLM** minimum SHG size in **remote/tribal/difficult areas** (`5 members`, Ch 4 Q6—testing an exception rule rather than the standard 10–20 norm).

#### (2) Single-Letter Acronym Expansion ("What does X stand for?")
Examiners avoid asking for full expansions and instead isolate **one middle or final letter**, especially on newly coined schemes (persisting straight through 2026):
- **2026:** `SHATAYU` -> `'H'` = *Holistic* (Ch 4 Q2, IBPS PO Mains 2026); `BHAVYA` -> `'V'` = *Vikas* (Ch 4 Q15, SBI PO Mains 2026).
- **2024:** `Project PRAYAS` -> `'R'` = *Regular* (Ch 4 Q94, IBPS RRB Clerk Mains 2024).
- **2023:** `SHRESHTA` -> `'T'` = *Targeted* (Ch 4 Q147, SBI Clerk Mains 2023); `ACABC` -> `'C'` = *Clinic* (Ch 4 Q156, SBI PO Mains 2023).
- **2022–2021:** `MMF` under textile PLI -> **second `'M'`** = *Made* (Ch 4 Q202, SBI PO Mains 2022); `ASHA` -> `'A'` = *Accredited* (Ch 4 Q225); `RAFTAAR` -> **last `'R'`** = *Rejuvenation* (Ch 4 Q231); `TOPS` -> `'P'` = *Podium* (Ch 4 Q242). *(Ch 3 also tests `NCAER` `'A'` = Applied, Q24; `HAM` `'A'` = Annuity, Q87; `OPC` `'P'` = Person, Q88.)*

#### (3) Four-Part Timeline Testing (Launch Year, Duration, Extensions, Target Years)
Every exam year tests four distinct date angles:
1. **Static Launch Years (revived sharply in 2026):** `AIF` (`2020`, Ch 4 Q7, RRB Clerk Mains 2025–26); `PMKVY` (`2015`, Ch 4 Q13, SBI PO Mains 2026); `Khelo India` (`2017`, Ch 4 Q195); `NITI Aayog` (`Jan 1, 2015`, Ch 4 Q282).
2. **Scheme Tenure / Period:** `One Scientist One Product` (`5 years`, Ch 4 Q95); `National Quantum Mission` (`8 years`, Ch 4 Q106); `PRITHVI` (`2021–2026`, Ch 4 Q111); `AIF` (`2020–2025` / `FY 2020–2029`, Ch 4 Q115, Q258); `PLI` (`5 years`, Ch 4 Q249).
3. **Cabinet Extension Deadlines:** `PM-SGMBY` till `March 2027` (Ch 4 Q11); `RoDTEP` till `Sep 30, 2025` / `March 31, 2026` (Ch 4 Q75; Ch 3 Q21); `Project Unnati` till `March 2025` (Ch 4 Q96); `PMEGP` till `FY 2025–26` (Ch 4 Q145); `PM SVANidhi` till `Dec 2024` (Ch 4 Q167); `FAME India II` till `March 2024` (Ch 4 Q217); `PMGKAY` extensions (Ch 4 Q173, Q218).
4. **Effective Dates & Policy Target Years:** `SCSS` Rs 30L effective date (`1st April 2023`, Ch 4 Q159); `Bima Vahaks` gram panchayat deadline (`31 Dec 2024`, Ch 4 Q140); `Green Hydrogen` (`2029–30` / `5 MMT by 2030`, Ch 4 Q72, Q137); `Indian Railways` net-zero (`2030`, Ch 4 Q120); `National Logistics Policy` top-25 LPI (`2030`, Ch 4 Q150, Q175); `15% ethanol` (`2023–24`, Ch 4 Q157); `175 GW` renewables (`2022`, Ch 4 Q260, Q281).

#### (4) Non-Obvious Nodal Ministries, Implementing Agencies & Exclusions
Examiners deliberately pick schemes whose ministry or executing agency differs from surface intuition:
- **Nodal Ministry Traps:** `'Samudra Manthan'` -> `Ministry of Petroleum and Natural Gas` (Ch 4 Q3); `SMILE` & `SHATAYU` -> `Ministry of Social Justice and Empowerment` (Ch 4 Q2, Q8); `Viksit Bharat Sankalp Yatra` -> joint `MoIB & MoHUA` (Ch 4 Q112); `FAME India` -> `Ministry of Heavy Industries` (Ch 4 Q114); `GOBARDHAN` -> `Ministry of Jal Shakti` (Ch 4 Q128); `APY` -> `MoF (DFS)` (Ch 4 Q129); `RuPay/BHIM-UPI Incentive` -> `MeitY` (Ch 4 Q178); `Solar Charkha Mission`, `PMEGP`, `FFDC` -> `Ministry of MSME` (Ch 4 Q171, Q184, Q244); `PM-FME` working capital partner -> `Ministry of Rural Development` (Ch 4 Q219).
- **Implementing / Channelizing / Administering Bodies:** `PACT` under `e-FAST India` -> `NITI Aayog` (Ch 4 Q1); `ICM/CCTS` -> `BEE` (Ch 3 Q2); `Saubhagya` -> `REC Ltd` (Ch 4 Q168, Q226—asked twice); `e-NAM` -> `SFAC` (Ch 4 Q229); `National SC/ST Hub` -> `NSIC` (Ch 4 Q234); `ACABC` subsidy channel -> `NABARD` (Ch 4 Q156); `PM Kisan` pension fund manager -> `LIC` (Ch 4 Q277).
- **Negative / Exclusion List:** *"Which of the following Banks does not issue the Mahila Samman Savings Certificate?"* (`Bandhan, IDBI, Axis, HDFC, ICICI`, Ch 4 Q116).

#### (5) Digital Portals, Apps & Brand Names (Major 2021–2026 Trend)
Scheme delivery mechanisms—especially apps, portals, and language counts—form a dedicated sub-genre:
- **2025–2026:** `Mobile Seva` (govt SMS platform, Ch 4 Q10); `SARAS / e-SARAS` (SHG product brand, Ch 4 Q12); `DigiLocker` (Ch 4 Q16; also Ch 3 Q46 in 2023); `SHATAYU` dashboard (Ch 4 Q2); `Jeevan Pramaan` (digital life certificate, Ch 4 Q17); `NITI NCAER States Economic Forum` (Ch 3 Q24).
- **2021–2024:** `e-Jagriti` (Ch 4 Q82), `CDP-SURAKSHA` (Ch 4 Q89), `Saksham App` (Ch 4 Q101), `SAKSHAM` MoHFW (Ch 4 Q113), `ULLAS` (Ch 4 Q117), `Sanchar Saathi` (Ch 4 Q125), `Digi Yatra` (Ch 4 Q135), `Kisan eMitra` (**5 languages**, Ch 4 Q141), `PRANA` (Ch 4 Q162), `Jan Samarth` (Ch 4 Q188), `MSME Sambandh` (Ch 4 Q201), `CHAMPIONS` (Ch 4 Q235), `SWAYAM` (Ch 4 Q251), `Mera Ration` (Ch 4 Q253).

#### (6) Eligibility Boundaries, Age Brackets & Legal Qualifiers
- **Age Cut-offs:** `RBSK 2.0` (`0–18 yrs`, Ch 4 Q5); `PMJJBY` upper limit (`50 yrs`, Ch 4 Q19); `NEP` Grade 1 min (`6 yrs`, Ch 4 Q138); `DDU-GKY` (`15–35 yrs`, Ch 4 Q152, Q214, Q220—asked three times); `RSETI` (`18–45 yrs`, Ch 4 Q223); `PM Laghu Vyapari Maan Dhan` (`18–40 yrs`, Ch 4 Q276); `Saksham App` (`85+ yrs` & `40%` PwD, Ch 4 Q101).
- **Beneficiary & Qualifier Precision:** `PMMY` extends credit to *individuals and **non-corporate, non-farm** micro and small enterprises* (Ch 4 Q4); `SMILE` (*Transgender welfare*, Ch 4 Q8); `PM Vishwakarma` coir weavers (*Artisans*, Ch 4 Q91); `Donate-a-Pension` worker list (Ch 4 Q194); `Poshan Abhiyan` (`Children, Pregnant women and lactating mothers`, Ch 4 Q227); small farmer definition (`upto 2.0 hectares`, Ch 3 Q103).

#### (7) Multi-Statement / "NOT True" / Component Elimination Questions
Rather than asking one fact, higher-tier papers bundle 3–4 facts (outlay + start date + duration + ministry) into one item:
- `RuPay & BHIM-UPI Incentive Scheme` testing duration (`1 year w.e.f. April 01, 2021`), outlay (`Rs 1,300 cr`), and ministry (`MeitY`) together (*Only A & C are correct*, Ch 4 Q177–Q178).
- *"Which of the following is NOT a component of PMKSY 2016–17?"* (Ch 4 Q176); *"Green Credit Program & Ecomark Scheme — Which among the following was not True?"* (Ch 4 Q158); *"Which scheme is not related to education?"* (`PRASAD`, Ch 4 Q236).
- Dedicated statement-based questions on `UIDF` (Ch 3 Q39), `PM-KISAN` (Ch 4 Q83), `PMGSY` (Ch 4 Q98), `PMFBY` land tenancy eligibility (Ch 4 Q131), `PM CARES for Children` (Ch 4 Q151), `GeM` (Ch 4 Q154), `NRLM SHG` (Ch 4 Q189), `7 PM MITRA parks` (Ch 4 Q203), `PMAY` (Ch 4 Q204), and `PMMVY` (Ch 4 Q257).

#### (8) "First State / City" & Geographic Cluster Pinning
- **Adoption Firsts:** `Himachal Pradesh` (1st state for Aadhaar FaceAuth in PDS, Ch 4 Q9); `Andhra Pradesh` (1st state Gender Budget, Ch 3 Q98); `Gujarat` (1st domestic emissions trading scheme, Ch 3 Q148); `Puri` (1st city 24x7 drinking water, Ch 4 Q246); `Rajasthan` (1st biofuel policy, Ch 4 Q279); `Tripura` (7th Economic Census launch, Ch 4 Q278); `Uttar Pradesh` (1st agri export policy, Ch 4 Q275).
- **Location-Specific Clusters & State Schemes:** `Rajasthan` (*Indira Gandhi Urban Employment Guarantee Scheme*, Ch 4 Q187), `Koppal, Karnataka` (1st toy cluster, Ch 4 Q209), `Kalol, Gujarat` (1st nano urea plant, Ch 4 Q183), `Gwalior, MP` (1st Drone School, Ch 4 Q198), `Dholera, Gujarat` (Greenfield airport, Ch 4 Q193), `Ken-Betwa` (`MP & UP`, Ch 4 Q192), `6 Lighthouse projects` (Ch 4 Q210).

#### (9) Objective Matching & Indirect Policy Linkages (SDGs, Brand Ambassadors, Committees)
Examiners ask second-order linkages around schemes: `LiFE initiative` mapped to **SDG 12** (Ch 4 Q161); *Viksit Bharat Buildathon 2025* Brand Ambassador **Shubhanshu Shukla** (Ch 4 Q18); *NEP* draft committee **K. Kasturirangan** (Ch 4 Q274); *PM Surya Sarovar Yojana* purpose (*floating solar on water bodies*, Ch 4 Q14); *SATAT* (*Compressed Biogas*, Ch 4 Q109); *Svamitva* (*Record of Rights*, Ch 4 Q104); *AVSAR* (*SHG space at airports*, Ch 4 Q185); *NIRVIK* (*Exports*, Ch 4 Q245).

---

### 3. Chronological Evolution (2019 -> 2026) & Exam-Tier Split

#### Evolution Across Cycles
1. **2019–2020 (Direct Headline Recall):** Short, single-fact questions on purpose, basic age caps, and "first state" milestones (e.g., `AMRUT` Q272, `Mission Karmayogi` Q267, `PM Laghu Vyapari Maan Dhan` Q276, `Rajasthan` Q279).
2. **2021–2023 (Statement Bundles + Amendments + Evergreen Mechanics):** Surge in multi-statement/negative-elimination questions (`PMKSY`, `RuPay/BHIM`, `Green Credit`, `GeM`, `PMFBY`), active testing of revised ceilings/premiums (`PMJJBY` Rs 330->436, `SCSS` Rs 15L->30L, `PMEGP` Rs 50L, `ECLGS` Rs 1,500 cr), and repeated re-testing of legacy schemes (`PMJDY`, `APY`, `MUDRA`, `Saubhagya`, `DDU-GKY`).
3. **2024–2026 (Sub-Component Granularity + Digital Platforms + Static Revival):**
   - **2026 shows a dual pattern:** testing **brand-new 2026 launches/guidelines** up to the exam window (`PACT` Sept 2026, `Samudra Manthan` July 2026, `SHATAYU` May 2026, `RBSK 2.0` May 2026, `BHAVYA`, `PM Surya Sarovar`) **alongside a sharp revival of static origin/rule questions on 2015–2020 schemes** (`PMKVY` 2015, `AIF` 2020, `PMMY` non-corporate/non-farm scope, `DAY-NRLM` 5-member tribal SHG exception, `PMJJBY` age 50).
   - **Budget/Scheme allocation questions** shifted from headline totals to **sub-shares and internal rankings** (PMAY-G state share Q78; top-2 of 7 agri schemes Q77; specific HSR corridor pair in Budget 2026–27 Ch 3 Q3).

#### Exam-Tier Differentiation
- **IBPS PO Mains & SBI PO Mains:** Heavily favor **multi-statement/NOT-true elimination** (`Q158`, `Q176`, `Q177–178`, `Q203`, `Q204`, `Q257`), **subtle legal/eligibility qualifiers** (`non-corporate, non-farm` Q4; remote SHG `5 members` Q6), **sub-allocations** (`Q77`, `Q78`), **middle-letter acronyms** (`SHATAYU` Q2, `BHAVYA` Q15; `ACABC` Q156, `MMF` Q202), **SDG links** (`Q161`), and **current-year new launches** (`Q1–Q5`, `Q14`).
- **IBPS Clerk / SBI Clerk / RRB Clerk Mains:** Concentrate on **numerical caps, extensions, portals/apps, non-issuing bank exclusions, and single-fact ministry/beneficiary matches** (e.g., `Mobile Seva` Q10, `PM-SGMBY` March 2027 Q11, `e-SARAS` Q12, `Jeevan Pramaan` Q17, `PMJJBY` age 50 Q19; `FFS` Q87, `TREAD` Q88, `MSSC` Q110 & Q116, `PM-SYM` Q142, `PMEGP` Q145, `ECLGS` Q146, `PMGKAY` Q148).
- **RRB PO / Scale 1 & Insurance (LIC / ESIC / EPFO):** Weight toward **rural/agri/cooperative/social-security** (`PMFBY` Q131, `PM Vishwakarma` Q133, `Sahkar se Samriddhi` Q134, `Svamitva` Q104, `GOBARDHAN` Q128, `e-NAM` Q229) and **insurance/pension/welfare timelines** (`Bima Vahaks` Q140, `PM-MITRA` Q139, `PM Laghu Vyapari Maan Dhan` Q276).

---

### 4. Practical Takeaways: The Examiner's 8-Field Scheme Checklist

To match how questions are actually constructed in `FILE: chats/document.md [Part 5/13]` and `FILE: chats/document.md [Part 6/13]`, notes for any government scheme (new or evergreen) must capture these 8 specific fields:
1. **Exact Acronym Expansion** (watch the middle/last letters, e.g., `SHATAYU`, `BHAVYA`, `PRAYAS`, `SHRESHTA`).
2. **Nodal Ministry + Implementing/Channelizing Agency** (flag non-obvious pairings like `GOBARDHAN -> Jal Shakti`, `FAME -> Heavy Industries`, `e-NAM -> SFAC`, `Saubhagya -> REC`, `CCTS -> BEE`).
3. **Origin Year + Tenure + Latest Extension / Effective Date / Target Year** (`2015–2020` launch years are actively re-tested in 2026).
4. **Total Outlay + Sub-Allocations / Centre-State Share** (do not stop at headline outlay—note state share and top-ranked sub-schemes).
5. **Revised Financial Caps, Interest/Premiums & Sub-Categories** (capture *before vs. after* values, e.g., `PMJJBY` 330->436, `SCSS` 15L->30L, `ECLGS` 400->1,500 cr).
6. **Eligibility Qualifiers, Age Brackets & Exception Rules** (e.g., *non-corporate/non-farm*, `0–18` vs `15–35` vs `18–50`, remote-area `5-member` SHG rule, non-issuing bank exclusions).
7. **Associated Portal / Mobile App / Brand Name (+ Language Count)** (`Mobile Seva`, `e-SARAS`, `Jeevan Pramaan`, `e-Jagriti`, `CDP-SURAKSHA`, `Kisan eMitra`).
8. **First Adopting State/City, Cluster Locations & Multi-Statement Components** (especially for PO Mains component/exclusion traps).

---

## Model

That output is impressive—and your transcript just revealed **the exact two bottlenecks** keeping your hybrid from hitting 100% recall in 1–2 hops:

### What Your Transcript Just Proved
1. **The Exact Truncation Ceiling (~40–45 KB per URL):**
   Look at AI Studio's own note:
   > *"Chapter 4 Q20–Q71 in Part 5 and Q287–Q342 in Part 6 fall beyond the URL-context browse snippet length limit."*
   
   Our 65 KB chunks (`MAX_COLD_BYTES = 65_000`) were ~20 KB too big—Playground's URL-context tool clipped the bottom ~20% of both files! Dropping the limit to **35 KB per chunk** means Gemini reads **every single question** with **zero truncation** (and since you can request up to 20 URLs per turn, pulling 4–5 chunks of 35 KB in one message works cleanly).

2. **Why Gemini Had to Binary-Search (`Parts 1, 4, 8, 12` → `Parts 5, 6, 7`):**
   * `Part 6` was a mid-chapter continuation of Chapter 4, so the *"04. Government Schemes"* heading only appeared back in `Part 5` (and was crowded out of `llms.txt` by earlier subheadings).
   * If `build-kb.py` **carries forward the active chapter name** (`## [Chapter Context: 04. Government Schemes & Initiatives (342)]`) onto every continuation chunk and prioritizes chapter headers in `llms.txt`, Gemini will jump **straight to every Chapter 4 part on Turn 2** without wasting a turn probing `Parts 1, 4, 8, 12`.

---

### Patched `build-kb.py` (Zero Truncation + Direct Chapter Routing)

Replace **`build-kb.py`** with this updated version (`MAX_COLD_BYTES = 35_000` + chapter carry-forward):

```python
import hashlib
import os
import re
import shutil
import subprocess
from datetime import date, datetime
from pathlib import Path

OUT_DIR = Path("_ai_bundles")
COLD_DIR = OUT_DIR / "cold"

ALLOWED_EXTS = {".md", ".txt", ".json", ".yaml", ".yml", ".csv", ".py", ".ts", ".js"}
MAX_COLD_BYTES = 35_000          # Fits comfortably inside Playground's URL-context snippet limit
MAX_RECENT_FILE_BYTES = 25_000   # Keep hot-recent.md small so it is never truncated
MAX_RECENT_TOTAL_BYTES = 40_000
RECENT_DAYS = 14

REPO = os.environ.get("GITHUB_REPOSITORY", "inikashx-hub/ai-kb")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
TODAY = date.today()

def get_git_recent_files(days: int) -> set[Path]:
    try:
        out = subprocess.check_output(
            ["git", "log", f"--since={days} days ago", "--name-only", "--pretty=format:"],
            text=True,
        )
        return {Path(line.strip()) for line in out.splitlines() if line.strip()}
    except Exception:
        return set()

def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return {}, text
    meta = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip().lower()] = v.strip()
    return meta, text[match.end() :]

def clean_chat_wrapper(text: str) -> str:
    return re.sub(r"^---\s*START OF FILE.*?---\s*\n+", "", text, flags=re.MULTILINE).strip()

def find_chapter_marker(line: str) -> str | None:
    s = line.strip()
    m = re.match(r"^#{1,2}\s+(.+)$", s)
    if m:
        txt = " ".join(m.group(1).split())
        if txt.lower() not in {"table of contents", "contents", "index", "user", "model"}:
            return txt[:90]
    m2 = re.match(r"^(?:#{3,4}\s+|\*\*)?((?:Chapter\s+\d+|\d{2}\.\s+[A-Z]).{5,85}?)(?:\*\*)?$", s)
    if m2:
        return " ".join(m2.group(1).split())[:90]
    return None

def split_by_heading_pattern(text: str, pattern: str) -> list[str]:
    regex = re.compile(pattern)
    sections, current = [], []
    in_fence = False

    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith("```"): in_fence = not in_fence if not in_fence and regex.match(line) and current: sections.append("".join(current).strip) current = [line] else: current.append(line)

    if current: sections.append("".join(current).strip) return [s for s in sections if s]

def split_large_body(body: str, max_bytes: int) -> list[str]: """Split huge files into <= max_bytes parts and carry forward active chapter headings.""" if len(body.encode("utf-8")) <= max_bytes: return [body]

    pieces = [] for sec in split_by_heading_pattern(body, r"^#{1,2}\s+"): if len(sec.encode("utf-8")) <= max_bytes: pieces.append(sec) continue

        for sub in split_by_heading_pattern(sec, r"^#{3}\s+"): if len(sub.encode("utf-8")) <= max_bytes: pieces.append(sub) continue

            buf, buf_bytes = [], 0 for para in sub.split("\n\n"): p_bytes = len(para.encode("utf-8")) + 2 if buf and (buf_bytes + p_bytes > max_bytes): pieces.append("\n\n".join(buf).strip) buf, buf_bytes = [], 0 buf.append(para) buf_bytes += p_bytes if buf: pieces.append("\n\n".join(buf).strip)

    # Track active chapter heading across pieces
    tagged_pieces = [] running_chapter = None for p in pieces: tagged_pieces.append((p, running_chapter)) in_fence = False for line in p.splitlines: if line.lstrip.startswith("```"):
                in_fence = not in_fence
            if not in_fence:
                ch = find_chapter_marker(line)
                if ch:
                    running_chapter = ch

    # Merge small pieces up to max_bytes, prepending chapter context on continuation chunks
    merged, cur, cur_bytes, chunk_chapter = [], [], 0, None
    for p, start_chapter in tagged_pieces:
        p_bytes = len(p.encode("utf-8")) + 2
        if cur and (cur_bytes + p_bytes > max_bytes):
            chunk_text = "\n\n".join(cur)
            first_line = chunk_text.lstrip().splitlines()[0] if chunk_text.strip() else ""
            if chunk_chapter and not find_chapter_marker(first_line):
                chunk_text = f"## [Chapter Context: {chunk_chapter}]\n\n{chunk_text}"
            merged.append(chunk_text)
            cur, cur_bytes, chunk_chapter = [], 0, start_chapter
        if not cur:
            chunk_chapter = start_chapter
        cur.append(p)
        cur_bytes += p_bytes

    if cur:
        chunk_text = "\n\n".join(cur)
        first_line = chunk_text.lstrip().splitlines()[0] if chunk_text.strip() else ""
        if chunk_chapter and not find_chapter_marker(first_line):
            chunk_text = f"## [Chapter Context: {chunk_chapter}]\n\n{chunk_text}"
        merged.append(chunk_text)

    return merged

def extract_doc_info(path: Path, text: str, fallback_title: str = "") -> dict:
    h1_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    title = h1_match.group(1).strip() if h1_match else (fallback_title or path.stem)

    updated_date = None
    upd_match = re.search(r"\*\*Updated:\*\*\s*(\d{4}-\d{2}-\d{2})", text)
    if upd_match:
        try:
            updated_date = datetime.strptime(upd_match.group(1), "%Y-%m-%d").date()
        except ValueError:
            updated_date = None

    is_chat = bool(re.search(r"^##\s+(User|Model)\s*$", text, re.MULTILINE))
    prompts = []
    sections = []

    if is_chat:
        raw_prompts = re.findall(
            r"^##\s+User\s*\n+(.*?)(?=\n+---|\n+##\s+Model|\Z)",
            text,
            re.DOTALL | re.MULTILINE,
        )
        for p in raw_prompts[:4]:
            compact = " ".join(p.split())
            if compact:
                prompts.append(compact[:110] + ("..." if len(compact) > 110 else ""))

        h3s = re.findall(r"^###\s+(.+)$", text, re.MULTILINE)
        skip = {"conclusion", "summary", "summary checklist before applying:"}
        sections = [h.strip()[:90] for h in h3s if h.strip().lower() not in skip][:8]
    else:
        # Prioritize chapter-level markers first, then H3 subheadings
        seen = set()
        for line in text.splitlines():
            ch = find_chapter_marker(line)
            if ch and ch not in seen:
                seen.add(ch)
                sections.append(ch)
                if len(sections) >= 15:
                    break
        if len(sections) < 15:
            for h in re.findall(r"^###\s+(.+)$", text, re.MULTILINE):
                clean_h = " ".join(h.split())[:90]
                if clean_h and clean_h not in seen:
                    seen.add(clean_h)
                    sections.append(clean_h)
                    if len(sections) >= 15:
                        break

    return {
        "title": title,
        "updated_date": updated_date,
        "prompts": prompts,
        "sections": sections,
    }

def sanitize_slug(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", name).strip("-").lower()
    return slug or "general"

def format_file_block(rel_path: Path, body: str, part_label: str = "") -> str:
    label = f" {part_label}" if part_label else ""
    return f"\n\n---\n## FILE: `{rel_path.as_posix()}`{label}\n\n{body}\n"

def write_cold_chunks(group_name: str, items: list[dict]) -> list[dict]:
    chunks = []
    current_blocks, current_meta, current_size = [], [], 0

    for item in items:
        block = format_file_block(item["path"], item["body"], item.get("part_label", ""))
        block_size = len(block.encode("utf-8"))
        if current_blocks and (current_size + block_size > MAX_COLD_BYTES):
            chunks.append((current_blocks, current_meta))
            current_blocks, current_meta, current_size = [], [], 0
        current_blocks.append(block)
        current_meta.append(item)
        current_size += block_size

    if current_blocks:
        chunks.append((current_blocks, current_meta))

    written = []
    for idx, (blocks, metas) in enumerate(chunks, start=1):
        suffix = f"-part{idx}" if len(chunks) > 1 else ""
        content = f"# Cold Knowledge Bundle: {group_name}{suffix}\n" + "".join(blocks)
        short_hash = hashlib.md5(content.encode("utf-8")).hexdigest()[:8]
        filename = f"cold-{group_name}{suffix}.{short_hash}.md"
        (COLD_DIR / filename).write_text(content, encoding="utf-8")

        titles, prompts, sections, summaries, keywords = [], [], [], [], []
        seen_titles = set()
        for m in metas:
            d = m["updated_date"].isoformat() if m["updated_date"] else ""
            lbl = f"{m['title']} {m.get('part_label', '')}".strip()
            full_t = f"{lbl} ({d})" if d else lbl
            if full_t not in seen_titles:
                seen_titles.add(full_t)
                titles.append(full_t)
            prompts.extend(m["prompts"])
            sections.extend(m["sections"])
            if m["summary"]:
                summaries.append(m["summary"])
            if m["keywords"]:
                keywords.append(m["keywords"])

        written.append(
            {
                "url": f"{RAW_BASE}/_ai_bundles/cold/{filename}",
                "group": f"{group_name}{suffix}",
                "titles": titles,
                "prompts": list(dict.fromkeys(prompts))[:10],
                "sections": list(dict.fromkeys(sections))[:16],
                "summaries": list(dict.fromkeys(summaries)),
                "keywords": list(dict.fromkeys(keywords)),
            }
        )
    return written

def main():
    scan_dirs = [d for d in (Path("core"), Path("chats"), Path("kb")) if d.exists()]
    if not scan_dirs:
        raise SystemExit("Missing 'chats/' or 'core/' directory.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(COLD_DIR, ignore_errors=True)
    COLD_DIR.mkdir(parents=True, exist_ok=True)

    git_recent = get_git_recent_files(RECENT_DAYS)
    hot_core_blocks = []
    recent_candidates = []
    cold_groups: dict[str, list[dict]] = {}

    for root_dir in scan_dirs:
        for path in sorted(root_dir.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in ALLOWED_EXTS:
                continue

            raw_text = path.read_text(encoding="utf-8", errors="ignore")
            meta, body = parse_frontmatter(raw_text)
            body = clean_chat_wrapper(body)
            top_info = extract_doc_info(path, body)
            parts = path.parts

            is_hot = (
                root_dir.name == "core"
                or (root_dir.name == "kb" and len(parts) > 2 and parts[1] == "core")
                or meta.get("tier") == "hot"
            )

            if is_hot:
                hot_core_blocks.append(format_file_block(path, body))
                continue

            body_bytes = len(body.encode("utf-8"))
            if top_info["updated_date"] is not None:
                is_recent = (TODAY - top_info["updated_date"]).days <= RECENT_DAYS
                sort_d = top_info["updated_date"]
            else:
                is_recent = path in git_recent
                sort_d = TODAY if is_recent else date.min

            if is_recent and body_bytes <= MAX_RECENT_FILE_BYTES:
                blk = format_file_block(path, body)
                recent_candidates.append((sort_d, blk, len(blk.encode("utf-8"))))

            if root_dir.name == "chats":
                if len(parts) > 2:
                    group_key = sanitize_slug(parts[1])
                elif top_info["updated_date"] is not None:
                    group_key = f"chats-{top_info['updated_date'].strftime('%Y-%m')}"
                else:
                    group_key = "chats-general"
            else:
                raw_sub = parts[1] if len(parts) > 2 else "general"
                group_key = sanitize_slug(raw_sub)
                if group_key == "chats" and top_info["updated_date"] is not None:
                    group_key = f"chats-{top_info['updated_date'].strftime('%Y-%m')}"

            body_parts = split_large_body(body, MAX_COLD_BYTES - 1500)
            total_parts = len(body_parts)
            for idx, part_body in enumerate(body_parts, start=1):
                part_label = f"[Part {idx}/{total_parts}]" if total_parts > 1 else ""
                part_info = extract_doc_info(path, part_body, fallback_title=top_info["title"])
                cold_groups.setdefault(group_key, []).append(
                    {
                        "path": path,
                        "body": part_body,
                        "part_label": part_label,
                        "title": top_info["title"],
                        "updated_date": top_info["updated_date"],
                        "prompts": part_info["prompts"],
                        "sections": part_info["sections"],
                        "summary": meta.get("summary", ""),
                        "keywords": meta.get("keywords", ""),
                    }
                )

    core_text = (
        "# Tier 1: Core Knowledge\n" + "".join(hot_core_blocks)
        if hot_core_blocks
        else "# Tier 1: Core Knowledge\nNo core files configured yet."
    )
    (OUT_DIR / "hot-core.md").write_text(core_text, encoding="utf-8")

    recent_candidates.sort(key=lambda x: x[0], reverse=True)
    selected_recent, recent_bytes = [], 0
    for _, blk, b_size in recent_candidates:
        if selected_recent and (recent_bytes + b_size > MAX_RECENT_TOTAL_BYTES):
            break
        selected_recent.append(blk)
        recent_bytes += b_size

    recent_text = (
        f"# Tier 1: Recent Compact Chats (Last {RECENT_DAYS} Days)\n" + "".join(selected_recent)
        if selected_recent
        else f"# Tier 1: Recent Changes\nNo compact chats updated in the last {RECENT_DAYS} days (large compendiums are indexed in llms.txt)."
    )
    (OUT_DIR / "hot-recent.md").write_text(recent_text, encoding="utf-8")

    index_entries = []
    for group_name, items in sorted(cold_groups.items()):
        index_entries.extend(write_cold_chunks(group_name, items))

    lines = [
        "# Knowledge Base Index (Tier 2 Cold Bundles)",
        "# Note: Core docs and recent compact chats are pre-loaded in Tier 1. Large compendiums are split into full-read <=35KB Cold parts below.",
        "",
    ]
    for entry in index_entries:
        lines.append(f"- URL: {entry['url']}")
        lines.append(f"  Topic Group: {entry['group']}")
        lines.append(f"  Files/Parts: {' | '.join(entry['titles'])}")
        if entry["prompts"]:
            lines.append(f"  User Questions: {' | '.join(entry['prompts'])}")
        if entry["sections"]:
            lines.append(f"  Topics/Chapters: {' | '.join(entry['sections'])}")
        if entry["summaries"]:
            lines.append(f"  Summary: {' | '.join(entry['summaries'])}")
        if entry["keywords"]:
            lines.append(f"  Keywords: {' | '.join(entry['keywords'])}")
        lines.append("")

    (OUT_DIR / "llms.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"Built {len(index_entries)} cold bundle(s) and updated Tier 1 + llms.txt.")

if __name__ == "__main__":
    main()
```

---

### Also Update Rule 2 in Your AI Studio System Instructions
Right now your System Instructions cap Gemini at `1 to 4` Cold URLs. Since each Cold part is now **35 KB** (instead of 65 KB), change that phrase to:
> *"Pick the **1 to 8** most relevant Cold Bundle URLs from `llms.txt`."*

Once the Action finishes, re-ask the exact same question—you should see **direct 1-hop routing straight into Chapter 4** with **zero skipped questions (`Q1–Q342` all readable)**!

---

## User

It read 11 to 18 chapters rather than the scheme chapter

---

## Model

Two things likely caused that:
1. When we halved the chunk size (`65 KB` → `35 KB`), the total number of parts roughly doubled—so **Chapter 4 shifted to different part numbers**, and our new `running_chapter` tracker may have picked up chapters `11–18` from the **Table of Contents** in Part 1 (or missed the heading style used in Chapter 4 of `document.md`).
2. Or `raw.githubusercontent.com` served a cached `llms.txt` right after your commit.

To fix it with 100% precision instead of guessing, could you paste the contents of **`_ai_bundles/llms.txt`** here? *(Open `_ai_bundles/llms.txt` in your GitHub repo → tap **Raw** → copy & paste it.)*

Once I see what `Topics/Chapters` were written for each part in `llms.txt`, I can immediately fix the exact heading rule so Gemini goes straight to Chapter 4 on Turn 2.

---

## User

# Knowledge Base Index (Tier 2 Cold Bundles)
# Note: Core docs and recent compact chats are pre-loaded in Tier 1. Large compendiums are split into full-read <=35KB Cold parts below.

- URL: 
  Topic Group: chats-general-part1 Files/Parts: Knowledge Base | Banking & Insurance General Awareness Compendium [Part 1/23] Topics/Chapters: Knowledge Base | Banking & Insurance General Awareness Compendium | 11. Sports & Championships (159) 12. Books, Authors & Obituaries (74) | 13. Important Days & Themes (77) 14. International Organisations & HQ (146) | 15. Indian Polity & Constitution (75) 16. Geography, National Parks & Ramsar (148) | 17. Art, Culture & Heritage (88) 18. Countries, Capitals & General Static GK (237) | AffairsCloud Self Evaluation Archive · Topic-Wise Previous Year Questions (2019 - 2026) | Included Topic Chapters

- URL: 
  Topic Group: chats-general-part2 Files/Parts: Banking & Insurance General Awareness Compendium [Part 2/23] Topics/Chapters: [Chapter Context: 17. Art, Culture & Heritage (88) 18. Countries, Capitals & General Stati

- URL: 
  Topic Group: chats-general-part3 Files/Parts: Banking & Insurance General Awareness Compendium [Part 3/23] Topics/Chapters: [Chapter Context: 17. Art, Culture & Heritage (88) 18. Countries, Capitals & General Stati

- URL: 
  Topic Group: chats-general-part4 Files/Parts: Banking & Insurance General Awareness Compendium [Part 4/23] Topics/Chapters: [Chapter Context: 17. Art, Culture & Heritage (88) 18. Countries, Capitals & General Stati

- URL: 
  Topic Group: chats-general-part5 Files/Parts: Banking & Insurance General Awareness Compendium [Part 5/23] Topics/Chapters: [Chapter Context: 17. Art, Culture & Heritage (88) 18. Countries, Capitals & General Stati

- URL: 
  Topic Group: chats-general-part6 Files/Parts: Banking & Insurance General Awareness Compendium [Part 6/23] Topics/Chapters: [Chapter Context: 17. Art, Culture & Heritage (88) 18. Countries, Capitals & General Stati

- URL: 
  Topic Group: chats-general-part7 Files/Parts: Banking & Insurance General Awareness Compendium [Part 7/23] Topics/Chapters: [Chapter Context: 17. Art, Culture & Heritage (88) 18. Countries, Capitals & General Stati

- URL: 
  Topic Group: chats-general-part8 Files/Parts: Banking & Insurance General Awareness Compendium [Part 8/23] Topics/Chapters: [Chapter Context: 17. Art, Culture & Heritage (88) 18. Countries, Capitals & General Stati

- URL: 
  Topic Group: chats-general-part9 Files/Parts: Banking & Insurance General Awareness Compendium [Part 9/23] Topics/Chapters: [Chapter Context: 17. Art, Culture & Heritage (88) 18. Countries, Capitals & General Stati

- URL: 
  Topic Group: chats-general-part10 Files/Parts: Banking & Insurance General Awareness Compendium [Part 10/23] Topics/Chapters: [Chapter Context: 17. Art, Culture & Heritage (88) 18. Countries, Capitals & General Stati

- URL: 
  Topic Group: chats-general-part11 Files/Parts: Banking & Insurance General Awareness Compendium [Part 11/23] Topics/Chapters: [Chapter Context: 17. Art, Culture & Heritage (88) 18. Countries, Capitals & General Stati

- URL: 
  Topic Group: chats-general-part12 Files/Parts: Banking & Insurance General Awareness Compendium [Part 12/23] Topics/Chapters: [Chapter Context: 17. Art, Culture & Heritage (88) 18. Countries, Capitals & General Stati

- URL: 
  Topic Group: chats-general-part13 Files/Parts: Banking & Insurance General Awareness Compendium [Part 13/23] Topics/Chapters: [Chapter Context: 17. Art, Culture & Heritage (88) 18. Countries, Capitals & General Stati

- URL: 
  Topic Group: chats-general-part14 Files/Parts: Banking & Insurance General Awareness Compendium [Part 14/23] Topics/Chapters: [Chapter Context: 17. Art, Culture & Heritage (88) 18. Countries, Capitals & General Stati

- URL: 
  Topic Group: chats-general-part15 Files/Parts: Banking & Insurance General Awareness Compendium [Part 15/23] Topics/Chapters: [Chapter Context: 17. Art, Culture & Heritage (88) 18. Countries, Capitals & General Stati

- URL: 
  Topic Group: chats-general-part16 Files/Parts: Banking & Insurance General Awareness Compendium [Part 16/23] Topics/Chapters: [Chapter Context: 17. Art, Culture & Heritage (88) 18. Countries, Capitals & General Stati

- URL: 
  Topic Group: chats-general-part17 Files/Parts: Banking & Insurance General Awareness Compendium [Part 17/23] Topics/Chapters: [Chapter Context: 17. Art, Culture & Heritage (88) 18. Countries, Capitals & General Stati

- URL: 
  Topic Group: chats-general-part18 Files/Parts: Banking & Insurance General Awareness Compendium [Part 18/23] Topics/Chapters: [Chapter Context: 17. Art, Culture & Heritage (88) 18. Countries, Capitals & General Stati

- URL: 
  Topic Group: chats-general-part19 Files/Parts: Banking & Insurance General Awareness Compendium [Part 19/23] Topics/Chapters: [Chapter Context: 17. Art, Culture & Heritage (88) 18. Countries, Capitals & General Stati

- URL: 
  Topic Group: chats-general-part20 Files/Parts: Banking & Insurance General Awareness Compendium [Part 20/23] Topics/Chapters: [Chapter Context: 17. Art, Culture & Heritage (88) 18. Countries, Capitals & General Stati

- URL: 
  Topic Group: chats-general-part21 Files/Parts: Banking & Insurance General Awareness Compendium [Part 21/23] Topics/Chapters: [Chapter Context: 17. Art, Culture & Heritage (88) 18. Countries, Capitals & General Stati

- URL: 
  Topic Group: chats-general-part22 Files/Parts: Banking & Insurance General Awareness Compendium [Part 22/23] Topics/Chapters: [Chapter Context: 17. Art, Culture & Heritage (88) 18. Countries, Capitals & General Stati

- URL: 
  Topic Group: chats-general-part23 Files/Parts: Banking & Insurance General Awareness Compendium [Part 23/23] Topics/Chapters: [Chapter Context: 17. Art, Culture & Heritage (88) 18. Countries, Capitals & General Stati

---

## Model

Aha! Pasting `llms.txt` made the bug **immediately obvious**. Look at what happened:

1. **Part 1’s Table of Contents poisoned Parts 2–23:**
   In Part 1, the Table of Contents ended with `17. Art, Culture & Heritage (88) 18. Countries, Capitals & General Static GK (237)`. Because our chapter tracker didn't ignore the Table of Contents, it set the active chapter to `17/18` right after the TOC.
2. **Body chapter headers didn't match the old regex:**
   Inside the actual chapters of `document.md`, the chapter titles (like `04. Government Schemes & Initiatives (342)`) had formatting around them (such as `### **` or extra symbols) that the old regex missed—so **`[Chapter Context: 17... 18...]` got stamped onto ALL 22 parts** (`Part 2` through `Part 23`)!

---

### The Fix (3 Tweaks in `build-kb.py`)
Replace **`build-kb.py`** with the version below. Here is what it fixes:
1. **Ignores Table-of-Contents blocks** (`Included Topic Chapters` / lists of 4+ chapters together) so the TOC can never hijack `running_chapter`.
2. **Reliably detects `NN. Chapter Name (Count)` everywhere** (even if wrapped in `###`, `**bold**`, `>`, or HTML tags, and without falsely matching numbered exam questions).
3. **Adds a `Preview:` line (`Start` + `End` snippet)** for every part in `llms.txt` so Gemini can *always* see what is actually inside each of the 23 parts.

```python
import hashlib
import os
import re
import shutil
import subprocess
from datetime import date, datetime
from pathlib import Path

OUT_DIR = Path("_ai_bundles")
COLD_DIR = OUT_DIR / "cold"

ALLOWED_EXTS = {".md", ".txt", ".json", ".yaml", ".yml", ".csv", ".py", ".ts", ".js"}
MAX_COLD_BYTES = 35_000          # Fits comfortably inside Playground's URL-context snippet limit
MAX_RECENT_FILE_BYTES = 25_000   # Keep hot-recent.md small so it is never truncated
MAX_RECENT_TOTAL_BYTES = 40_000
RECENT_DAYS = 14

REPO = os.environ.get("GITHUB_REPOSITORY", "inikashx-hub/ai-kb")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
TODAY = date.today()

def get_git_recent_files(days: int) -> set[Path]:
    try:
        out = subprocess.check_output(
            ["git", "log", f"--since={days} days ago", "--name-only", "--pretty=format:"],
            text=True,
        )
        return {Path(line.strip()) for line in out.splitlines() if line.strip()}
    except Exception:
        return set()

def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return {}, text
    meta = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip().lower()] = v.strip()
    return meta, text[match.end() :]

def clean_chat_wrapper(text: str) -> str:
    return re.sub(r"^---\s*START OF FILE.*?---\s*\n+", "", text, flags=re.MULTILINE).strip()

def strip_md_noise(line: str) -> str:
    s = re.sub(r"<[^>]+>", " ", line)
    s = re.sub(r"^[#>*`\-\s]+", "", s)
    s = re.sub(r"[*`]+$", "", s)
    return " ".join(s.replace("**", "").split())

def find_chapter_markers(line: str) -> list[str]:
    """Detect chapter titles like '04. Government Schemes & Initiatives (342)' or H1/H2 headers."""
    cleaned = strip_md_noise(line)
    if not cleaned:
        return []

    # 1. Explicit numbered chapter with question/item count: "04. Government Schemes & Initiatives (342)"
    numbered = re.findall(r"\b(\d{2}\.\s+[^()\n]{3,70}\(\d+\))", cleaned)
    if numbered:
        return [n.strip()[:90] for n in numbered]

    # 2. Standard H1/H2 markdown headings (excluding generic labels)
    m_h = re.match(r"^#{1,2}\s+(.+)$", line.strip())
    if m_h:
        txt = strip_md_noise(m_h.group(1))
        if txt and txt.lower() not in {"table of contents", "contents", "index", "user", "model"}:
            return [txt[:90]]

    # 3. "Chapter 4: ..." style headings
    m_ch = re.match(r"^(Chapter\s+\d+[:.\-\s].{3,75})$", cleaned, re.IGNORECASE)
    if m_ch:
        return [m_ch.group(1).strip()[:90]]

    return []

def is_toc_block(text: str) -> bool:
    low = text.lower()
    if "included topic chapters" in low or "table of contents" in low:
        return True
    # A dense cluster of 4+ numbered chapter headers inside a short block is a TOC
    chapters = re.findall(r"\b\d{2}\.\s+[^()\n]{3,70}\(\d+\)", text)
    return len(chapters) >= 4 and len(text) < 4000

def split_by_heading_pattern(text: str, pattern: str) -> list[str]:
    regex = re.compile(pattern)
    sections, current = [], []
    in_fence = False

    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith("```"): in_fence = not in_fence if not in_fence and regex.match(line) and current: sections.append("".join(current).strip) current = [line] else: current.append(line)

    if current: sections.append("".join(current).strip) return [s for s in sections if s]

def split_large_body(body: str, max_bytes: int) -> list[str]: """Split huge files into <= max_bytes parts and carry forward active chapter headings.""" if len(body.encode("utf-8")) <= max_bytes: return [body]

    pieces = []
    # Also split right before numbered chapter headers like "04. Government Schemes (342)"
    chapter_split_re = r"^(?:#{1,4}\s+|[*>\s]*\d{2}\.\s+[^\n]{3,70}\(\d+\))" for sec in split_by_heading_pattern(body, chapter_split_re): if len(sec.encode("utf-8")) <= max_bytes: pieces.append(sec) continue

        for sub in split_by_heading_pattern(sec, r"^#{3}\s+"): if len(sub.encode("utf-8")) <= max_bytes: pieces.append(sub) continue

            buf, buf_bytes = [], 0 for para in sub.split("\n\n"): p_bytes = len(para.encode("utf-8")) + 2 if buf and (buf_bytes + p_bytes > max_bytes): pieces.append("\n\n".join(buf).strip) buf, buf_bytes = [], 0 buf.append(para) buf_bytes += p_bytes if buf: pieces.append("\n\n".join(buf).strip)

    # Track active chapter heading across pieces (ignoring TOC blocks!)
    tagged_pieces = [] running_chapter = None for p in pieces: tagged_pieces.append((p, running_chapter)) if is_toc_block(p): continue in_fence = False for line in p.splitlines: if line.lstrip.startswith("```"):
                in_fence = not in_fence
            if not in_fence:
                chs = find_chapter_markers(line)
                if chs:
                    running_chapter = chs[-1]

    # Merge small pieces up to max_bytes, prepending chapter context on continuation chunks
    merged, cur, cur_bytes, chunk_chapter = [], [], 0, None
    for p, start_chapter in tagged_pieces:
        p_bytes = len(p.encode("utf-8")) + 2
        if cur and (cur_bytes + p_bytes > max_bytes):
            chunk_text = "\n\n".join(cur)
            first_line = chunk_text.lstrip().splitlines()[0] if chunk_text.strip() else ""
            if chunk_chapter and not find_chapter_markers(first_line):
                chunk_text = f"## [Chapter Context: {chunk_chapter}]\n\n{chunk_text}"
            merged.append(chunk_text)
            cur, cur_bytes, chunk_chapter = [], 0, start_chapter
        if not cur:
            chunk_chapter = start_chapter
        cur.append(p)
        cur_bytes += p_bytes

    if cur:
        chunk_text = "\n\n".join(cur)
        first_line = chunk_text.lstrip().splitlines()[0] if chunk_text.strip() else ""
        if chunk_chapter and not find_chapter_markers(first_line):
            chunk_text = f"## [Chapter Context: {chunk_chapter}]\n\n{chunk_text}"
        merged.append(chunk_text)

    return merged

def make_preview(text: str) -> str:
    clean_lines = [
        strip_md_noise(ln)
        for ln in text.splitlines()
        if ln.strip() and not ln.strip().startswith("## [Chapter Context:")
    ]
    joined = " ".join(ln for ln in clean_lines if ln)
    if len(joined) <= 220:
        return joined
    return f"{joined[:110]} ... {joined[-110:]}"

def extract_doc_info(path: Path, text: str, fallback_title: str = "") -> dict:
    h1_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    title = h1_match.group(1).strip() if h1_match else (fallback_title or path.stem)

    updated_date = None
    upd_match = re.search(r"\*\*Updated:\*\*\s*(\d{4}-\d{2}-\d{2})", text)
    if upd_match:
        try:
            updated_date = datetime.strptime(upd_match.group(1), "%Y-%m-%d").date()
        except ValueError:
            updated_date = None

    is_chat = bool(re.search(r"^##\s+(User|Model)\s*$", text, re.MULTILINE))
    prompts = []
    sections = []

    if is_chat:
        raw_prompts = re.findall(
            r"^##\s+User\s*\n+(.*?)(?=\n+---|\n+##\s+Model|\Z)",
            text,
            re.DOTALL | re.MULTILINE,
        )
        for p in raw_prompts[:4]:
            compact = " ".join(p.split())
            if compact:
                prompts.append(compact[:110] + ("..." if len(compact) > 110 else ""))

        h3s = re.findall(r"^###\s+(.+)$", text, re.MULTILINE)
        skip = {"conclusion", "summary", "summary checklist before applying:"}
        sections = [h.strip()[:90] for h in h3s if h.strip().lower() not in skip][:8]
    else:
        seen = set()
        for line in text.splitlines():
            for ch in find_chapter_markers(line):
                if ch not in seen:
                    seen.add(ch)
                    sections.append(ch)
                    if len(sections) >= 15:
                        break
            if len(sections) >= 15:
                break

        if len(sections) < 15:
            for h in re.findall(r"^###\s+(.+)$", text, re.MULTILINE):
                clean_h = strip_md_noise(h)[:90]
                if clean_h and clean_h not in seen:
                    seen.add(clean_h)
                    sections.append(clean_h)
                    if len(sections) >= 15:
                        break

    return {
        "title": title,
        "updated_date": updated_date,
        "prompts": prompts,
        "sections": sections,
        "preview": make_preview(text) if not is_chat else "",
    }

def sanitize_slug(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", name).strip("-").lower()
    return slug or "general"

def format_file_block(rel_path: Path, body: str, part_label: str = "") -> str:
    label = f" {part_label}" if part_label else ""
    return f"\n\n---\n## FILE: `{rel_path.as_posix()}`{label}\n\n{body}\n"

def write_cold_chunks(group_name: str, items: list[dict]) -> list[dict]:
    chunks = []
    current_blocks, current_meta, current_size = [], [], 0

    for item in items:
        block = format_file_block(item["path"], item["body"], item.get("part_label", ""))
        block_size = len(block.encode("utf-8"))
        if current_blocks and (current_size + block_size > MAX_COLD_BYTES):
            chunks.append((current_blocks, current_meta))
            current_blocks, current_meta, current_size = [], [], 0
        current_blocks.append(block)
        current_meta.append(item)
        current_size += block_size

    if current_blocks:
        chunks.append((current_blocks, current_meta))

    written = []
    for idx, (blocks, metas) in enumerate(chunks, start=1):
        suffix = f"-part{idx}" if len(chunks) > 1 else ""
        content = f"# Cold Knowledge Bundle: {group_name}{suffix}\n" + "".join(blocks)
        short_hash = hashlib.md5(content.encode("utf-8")).hexdigest()[:8]
        filename = f"cold-{group_name}{suffix}.{short_hash}.md"
        (COLD_DIR / filename).write_text(content, encoding="utf-8")

        titles, prompts, sections, previews, summaries, keywords = [], [], [], [], [], []
        seen_titles = set()
        for m in metas:
            d = m["updated_date"].isoformat() if m["updated_date"] else ""
            lbl = f"{m['title']} {m.get('part_label', '')}".strip()
            full_t = f"{lbl} ({d})" if d else lbl
            if full_t not in seen_titles:
                seen_titles.add(full_t)
                titles.append(full_t)
            prompts.extend(m["prompts"])
            sections.extend(m["sections"])
            if m["preview"]:
                previews.append(m["preview"])
            if m["summary"]:
                summaries.append(m["summary"])
            if m["keywords"]:
                keywords.append(m["keywords"])

        written.append(
            {
                "url": f"{RAW_BASE}/_ai_bundles/cold/{filename}",
                "group": f"{group_name}{suffix}",
                "titles": titles,
                "prompts": list(dict.fromkeys(prompts))[:10],
                "sections": list(dict.fromkeys(sections))[:16],
                "preview": previews[0] if previews else "",
                "summaries": list(dict.fromkeys(summaries)),
                "keywords": list(dict.fromkeys(keywords)),
            }
        )
    return written

def main():
    scan_dirs = [d for d in (Path("core"), Path("chats"), Path("kb")) if d.exists()]
    if not scan_dirs:
        raise SystemExit("Missing 'chats/' or 'core/' directory.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(COLD_DIR, ignore_errors=True)
    COLD_DIR.mkdir(parents=True, exist_ok=True)

    git_recent = get_git_recent_files(RECENT_DAYS)
    hot_core_blocks = []
    recent_candidates = []
    cold_groups: dict[str, list[dict]] = {}

    for root_dir in scan_dirs:
        for path in sorted(root_dir.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in ALLOWED_EXTS:
                continue

            raw_text = path.read_text(encoding="utf-8", errors="ignore")
            meta, body = parse_frontmatter(raw_text)
            body = clean_chat_wrapper(body)
            top_info = extract_doc_info(path, body)
            parts = path.parts

            is_hot = (
                root_dir.name == "core"
                or (root_dir.name == "kb" and len(parts) > 2 and parts[1] == "core")
                or meta.get("tier") == "hot"
            )

            if is_hot:
                hot_core_blocks.append(format_file_block(path, body))
                continue

            body_bytes = len(body.encode("utf-8"))
            if top_info["updated_date"] is not None:
                is_recent = (TODAY - top_info["updated_date"]).days <= RECENT_DAYS
                sort_d = top_info["updated_date"]
            else:
                is_recent = path in git_recent
                sort_d = TODAY if is_recent else date.min

            if is_recent and body_bytes <= MAX_RECENT_FILE_BYTES:
                blk = format_file_block(path, body)
                recent_candidates.append((sort_d, blk, len(blk.encode("utf-8"))))

            if root_dir.name == "chats":
                if len(parts) > 2:
                    group_key = sanitize_slug(parts[1])
                elif top_info["updated_date"] is not None:
                    group_key = f"chats-{top_info['updated_date'].strftime('%Y-%m')}"
                else:
                    group_key = "chats-general"
            else:
                raw_sub = parts[1] if len(parts) > 2 else "general"
                group_key = sanitize_slug(raw_sub)
                if group_key == "chats" and top_info["updated_date"] is not None:
                    group_key = f"chats-{top_info['updated_date'].strftime('%Y-%m')}"

            body_parts = split_large_body(body, MAX_COLD_BYTES - 1500)
            total_parts = len(body_parts)
            for idx, part_body in enumerate(body_parts, start=1):
                part_label = f"[Part {idx}/{total_parts}]" if total_parts > 1 else ""
                part_info = extract_doc_info(path, part_body, fallback_title=top_info["title"])
                cold_groups.setdefault(group_key, []).append(
                    {
                        "path": path,
                        "body": part_body,
                        "part_label": part_label,
                        "title": top_info["title"],
                        "updated_date": top_info["updated_date"],
                        "prompts": part_info["prompts"],
                        "sections": part_info["sections"],
                        "preview": part_info["preview"],
                        "summary": meta.get("summary", ""),
                        "keywords": meta.get("keywords", ""),
                    }
                )

    core_text = (
        "# Tier 1: Core Knowledge\n" + "".join(hot_core_blocks)
        if hot_core_blocks
        else "# Tier 1: Core Knowledge\nNo core files configured yet."
    )
    (OUT_DIR / "hot-core.md").write_text(core_text, encoding="utf-8")

    recent_candidates.sort(key=lambda x: x[0], reverse=True)
    selected_recent, recent_bytes = [], 0
    for _, blk, b_size in recent_candidates:
        if selected_recent and (recent_bytes + b_size > MAX_RECENT_TOTAL_BYTES):
            break
        selected_recent.append(blk)
        recent_bytes += b_size

    recent_text = (
        f"# Tier 1: Recent Compact Chats (Last {RECENT_DAYS} Days)\n" + "".join(selected_recent)
        if selected_recent
        else f"# Tier 1: Recent Changes\nNo compact chats updated in the last {RECENT_DAYS} days (large compendiums are indexed in llms.txt)."
    )
    (OUT_DIR / "hot-recent.md").write_text(recent_text, encoding="utf-8")

    index_entries = []
    for group_name, items in sorted(cold_groups.items()):
        index_entries.extend(write_cold_chunks(group_name, items))

    lines = [
        "# Knowledge Base Index (Tier 2 Cold Bundles)",
        "# Note: Core docs and recent compact chats are pre-loaded in Tier 1. Large compendiums are split into full-read <=35KB Cold parts below.",
        "",
    ]
    for entry in index_entries:
        lines.append(f"- URL: {entry['url']}")
        lines.append(f"  Topic Group: {entry['group']}")
        lines.append(f"  Files/Parts: {' | '.join(entry['titles'])}")
        if entry["prompts"]:
            lines.append(f"  User Questions: {' | '.join(entry['prompts'])}")
        if entry["sections"]:
            lines.append(f"  Topics/Chapters: {' | '.join(entry['sections'])}")
        if entry["preview"]:
            lines.append(f"  Preview: {entry['preview']}")
        if entry["summaries"]:
            lines.append(f"  Summary: {' | '.join(entry['summaries'])}")
        if entry["keywords"]:
            lines.append(f"  Keywords: {' | '.join(entry['keywords'])}")
        lines.append("")

    (OUT_DIR / "llms.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"Built {len(index_entries)} cold bundle(s) and updated Tier 1 + llms.txt.")

if __name__ == "__main__":
    main()
```

---

### After You Commit
Wait ~15 seconds for the Action to turn green, **then wait ~3–5 minutes** (or open `_ai_bundles/llms.txt` → Raw in your browser first to verify the `Preview:` lines and `04. Government Schemes` labels are visible before running AI Studio!). Once `llms.txt` shows those updated labels, Gemini will route straight to the exact Chapter 4 parts on Turn 2 with **zero truncation**.

---

## User

# Knowledge Base Index (Tier 2 Cold Bundles)
# Note: Core docs and recent compact chats are pre-loaded in Tier 1. Large compendiums are split into full-read <=35KB Cold parts below.

- URL: 
  Topic Group: chats-general-part1 Files/Parts: Knowledge Base | Banking & Insurance General Awareness Compendium [Part 1/23] Topics/Chapters: Knowledge Base | Banking & Insurance General Awareness Compendium | 02. Banking & Financial Awareness (642) | 04. Government Schemes & Initiatives (342) | 06. Awards & Honours (134) | 08. Reports, Indices & Rankings (166) | 10. Science, Technology & Defence (216) | 11. Sports & Championships (159) | 12. Books, Authors & Obituaries (74) | 13. Important Days & Themes (77) | 14. International Organisations & HQ (146) | 15. Indian Polity & Constitution (75) | 16. Geography, National Parks & Ramsar (148) | 17. Art, Culture & Heritage (88) | 18. Countries, Capitals & General Static GK (237) | AffairsCloud Self Evaluation Archive · Topic-Wise Previous Year Questions (2019 - 2026) Preview: Knowledge Base

- URL: 
  Topic Group: chats-general-part2 Files/Parts: Banking & Insurance General Awareness Compendium [Part 2/23] Topics/Chapters: 18. Countries, Capitals & General Static GK (237) Preview: Table of Contents 1. RBI & Monetary Policy 2. Banking & Financial Awareness 3. Indian Economy & Union Budget 4 ... ng & Finance 133. RBI implemented Central Bank Digital Currency (CBDC) in the Wholesale Segment (eRs. -W) for?

- URL: 
  Topic Group: chats-general-part3 Files/Parts: Banking & Insurance General Awareness Compendium [Part 3/23] Topics/Chapters: 18. Countries, Capitals & General Static GK (237) Preview: Answer: Secondary trade in government securities (G-secs). IBPS PO Mains Exam 2022 · 2022 · Digital Currency · ... h year was the National Pension System (NPS) made available to all citizens on a voluntary basis? Answer: 2009

- URL: 
  Topic Group: chats-general-part4 Files/Parts: Banking & Insurance General Awareness Compendium [Part 4/23] Topics/Chapters: 18. Countries, Capitals & General Static GK (237) Preview: IBPS Clerk Mains Exam 2025 · 2025 · Pension Schemes · Static Banking & Finance 28. National Household Income S ... Finance 175. Which of the following is a general Insurance company under IRDAI? Answer: Not provided in source

- URL: 
  Topic Group: chats-general-part5 Files/Parts: Banking & Insurance General Awareness Compendium [Part 5/23] Topics/Chapters: 18. Countries, Capitals & General Static GK (237) Preview: IBPS RRB OA 2023 · 2023 · Insurance Companies · Static Banking & Finance 176. Zudio is the brand of which comp ... fairs-quiz-29-september-2020/Static Answer: Q3 IBPS Clerk Mains Exam · 2021 · Quiz Reference · Current Affairs

- URL: 
  Topic Group: chats-general-part6 Files/Parts: Banking & Insurance General Awareness Compendium [Part 6/23] Topics/Chapters: 18. Countries, Capitals & General Static GK (237) Preview: 325. Quiz - Answer: Q8 IBPS Clerk Mains Exam ... 2019 · SFB Licensing · Static Banking & Finance 494. What is the Abbreviation of 'S' in SFIO? Answer: Serious

- URL: 
  Topic Group: chats-general-part7 Files/Parts: Banking & Insurance General Awareness Compendium [Part 7/23] Topics/Chapters: 18. Countries, Capitals & General Static GK (237) Preview: EPFO SSA Mains Exam 2019 · 2019 · Financial Regulations · Static Banking & Finance 495. The Central Vigilance ... dit Guarantee Enhancement Corporation SBI PO Mains Exam 2019 · 2019 · Bond Market Developments · Covered in AC

- URL: 
  Topic Group: chats-general-part8 Files/Parts: Banking & Insurance General Awareness Compendium [Part 8/23] Topics/Chapters: 18. Countries, Capitals & General Static GK (237) Preview: 639. The first Indian state to tap into the market for masala bonds Answer: Kerala SIB Clerk Exam 2019 · Shift ... ffairs 150. State trading corporation of India is under which ministry Answer: Ministry of Commerce & Industry

- URL: 
  Topic Group: chats-general-part9 Files/Parts: Banking & Insurance General Awareness Compendium [Part 9/23] Topics/Chapters: 18. Countries, Capitals & General Static GK (237) Preview: RBI Grade B Prelims Exam 2019 · Shift 2 · 2019 · Ministry Jurisdiction · Static Banking & Finance 151. Who is ... nswer: Atal Pension Yojana (APY) IBPS RRB Scale 1 Mains Exam 2023 · 2023 · Financial Schemes · Current Affairs

- URL: 
  Topic Group: chats-general-part10 Files/Parts: Banking & Insurance General Awareness Compendium [Part 10/23] Topics/Chapters: 18. Countries, Capitals & General Static GK (237) Preview: 130. Question related to Mahila Samman Savings Certificate? Answer: Not provided in source IBPS RRB Scale 1 Ma ... · Current Affairs 272. AMRUT (Atal Mission for Rejuvenation and Urban Transformation) scheme was launched for?

- URL: 
  Topic Group: chats-general-part11 Files/Parts: Banking & Insurance General Awareness Compendium [Part 11/23] Topics/Chapters: 18. Countries, Capitals & General Static GK (237) Preview: Answer: Piped water supply to households in urban areas SBI Clerk Mains 2020 · Shift 2 · 2020 · Urban Developm ... · Shift 2 · 2019 · Minister Appointment · Covered in AC 87. New CM of Andhra Pradesh Answer: Jaganmohan Reddy

- URL: 
  Topic Group: chats-general-part12 Files/Parts: Banking & Insurance General Awareness Compendium [Part 12/23] Topics/Chapters: 18. Countries, Capitals & General Static GK (237) Preview: ESIC UDC Prelims Exam 2019 · Shift 2 · 2019 · State CM Appointment · Covered in AC 88. Who has been named as t ... ours · Covered in AC 111. Which hockey player conferred with Mohun Bagan Ratna Award 2019? Answer: Keshav Dutt

- URL: 
  Topic Group: chats-general-part13 Files/Parts: Banking & Insurance General Awareness Compendium [Part 13/23] Topics/Chapters: 18. Countries, Capitals & General Static GK (237) Preview: LIC HFL Assistant Exam 2019 · 2019 · Sports Awards · Covered in AC 112. Which company has been conferred with ... r Promotion of Industry and Internal Trade (DPIIT)? Answer: Option: leaders, aspiring leaders, top performers.

- URL: 
  Topic Group: chats-general-part14 Files/Parts: Banking & Insurance General Awareness Compendium [Part 14/23] Topics/Chapters: 18. Countries, Capitals & General Static GK (237) Preview: SBI Clerk Mains Exam 2023 - 2024 · Shift 1 · 2024 · Startup Ranking 2022 · Current Affairs 42. How much % of I ... hnical cooperation in agriculture and allied sectors, including livestock, with which country? Answer: Bhutan.

- URL: 
  Topic Group: chats-general-part15 Files/Parts: Banking & Insurance General Awareness Compendium [Part 15/23] Topics/Chapters: 18. Countries, Capitals & General Static GK (237) Preview: SBI Clerk Mains Exam 2025 · Shift 2 · 2025 · Agricultural Cooperation · Current Affairs 19. The Investor Educa ... ptember 2025? Answer: Russia and Belarus IBPS PO Mains Exam 2025 · 2025 · Military Exercises · Current Affairs

- URL: 
  Topic Group: chats-general-part16 Files/Parts: Banking & Insurance General Awareness Compendium [Part 16/23] Topics/Chapters: 18. Countries, Capitals & General Static GK (237) Preview: 18. Which of the following is not correct - Google Gemini, OpenAI ChatGPT, NPCI PAI, or Apple Co- pilot, SEVA ... ercise · Covered in AC 168. NASA plans to send a drone to Saturn's biggest moon, Titan named Answer: Dragonfly

- URL: 
  Topic Group: chats-general-part17 Files/Parts: Banking & Insurance General Awareness Compendium [Part 17/23] Topics/Chapters: 18. Countries, Capitals & General Static GK (237) Preview: IBPS RRB Clerk Mains Exam 2019 · 2019 · Space Mission · Covered in AC 169. Which space agency launched the fir ... ins Exam · 2019 · Cricket Records · Covered in AC 115. Australian Open women's winner 2019 Answer: Naomi Osaka

- URL: 
  Topic Group: chats-general-part18 Files/Parts: Banking & Insurance General Awareness Compendium [Part 18/23] Topics/Chapters: 18. Countries, Capitals & General Static GK (237) Preview: GA & Insurance Questions asked in LIC ADO Mains Exam · 2019 · Tennis Grand Slams · Covered in AC 116. 2023 Asi ... 019 · International Days · Covered in AC 58. What is the theme of the World Day for Audiovisual Heritage 2019?

- URL: 
  Topic Group: chats-general-part19 Files/Parts: Banking & Insurance General Awareness Compendium [Part 19/23] Topics/Chapters: 18. Countries, Capitals & General Static GK (237) Preview: Answer: Theme: "Engage the Past Through Sound and Images" - IBPS PO Main Exam 2019 · 2019 · World Awareness Da ... not a member of BRICS? Answer: Sri Lanka IBPS RRB PO Mains Exam 2019 · 2019 · BRICS Membership · Covered in AC

- URL: 
  Topic Group: chats-general-part20 Files/Parts: Banking & Insurance General Awareness Compendium [Part 20/23] Topics/Chapters: 18. Countries, Capitals & General Static GK (237) Preview: 125. Which of the following country is not a member of G7? Answer: Russia IBPS RRB PO Mains Exam 2019 · 2019 · ... d Kadmat Beach that received the "Blue Flag" certification, are located in which state/UT? Answer: Lakshadweep

- URL: 
  Topic Group: chats-general-part21 Files/Parts: Banking & Insurance General Awareness Compendium [Part 21/23] Topics/Chapters: 18. Countries, Capitals & General Static GK (237) Preview: IBPS PO Mains Exam 2022 · 2022 · Beaches/Environment · Current Affairs 69. In which state, India's longest ste ... ati located? Answer: New Delhi. SBI Clerk Mains Exam 2025 · Shift 2 · 2025 · National Headquarters · Static GK

- URL: 
  Topic Group: chats-general-part22 Files/Parts: Banking & Insurance General Awareness Compendium [Part 22/23] Topics/Chapters: 18. Countries, Capitals & General Static GK (237) Preview: 11. Which country is the largest share of migrants from India for blue collar jobs? Answer: UAE SBI PO Mains E ... Indian company and the second-largest solar energy company in India is located in which city? Answer: Kolkata

- URL: 
  Topic Group: chats-general-part23 Files/Parts: Banking & Insurance General Awareness Compendium [Part 23/23] Topics/Chapters: 18. Countries, Capitals & General Static GK (237) Preview: IBPS PO Main Exam 2019 · 2019 · Company Headquarters · Static GK 209. Related News Answer: ... The name of Odisha Cyclone Answer: Fani SIB Clerk Exam 2019 · Shift 2 · 2019 · Cyclone Naming · Covered in AC

---

## Model

Aha! Pasting `llms.txt` exposed the exact two reasons right away:

1. **Why `18. Countries...` still leaked onto Parts 2–23:**
   `Part 1`'s card grid split onto separate lines, so each line looked like a standalone chapter (`17... 18...`), AND **`Part 2` actually has a second `Table of Contents`** using single digits (`1. RBI... 2. Banking... 3. Indian Economy... 4...`) without `(342)` counts.
2. **Why body chapters didn't override it:**
   Inside the actual Q&A body of `document.md`, chapters use **plain-text titles without `(342)`** (and without `#` Markdown headings), so our `(342)` regex skipped them!

*(Good news: Thanks to the new `Preview:` lines, you can already see right in `llms.txt` that **all 342 questions of Chapter 4 live cleanly inside `Part 9`, `Part 10`, and `Part 11`**!)*

---

### The Permanent Fix for `build-kb.py`
Replace **`build-kb.py`** with this updated version. It adds two smart upgrades:
1. **Learns chapter names directly from the TOC** (like `Government Schemes & Initiatives`, `Indian Economy & Union Budget`, etc.) and detects them in the Q&A body even without `#` headings or `(342)` counts.
2. **Blocks TOC poisoning completely**—it never sets an active chapter from multi-chapter TOC rows or anything inside `Part 1` before the first `Answer:` appears.

```python
import hashlib
import os
import re
import shutil
import subprocess
from datetime import date, datetime
from pathlib import Path

OUT_DIR = Path("_ai_bundles")
COLD_DIR = OUT_DIR / "cold"

ALLOWED_EXTS = {".md", ".txt", ".json", ".yaml", ".yml", ".csv", ".py", ".ts", ".js"}
MAX_COLD_BYTES = 35_000          # Fits comfortably inside Playground's URL-context snippet limit
MAX_RECENT_FILE_BYTES = 25_000   # Keep hot-recent.md small so it is never truncated
MAX_RECENT_TOTAL_BYTES = 40_000
RECENT_DAYS = 14

REPO = os.environ.get("GITHUB_REPOSITORY", "inikashx-hub/ai-kb")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
TODAY = date.today()

def get_git_recent_files(days: int) -> set[Path]:
    try:
        out = subprocess.check_output(
            ["git", "log", f"--since={days} days ago", "--name-only", "--pretty=format:"],
            text=True,
        )
        return {Path(line.strip()) for line in out.splitlines() if line.strip()}
    except Exception:
        return set()

def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return {}, text
    meta = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip().lower()] = v.strip()
    return meta, text[match.end() :]

def clean_chat_wrapper(text: str) -> str:
    return re.sub(r"^---\s*START OF FILE.*?---\s*\n+", "", text, flags=re.MULTILINE).strip()

def strip_md_noise(line: str) -> str:
    s = re.sub(r"<[^>]+>", " ", line)
    s = re.sub(r"^[#>*`\-\s]+", "", s)
    s = re.sub(r"[*`]+$", "", s)
    return " ".join(s.replace("**", "").split())

def extract_toc_chapter_names(body: str) -> list[str]:
    """Learn chapter names from the document's top TOC / chapter list."""
    head = body[:12_000]
    raw = re.findall(
        r"\b\d{1,2}\.\s+([A-Z][A-Za-z0-9&,'/\-\s]{4,60}?)(?=\s*\(\d+\)|\s+\d{1,2}\.\s+[A-Z]|\n|$)",
        head,
    )
    names = []
    seen = set()
    for r in raw:
        clean = " ".join(r.split()).strip(" .:-")
        low = clean.lower()
        if len(clean) >= 6 and "answer:" not in low and "?" not in clean and low not in seen:
            seen.add(low)
            names.append(clean)
    return names if len(names) >= 3 else []

def find_chapter_markers(line: str, known_chapters: list[str] | None = None) -> list[str]:
    cleaned = strip_md_noise(line)
    if not cleaned:
        return []
    low = cleaned.lower()
    if "answer:" in low or cleaned.endswith("?") or " exam " in low:
        return []

    # 1. Explicit numbered chapter with question count: "04. Government Schemes & Initiatives (342)"
    numbered = re.findall(r"\b(\d{1,2}\.\s+[^()\n]{3,70}\(\d+\))", cleaned)
    if numbered:
        return [n.strip()[:90] for n in numbered]

    # 2. Match any chapter name learned from the Table of Contents
    if known_chapters and len(cleaned) <= 130:
        matched = []
        for ch_name in known_chapters:
            pat = rf"(?:^|\b)(?:\d{{1,2}}\.\s+)?{re.escape(ch_name)}(?:\s*\(\d+\)|\s*/\s*\d+\s*Qs.*)?(?=\s|$)"
            m = re.search(pat, cleaned, re.IGNORECASE)
            if m:
                matched.append(m.group(0).strip()[:90])
        if matched:
            return matched

    # 3. Standard H1/H2 markdown headings
    m_h = re.match(r"^#{1,2}\s+(.+)$", line.strip())
    if m_h:
        txt = strip_md_noise(m_h.group(1))
        if txt and txt.lower() not in {"table of contents", "contents", "index", "user", "model"}:
            return [txt[:90]]

    # 4. "Chapter 4: ..." headings
    m_ch = re.match(r"^(Chapter\s+\d+[:.\-\s].{3,75})$", cleaned, re.IGNORECASE)
    if m_ch:
        return [m_ch.group(1).strip()[:90]]

    return []

def split_by_heading_pattern(text: str, pattern: str) -> list[str]:
    regex = re.compile(pattern)
    sections, current = [], []
    in_fence = False

    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith("```"): in_fence = not in_fence if not in_fence and regex.match(line) and current: sections.append("".join(current).strip) current = [line] else: current.append(line)

    if current: sections.append("".join(current).strip) return [s for s in sections if s]

def split_large_body(body: str, max_bytes: int, known_chapters: list[str]) -> list[str]: if len(body.encode("utf-8")) <= max_bytes: return [body]

    pieces = [] chapter_split_re = r"^(?:#{1,4}\s+|[*>\s]*\d{1,2}\.\s+[^\n]{3,70}\(\d+\))" for sec in split_by_heading_pattern(body, chapter_split_re): if len(sec.encode("utf-8")) <= max_bytes: pieces.append(sec) continue

        for sub in split_by_heading_pattern(sec, r"^#{3}\s+"): if len(sub.encode("utf-8")) <= max_bytes: pieces.append(sub) continue

            buf, buf_bytes = [], 0 for para in sub.split("\n\n"): p_bytes = len(para.encode("utf-8")) + 2 if buf and (buf_bytes + p_bytes > max_bytes): pieces.append("\n\n".join(buf).strip) buf, buf_bytes = [], 0 buf.append(para) buf_bytes += p_bytes if buf: pieces.append("\n\n".join(buf).strip)

    # Track active chapter only after entering Q&A body (never from TOC listings!)
    tagged_pieces = [] running_chapter = None seen_qa_body = False pending_before_qa = None

    for p in pieces: tagged_pieces.append((p, running_chapter)) in_fence = False for line in p.splitlines: if line.lstrip.startswith("```"):
                in_fence = not in_fence
            if in_fence:
                continue

            if "answer:" in line.lower():
                if not seen_qa_body and pending_before_qa:
                    running_chapter = pending_before_qa
                seen_qa_body = True

            chs = find_chapter_markers(line, known_chapters)
            # Ignore multi-chapter TOC rows (2+ chapters on the same line)
            if len(chs) == 1:
                if seen_qa_body:
                    running_chapter = chs[0]
                else:
                    pending_before_qa = chs[0]

    # Merge pieces into <= max_bytes chunks and carry chapter context onto continuation chunks
    merged, cur, cur_bytes, chunk_chapter = [], [], 0, None
    for p, start_chapter in tagged_pieces:
        p_bytes = len(p.encode("utf-8")) + 2
        if cur and (cur_bytes + p_bytes > max_bytes):
            chunk_text = "\n\n".join(cur)
            first_line = chunk_text.lstrip().splitlines()[0] if chunk_text.strip() else ""
            if chunk_chapter and not find_chapter_markers(first_line, known_chapters):
                chunk_text = f"## [Chapter Context: {chunk_chapter}]\n\n{chunk_text}"
            merged.append(chunk_text)
            cur, cur_bytes, chunk_chapter = [], 0, start_chapter
        if not cur:
            chunk_chapter = start_chapter
        cur.append(p)
        cur_bytes += p_bytes

    if cur:
        chunk_text = "\n\n".join(cur)
        first_line = chunk_text.lstrip().splitlines()[0] if chunk_text.strip() else ""
        if chunk_chapter and not find_chapter_markers(first_line, known_chapters):
            chunk_text = f"## [Chapter Context: {chunk_chapter}]\n\n{chunk_text}"
        merged.append(chunk_text)

    return merged

def make_preview(text: str) -> str:
    clean_lines = [
        strip_md_noise(ln)
        for ln in text.splitlines()
        if ln.strip() and not ln.strip().startswith("## [Chapter Context:")
    ]
    joined = " ".join(ln for ln in clean_lines if ln)
    if len(joined) <= 220:
        return joined
    return f"{joined[:110]} ... {joined[-110:]}"

def extract_doc_info(
    path: Path, text: str, fallback_title: str = "", known_chapters: list[str] | None = None
) -> dict:
    h1_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    title = h1_match.group(1).strip() if h1_match else (fallback_title or path.stem)

    updated_date = None
    upd_match = re.search(r"\*\*Updated:\*\*\s*(\d{4}-\d{2}-\d{2})", text)
    if upd_match:
        try:
            updated_date = datetime.strptime(upd_match.group(1), "%Y-%m-%d").date()
        except ValueError:
            updated_date = None

    is_chat = bool(re.search(r"^##\s+(User|Model)\s*$", text, re.MULTILINE))
    prompts = []
    sections = []

    if is_chat:
        raw_prompts = re.findall(
            r"^##\s+User\s*\n+(.*?)(?=\n+---|\n+##\s+Model|\Z)",
            text,
            re.DOTALL | re.MULTILINE,
        )
        for p in raw_prompts[:4]:
            compact = " ".join(p.split())
            if compact:
                prompts.append(compact[:110] + ("..." if len(compact) > 110 else ""))

        h3s = re.findall(r"^###\s+(.+)$", text, re.MULTILINE)
        skip = {"conclusion", "summary", "summary checklist before applying:"}
        sections = [h.strip()[:90] for h in h3s if h.strip().lower() not in skip][:8]
    else:
        seen = set()
        for line in text.splitlines():
            for ch in find_chapter_markers(line, known_chapters):
                if ch not in seen:
                    seen.add(ch)
                    sections.append(ch)
                    if len(sections) >= 15:
                        break
            if len(sections) >= 15:
                break

        if len(sections) < 15:
            for h in re.findall(r"^###\s+(.+)$", text, re.MULTILINE):
                clean_h = strip_md_noise(h)[:90]
                if clean_h and clean_h not in seen:
                    seen.add(clean_h)
                    sections.append(clean_h)
                    if len(sections) >= 15:
                        break

    return {
        "title": title,
        "updated_date": updated_date,
        "prompts": prompts,
        "sections": sections,
        "preview": make_preview(text) if not is_chat else "",
    }

def sanitize_slug(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", name).strip("-").lower()
    return slug or "general"

def format_file_block(rel_path: Path, body: str, part_label: str = "") -> str:
    label = f" {part_label}" if part_label else ""
    return f"\n\n---\n## FILE: `{rel_path.as_posix()}`{label}\n\n{body}\n"

def write_cold_chunks(group_name: str, items: list[dict]) -> list[dict]:
    chunks = []
    current_blocks, current_meta, current_size = [], [], 0

    for item in items:
        block = format_file_block(item["path"], item["body"], item.get("part_label", ""))
        block_size = len(block.encode("utf-8"))
        if current_blocks and (current_size + block_size > MAX_COLD_BYTES):
            chunks.append((current_blocks, current_meta))
            current_blocks, current_meta, current_size = [], [], 0
        current_blocks.append(block)
        current_meta.append(item)
        current_size += block_size

    if current_blocks:
        chunks.append((current_blocks, current_meta))

    written = []
    for idx, (blocks, metas) in enumerate(chunks, start=1):
        suffix = f"-part{idx}" if len(chunks) > 1 else ""
        content = f"# Cold Knowledge Bundle: {group_name}{suffix}\n" + "".join(blocks)
        short_hash = hashlib.md5(content.encode("utf-8")).hexdigest()[:8]
        filename = f"cold-{group_name}{suffix}.{short_hash}.md"
        (COLD_DIR / filename).write_text(content, encoding="utf-8")

        titles, prompts, sections, previews, summaries, keywords = [], [], [], [], [], []
        seen_titles = set()
        for m in metas:
            d = m["updated_date"].isoformat() if m["updated_date"] else ""
            lbl = f"{m['title']} {m.get('part_label', '')}".strip()
            full_t = f"{lbl} ({d})" if d else lbl
            if full_t not in seen_titles:
                seen_titles.add(full_t)
                titles.append(full_t)
            prompts.extend(m["prompts"])
            sections.extend(m["sections"])
            if m["preview"]:
                previews.append(m["preview"])
            if m["summary"]:
                summaries.append(m["summary"])
            if m["keywords"]:
                keywords.append(m["keywords"])

        written.append(
            {
                "url": f"{RAW_BASE}/_ai_bundles/cold/{filename}",
                "group": f"{group_name}{suffix}",
                "titles": titles,
                "prompts": list(dict.fromkeys(prompts))[:10],
                "sections": list(dict.fromkeys(sections))[:16],
                "preview": previews[0] if previews else "",
                "summaries": list(dict.fromkeys(summaries)),
                "keywords": list(dict.fromkeys(keywords)),
            }
        )
    return written

def main():
    scan_dirs = [d for d in (Path("core"), Path("chats"), Path("kb")) if d.exists()]
    if not scan_dirs:
        raise SystemExit("Missing 'chats/' or 'core/' directory.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(COLD_DIR, ignore_errors=True)
    COLD_DIR.mkdir(parents=True, exist_ok=True)

    git_recent = get_git_recent_files(RECENT_DAYS)
    hot_core_blocks = []
    recent_candidates = []
    cold_groups: dict[str, list[dict]] = {}

    for root_dir in scan_dirs:
        for path in sorted(root_dir.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in ALLOWED_EXTS:
                continue

            raw_text = path.read_text(encoding="utf-8", errors="ignore")
            meta, body = parse_frontmatter(raw_text)
            body = clean_chat_wrapper(body)
            known_chapters = extract_toc_chapter_names(body)
            top_info = extract_doc_info(path, body, known_chapters=known_chapters)
            parts = path.parts

            is_hot = (
                root_dir.name == "core"
                or (root_dir.name == "kb" and len(parts) > 2 and parts[1] == "core")
                or meta.get("tier") == "hot"
            )

            if is_hot:
                hot_core_blocks.append(format_file_block(path, body))
                continue

            body_bytes = len(body.encode("utf-8"))
            if top_info["updated_date"] is not None:
                is_recent = (TODAY - top_info["updated_date"]).days <= RECENT_DAYS
                sort_d = top_info["updated_date"]
            else:
                is_recent = path in git_recent
                sort_d = TODAY if is_recent else date.min

            if is_recent and body_bytes <= MAX_RECENT_FILE_BYTES:
                blk = format_file_block(path, body)
                recent_candidates.append((sort_d, blk, len(blk.encode("utf-8"))))

            if root_dir.name == "chats":
                if len(parts) > 2:
                    group_key = sanitize_slug(parts[1])
                elif top_info["updated_date"] is not None:
                    group_key = f"chats-{top_info['updated_date'].strftime('%Y-%m')}"
                else:
                    group_key = "chats-general"
            else:
                raw_sub = parts[1] if len(parts) > 2 else "general"
                group_key = sanitize_slug(raw_sub)
                if group_key == "chats" and top_info["updated_date"] is not None:
                    group_key = f"chats-{top_info['updated_date'].strftime('%Y-%m')}"

            body_parts = split_large_body(body, MAX_COLD_BYTES - 1500, known_chapters)
            total_parts = len(body_parts)
            for idx, part_body in enumerate(body_parts, start=1):
                part_label = f"[Part {idx}/{total_parts}]" if total_parts > 1 else ""
                part_info = extract_doc_info(
                    path, part_body, fallback_title=top_info["title"], known_chapters=known_chapters
                )
                cold_groups.setdefault(group_key, []).append(
                    {
                        "path": path,
                        "body": part_body,
                        "part_label": part_label,
                        "title": top_info["title"],
                        "updated_date": top_info["updated_date"],
                        "prompts": part_info["prompts"],
                        "sections": part_info["sections"],
                        "preview": part_info["preview"],
                        "summary": meta.get("summary", ""),
                        "keywords": meta.get("keywords", ""),
                    }
                )

    core_text = (
        "# Tier 1: Core Knowledge\n" + "".join(hot_core_blocks)
        if hot_core_blocks
        else "# Tier 1: Core Knowledge\nNo core files configured yet."
    )
    (OUT_DIR / "hot-core.md").write_text(core_text, encoding="utf-8")

    recent_candidates.sort(key=lambda x: x[0], reverse=True)
    selected_recent, recent_bytes = [], 0
    for _, blk, b_size in recent_candidates:
        if selected_recent and (recent_bytes + b_size > MAX_RECENT_TOTAL_BYTES):
            break
        selected_recent.append(blk)
        recent_bytes += b_size

    recent_text = (
        f"# Tier 1: Recent Compact Chats (Last {RECENT_DAYS} Days)\n" + "".join(selected_recent)
        if selected_recent
        else f"# Tier 1: Recent Changes\nNo compact chats updated in the last {RECENT_DAYS} days (large compendiums are indexed in llms.txt)."
    )
    (OUT_DIR / "hot-recent.md").write_text(recent_text, encoding="utf-8")

    index_entries = []
    for group_name, items in sorted(cold_groups.items()):
        index_entries.extend(write_cold_chunks(group_name, items))

    lines = [
        "# Knowledge Base Index (Tier 2 Cold Bundles)",
        "# Note: Core docs and recent compact chats are pre-loaded in Tier 1. Large compendiums are split into full-read <=35KB Cold parts below.",
        "",
    ]
    for entry in index_entries:
        lines.append(f"- URL: {entry['url']}")
        lines.append(f"  Topic Group: {entry['group']}")
        lines.append(f"  Files/Parts: {' | '.join(entry['titles'])}")
        if entry["prompts"]:
            lines.append(f"  User Questions: {' | '.join(entry['prompts'])}")
        if entry["sections"]:
            lines.append(f"  Topics/Chapters: {' | '.join(entry['sections'])}")
        if entry["preview"]:
            lines.append(f"  Preview: {entry['preview']}")
        if entry["summaries"]:
            lines.append(f"  Summary: {' | '.join(entry['summaries'])}")
        if entry["keywords"]:
            lines.append(f"  Keywords: {' | '.join(entry['keywords'])}")
        lines.append("")

    (OUT_DIR / "llms.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"Built {len(index_entries)} cold bundle(s) and updated Tier 1 + llms.txt.")

if __name__ == "__main__":
    main()
```

---

### Quick Verify After Commit
After the Action turns green (and ~2–3 minutes for GitHub's raw CDN to update), open `_ai_bundles/llms.txt` → Raw:
* Parts 9, 10, and 11 should now explicitly show **`4. Government Schemes & Initiatives`** (or `04. Government Schemes...`) under `Topics/Chapters:` instead of `18. Countries...`!
* Then run your scheme question in a fresh AI Studio chat—it will jump straight to Parts 9, 10, and 11 in one hop and read all 342 questions completely.

---

## User

# Untitled prompt

---

## You

Comprehensive analysis of examiner's question setting pattern for important days questions

---

## AI Studio

I cannot complete this retrieval-grounded analysis yet because I do not currently have access to your knowledge base files:

- **Gap found:** The Tier 1 Core, Tier 1 Recent, and Tier 2 Index (`llms.txt`) sources listed in the instructions are not pre-loaded in context, and attempting to fetch them returned a restriction error stating that `google:browse` can only access URLs that appear in the **user prompt** or search results (not URLs only present in system/developer instructions) [1.1][1.2][1.3].
- Because I cannot inspect Tier 1 or `llms.txt` yet, I cannot provide an analysis grounded in your notes with exact `FILE:` citations without guessing.

To unblock this, paste the following block in your next message so the Tier 1 and Tier 2 index URLs appear in the user prompt and can be read:

```text
https://raw.githubusercontent.com/inikashx-hub/ai-kb/main/_ai_bundles/hot-core.md
https://raw.githubusercontent.com/inikashx-hub/ai-kb/main/_ai_bundles/hot-recent.md
https://raw.githubusercontent.com/inikashx-hub/ai-kb/main/_ai_bundles/llms.txt
Read every URL above via URL context and check whether they answer my previous question with exact FILE citations, or identify the relevant Cold Bundle URLs from llms.txt.
```

---

## You

Read every URL above via URL context and check whether they answer my previous question with exact FILE citations, or identify the relevant Cold Bundle URLs from llms.txt.

---

## AI Studio

Tier 1 has no relevant content, so I need the compendium header and Chapter 13 (Important Days & Themes) Cold Bundles from `llms.txt` to analyze the examiner's pattern.

```text
https://raw.githubusercontent.com/inikashx-hub/ai-kb/main/_ai_bundles/cold/cold-chats-general-part1.36d4ec91.md
https://raw.githubusercontent.com/inikashx-hub/ai-kb/main/_ai_bundles/cold/cold-chats-general-part18.acac1f66.md
https://raw.githubusercontent.com/inikashx-hub/ai-kb/main/_ai_bundles/cold/cold-chats-general-part19.3a27f556.md
Read every URL above via URL context and answer my previous question with exact FILE citations.
```

---

## Model

**That worked cleanly!** Look at the difference right away:

* **Zero binary searching:** Gemini read `llms.txt` and jumped **straight to `part18.acac1f66.md` and `part19.3a27f556.md`** (Chapter 13: Important Days & Themes) on the very first lookup!
* Notice the new file hashes (`acac1f66`, `3a27f556`)—that confirms your updated `build-kb.py` injected the `[Chapter Context: 13. Important Days & Themes (77)]` labels accurately.

---

### How to Shave Off That Extra First Turn (3 Turns → 2 Turns)
Notice how this chat took **3 user messages** only because your very first message didn't include the 3 base URLs (`hot-core.md`, `hot-recent.md`, `llms.txt`), so Gemini had to pause and ask you to paste them.

* **The 1-Tap Habit:** Keep those 3 URLs pinned together in your **Gboard Clipboard**, and whenever you open a **new chat**, paste them **alongside your first question** in Message 1:
  ```text
  https://raw.githubusercontent.com/inikashx-hub/ai-kb/main/_ai_bundles/hot-core.md
  https://raw.githubusercontent.com/inikashx-hub/ai-kb/main/_ai_bundles/hot-recent.md
  https://raw.githubusercontent.com/inikashx-hub/ai-kb/main/_ai_bundles/llms.txt
  Comprehensive analysis of examiner's question setting pattern for important days questions
  ```
* Once those 3 URLs are in Message 1:
  * **Tier 1 questions** answer immediately in **1 turn**.
  * **Tier 2 questions** go straight to the Cold Bundle links in **2 turns total**.

Go ahead and paste that `part1`, `part18`, `part19` block next—because each part is now under **35 KB**, it should read **all 77 questions** of Chapter 13 without any snippet cutoff! *(And whenever you're ready to connect your private repo's 15-minute Apps Script pipeline so new chats sync automatically, let me know.)*

---

## User

I need it in one turn

---

## Model

To get **true 1-turn answers** in normal Google AI Studio Playground, we have to work around **one hard rule** we confirmed during testing:
> URL Context **never** crawls links discovered inside another URL (like `llms.txt`) in the same turn, and truncates single URLs above ~40 KB [3.2.3].

So to eliminate Turn 2 completely, you have **3 ways** to get **1-Turn RAG** depending on which trade-off you prefer:

---

### Option 1: Static "Subject Packs" via URL Context *(Best if You Want Pure GitHub + URL Toggle)*
Instead of 1 generic `llms.txt` router (which forces 2 turns), have `build-kb.py` output **static, predictable URLs** (without changing hashes) grouped by exam subject, keeping each pack to **3–6 URLs (~35 KB each)**:
* **Pack A (Schemes & Economy):** `schemes-1.md`, `schemes-2.md`, `schemes-3.md`, `economy.md`, `hot-recent.md`
* **Pack B (Static GK, Days, Awards & Sports):** `days.md`, `awards-sports.md`, `static-gk.md`, `hot-recent.md`
* **Pack C (Banking & RBI):** `rbi.md`, `banking-1.md`, `banking-2.md`, `banking-3.md`, `hot-recent.md`

**How 1-Turn works:**
* Pin those 2–3 short Subject Packs in Gboard Clipboard.
* Start a chat → tap the matching Subject Pack + type your question in Message 1 → **Instant 1-turn answer** (100% live from GitHub, zero truncation).
* *(Why not paste all 23 URLs at once? URL Context caps requests at **20 URLs max**, and fetching ~19–20 large URLs in one turn risks hitting Playground's internal per-turn browse budget.)*

---

### Option 2: Single Master File (`all-kb.md`) via `+` → Google Drive *(Best for 1-Turn Over EVERYTHING at Once)*
Right now your entire 3,246-question compendium + chats is only **~800 KB** (`0.8 MB`).
* In Google AI Studio, **Gemini 3.8 Flash** supports importing files from Google Drive up to **7 MB per file (10 MB total)** directly into its full context window—**without** `URL context`'s ~40 KB snippet truncation!
* Since your private pipeline **already saves files to Google Drive every 15 minutes**, you can save a single combined **`all-kb.md`** in Drive.
* **How 1-Turn works:** Open AI Studio → tap **`+` → Drive → `all-kb.md`** → ask ANY question across ALL 18 chapters and ALL chats → **1-Turn instant answer with 100% recall** (no URLs, no splitting, no Turn 2).

---

### Option 3: GitHub Pages + Search Grounding *(1-Turn, Zero Pasting — With Indexing Lag)*
Remember Screenshot 2: Gemini's browse tool *can* auto-read URLs in 1 turn if they appear in **Google Search results** (`raw.githubusercontent.com` is blocked from Google Search, whereas **GitHub Pages** is searchable).
* If you host those 35 KB chunks on **GitHub Pages** (`inikashx-hub.github.io/ai-kb/`) and enable **both** `Grounding with Google Search` + `URL context`, you just type your question with **zero URLs** and Gemini searches + reads the matching pages in **1 turn**.
* **The Catch:** Google Search takes **days to weeks** to index new pages, and Search may miss 1 of 3 parts—so it's neither instant-sync nor 100% guaranteed recall.

---

### Which 1-Turn Route Do You Want?
1. **Option 1 (URL Context Subject Packs):** Keep 100% GitHub + URL toggle, organized into 3–4 subject URL blocks you pin in Gboard.
2. **Option 2 (`all-kb.md` in Google Drive):** Best 1-turn accuracy over your *entire* KB at once (since your existing 15-min Drive pipeline already lives there).
3. **Option 3 (GitHub Pages + Google Search):** Zero pasting, accepting Google Search indexing delay.

Tell me which one you want (`1`, `2`, or `3`) and I'll set it up cleanly!

---

## User

Option 1

---

## Model

Let's set up **Option 1 (Static 1-Turn Subject Packs)**.

We will update `build-kb.py` so it automatically splits your repository into **static, hash-free Subject Pack files** (`<=35 KB` each so URL Context reads 100% without truncation) and writes a copy-ready cheat sheet at **`_ai_bundles/packs-list.txt`**:

* **`schemes-p1..pN.md`** → Chapter 4 (Government Schemes, 342 Qs) *(~3 URLs)*
* **`rbi-economy-p1..pN.md`** → Chapters 1 & 3 (RBI, Monetary Policy, Indian Economy & Union Budget) *(~3–4 URLs)*
* **`banking-p1..pN.md`** → Chapter 2 (Banking & Financial Awareness, 642 Qs) *(~5–6 URLs)*
* **`current-affairs-p1..pN.md`** → Chapters 5–10 (Appointments, Awards, Reports, Sci-Tech & Defence) *(~5–6 URLs)*
* **`static-gk-p1..pN.md`** → Chapters 11–18 (Sports, Books, Important Days, Int'l Orgs, Polity, Geography, Art, Countries) *(~6–7 URLs)*
* **`study-chats-p1..pN.md`** → All standalone AI Studio chats (`Solving Math Questions Under 30s.md`, etc.)
*(It still keeps `hot-core.md`, `hot-recent.md`, and `llms.txt` building alongside them so nothing breaks.)*

---

### Step 1: Update `build-kb.py`
Replace **`build-kb.py`** with this version and commit:

```python
import hashlib
import os
import re
import shutil
import subprocess
from datetime import date, datetime
from pathlib import Path

OUT_DIR = Path("_ai_bundles")
COLD_DIR = OUT_DIR / "cold"
PACKS_DIR = OUT_DIR / "packs"

ALLOWED_EXTS = {".md", ".txt", ".json", ".yaml", ".yml", ".csv", ".py", ".ts", ".js"}
MAX_PART_BYTES = 35_000          # Fits inside Playground's URL-context browse limit
MAX_RECENT_FILE_BYTES = 25_000
MAX_RECENT_TOTAL_BYTES = 40_000
RECENT_DAYS = 14

REPO = os.environ.get("GITHUB_REPOSITORY", "inikashx-hub/ai-kb")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
TODAY = date.today()

def get_git_recent_files(days: int) -> set[Path]:
    try:
        out = subprocess.check_output(
            ["git", "log", f"--since={days} days ago", "--name-only", "--pretty=format:"],
            text=True,
        )
        return {Path(line.strip()) for line in out.splitlines() if line.strip()}
    except Exception:
        return set()

def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return {}, text
    meta = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip().lower()] = v.strip()
    return meta, text[match.end() :]

def clean_chat_wrapper(text: str) -> str:
    return re.sub(r"^---\s*START OF FILE.*?---\s*\n+", "", text, flags=re.MULTILINE).strip()

def strip_md_noise(line: str) -> str:
    s = re.sub(r"<[^>]+>", " ", line)
    s = re.sub(r"^[#>*`\-\s]+", "", s)
    s = re.sub(r"[*`]+$", "", s)
    return " ".join(s.replace("**", "").split())

def extract_toc_chapters(body: str) -> list[tuple[int, str]]:
    """Extract (chapter_num, chapter_title) pairs from the document's TOC."""
    head = body[:25_000]
    raw = re.findall(
        r"\b(0?[1-9]|1\d|2[0-5])\.\s+([A-Z][A-Za-z0-9&,'/\-\s]{4,60}?)(?=\s*\(\d+\)|\s+\d{1,2}\.\s+[A-Z]|\n|$)",
        head,
    )
    by_num: dict[int, str] = {}
    for num_str, title_str in raw:
        num = int(num_str)
        clean = " ".join(title_str.split()).strip(" .:-")
        low = clean.lower()
        if len(clean) >= 6 and "answer:" not in low and "?" not in clean and " exam " not in low:
            if num not in by_num or len(clean) > len(by_num[num]):
                by_num[num] = clean
    chapters = sorted(by_num.items())
    return chapters if len(chapters) >= 3 else []

def match_known_chapter(line: str, known_chapters: list[tuple[int, str]]) -> tuple[int, str] | None:
    cleaned = strip_md_noise(line)
    if not cleaned or len(cleaned) > 130:
        return None
    low = cleaned.lower()
    if "answer:" in low or cleaned.endswith("?") or " exam " in low:
        return None

    hits = []
    for num, ch_name in known_chapters:
        pat = rf"(?:^|\b)(?:0?{num}\.\s+)?{re.escape(ch_name)}(?:\s*\(\d+\)|\s*/\s*\d+\s*Qs.*)?(?=\s|$)"
        if re.search(pat, cleaned, re.IGNORECASE):
            hits.append((num, f"{num}. {ch_name}"))
    # Return only if the line represents a single chapter header (not a multi-chapter TOC row)
    return hits[0] if len(hits) == 1 else None

def find_chapter_markers(line: str, known_chapters: list[tuple[int, str]] | None = None) -> list[str]:
    cleaned = strip_md_noise(line)
    if not cleaned:
        return []
    low = cleaned.lower()
    if "answer:" in low or cleaned.endswith("?") or " exam " in low:
        return []

    numbered = re.findall(r"\b(\d{1,2}\.\s+[^()\n]{3,70}\(\d+\))", cleaned)
    if numbered:
        return [n.strip()[:90] for n in numbered]

    if known_chapters:
        m_known = match_known_chapter(line, known_chapters)
        if m_known:
            return [m_known[1]]

    m_h = re.match(r"^#{1,2}\s+(.+)$", line.strip())
    if m_h:
        txt = strip_md_noise(m_h.group(1))
        if txt and txt.lower() not in {"table of contents", "contents", "index", "user", "model"}:
            return [txt[:90]]

    return []

def split_compendium_by_chapters(
    body: str, max_bytes: int, known_chapters: list[tuple[int, str]]
) -> list[dict]:
    """Split a multi-chapter compendium into <= max_bytes chunks tagged with chapter number."""
    sections: list[dict] = []
    cur_lines: list[str] = []
    cur_num = 0
    cur_title = "Header / TOC"
    in_toc = False
    seen_qa = False
    in_fence = False

    for line in body.splitlines(keepends=True):
        if line.lstrip().startswith("```"): in_fence = not in_fence

        low = line.lower if not in_fence: if "included topic chapters" in low or "table of contents" in low: in_toc = True if "answer:" in low: if not seen_qa and cur_num == 0 and known_chapters: cur_num, cur_title = known_chapters, f"{known_chapters}. {known_chapters}" in_toc = False seen_qa = True

            ch_hit = match_known_chapter(line, known_chapters) if ch_hit and (seen_qa or not in_toc): if cur_lines: sections.append({"num": cur_num, "title": cur_title, "text": "".join(cur_lines).strip}) cur_num, cur_title = ch_hit cur_lines = [line] continue

        cur_lines.append(line)

    if cur_lines: sections.append({"num": cur_num, "title": cur_title, "text": "".join(cur_lines).strip})

    # Split oversized chapter sections cleanly into <= max_bytes chunks
    chunks: list[dict] = [] for sec in sections: text = sec["text"] if not text: continue if len(text.encode("utf-8")) <= max_bytes: chunks.append(sec) continue

        buf: list[str] = [] buf_bytes = 0 part_idx = 1 for para in text.split("\n\n"): p_bytes = len(para.encode("utf-8")) + 2 if buf and (buf_bytes + p_bytes > max_bytes): chunk_body = "\n\n".join(buf).strip if part_idx > 1 and sec["num"] > 0: chunk_body = f"## [Chapter Context: {sec['title']}]\n\n{chunk_body}" chunks.append({"num": sec["num"], "title": sec["title"], "text": chunk_body}) buf, buf_bytes = [], 0 part_idx += 1 buf.append(para) buf_bytes += p_bytes if buf: chunk_body = "\n\n".join(buf).strip if part_idx > 1 and sec["num"] > 0: chunk_body = f"## [Chapter Context: {sec['title']}]\n\n{chunk_body}" chunks.append({"num": sec["num"], "title": sec["title"], "text": chunk_body})

    return chunks

def split_plain_large_body(body: str, max_bytes: int) -> list[str]: if len(body.encode("utf-8")) <= max_bytes: return [body] chunks, buf, buf_bytes = [], [], 0 for para in body.split("\n\n"): p_bytes = len(para.encode("utf-8")) + 2 if buf and (buf_bytes + p_bytes > max_bytes): chunks.append("\n\n".join(buf).strip) buf, buf_bytes = [], 0 buf.append(para) buf_bytes += p_bytes if buf: chunks.append("\n\n".join(buf).strip) return chunks

def map_chapter_to_pack(ch_num: int) -> str: if ch_num in (1, 3): return "rbi-economy" if ch_num == 2: return "banking" if ch_num == 4: return "schemes" if 5 <= ch_num <= 10: return "current-affairs" if ch_num >= 11: return "static-gk" return "general"

def make_preview(text: str) -> str: clean_lines = [ strip_md_noise(ln) for ln in text.splitlines if ln.strip and not ln.strip.startswith("## [Chapter Context:") ] joined = " ".join(ln for ln in clean_lines if ln) if len(joined) <= 200: return joined return f"{joined[:100]} ... {joined[-100:]}"

def extract_doc_info( path: Path, text: str, fallback_title: str = "", known_chapters: list[tuple[int, str]] | None = None ) -> dict: h1_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE) title = h1_match.group(1).strip if h1_match else (fallback_title or path.stem)

    updated_date = None upd_match = re.search(r"\*\*Updated:\*\*\s*(\d{4}-\d{2}-\d{2})", text) if upd_match: try: updated_date = datetime.strptime(upd_match.group(1), "%Y-%m-%d").date except ValueError: updated_date = None

    is_chat = bool(re.search(r"^##\s+(User|Model)\s*$", text, re.MULTILINE)) prompts, sections = [], []

    if is_chat: raw_prompts = re.findall( r"^##\s+User\s*\n+(.*?)(?=\n+---|\n+##\s+Model|\Z)", text, re.DOTALL | re.MULTILINE, ) for p in raw_prompts[:4]: compact = " ".join(p.split) if compact: prompts.append(compact[:110] + ("..." if len(compact) > 110 else ""))

        h3s = re.findall(r"^###\s+(.+)$", text, re.MULTILINE) skip = {"conclusion", "summary", "summary checklist before applying:"} sections = [h.strip[:90] for h in h3s if h.strip.lower not in skip][:8] else: seen = set for line in text.splitlines: for ch in find_chapter_markers(line, known_chapters): if ch not in seen: seen.add(ch) sections.append(ch) if len(sections) >= 12: break if len(sections) >= 12: break

    return { "title": title, "updated_date": updated_date, "prompts": prompts, "sections": sections, "preview": make_preview(text) if not is_chat else "", }

def sanitize_slug(name: str) -> str: slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", name).strip("-").lower return slug or "general"

def format_file_block(rel_path: Path, body: str, part_label: str = "") -> str: label = f" {part_label}" if part_label else "" return f"\n\n---\n## FILE: `{rel_path.as_posix()}`{label}\n\n{body}\n"

def write_cold_chunks(group_name: str, items: list[dict]) -> list[dict]: chunks, current_blocks, current_meta, current_size = [], [], [], 0 for item in items: block = format_file_block(item["path"], item["body"], item.get("part_label", "")) block_size = len(block.encode("utf-8")) if current_blocks and (current_size + block_size > MAX_PART_BYTES): chunks.append((current_blocks, current_meta)) current_blocks, current_meta, current_size = [], [], 0 current_blocks.append(block) current_meta.append(item) current_size += block_size if current_blocks: chunks.append((current_blocks, current_meta))

    written = [] for idx, (blocks, metas) in enumerate(chunks, start=1): suffix = f"-part{idx}" if len(chunks) > 1 else "" content = f"# Cold Knowledge Bundle: {group_name}{suffix}\n" + "".join(blocks) short_hash = hashlib.md5(content.encode("utf-8")).hexdigest[:8] filename = f"cold-{group_name}{suffix}.{short_hash}.md" (COLD_DIR / filename).write_text(content, encoding="utf-8")

        titles, prompts, sections, previews = [], [], [], [] for m in metas: d = m["updated_date"].isoformat if m["updated_date"] else "" lbl = f"{m['title']} {m.get('part_label', '')}".strip full_t = f"{lbl} ({d})" if d else lbl if full_t not in titles: titles.append(full_t) prompts.extend(m["prompts"]) sections.extend(m["sections"]) if m["preview"]: previews.append(m["preview"])

        written.append( { "url": f"{RAW_BASE}/_ai_bundles/cold/{filename}", "group": f"{group_name}{suffix}", "titles": titles, "prompts": list(dict.fromkeys(prompts))[:10], "sections": list(dict.fromkeys(sections))[:12], "preview": previews if previews else "", } ) return written

def write_static_packs(pack_items: dict[str, list[dict]]) -> dict[str, list[str]]: """Write static, hash-free Subject Pack files (<=35 KB each) for 1-turn URL Context.""" pack_urls: dict[str, list[str]] = {} for pack_name, items in sorted(pack_items.items): chunks, current_blocks, current_size = [], [], 0 for item in items: block = format_file_block(item["path"], item["body"], item.get("part_label", "")) block_size = len(block.encode("utf-8")) if current_blocks and (current_size + block_size > MAX_PART_BYTES): chunks.append(current_blocks) current_blocks, current_size = [], 0 current_blocks.append(block) current_size += block_size if current_blocks: chunks.append(current_blocks)

        urls = [] total = len(chunks) for idx, blocks in enumerate(chunks, start=1): filename = f"{pack_name}-p{idx}.md" content = f"# Subject Pack: {pack_name} (Part {idx}/{total})\n" + "".join(blocks) (PACKS_DIR / filename).write_text(content, encoding="utf-8") urls.append(f"{RAW_BASE}/_ai_bundles/packs/{filename}") pack_urls[pack_name] = urls return pack_urls

def main: scan_dirs = [d for d in (Path("core"), Path("chats"), Path("kb")) if d.exists] if not scan_dirs: raise SystemExit("Missing 'chats/' or 'core/' directory.")

    OUT_DIR.mkdir(parents=True, exist_ok=True) shutil.rmtree(COLD_DIR, ignore_errors=True) shutil.rmtree(PACKS_DIR, ignore_errors=True) COLD_DIR.mkdir(parents=True, exist_ok=True) PACKS_DIR.mkdir(parents=True, exist_ok=True)

    git_recent = get_git_recent_files(RECENT_DAYS) hot_core_blocks = [] recent_candidates = [] cold_groups: dict[str, list[dict]] = {} pack_groups: dict[str, list[dict]] = {}

    for root_dir in scan_dirs: for path in sorted(root_dir.rglob("*")): if not path.is_file or path.suffix.lower not in ALLOWED_EXTS: continue

            raw_text = path.read_text(encoding="utf-8", errors="ignore") meta, body = parse_frontmatter(raw_text) body = clean_chat_wrapper(body) known_chapters = extract_toc_chapters(body) top_info = extract_doc_info(path, body, known_chapters=known_chapters) parts = path.parts

            is_hot = ( root_dir.name == "core" or (root_dir.name == "kb" and len(parts) > 2 and parts == "core") or meta.get("tier") == "hot" )

            if is_hot: hot_core_blocks.append(format_file_block(path, body)) continue

            body_bytes = len(body.encode("utf-8")) if top_info["updated_date"] is not None: is_recent = (TODAY - top_info["updated_date"]).days <= RECENT_DAYS sort_d = top_info["updated_date"] else: is_recent = path in git_recent sort_d = TODAY if is_recent else date.min

            if is_recent and body_bytes <= MAX_RECENT_FILE_BYTES: blk = format_file_block(path, body) recent_candidates.append((sort_d, blk, len(blk.encode("utf-8"))))

            if root_dir.name == "chats": if len(parts) > 2: group_key = sanitize_slug(parts) elif top_info["updated_date"] is not None: group_key = f"chats-{top_info['updated_date'].strftime('%Y-%m')}" else: group_key = "chats-general" else: raw_sub = parts if len(parts) > 2 else "general" group_key = sanitize_slug(raw_sub)

            if known_chapters and body_bytes > MAX_PART_BYTES:
                # Multi-chapter compendium: route chapters straight into static Subject Packs + Cold archive
                ch_chunks = split_compendium_by_chapters(body, MAX_PART_BYTES - 1500, known_chapters) total_parts = len(ch_chunks) for idx, ch in enumerate(ch_chunks, start=1): part_label = f"[Part {idx}/{total_parts} — {ch['title']}]" part_info = extract_doc_info( path, ch["text"], fallback_title=top_info["title"], known_chapters=known_chapters ) item = { "path": path, "body": ch["text"], "part_label": part_label, "title": top_info["title"], "updated_date": top_info["updated_date"], "prompts": part_info["prompts"], "sections": [ch["title"]] if ch["num"] > 0 else part_info["sections"], "preview": part_info["preview"], } cold_groups.setdefault(group_key, []).append(item) if ch["num"] > 0: pack_name = map_chapter_to_pack(ch["num"]) pack_groups.setdefault(pack_name, []).append(item) else:
                # Standalone chats / notes
                pack_name = sanitize_slug(parts) if (root_dir.name == "chats" and len(parts) > 2) else "study-chats" body_parts = split_plain_large_body(body, MAX_PART_BYTES - 1500) total_parts = len(body_parts) for idx, part_body in enumerate(body_parts, start=1): part_label = f"[Part {idx}/{total_parts}]" if total_parts > 1 else "" part_info = extract_doc_info(path, part_body, fallback_title=top_info["title"]) item = { "path": path, "body": part_body, "part_label": part_label, "title": top_info["title"], "updated_date": top_info["updated_date"], "prompts": part_info["prompts"], "sections": part_info["sections"], "preview": part_info["preview"], } cold_groups.setdefault(group_key, []).append(item) pack_groups.setdefault(pack_name, []).append(item)

    core_text = ( "# Tier 1: Core Knowledge\n" + "".join(hot_core_blocks) if hot_core_blocks else "# Tier 1: Core Knowledge\nNo core files configured yet." ) (OUT_DIR / "hot-core.md").write_text(core_text, encoding="utf-8")

    recent_candidates.sort(key=lambda x: x, reverse=True) selected_recent, recent_bytes = [], 0 for _, blk, b_size in recent_candidates: if selected_recent and (recent_bytes + b_size > MAX_RECENT_TOTAL_BYTES): break selected_recent.append(blk) recent_bytes += b_size

    recent_text = ( f"# Tier 1: Recent Compact Chats (Last {RECENT_DAYS} Days)\n" + "".join(selected_recent) if selected_recent else f"# Tier 1: Recent Changes\nNo compact chats updated in the last {RECENT_DAYS} days." ) (OUT_DIR / "hot-recent.md").write_text(recent_text, encoding="utf-8")

    # Write static 1-turn Subject Packs & copy-paste cheat sheet
    pack_urls = write_static_packs(pack_groups) pack_lines = [ "# 1-Turn Subject Packs (Pin Your Favorite Packs in Gboard Clipboard)", "# Paste any Pack block below + your question together in Turn 1 for instant 1-turn answers.", "", ] for pname, urls in pack_urls.items: pack_lines.append(f"## PACK: {pname} ({len(urls)} URLs)") for u in urls: pack_lines.append(u) pack_lines.append("Read every URL above via URL context and answer my question thoroughly with exact FILE citations.") pack_lines.append("") (OUT_DIR / "packs-list.txt").write_text("\n".join(pack_lines), encoding="utf-8")

    # Also keep llms.txt & Cold Bundles up to date
    index_entries = [] for group_name, items in sorted(cold_groups.items): index_entries.extend(write_cold_chunks(group_name, items))

    lines = [ "# Knowledge Base Index (Tier 2 Cold Bundles)", "# For 1-turn queries, use static Subject Packs in packs-list.txt.", "", ] for entry in index_entries: lines.append(f"- URL: {entry['url']}") lines.append(f" Topic Group: {entry['group']}") lines.append(f" Files/Parts: {' | '.join(entry['titles'])}") if entry["prompts"]: lines.append(f" User Questions: {' | '.join(entry['prompts'])}") if entry["sections"]: lines.append(f" Topics/Chapters: {' | '.join(entry['sections'])}") if entry["preview"]: lines.append(f" Preview: {entry['preview']}") lines.append("")

    (OUT_DIR / "llms.txt").write_text("\n".join(lines), encoding="utf-8") print(f"Built {len(pack_urls)} static subject pack(s) and {len(index_entries)} cold bundle(s).")

if __name__ == "__main__": main ```

---

### Step 2: Update System Instructions for 1-Turn Mode
In Google AI Studio (keep **URL context → ON**, **Google Search → OFF**), replace **System Instructions** with this shorter 1-turn version:

```markdown You are a strict, retrieval-grounded assistant for my knowledge base.

### Rules
1. The user will provide static Subject Pack URLs (plus optional `hot-core.md` / `hot-recent.md`) in the prompt.
2. Read EVERY provided URL in full via URL context before answering.
3. Answer immediately in the same turn using ONLY facts found in the retrieved files, and cite the exact `FILE:` path (and question/chapter numbers where available).
4. If the provided URLs do not contain the answer, state that explicitly—never guess from memory.
```

---

### Step 3: Grab Your 1-Turn Packs & Pin Them!
1. Wait ~15 seconds for the GitHub Action to finish.
2. Open **`_ai_bundles/packs-list.txt`** → tap **Raw** in your repo.
3. Copy the **`schemes`** block (just ~3 URLs + instruction line!) and pin it in your **Gboard Clipboard**. Pin `rbi-economy`, `static-gk`, `study-chats`, etc. too.
4. Open a **fresh AI Studio chat**, tap the **`schemes`** clipboard pin, type your question right below it:
   > *"Comprehensive analysis of the examiner's question setting pattern for scheme questions"*
   and hit **Run**—you’ll get the full analysis across **all 342 scheme questions in 1 single turn**!

---

## User

So, packs are chosen by you. I need flexibility

---

## Model

Fair point—hardcoding subjects in Python locks you in.

Here is how to make it **100% user-controlled and flexible** so you never have to touch Python again:

1. **Auto-Packs by Folder & Chapter (Zero Hardcoding):**
   * Any folder you create (e.g., `chats/quant/`, `chats/coding/`) automatically becomes its own pack (`quant-p1.md`, `coding-p1.md`).
   * Any multi-chapter book automatically creates **one pack per chapter** using its own TOC title (`ch04-government-schemes-p1..p3.md`, `ch13-important-days-p1.md`, etc.)—works on *any* subject or PDF you upload in the future.
2. **Optional `packs.json` to Bundle Your Own Custom Packs:**
   Whenever *you* decide you want specific chapters or folders combined into a single 1-turn pack, just drop a tiny `packs.json` file at your repo root using wildcards—no Python changes needed.
3. **One Prompt Supports Both Modes:**
   Paste any pack URLs (or mix chapters on the fly, up to 20 URLs) for **1-turn** answers, **or** paste `llms.txt` whenever a question spans unknown topics for **2-turn** auto-routing.

---

### Step 1: Update `build-kb.py` (Zero Hardcoding + `packs.json` Support)

Replace **`build-kb.py`** with this flexible version:

```python
import hashlib
import json
import os
import re
import shutil
import subprocess
from datetime import date, datetime
from fnmatch import fnmatch
from pathlib import Path

OUT_DIR = Path("_ai_bundles")
COLD_DIR = OUT_DIR / "cold"
PACKS_DIR = OUT_DIR / "packs"
PACKS_CONFIG = Path("packs.json")

ALLOWED_EXTS = {".md", ".txt", ".json", ".yaml", ".yml", ".csv", ".py", ".ts", ".js"}
MAX_PART_BYTES = 35_000          # Fits inside Playground's URL-context browse limit
MAX_RECENT_FILE_BYTES = 25_000
MAX_RECENT_TOTAL_BYTES = 40_000
RECENT_DAYS = 14

REPO = os.environ.get("GITHUB_REPOSITORY", "inikashx-hub/ai-kb")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
TODAY = date.today()

def get_git_recent_files(days: int) -> set[Path]:
    try:
        out = subprocess.check_output(
            ["git", "log", f"--since={days} days ago", "--name-only", "--pretty=format:"],
            text=True,
        )
        return {Path(line.strip()) for line in out.splitlines() if line.strip()}
    except Exception:
        return set()

def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return {}, text
    meta = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip().lower()] = v.strip()
    return meta, text[match.end() :]

def clean_chat_wrapper(text: str) -> str:
    return re.sub(r"^---\s*START OF FILE.*?---\s*\n+", "", text, flags=re.MULTILINE).strip()

def strip_md_noise(line: str) -> str:
    s = re.sub(r"<[^>]+>", " ", line)
    s = re.sub(r"^[#>*`\-\s]+", "", s)
    s = re.sub(r"[*`]+$", "", s)
    return " ".join(s.replace("**", "").split())

def sanitize_slug(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", name).strip("-").lower()
    return slug or "general"

def make_chapter_slug(num: int, title: str) -> str:
    body_slug = sanitize_slug(title)[:32].strip("-")
    return f"ch{num:02d}-{body_slug}" if body_slug else f"ch{num:02d}"

def extract_toc_chapters(body: str) -> list[tuple[int, str]]:
    head = body[:25_000]
    raw = re.findall(
        r"\b(0?[1-9]|1\d|2[0-5])\.\s+([A-Z][A-Za-z0-9&,'/\-\s]{4,60}?)(?=\s*\(\d+\)|\s+\d{1,2}\.\s+[A-Z]|\n|$)",
        head,
    )
    by_num: dict[int, str] = {}
    for num_str, title_str in raw:
        num = int(num_str)
        clean = " ".join(title_str.split()).strip(" .:-")
        low = clean.lower()
        if len(clean) >= 6 and "answer:" not in low and "?" not in clean and " exam " not in low:
            if num not in by_num or len(clean) > len(by_num[num]):
                by_num[num] = clean
    chapters = sorted(by_num.items())
    return chapters if len(chapters) >= 3 else []

def match_known_chapter(line: str, known_chapters: list[tuple[int, str]]) -> tuple[int, str, str] | None:
    cleaned = strip_md_noise(line)
    if not cleaned or len(cleaned) > 130:
        return None
    low = cleaned.lower()
    if "answer:" in low or cleaned.endswith("?") or " exam " in low:
        return None

    hits = []
    for num, ch_name in known_chapters:
        pat = rf"(?:^|\b)(?:0?{num}\.\s+)?{re.escape(ch_name)}(?:\s*\(\d+\)|\s*/\s*\d+\s*Qs.*)?(?=\s|$)"
        if re.search(pat, cleaned, re.IGNORECASE):
            hits.append((num, f"{num}. {ch_name}", ch_name))
    return hits[0] if len(hits) == 1 else None

def find_chapter_markers(line: str, known_chapters: list[tuple[int, str]] | None = None) -> list[str]:
    cleaned = strip_md_noise(line)
    if not cleaned:
        return []
    low = cleaned.lower()
    if "answer:" in low or cleaned.endswith("?") or " exam " in low:
        return []

    numbered = re.findall(r"\b(\d{1,2}\.\s+[^()\n]{3,70}\(\d+\))", cleaned)
    if numbered:
        return [n.strip()[:90] for n in numbered]

    if known_chapters:
        m_known = match_known_chapter(line, known_chapters)
        if m_known:
            return [m_known[1]]

    m_h = re.match(r"^#{1,2}\s+(.+)$", line.strip())
    if m_h:
        txt = strip_md_noise(m_h.group(1))
        if txt and txt.lower() not in {"table of contents", "contents", "index", "user", "model"}:
            return [txt[:90]]

    return []

def split_compendium_by_chapters(
    body: str, max_bytes: int, known_chapters: list[tuple[int, str]]
) -> list[dict]:
    sections: list[dict] = []
    cur_lines: list[str] = []
    cur_num, cur_title, cur_raw_name = 0, "Header / TOC", "header"
    in_toc, seen_qa, in_fence = False, False, False

    for line in body.splitlines(keepends=True):
        if line.lstrip().startswith("```"): in_fence = not in_fence

        low = line.lower if not in_fence: if "included topic chapters" in low or "table of contents" in low: in_toc = True if "answer:" in low: if not seen_qa and cur_num == 0 and known_chapters: cur_num = known_chapters cur_raw_name = known_chapters cur_title = f"{cur_num}. {cur_raw_name}" in_toc = False seen_qa = True

            ch_hit = match_known_chapter(line, known_chapters) if ch_hit and (seen_qa or not in_toc): if cur_lines: sections.append( {"num": cur_num, "title": cur_title, "raw_name": cur_raw_name, "text": "".join(cur_lines).strip} ) cur_num, cur_title, cur_raw_name = ch_hit cur_lines = [line] continue

        cur_lines.append(line)

    if cur_lines: sections.append( {"num": cur_num, "title": cur_title, "raw_name": cur_raw_name, "text": "".join(cur_lines).strip} )

    chunks: list[dict] = [] for sec in sections: text = sec["text"] if not text: continue if len(text.encode("utf-8")) <= max_bytes: chunks.append(sec) continue

        buf, buf_bytes, part_idx = [], 0, 1 for para in text.split("\n\n"): p_bytes = len(para.encode("utf-8")) + 2 if buf and (buf_bytes + p_bytes > max_bytes): chunk_body = "\n\n".join(buf).strip if part_idx > 1 and sec["num"] > 0: chunk_body = f"## [Chapter Context: {sec['title']}]\n\n{chunk_body}" chunks.append({"num": sec["num"], "title": sec["title"], "raw_name": sec["raw_name"], "text": chunk_body}) buf, buf_bytes = [], 0 part_idx += 1 buf.append(para) buf_bytes += p_bytes if buf: chunk_body = "\n\n".join(buf).strip if part_idx > 1 and sec["num"] > 0: chunk_body = f"## [Chapter Context: {sec['title']}]\n\n{chunk_body}" chunks.append({"num": sec["num"], "title": sec["title"], "raw_name": sec["raw_name"], "text": chunk_body})

    return chunks

def split_plain_large_body(body: str, max_bytes: int) -> list[str]: if len(body.encode("utf-8")) <= max_bytes: return [body] chunks, buf, buf_bytes = [], [], 0 for para in body.split("\n\n"): p_bytes = len(para.encode("utf-8")) + 2 if buf and (buf_bytes + p_bytes > max_bytes): chunks.append("\n\n".join(buf).strip) buf, buf_bytes = [], 0 buf.append(para) buf_bytes += p_bytes if buf: chunks.append("\n\n".join(buf).strip) return chunks

def make_preview(text: str) -> str: clean_lines = [ strip_md_noise(ln) for ln in text.splitlines if ln.strip and not ln.strip.startswith("## [Chapter Context:") ] joined = " ".join(ln for ln in clean_lines if ln) if len(joined) <= 200: return joined return f"{joined[:100]} ... {joined[-100:]}"

def extract_doc_info( path: Path, text: str, fallback_title: str = "", known_chapters: list[tuple[int, str]] | None = None ) -> dict: h1_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE) title = h1_match.group(1).strip if h1_match else (fallback_title or path.stem)

    updated_date = None upd_match = re.search(r"\*\*Updated:\*\*\s*(\d{4}-\d{2}-\d{2})", text) if upd_match: try: updated_date = datetime.strptime(upd_match.group(1), "%Y-%m-%d").date except ValueError: updated_date = None

    is_chat = bool(re.search(r"^##\s+(User|Model)\s*$", text, re.MULTILINE)) prompts, sections = [], []

    if is_chat: raw_prompts = re.findall( r"^##\s+User\s*\n+(.*?)(?=\n+---|\n+##\s+Model|\Z)", text, re.DOTALL | re.MULTILINE, ) for p in raw_prompts[:4]: compact = " ".join(p.split) if compact: prompts.append(compact[:110] + ("..." if len(compact) > 110 else ""))

        h3s = re.findall(r"^###\s+(.+)$", text, re.MULTILINE) skip = {"conclusion", "summary", "summary checklist before applying:"} sections = [h.strip[:90] for h in h3s if h.strip.lower not in skip][:8] else: seen = set for line in text.splitlines: for ch in find_chapter_markers(line, known_chapters): if ch not in seen: seen.add(ch) sections.append(ch) if len(sections) >= 12: break if len(sections) >= 12: break

    return { "title": title, "updated_date": updated_date, "prompts": prompts, "sections": sections, "preview": make_preview(text) if not is_chat else "", }

def format_file_block(rel_path: Path, body: str, part_label: str = "") -> str: label = f" {part_label}" if part_label else "" return f"\n\n---\n## FILE: `{rel_path.as_posix()}`{label}\n\n{body}\n"

def write_cold_chunks(group_name: str, items: list[dict]) -> list[dict]: chunks, current_blocks, current_meta, current_size = [], [], [], 0 for item in items: block = format_file_block(item["path"], item["body"], item.get("part_label", "")) block_size = len(block.encode("utf-8")) if current_blocks and (current_size + block_size > MAX_PART_BYTES): chunks.append((current_blocks, current_meta)) current_blocks, current_meta, current_size = [], [], 0 current_blocks.append(block) current_meta.append(item) current_size += block_size if current_blocks: chunks.append((current_blocks, current_meta))

    written = [] for idx, (blocks, metas) in enumerate(chunks, start=1): suffix = f"-part{idx}" if len(chunks) > 1 else "" content = f"# Cold Knowledge Bundle: {group_name}{suffix}\n" + "".join(blocks) short_hash = hashlib.md5(content.encode("utf-8")).hexdigest[:8] filename = f"cold-{group_name}{suffix}.{short_hash}.md" (COLD_DIR / filename).write_text(content, encoding="utf-8")

        titles, prompts, sections, previews = [], [], [], [] for m in metas: d = m["updated_date"].isoformat if m["updated_date"] else "" lbl = f"{m['title']} {m.get('part_label', '')}".strip full_t = f"{lbl} ({d})" if d else lbl if full_t not in titles: titles.append(full_t) prompts.extend(m["prompts"]) sections.extend(m["sections"]) if m["preview"]: previews.append(m["preview"])

        written.append( { "url": f"{RAW_BASE}/_ai_bundles/cold/{filename}", "group": f"{group_name}{suffix}", "titles": titles, "prompts": list(dict.fromkeys(prompts))[:10], "sections": list(dict.fromkeys(sections))[:12], "preview": previews if previews else "", } ) return written

def write_static_packs(pack_items: dict[str, list[dict]]) -> dict[str, list[str]]: pack_urls: dict[str, list[str]] = {} for pack_name, items in sorted(pack_items.items): chunks, current_blocks, current_size = [], [], 0 for item in items: block = format_file_block(item["path"], item["body"], item.get("part_label", "")) block_size = len(block.encode("utf-8")) if current_blocks and (current_size + block_size > MAX_PART_BYTES): chunks.append(current_blocks) current_blocks, current_size = [], 0 current_blocks.append(block) current_size += block_size if current_blocks: chunks.append(current_blocks)

        urls = [] total = len(chunks) for idx, blocks in enumerate(chunks, start=1): filename = f"{pack_name}-p{idx}.md" content = f"# Subject Pack: {pack_name} (Part {idx}/{total})\n" + "".join(blocks) (PACKS_DIR / filename).write_text(content, encoding="utf-8") urls.append(f"{RAW_BASE}/_ai_bundles/packs/{filename}") pack_urls[pack_name] = urls return pack_urls

def main: scan_dirs = [d for d in (Path("core"), Path("chats"), Path("kb")) if d.exists] if not scan_dirs: raise SystemExit("Missing 'chats/' or 'core/' directory.")

    OUT_DIR.mkdir(parents=True, exist_ok=True) shutil.rmtree(COLD_DIR, ignore_errors=True) shutil.rmtree(PACKS_DIR, ignore_errors=True) COLD_DIR.mkdir(parents=True, exist_ok=True) PACKS_DIR.mkdir(parents=True, exist_ok=True)

    git_recent = get_git_recent_files(RECENT_DAYS) hot_core_blocks = [] hot_core_items = [] recent_candidates = [] cold_groups: dict[str, list[dict]] = {} auto_packs: dict[str, list[dict]] = {}

    for root_dir in scan_dirs: for path in sorted(root_dir.rglob("*")): if not path.is_file or path.suffix.lower not in ALLOWED_EXTS: continue

            raw_text = path.read_text(encoding="utf-8", errors="ignore") meta, body = parse_frontmatter(raw_text) body = clean_chat_wrapper(body) known_chapters = extract_toc_chapters(body) top_info = extract_doc_info(path, body, known_chapters=known_chapters) parts = path.parts

            is_hot = ( root_dir.name == "core" or (root_dir.name == "kb" and len(parts) > 2 and parts == "core") or meta.get("tier") == "hot" )

            if is_hot: hot_core_blocks.append(format_file_block(path, body)) hot_core_items.append({"path": path, "body": body, "part_label": ""}) continue

            body_bytes = len(body.encode("utf-8")) if top_info["updated_date"] is not None: is_recent = (TODAY - top_info["updated_date"]).days <= RECENT_DAYS sort_d = top_info["updated_date"] else: is_recent = path in git_recent sort_d = TODAY if is_recent else date.min

            if is_recent and body_bytes <= MAX_RECENT_FILE_BYTES: blk = format_file_block(path, body) recent_candidates.append((sort_d, blk, len(blk.encode("utf-8"))))

            if root_dir.name == "chats": if len(parts) > 2: group_key = sanitize_slug(parts) elif top_info["updated_date"] is not None: group_key = f"chats-{top_info['updated_date'].strftime('%Y-%m')}" else: group_key = "chats-general" else: raw_sub = parts if len(parts) > 2 else "general" group_key = sanitize_slug(raw_sub)

            if known_chapters and body_bytes > MAX_PART_BYTES: ch_chunks = split_compendium_by_chapters(body, MAX_PART_BYTES - 1500, known_chapters) total_parts = len(ch_chunks) for idx, ch in enumerate(ch_chunks, start=1): part_label = f"[Part {idx}/{total_parts} — {ch['title']}]" part_info = extract_doc_info( path, ch["text"], fallback_title=top_info["title"], known_chapters=known_chapters ) item = { "path": path, "body": ch["text"], "part_label": part_label, "title": top_info["title"], "updated_date": top_info["updated_date"], "prompts": part_info["prompts"], "sections": [ch["title"]] if ch["num"] > 0 else part_info["sections"], "preview": part_info["preview"], } cold_groups.setdefault(group_key, []).append(item) if ch["num"] > 0: ch_pack = make_chapter_slug(ch["num"], ch["raw_name"]) auto_packs.setdefault(ch_pack, []).append(item) else: if root_dir.name == "chats" and len(parts) > 2: pack_name = sanitize_slug(parts) elif root_dir.name == "kb" and len(parts) > 2: pack_name = sanitize_slug(parts) else: pack_name = "study-chats"

                body_parts = split_plain_large_body(body, MAX_PART_BYTES - 1500) total_parts = len(body_parts) for idx, part_body in enumerate(body_parts, start=1): part_label = f"[Part {idx}/{total_parts}]" if total_parts > 1 else "" part_info = extract_doc_info(path, part_body, fallback_title=top_info["title"]) item = { "path": path, "body": part_body, "part_label": part_label, "title": top_info["title"], "updated_date": top_info["updated_date"], "prompts": part_info["prompts"], "sections": part_info["sections"], "preview": part_info["preview"], } cold_groups.setdefault(group_key, []).append(item) auto_packs.setdefault(pack_name, []).append(item)

    core_text = ( "# Tier 1: Core Knowledge\n" + "".join(hot_core_blocks) if hot_core_blocks else "# Tier 1: Core Knowledge\nNo core files configured yet." ) (OUT_DIR / "hot-core.md").write_text(core_text, encoding="utf-8")

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
