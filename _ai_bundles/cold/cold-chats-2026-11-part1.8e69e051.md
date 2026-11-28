# Cold Knowledge Bundle: chats-2026-11-part1


---
## FILE: `chats/Optimizing Two-Step LLM Routing.md` [Part 1/14]

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
