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
            d = m["updated_date"].isoformat() if m["updated_date"] else ""
            lbl = f"{m['title']} {m.get('part_label', '')}".strip()
            full_t = f"{lbl} ({d})" if d else lbl
            if full_t not in titles:
                titles.append(full_t)
            prompts.extend(m["prompts"])
            sections.extend(m["sections"])
            if m["preview"]:
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


def write_static_packs(pack_items: dict[str, list[dict]]) -> dict[str, list[str]]:
    pack_urls: dict[str, list[str]] = {}
    for pack_name, items in sorted(pack_items.items()):
        chunks, current_blocks, current_size = [], [], 0
        for item in items:
            block = format_file_block(item["path"], item["body"], item.get("part_label", ""))
            block_size = len(block.encode("utf-8"))
            if current_blocks and (current_size + block_size > MAX_PART_BYTES):
                chunks.append(current_blocks)
                current_blocks, current_size = [], 0
            current_blocks.append(block)
            current_size += block_size
        if current_blocks:
            chunks.append(current_blocks)

        urls = []
        total = len(chunks)
        for idx, blocks in enumerate(chunks, start=1):
            filename = f"{pack_name}-p{idx}.md"
            content = f"# Subject Pack: {pack_name} (Part {idx}/{total})\n" + "".join(blocks)
            (PACKS_DIR / filename).write_text(content, encoding="utf-8")
            urls.append(f"{RAW_BASE}/_ai_bundles/packs/{filename}")
        pack_urls[pack_name] = urls
    return pack_urls


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

    for root_dir in scan_dirs:
        for path in sorted(root_dir.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in ALLOWED_EXTS:
                continue

            raw_text = path.read_text(encoding="utf-8", errors="ignore")
            meta, body = parse_frontmatter(raw_text)
            body = clean_chat_wrapper(body)
            known_chapters = extract_toc_chapters(body)
            top_info = extract_doc_info(path, body, known_chapters=known_chapters)
            parts = path.parts

            is_hot = (
                root_dir.name == "core"
                or (root_dir.name == "kb" and len(parts) > 2 and parts[1] == "core")
                or meta.get("tier") == "hot"
            )

            if is_hot:
                hot_core_blocks.append(format_file_block(path, body))
                hot_core_items.append({"path": path, "body": body, "part_label": ""})
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
                        ch_pack = make_chapter_slug(ch["num"], ch["raw_name"])
                        auto_packs.setdefault(ch_pack, []).append(item)
            else:
                if root_dir.name == "chats" and len(parts) > 2:
                    pack_name = sanitize_slug(parts[1])
                elif root_dir.name == "kb" and len(parts) > 2:
                    pack_name = sanitize_slug(parts[1])
                else:
                    pack_name = "study-chats"

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

    # Apply optional user-defined packs.json (wildcard rules over auto-packs & core)
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
                custom_packs[f"custom-{sanitize_slug(custom_name)}"] = matched_items

    combined_packs = {**auto_packs, **custom_packs}
    pack_urls = write_static_packs(combined_packs)

    pack_lines = [
        "# 1-Turn Dynamic Packs (Auto-generated from folders, chapters, and optional packs.json)",
        "# Mix and match any URLs below in Turn 1, or define your own combos in packs.json.",
        "",
    ]
    for pname, urls in pack_urls.items():
        pack_lines.append(f"## PACK: {pname} ({len(urls)} URLs)")
        for u in urls:
            pack_lines.append(u)
        pack_lines.append("Read every URL above via URL context and answer my question with exact FILE citations.")
        pack_lines.append("")
    (OUT_DIR / "packs-list.txt").write_text("\n".join(pack_lines), encoding="utf-8")

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
    print(f"Built {len(pack_urls)} pack(s) and {len(index_entries)} cold bundle(s).")


if __name__ == "__main__":
    main()
