# Subject Pack: chat-optimizing-two-step-llm-routing (Part 7/14)


---
## FILE: `chats/Optimizing Two-Step LLM Routing.md` [Part 7/14]

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
