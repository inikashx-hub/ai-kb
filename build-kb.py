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
MAX_URLS_PER_PROMPT = 20         # Google AI Studio URL Context cap per prompt
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


def prettify_label(name: str) -> str:
    s = re.sub(r"[-_]+", " ", str(name or "")).strip()
    return " ".join(w.upper() if w.lower() in {"kb", "ga", "rbi", "ai", "pdf", "hq"} else w.capitalize() for w in s.split()) or "General"


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
        if line.lstrip().startswith("```"):
            in_fence = not in_fence

        low = line.lower()
        if not in_fence:
            if "included topic chapters" in low or "table of contents" in low:
                in_toc = True
            if "answer:" in low:
                if not seen_qa and cur_num == 0 and known_chapters:
                    cur_num = known_chapters[0][0]
                    cur_raw_name = known_chapters[0][1]
                    cur_title = f"{cur_num}. {cur_raw_name}"
                in_toc = False
                seen_qa = True

            ch_hit = match_known_chapter(line, known_chapters)
            if ch_hit and (seen_qa or not in_toc):
                if cur_lines:
                    sections.append(
                        {"num": cur_num, "title": cur_title, "raw_name": cur_raw_name, "text": "".join(cur_lines).strip()}
                    )
                cur_num, cur_title, cur_raw_name = ch_hit
                cur_lines = [line]
                continue

        cur_lines.append(line)

    if cur_lines:
        sections.append(
            {"num": cur_num, "title": cur_title, "raw_name": cur_raw_name, "text": "".join(cur_lines).strip()}
        )

    chunks: list[dict] = []
    for sec in sections:
        text = sec["text"]
        if not text:
            continue
        if len(text.encode("utf-8")) <= max_bytes:
            chunks.append(sec)
            continue

        buf, buf_bytes, part_idx = [], 0, 1
        for para in text.split("\n\n"):
            p_bytes = len(para.encode("utf-8")) + 2
            if buf and (buf_bytes + p_bytes > max_bytes):
                chunk_body = "\n\n".join(buf).strip()
                if part_idx > 1 and sec["num"] > 0:
                    chunk_body = f"## [Chapter Context: {sec['title']}]\n\n{chunk_body}"
                chunks.append({"num": sec["num"], "title": sec["title"], "raw_name": sec["raw_name"], "text": chunk_body})
                buf, buf_bytes = [], 0
                part_idx += 1
            buf.append(para)
            buf_bytes += p_bytes
        if buf:
            chunk_body = "\n\n".join(buf).strip()
            if part_idx > 1 and sec["num"] > 0:
                chunk_body = f"## [Chapter Context: {sec['title']}]\n\n{chunk_body}"
            chunks.append({"num": sec["num"], "title": sec["title"], "raw_name": sec["raw_name"], "text": chunk_body})

    return chunks


def split_plain_large_body(body: str, max_bytes: int) -> list[str]:
    if len(body.encode("utf-8")) <= max_bytes:
        return [body]
    chunks, buf, buf_bytes = [], [], 0
    for para in body.split("\n\n"):
        p_bytes = len(para.encode("utf-8")) + 2
        if buf and (buf_bytes + p_bytes > max_bytes):
            chunks.append("\n\n".join(buf).strip())
            buf, buf_bytes = [], 0
        buf.append(para)
        buf_bytes += p_bytes
    if buf:
        chunks.append("\n\n".join(buf).strip())
    return chunks


def make_preview(text: str) -> str:
    clean_lines = [
        strip_md_noise(ln)
        for ln in text.splitlines()
        if ln.strip() and not ln.strip().startswith("## [Chapter Context:")
    ]
    joined = " ".join(ln for ln in clean_lines if ln)
    if len(joined) <= 200:
        return joined
    return f"{joined[:100]} ... {joined[-100:]}"


