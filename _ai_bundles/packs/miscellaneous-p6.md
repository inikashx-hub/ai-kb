# Subject Pack: miscellaneous (Part 6/14)


---
## FILE: `chats/Optimizing Two-Step LLM Routing.md` [Part 6/14]

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
