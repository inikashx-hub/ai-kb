# Subject Pack: ch04-enforce-strict-router-grounding (Part 2/14)


---
## FILE: `chats/Optimizing Two-Step LLM Routing.md` [Part 5/17 — 4. Enforce Strict Router & Grounding Rules]

## [Chapter Context: 4. Enforce Strict Router & Grounding Rules]

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