def extract_doc_info(
    path: Path, text: str, fallback_title: str = "", known_chapters: list[tuple[int, str]] | None = None
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
    prompts, sections = [], []

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
                    if len(sections) >= 12:
                        break
            if len(sections) >= 12:
                break

    return {
        "title": title,
        "updated_date": updated_date,
        "prompts": prompts,
        "sections": sections,
        "preview": make_preview(text) if not is_chat else "",
        "is_chat": is_chat,
    }


def format_file_block(rel_path: Path, body: str, part_label: str = "") -> str:
    label = f" {part_label}" if part_label else ""
    return f"\n\n---\n## FILE: `{rel_path.as_posix()}`{label}\n\n{body}\n"


def write_cold_chunks(group_name: str, items: list[dict]) -> list[dict]:
    chunks, current_blocks, current_meta, current_size = [], [], [], 0
    for item in items:
        block = format_file_block(item["path"], item["body"], item.get("part_label", ""))
        block_size = len(block.encode("utf-8"))
        if current_blocks and (current_size + block_size > MAX_PART_BYTES):
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

        titles, prompts, sections, previews = [], [], [], []
        for m in metas:
            d = m["updated_date"].isoformat() if m.get("updated_date") else ""
            lbl = f"{m.get('title', m['path'].stem)} {m.get('part_label', '')}".strip()
            full_t = f"{lbl} ({d})" if d else lbl
            if full_t not in titles:
                titles.append(full_t)
            prompts.extend(m.get("prompts", []))
            sections.extend(m.get("sections", []))
            if m.get("preview"):
                previews.append(m["preview"])

        written.append(
            {
                "url": f"{RAW_BASE}/_ai_bundles/cold/{filename}",
                "group": f"{group_name}{suffix}",
                "titles": titles,
                "prompts": list(dict.fromkeys(prompts))[:10],
                "sections": list(dict.fromkeys(sections))[:12],
                "preview": previews[0] if previews else "",
            }
        )
    return written


def write_pack_topic_index(pack_name: str, pack_title: str, part_entries: list[dict]) -> list[str]:
    entry_blocks = []
    total = len(part_entries)
    for idx, ent in enumerate(part_entries, start=1):
        el = [
            f"- URL: {ent['url']}",
            f"  Part: {idx}/{total}",
            f"  Files/Parts: {' | '.join(ent['titles'])}",
        ]
        if ent["prompts"]:
            el.append(f"  User Questions: {' | '.join(ent['prompts'])}")
        if ent["sections"]:
            el.append(f"  Topics/Chapters: {' | '.join(ent['sections'])}")
        if ent["preview"]:
            el.append(f"  Preview: {ent['preview']}")
        el.append("")
        entry_blocks.append("\n".join(el))

    chunks, cur, cur_size = [], [], 0
    for blk in entry_blocks:
        b_size = len(blk.encode("utf-8"))
        if cur and (cur_size + b_size > MAX_PART_BYTES):
            chunks.append(cur)
            cur, cur_size = [], 0
        cur.append(blk)
        cur_size += b_size
    if cur:
        chunks.append(cur)

    index_urls = []
    for idx, blks in enumerate(chunks, start=1):
        suffix = f"-p{idx}" if len(chunks) > 1 else ""
        fname = f"{pack_name}-index{suffix}.md"
        header = [
            f"# Topic Index: {pack_title} ({total} Parts)",
            f"# This topic has > {MAX_URLS_PER_PROMPT} parts. Output ONLY the 1 to 8 most relevant Part URLs below for the user's question.",
            "",
        ]
        (PACKS_DIR / fname).write_text("\n".join(header + blks), encoding="utf-8")
        index_urls.append(f"{RAW_BASE}/_ai_bundles/packs/{fname}")
    return index_urls


def write_static_packs(
    pack_items: dict[str, list[dict]], pack_meta: dict[str, dict]
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    pack_urls: dict[str, list[str]] = {}
    pack_index_urls: dict[str, list[str]] = {}

    for pack_name, items in sorted(pack_items.items()):
        chunks, current_blocks, current_meta, current_size = [], [], [], 0
        for item in items:
            block = format_file_block(item["path"], item["body"], item.get("part_label", ""))
            block_size = len(block.encode("utf-8"))
            if current_blocks and (current_size + block_size > MAX_PART_BYTES):
                chunks.append((current_blocks, current_meta))
                current_blocks, current_meta, current_size = [], [], 0
            current_blocks.append(block)
            current_meta.append(item)
            current_size += block_size
        if current_blocks:
            chunks.append((current_blocks, current_meta))

        urls = []
        part_entries = []
        total = len(chunks)
        for idx, (blocks, metas) in enumerate(chunks, start=1):
            filename = f"{pack_name}-p{idx}.md"
            content = f"# Subject Pack: {pack_name} (Part {idx}/{total})\n" + "".join(blocks)
            (PACKS_DIR / filename).write_text(content, encoding="utf-8")
            url = f"{RAW_BASE}/_ai_bundles/packs/{filename}"
            urls.append(url)

            titles, prompts, sections, previews = [], [], [], []
            for m in metas:
                d = m["updated_date"].isoformat() if m.get("updated_date") else ""
                lbl = f"{m.get('title', m['path'].stem)} {m.get('part_label', '')}".strip()
                full_t = f"{lbl} ({d})" if d else lbl
                if full_t not in titles:
                    titles.append(full_t)
                prompts.extend(m.get("prompts", []))
                sections.extend(m.get("sections", []))
                if m.get("preview"):
                    previews.append(m["preview"])

            part_entries.append(
                {
                    "url": url,
                    "titles": titles,
                    "prompts": list(dict.fromkeys(prompts))[:6],
                    "sections": list(dict.fromkeys(sections))[:8],
                    "preview": previews[0] if previews else "",
                }
            )

        pack_urls[pack_name] = urls
        if len(urls) > MAX_URLS_PER_PROMPT:
            pack_title = pack_meta.get(pack_name, {}).get("title", pack_name)
            pack_index_urls[pack_name] = write_pack_topic_index(pack_name, pack_title, part_entries)
        else:
            pack_index_urls[pack_name] = []

    return pack_urls, pack_index_urls


def build_one_tap_html(data_payload: dict) -> str:
    safe_json = json.dumps(data_payload, ensure_ascii=False).replace("</", "<\\/")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1" />
  <title>AI KB — 1-Tap Packs</title>
  <style>
    :root {{
      --bg: #0b1020; --card: #141b2d; --card2: #1b243b; --border: #283454;
      --text: #eef2ff; --muted: #94a3b8; --accent: #3b82f6; --ok: #10b981; --warn: #f59e0b;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0; font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      background: var(--bg); color: var(--text); padding: 14px 12px 96px;
    }}
    .wrap {{ max-width: 780px; margin: 0 auto; }}
    h1 {{ font-size: 1.25rem; margin: 0 0 4px; }}
    .sub {{ font-size: 0.84rem; color: var(--muted); margin-bottom: 12px; }}
    .quick {{ display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }}
    .chip {{
      border: 1px solid var(--border); background: var(--card); color: var(--text);
      padding: 6px 10px; border-radius: 999px; font-size: 0.8rem; cursor: pointer;
    }}
    .chip.active {{ background: var(--accent); border-color: var(--accent); color: #fff; font-weight: 600; }}
    .chip.ok {{ background: var(--ok); border-color: var(--ok); color: #052e16; font-weight: 600; }}
    .search {{
      width: 100%; padding: 10px 12px; border-radius: 10px; border: 1px solid var(--border);
      background: var(--card); color: var(--text); font-size: 0.95rem; margin-bottom: 10px;
    }}
    .tabs {{ display: flex; gap: 6px; overflow-x: auto; padding-bottom: 8px; margin-bottom: 10px; }}
    .section-title {{
      font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.06em;
      color: #93c5fd; margin: 16px 2px 8px; font-weight: 700;
    }}
    .card {{
      background: var(--card); border: 1px solid var(--border); border-radius: 12px;
      padding: 11px 12px; margin-bottom: 9px;
    }}
    .card.selected {{ border-color: var(--accent); background: var(--card2); }}
    .row {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; }}
    .title {{ font-size: 0.96rem; font-weight: 600; line-height: 1.3; }}
    .meta {{ font-size: 0.78rem; color: var(--muted); margin-top: 4px; line-height: 1.35; }}
    .badge {{
      display: inline-block; font-size: 0.72rem; padding: 2px 7px; border-radius: 999px;
      background: #1e293b; color: #cbd5e1; margin-right: 6px;
    }}
    .badge.idx {{ background: #312e81; color: #c7d2fe; border: 1px solid #4f46e5; }}
    .btns {{ display: flex; gap: 6px; flex-shrink: 0; }}
    button {{
      border: 1px solid var(--border); background: #223052; color: #fff;
      padding: 7px 11px; border-radius: 8px; font-size: 0.82rem; font-weight: 600; cursor: pointer;
    }}
    button.copy-btn {{ background: var(--accent); border-color: var(--accent); }}
    button.copy-btn.idx-btn {{ background: #4f46e5; border-color: #6366f1; }}
    button.copy-btn.copied {{ background: var(--ok); border-color: var(--ok); color: #052e16; }}
    button.sel-btn.on {{ background: #1d4ed8; border-color: #60a5fa; }}
    details {{ margin-top: 8px; }}
    summary {{ font-size: 0.78rem; color: var(--muted); cursor: pointer; }}
    .parts {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 7px; }}
    .part-btn {{ background: #0f172a; font-size: 0.75rem; padding: 4px 8px; border-radius: 6px; }}
    .batch-btn {{ background: #1e293b; border-color: #475569; font-size: 0.75rem; padding: 5px 9px; border-radius: 6px; }}
    .bar {{
      position: fixed; left: 0; right: 0; bottom: 0; background: #0f172a;
      border-top: 1px solid var(--border); padding: 10px 12px; display: none;
      align-items: center; justify-content: space-between; gap: 10px; z-index: 20;
    }}
    .bar.show {{ display: flex; }}
    .bar-info {{ font-size: 0.84rem; }}
    .bar-info.over {{ color: #fca5a5; font-weight: 600; }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>AI KB — 1-Tap Packs</h1>
    <div class="sub" id="subInfo"></div>
    <div class="quick" id="quickBar"></div>
    <input class="search" id="searchBox" type="search" placeholder="Search subject, chapter, or chat..." />
    <div class="tabs" id="subjectTabs"></div>
    <div id="listRoot"></div>
  </div>
  <div class="bar" id="mixBar">
    <div class="bar-info" id="mixInfo"></div>
    <div class="btns">
      <button id="mixClearBtn">Clear</button>
      <button class="copy-btn" id="mixCopyBtn">Copy Mix</button>
    </div>
  </div>
  <script id="kb-data" type="application/json">{safe_json}</script>
  <script>
    const DATA = JSON.parse(document.getElementById('kb-data').textContent);
    const PROMPT_LINE = "Read every URL above via URL context and answer my question with exact FILE citations.";
    const DISCOVERY_LINE = "Read the Knowledge Base Index via URL context and output only the 1 to 8 most relevant Cold Bundle URLs for my question.";
    const TOPIC_INDEX_LINE = "Read the Topic Index above via URL context and output a single text code block with ONLY the 1 to 8 most relevant Part URLs for my question, followed by:\\n" + PROMPT_LINE;
    let activeSubject = "all";
    const selected = new Set();

    function copyText(text, btn, labelAfter) {{
      const done = () => {{
        if (!btn) return;
        const orig = btn.textContent;
        btn.textContent = labelAfter || "Copied!";
        btn.classList.add("copied", "ok");
        setTimeout(() => {{ btn.textContent = orig; btn.classList.remove("copied", "ok"); }}, 1400);
      }};
      if (navigator.clipboard && navigator.clipboard.writeText) {{
        navigator.clipboard.writeText(text).then(done).catch(() => fallbackCopy(text, done));
      }} else {{
        fallbackCopy(text, done);
      }}
    }}

    function fallbackCopy(text, done) {{
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      try {{ document.execCommand("copy"); }} catch (e) {{}}
      document.body.removeChild(ta);
      done();
    }}

    function effectiveUrls(p) {{
      return (p.index_urls && p.index_urls.length > 0) ? p.index_urls : p.urls;
    }}

    function updateMixBar() {{
      const bar = document.getElementById("mixBar");
      const info = document.getElementById("mixInfo");
      if (selected.size === 0) {{ bar.classList.remove("show"); return; }}
      let totalUrls = 0;
      DATA.packs.forEach(p => {{ if (selected.has(p.name)) totalUrls += effectiveUrls(p).length; }});
      bar.classList.add("show");
      info.textContent = `Selected: ${{selected.size}} pack(s) • ${{totalUrls}} / 20 URLs`;
      info.classList.toggle("over", totalUrls > 20);
    }}

    function renderQuick() {{
      document.getElementById("subInfo").textContent = `${{DATA.repo}} • ${{DATA.packs.length}} pack(s) • Built ${{DATA.built}}`;
      const qb = document.getElementById("quickBar");
      const items = [
        {{ label: "Copy llms.txt (2-Turn)", text: DATA.quick.llms + "\\n" + DISCOVERY_LINE }},
        {{ label: "Copy Core + Recent", text: DATA.quick.core + "\\n" + DATA.quick.recent + "\\n" + PROMPT_LINE }},
        {{ label: "Copy Core Only", text: DATA.quick.core + "\\n" + PROMPT_LINE }}
      ];
      items.forEach(it => {{
        const b = document.createElement("button");
        b.className = "chip";
        b.textContent = it.label;
        b.onclick = () => copyText(it.text, b, "Copied!");
        qb.appendChild(b);
      }});
    }}

    function renderTabs() {{
      const tabs = document.getElementById("subjectTabs");
      tabs.innerHTML = "";
      const all = [{{ slug: "all", label: `All (${{DATA.packs.length}})` }}, ...DATA.subjects];
      all.forEach(s => {{
        const b = document.createElement("button");
        b.className = "chip" + (activeSubject === s.slug ? " active" : "");
        b.textContent = s.label;
        b.onclick = () => {{ activeSubject = s.slug; renderTabs(); renderList(); }};
        tabs.appendChild(b);
      }});
    }}

    function renderList() {{
      const q = document.getElementById("searchBox").value.trim().toLowerCase();
      const root = document.getElementById("listRoot");
      root.innerHTML = "";

      const filtered = DATA.packs.filter(p => {{
        if (activeSubject !== "all" && p.subject_slug !== activeSubject) return false;
        if (!q) return true;
        return (p.title + " " + p.name + " " + p.subject_label + " " + p.summary).toLowerCase().includes(q);
      }});

      const groups = new Map();
      filtered.forEach(p => {{
        if (!groups.has(p.subject_label)) groups.set(p.subject_label, []);
        groups.get(p.subject_label).push(p);
      }});

      if (groups.size === 0) {{
        const empty = document.createElement("div");
        empty.className = "meta";
        empty.textContent = "No matching packs found.";
        root.appendChild(empty);
        return;
      }}

      groups.forEach((packs, subjLabel) => {{
        const h = document.createElement("div");
        h.className = "section-title";
        h.textContent = `${{subjLabel}} (${{packs.length}})`;
        root.appendChild(h);

        packs.forEach(p => {{
          const isLarge = p.index_urls && p.index_urls.length > 0;
          const card = document.createElement("div");
          card.className = "card" + (selected.has(p.name) ? " selected" : "");

          const row = document.createElement("div");
          row.className = "row";

          const left = document.createElement("div");
          const title = document.createElement("div");
          title.className = "title";
          title.textContent = p.title;
          left.appendChild(title);

          const meta = document.createElement("div");
          meta.className = "meta";
          const badge = document.createElement("span");
          badge.className = "badge" + (isLarge ? " idx" : "");
          badge.textContent = isLarge
            ? `${{p.urls.length}} parts • Topic Index (${{p.index_urls.length}} URL)`
            : `${{p.urls.length}} URL${{p.urls.length > 1 ? "s" : ""}}`;
          meta.appendChild(badge);
          const sumSpan = document.createElement("span");
          sumSpan.textContent = p.summary;
          meta.appendChild(sumSpan);
          left.appendChild(meta);

          const btns = document.createElement("div");
          btns.className = "btns";

          const selBtn = document.createElement("button");
          selBtn.className = "sel-btn" + (selected.has(p.name) ? " on" : "");
          selBtn.textContent = selected.has(p.name) ? "✓" : "+";
          selBtn.onclick = () => {{
            if (selected.has(p.name)) selected.delete(p.name); else selected.add(p.name);
            updateMixBar();
            renderList();
          }};

          const copyBtn = document.createElement("button");
          copyBtn.className = "copy-btn" + (isLarge ? " idx-btn" : "");
          copyBtn.textContent = isLarge ? "Copy Index" : "Copy";
          copyBtn.onclick = () => {{
            const txt = isLarge
              ? (p.index_urls.join("\\n") + "\\n" + TOPIC_INDEX_LINE)
              : (p.urls.join("\\n") + "\\n" + PROMPT_LINE);
            copyText(txt, copyBtn, "Copied!");
          }};

          btns.appendChild(selBtn);
          btns.appendChild(copyBtn);
          row.appendChild(left);
          row.appendChild(btns);
          card.appendChild(row);

          if (p.urls.length > 1) {{
            const det = document.createElement("details");
            const sum = document.createElement("summary");
            sum.textContent = isLarge
              ? `20-URL batches & individual parts (${{p.urls.length}} parts)`
              : `Copy individual part (${{p.urls.length}} parts)`;
            det.appendChild(sum);

            if (isLarge) {{
              const batchDiv = document.createElement("div");
              batchDiv.className = "parts";
              for (let start = 0; start < p.urls.length; start += 20) {{
                const end = Math.min(start + 20, p.urls.length);
                const slice = p.urls.slice(start, end);
                const bb = document.createElement("button");
                bb.className = "batch-btn";
                bb.textContent = `Batch P${{start + 1}}–P${{end}}`;
                bb.onclick = () => copyText(slice.join("\\n") + "\\n" + PROMPT_LINE, bb, "Copied!");
                batchDiv.appendChild(bb);
              }}
              det.appendChild(batchDiv);
            }}

            const partsDiv = document.createElement("div");
            partsDiv.className = "parts";
            p.urls.forEach((u, idx) => {{
              const pb = document.createElement("button");
              pb.className = "part-btn";
              pb.textContent = `P${{idx + 1}}`;
              pb.onclick = () => copyText(u + "\\n" + PROMPT_LINE, pb, "✓");
              partsDiv.appendChild(pb);
            }});
            det.appendChild(partsDiv);
            card.appendChild(det);
          }}

          root.appendChild(card);
        }});
      }});
    }}

    document.getElementById("searchBox").addEventListener("input", renderList);
    document.getElementById("mixClearBtn").onclick = () => {{ selected.clear(); updateMixBar(); renderList(); }};
    document.getElementById("mixCopyBtn").onclick = () => {{
      const urls = [];
      let hasIndex = false;
      DATA.packs.forEach(p => {{
        if (selected.has(p.name)) {{
          if (p.index_urls && p.index_urls.length > 0) hasIndex = true;
          urls.push(...effectiveUrls(p));
        }}
      }});
      const suffix = hasIndex ? TOPIC_INDEX_LINE : PROMPT_LINE;
      copyText([...new Set(urls)].join("\\n") + "\\n" + suffix, document.getElementById("mixCopyBtn"), "Copied!");
    }};

    renderQuick();
    renderTabs();
    renderList();
  </script>
</body>
</html>
"""


def main():
    scan_dirs = [d for d in (Path("core"), Path("chats"), Path("kb")) if d.exists()]
    if not scan_dirs:
        raise SystemExit("Missing 'chats/' or 'core/' directory.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(COLD_DIR, ignore_errors=True)
    shutil.rmtree(PACKS_DIR, ignore_errors=True)
    COLD_DIR.mkdir(parents=True, exist_ok=True)
    PACKS_DIR.mkdir(parents=True, exist_ok=True)

    git_recent = get_git_recent_files(RECENT_DAYS)
    hot_core_blocks = []
    hot_core_items = []
    recent_candidates = []
    cold_groups: dict[str, list[dict]] = {}
    auto_packs: dict[str, list[dict]] = {}
    pack_meta: dict[str, dict] = {}

    def register_pack_meta(pname: str, subj_slug: str, subj_label: str, title: str, sort_key: str):
        if pname not in pack_meta:
            pack_meta[pname] = {
                "subject_slug": subj_slug,
                "subject_label": subj_label,
                "title": title,
                "sort_key": sort_key,
                "files": [],
            }

    root_kb_books = [
        p for d in (Path("kb"),) if d.exists()
        for p in d.iterdir()
        if p.is_file() and p.suffix.lower() in ALLOWED_EXTS
    ]
    multi_root_kb_books = len(root_kb_books) > 1

    for root_dir in scan_dirs:
        for path in sorted(root_dir.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in ALLOWED_EXTS:
                continue

            raw_text = path.read_text(encoding="utf-8", errors="ignore")
            meta, body = parse_frontmatter(raw_text)
            body = clean_chat_wrapper(body)
            is_chat_doc = bool(re.search(r"^##\s+(User|Model)\s*$", body, re.MULTILINE))
            known_chapters = [] if is_chat_doc else extract_toc_chapters(body)
            top_info = extract_doc_info(path, body, known_chapters=known_chapters)
            parts = path.parts

            is_hot = (
                root_dir.name == "core"
                or (root_dir.name == "kb" and len(parts) > 2 and parts[1] == "core")
                or meta.get("tier") == "hot"
            )

            if is_hot:
                hot_core_blocks.append(format_file_block(path, body))
                hot_core_items.append(
                    {
                        "path": path,
                        "body": body,
                        "part_label": "",
                        "title": top_info["title"],
                        "updated_date": top_info["updated_date"],
                        "prompts": top_info["prompts"],
                        "sections": top_info["sections"],
                        "preview": top_info["preview"],
                    }
                )
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

            if known_chapters and body_bytes > MAX_PART_BYTES:
                if len(parts) > 2:
                    subj_slug = sanitize_slug(parts[1])
                    subj_label = prettify_label(parts[1])
                    book_prefix = f"{subj_slug}-"
                else:
                    subj_slug = "books"
                    subj_label = "Books & Compendiums"
                    book_prefix = f"{sanitize_slug(path.stem)[:16]}-" if multi_root_kb_books else ""

                ch_chunks = split_compendium_by_chapters(body, MAX_PART_BYTES - 1500, known_chapters)
                total_parts = len(ch_chunks)
                for idx, ch in enumerate(ch_chunks, start=1):
                    part_label = f"[Part {idx}/{total_parts} — {ch['title']}]"
                    part_info = extract_doc_info(
                        path, ch["text"], fallback_title=top_info["title"], known_chapters=known_chapters
                    )
                    item = {
                        "path": path,
                        "body": ch["text"],
                        "part_label": part_label,
                        "title": top_info["title"],
                        "updated_date": top_info["updated_date"],
                        "prompts": part_info["prompts"],
                        "sections": [ch["title"]] if ch["num"] > 0 else part_info["sections"],
                        "preview": part_info["preview"],
                    }
                    cold_groups.setdefault(group_key, []).append(item)
                    if ch["num"] > 0:
                        ch_pack = f"{book_prefix}{make_chapter_slug(ch['num'], ch['raw_name'])}"
                        register_pack_meta(ch_pack, subj_slug, subj_label, ch["title"], f"0_{subj_slug}_{ch['num']:02d}")
                        if top_info["title"] not in pack_meta[ch_pack]["files"]:
                            pack_meta[ch_pack]["files"].append(top_info["title"])
                        auto_packs.setdefault(ch_pack, []).append(item)
            else:
                if len(parts) > 2:
                    subj_slug = sanitize_slug(parts[1])
                    subj_label = prettify_label(parts[1])
                    if len(parts) > 3:
                        topic_slug = sanitize_slug(parts[2])
                        pack_name = f"{subj_slug}-{topic_slug}"
                        pack_title = f"{subj_label}: {prettify_label(parts[2])}"
                    else:
                        pack_name = subj_slug
                        pack_title = f"{subj_label} (All Notes/Chats)"
                    sort_key = f"1_{subj_slug}_{pack_name}"
                else:
                    subj_slug = "study-chats"
                    subj_label = "Study Chats"
                    if body_bytes > MAX_PART_BYTES:
                        pack_name = f"chat-{sanitize_slug(path.stem)[:36]}"
                        pack_title = top_info["title"]
                        sort_key = f"2_study-chats_{pack_name}"
                    else:
                        pack_name = "study-chats"
                        pack_title = "Study Chats (Compact)"
                        sort_key = "2_study-chats_00"

                register_pack_meta(pack_name, subj_slug, subj_label, pack_title, sort_key)
                if top_info["title"] not in pack_meta[pack_name]["files"]:
                    pack_meta[pack_name]["files"].append(top_info["title"])

                body_parts = split_plain_large_body(body, MAX_PART_BYTES - 1500)
                total_parts = len(body_parts)
                for idx, part_body in enumerate(body_parts, start=1):
                    part_label = f"[Part {idx}/{total_parts}]" if total_parts > 1 else ""
                    part_info = extract_doc_info(path, part_body, fallback_title=top_info["title"])
                    item = {
                        "path": path,
                        "body": part_body,
                        "part_label": part_label,
                        "title": top_info["title"],
                        "updated_date": top_info["updated_date"],
                        "prompts": part_info["prompts"],
                        "sections": part_info["sections"],
                        "preview": part_info["preview"],
                    }
                    cold_groups.setdefault(group_key, []).append(item)
                    auto_packs.setdefault(pack_name, []).append(item)

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
        else f"# Tier 1: Recent Changes\nNo compact chats updated in the last {RECENT_DAYS} days."
    )
    (OUT_DIR / "hot-recent.md").write_text(recent_text, encoding="utf-8")

    all_pack_sources = dict(auto_packs)
    if hot_core_items:
        all_pack_sources["core"] = hot_core_items

    custom_packs: dict[str, list[dict]] = {}
    if PACKS_CONFIG.exists():
        cfg = json.loads(PACKS_CONFIG.read_text(encoding="utf-8"))
        for custom_name, patterns in cfg.items():
            matched_items = []
            for src_name, src_items in sorted(all_pack_sources.items()):
                if any(fnmatch(src_name, pat) for pat in patterns):
                    matched_items.extend(src_items)
            if matched_items:
                cname = f"custom-{sanitize_slug(custom_name)}"
                custom_packs[cname] = matched_items
                register_pack_meta(cname, "custom", "Custom Combos", prettify_label(custom_name), f"3_custom_{cname}")
                pack_meta[cname]["files"] = [f"Matched: {', '.join(patterns)}"]

    combined_packs = {**auto_packs, **custom_packs}
    pack_urls, pack_index_urls = write_static_packs(combined_packs, pack_meta)

    ordered_pack_names = sorted(pack_urls.keys(), key=lambda n: (pack_meta[n]["sort_key"], n))

    pack_lines = [
        "# 1-Turn Dynamic Packs (Grouped by Subject / Book)",
        "# Packs > 20 parts automatically use a 1-URL Topic Index so they fit AI Studio's URL Context cap.",
        "",
    ]
    by_subject_lines: dict[str, list[str]] = {}
    current_subject = None

    for pname in ordered_pack_names:
        urls = pack_urls[pname]
        idx_urls = pack_index_urls.get(pname, [])
        meta_p = pack_meta[pname]
        s_slug = meta_p["subject_slug"]
        s_label = meta_p["subject_label"]

        if s_label != current_subject:
            pack_lines.append("# ========================================")
            pack_lines.append(f"# SUBJECT: {s_label}")
            pack_lines.append("# ========================================")
            pack_lines.append("")
            current_subject = s_label

        if idx_urls:
            block = [
                f"## PACK: {meta_p['title']} [{pname}] ({len(urls)} Parts — Topic Index)",
                *idx_urls,
                "Read the Topic Index above via URL context and output ONLY the 1 to 8 most relevant Part URLs for my question.",
                "",
            ]
        else:
            block = [
                f"## PACK: {meta_p['title']} [{pname}] ({len(urls)} URLs)",
                *urls,
                "Read every URL above via URL context and answer my question with exact FILE citations.",
                "",
            ]

        pack_lines.extend(block)
        by_subject_lines.setdefault(
            s_slug,
            [f"# 1-Turn Packs — Subject: {s_label}", ""],
        ).extend(block)

    (OUT_DIR / "packs-list.txt").write_text("\n".join(pack_lines), encoding="utf-8")
    for s_slug, s_lines in by_subject_lines.items():
        (PACKS_DIR / f"list-{s_slug}.txt").write_text("\n".join(s_lines), encoding="utf-8")

    seen_subj = {}
    for pname in ordered_pack_names:
        m = pack_meta[pname]
        seen_subj[m["subject_slug"]] = m["subject_label"]

    html_packs = []
    for pname in ordered_pack_names:
        m = pack_meta[pname]
        files_preview = ", ".join(m["files"][:3]) + ("..." if len(m["files"]) > 3 else "")
        html_packs.append(
            {
                "name": pname,
                "title": m["title"],
                "subject_slug": m["subject_slug"],
                "subject_label": m["subject_label"],
                "urls": pack_urls[pname],
                "index_urls": pack_index_urls.get(pname, []),
                "summary": files_preview,
            }
        )

    html_payload = {
        "repo": REPO,
        "built": TODAY.isoformat(),
        "quick": {
            "llms": f"{RAW_BASE}/_ai_bundles/llms.txt",
            "core": f"{RAW_BASE}/_ai_bundles/hot-core.md",
            "recent": f"{RAW_BASE}/_ai_bundles/hot-recent.md",
        },
        "subjects": [{"slug": k, "label": v} for k, v in seen_subj.items()],
        "packs": html_packs,
    }
    html_text = build_one_tap_html(html_payload)
    (OUT_DIR / "packs.html").write_text(html_text, encoding="utf-8")
    Path("index.html").write_text(html_text, encoding="utf-8")
    if not Path(".nojekyll").exists():
        Path(".nojekyll").write_text("", encoding="utf-8")

    index_entries = []
    for group_name, items in sorted(cold_groups.items()):
        index_entries.extend(write_cold_chunks(group_name, items))

    lines = [
        "# Knowledge Base Index (Tier 2 Cold Bundles)",
        "# Use static pack URLs from packs-list.txt for 1-turn, or llms.txt for 2-turn discovery.",
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
        lines.append("")

    (OUT_DIR / "llms.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"Built {len(pack_urls)} pack(s) across {len(seen_subj)} subject(s) and {len(index_entries)} cold bundle(s).")


if __name__ == "__main__":
    main()
