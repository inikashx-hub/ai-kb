# Cold Knowledge Bundle: chats-2026-11-part5


---
## FILE: `chats/Optimizing Two-Step LLM Routing.md` [Part 5/14]

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
