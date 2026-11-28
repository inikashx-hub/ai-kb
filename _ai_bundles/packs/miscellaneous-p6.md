# Subject Pack: miscellaneous (Part 6/24)


---
## FILE: `chats/Fixing GitHub Actions Workflow Errors.md` [Part 6/10]

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

CSS = """
@page {
  size: A4 portrait;
  margin: 14mm 13mm;
  @bottom-right { content: "Page " counter(page) " of " counter(pages); font-size: 8pt; color: #64748b; }
}
@page wide {
  size: A4 landscape;
  margin: 11mm 12mm;
  @bottom-right { content: "Page " counter(page) " of " counter(pages); font-size: 8pt; color: #64748b; }
}
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
            timeout=60
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

def build_pdf_bytes(md_text, assets):
    clean_md, math_items = prepare_markdown_and_math(md_text)
    soup = BeautifulSoup(md.render(clean_md), 'html.parser')
    for a in soup.find_all('a'):
        a.unwrap()

    for tbl in soup.find_all('table'):
        for cell in tbl.find_all(['th', 'td']):
            for txt_node in list(cell.find_all(string=True)):
                if txt_node.parent and txt_node.parent.name in ('code', 'pre'):
                    continue
                val = str(txt_node)
                if re.search(r'<br\s*/?>', val, re.I):
                    parts = re.split(r'<br\s*/?>', val, flags=re.I)
                    new_nodes = []
                    for idx, part in enumerate(parts):
                        if part:
                            new_nodes.append(NavigableString(part))
                        if idx < len(parts) - 1:
                            new_nodes.append(soup.new_tag('br'))
                    if new_nodes:
                        txt_node.replace_with(*new_nodes)

        rows = tbl.find_all('tr')
        if rows:
            col_count = max(len(r.find_all(['th', 'td'])) for r in rows)
            if col_count > 0:
                max_lens = [4] * col_count
                for r in rows:
                    for idx, cell in enumerate(r.find_all(['th', 'td'])):
                        if idx < col_count:
                            for seg in cell.get_text('\n').split('\n'):
                                max_lens[idx] = max(max_lens[idx], len(seg.strip()))
                weights = [max(8, min(45, l + 2)) for l in max_lens]
                total_w = sum(weights)
                colgroup = soup.new_tag('colgroup')
                for w in weights:
                    colgroup.append(soup.new_tag('col', style=f'width: {(w / total_w) * 100:.1f}%;'))
                tbl.insert(0, colgroup)
                if col_count >= 5:
                    tbl['class'] = tbl.get('class', []) + ['compact-tbl']
                    wrapper = soup.new_tag('div', attrs={'class': 'wide-page'})
                    tbl.wrap(wrapper)

    rendered_svgs = render_math_batch(math_items)
    body_html = str(soup)
    for idx, item in enumerate(math_items):
        svg_markup = rendered_svgs[idx] if idx < len(rendered_svgs) else None
        cls = 'math-display' if item['display'] else 'math-inline'
        if svg_markup:
            replacement = f'<span class="{cls}">{svg_markup}</span>'
        else:
            replacement = f'<span class="{cls} math-fallback">{html.escape(item["expr"])}</span>'
        body_html = body_html.replace(f'\uE000M{idx}\uE001', replacement)

    assets_html = ''
    for asset in assets:
        mime = asset.get('mimeType', 'image/png')
        b64 = asset.get('dataB64', '')
        if b64:
            assets_html += f'<div class="diagram"><img src="data:{mime};base64,{b64}" /></div>'

    full_html = f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{body_html}{assets_html}</body></html>'
    return HTML(string=full_html).write_pdf()

def delete_github_job(rel_path):
    url = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{rel_path}'
    headers = {'Authorization': f'Bearer {GITHUB_TOKEN}', 'Accept': 'application/vnd.github+json'}
    r = requests.get(url, headers=headers, timeout=20)
    if r.status_code == 200:
        sha = r.json().get('sha')
        requests.delete(url, headers=headers, json={'message': f'Done {rel_path}', 'sha': sha}, timeout=20)

def main():
    if not os.path.isdir('jobs'):
        print('No jobs directory found.')
        return

    job_files = sorted(f for f in os.listdir('jobs') if f.endswith('.json'))
    print(f'Found {len(job_files)} queued jobs.')

    for fname in job_files:
        path = os.path.join('jobs', fname)
        with open(path, 'r', encoding='utf-8') as f:
            job = json.load(f)

        pdf_bytes = build_pdf_bytes(job['mdText'], job.get('assets', []))
        pdf_b64 = base64.b64encode(pdf_bytes).decode('ascii')

        for attempt in range(1, 5):
            try:
                resp = requests.post(
                    GAS_WEBHOOK_URL,
                    json={
                        'secret': GAS_SECRET,
                        'sourceId': job['sourceId'],
                        'updatedMs': job['updatedMs'],
                        'pdfName': f"{job['baseName']}.pdf",
                        'pdfB64': pdf_b64
                    },
                    timeout=90
                )
                try:
                    res_json = resp.json()
                except Exception:
                    raise RuntimeError(
                        f"Non-JSON response for {fname} "
                        f"(status={resp.status_code}, url={resp.url}): {resp.text[:500]}"
                    )

                if res_json.get('ok'):
                    break

                err_msg = str(res_json.get('error', res_json))
                if 'lock timeout' in err_msg.lower() and attempt < 4:
                    wait_s = attempt * 15
                    print(f"Lock busy for {fname}, retrying in {wait_s}s (attempt {attempt}/4)...")
                    time.sleep(wait_s)
                    continue
                raise RuntimeError(f"Callback failed for {fname}: {res_json}")
            except Exception as e:
                if attempt < 4 and ('lock timeout' in str(e).lower() or 'timed out' in str(e).lower()):
                    wait_s = attempt * 15
                    print(f"Retrying {fname} in {wait_s}s (attempt {attempt}/4): {e}")
                    time.sleep(wait_s)
                    continue
                raise

        delete_github_job(f'jobs/{fname}')
        print(f"Delivered: {job['baseName']}.pdf")

if __name__ == '__main__':
    main()
```

---

### After committing both files on GitHub
1. In Google Apps Script, run **`requeueAllPastChats`** once (and **`syncCleanMarkdown`** once more if it pauses at the 220s guard).
2. In GitHub **Actions**, check the new run to confirm **`Install MathJax for LaTeX equations`** succeeds ✅ — then inspect **`Solving Math Questions Under 30s.pdf`** in Drive!

---

## Model

**search** github api 422 "Workflow does not have 'workflow_dispatch' trigger" YES!! Look at `1.1.2` and `1.2.1`! Exact causes of `422: "Workflow does not have 'workflow_dispatch' trigger"`:
1. **`on: workflow_dispatch:` is broken / missing / mis-indented in `.github/workflows/build-pdfs.yml`** (e.g. a paste glitch on mobile left template lines from GitHub's `main.yml` starter template, or mis-indented `workflow_dispatch:`) [1.1.2, 1.2.1].
2. **Wait — ALSO check `1.2.1`!!**
   Could **GitHub's workflow registry** still be pointing at an old deleted/renamed `.GitHub/workflows/build-pdfs.yml` or disabled workflow, OR did `build-pdfs.yml` fail to parse YAML? Let's check BOTH clearly:
   - Open `.github/workflows/build-pdfs.yml` on `main` and check lines 1–10:
     1. Must be at path **`.github/workflows/build-pdfs.yml`** (all lowercase, NOT `.GitHub/workflows/`!).
     2. Lines 1–5 must be **exact**:
        ```yaml
        name: Build AI Studio PDFs

        on:
          workflow_dispatch:
        ```
        *(Note: `workflow_dispatch:` MUST be indented **2 spaces** under `on:` — NOT on the same line, NOT 0 spaces, and NOT mixed with leftover lines from GitHub's `main.yml` starter workflow like `on: [push]`!)*
     3. Also check if **`.GitHub/workflows/build-pdfs.yml`** (the old capital-G folder) still exists in the repo! If two `build-pdfs.yml` files exist or `.github/workflows/build-pdfs.yml` has a syntax error, GitHub Actions gets confused.
   - And check **GitHub → Actions → Build AI Studio PDFs**: if GitHub shows a red banner (`Invalid workflow file`) or the **Run workflow** button is missing, that confirms `.github/workflows/build-pdfs.yml` has a YAML / indentation mistake!

AND notice one super helpful thing to remind them:
- **Good news:** `MD: 37, Queued for PDF: 37.` means those 37 `.json` jobs are **already safely queued inside `jobs/` on GitHub**!
- As soon as you fix `.github/workflows/build-pdfs.yml` on `main`, just run **`syncCleanMarkdown`** in Apps Script again — it will queue the next batch of the remaining 80 chats **and** trigger GitHub Actions cleanly! (And if you want to test immediately, you can also tap **Run workflow** on GitHub right after fixing `build-pdfs.yml`.)

Wait — let's ALSO check one small thing in their `12:09` screenshot! Look at the left panel in Apps Script (`12:09`): `Untitled 2.gs`! Wait — do they have TWO `.gs` files (`Code.gs` AND `Untitled 2.gs`), or just `Untitled 2.gs`? Look closely at the **Files** sidebar on the left (`12:09`): There is ONLY **one** file listed under **Files**: `Untitled 2.gs`! And look at the **Execution log**:
`12:07:51 PM Error GitHub workflow trigger failed (422)...`
`12:07:51 PM Info Paused at time guard. MD: 37, Queued for PDF: 37.`
So there is NO duplicate `.gs` file issue — only `Untitled 2.gs` ran, and it ran cleanly!

Let's write a super clear, short, actionable reply!The good news in that log: **`MD: 37, Queued for PDF: 37`** worked — all 37 updated jobs are already safely sitting in `jobs/` on GitHub!

The **`422` error** (`"Workflow does not have 'workflow_dispatch' trigger"`) means GitHub cannot find a valid `workflow_dispatch:` trigger in **`.github/workflows/build-pdfs.yml`** on `main` right now . When editing on mobile, this usually happens for one of three reasons:

### Check `.github/workflows/build-pdfs.yml` on GitHub
1. **Check the exact path:** Make sure the file is at lowercase **`.github/workflows/build-pdfs.yml`** (and verify the old **`.GitHub/workflows/build-pdfs.yml`** is deleted if it's still there).
2. **Check the top 5 lines for indentation / leftover template text:** 
   Open **`.github/workflows/build-pdfs.yml`**, tap **Edit (✏️)**, select everything, and make sure the file starts cleanly with:
   ```yaml
   name: Build AI Studio PDFs

   on:
     workflow_dispatch:
   ```
   *(Make sure `workflow_dispatch:` is indented **2 spaces** under `on:`, and there are no leftover `on: [push]` lines from GitHub's starter template.)*
3. **Quick sanity check in the Actions tab:** 
   After committing `.github/workflows/build-pdfs.yml`, open **Actions → Build AI Studio PDFs**.
   * If GitHub shows a red **"Invalid workflow file"** banner, share a screenshot of `build-pdfs.yml` here so we can spot the syntax typo.
   * If you see the **`Run workflow`** button, the `422` error is fixed!

---

### Next step once `build-pdfs.yml` is fixed
Run **`syncCleanMarkdown`** in Apps Script again — it will queue the next batch of your remaining chats **and** automatically trigger GitHub Actions (`triggerGitHubWorkflow_`) to render the 37 jobs already waiting in `jobs/` plus the new batch.

---

## Model

Look at your **Code** tab screenshot: the folder shows **`.github`** by itself (earlier when `workflows` was the only subfolder, GitHub displayed `.GitHub/workflows`).

That usually means either:
1. **`build-pdfs.yml` was saved directly inside `.github/`** (or inside `.github/Workflows/` with a capital `W`) instead of exact lowercase **`.github/workflows/build-pdfs.yml`**, **OR**
2. There is a **YAML syntax error** inside `build-pdfs.yml`.

Tap **`.github`** on your **Code** tab and share a screenshot of what's inside (and of `build-pdfs.yml` if it's in `.github/workflows/`).

---

## Model

Found it! Look at the path at the top of your screenshot: **`AI-Studio-pdf-worker / .github / build-pdfs.yml`**

The **`workflows/`** folder is missing — GitHub Actions only reads workflows stored inside **`.github/workflows/build-pdfs.yml`** (not `.github/build-pdfs.yml`). Your YAML contents look completely fine!

---

### Fix it in 15 seconds on Mobile

1. On that `build-pdfs.yml` page (Screenshot 2), tap **`•••`** (top right of the file box) → **Edit file** (or the **✏️** icon).
2. In the filename box at the top (`build-pdfs.yml`), type **`workflows/`** right in front of it so it reads:
   ```text
   workflows/build-pdfs.yml
   ```
   *(The full breadcrumb at the top will turn into: `AI-Studio-pdf-worker / .github / workflows / build-pdfs.yml` — all lowercase.)*
3. Tap **Commit changes…** → **Commit changes** (to `main`).

*(If GitHub's mobile keyboard doesn't accept `/` in the filename box, just use **Actions → `•••` → New workflow → set up a workflow yourself** to create `build-pdfs.yml` inside `.github/workflows/`, paste your YAML, commit it, and delete `.github/build-pdfs.yml`.)*

---

### Now run it!
1. Open **Actions** → tap the left sidebar icon (`◧`) → tap **`Build AI Studio PDFs`** → **Run workflow** → **Run workflow** (this immediately renders the **37** jobs already waiting in `jobs/` with MathJax!).
2. Run **`syncCleanMarkdown`** in Apps Script once or twice more to queue the remaining past chats (and this time Apps Script's automatic trigger won't hit `422`!).

---

## User

Execution limits on GitHub free tier

---

## Model

**search** github actions free tier minutes private repository 2025 2026 github actions usage limits workflow timeout concurrency api rate limit 2026 Let's check ALL the official numbers carefully and run one quick search on `docs.github.com` for GitHub Actions usage limits (`max job execution time`, `concurrent jobs`, `workflow run queue`) AND `GitHub Free` Actions minutes/storage + `2026` pricing changes if any!**search** site:docs.github.com "Usage limits, billing, and administration" github actions site:docs.github.com "About billing for GitHub Actions" "GitHub Free" Look at `1.2.1` and `2.1.1` / `2.2.1` (`docs.github.com`)! Let's verify every single limit right from official GitHub documentation (and check if anything changed in 2026, e.g., self-hosted vs GitHub-hosted)! Wait: let's also check `GitHub Actions` private repo storage (500 MB) and concurrent jobs on GitHub Free (`20` total concurrent jobs on Ubuntu/Linux) and `1,000` API requests/hour for `GITHUB_TOKEN`, plus workflow run time (`6 hours` per job / `72 hours` per run? Or `35 days`?). Let's run a targeted search on `docs.github.com` for those exact numbers so every number we quote is 100% verified!**search** site:docs.github.com "Job execution time" "Workflow run time" "Concurrent jobs" github actions site:docs.github.com "GITHUB_TOKEN" "1,000 requests per hour" site:docs.github.com "GitHub Free" "2,000" "500 MB" actions EVERY NUMBER IS 100% VERIFIED DIRECTLY FROM OFFICIAL `docs.github.com` RESULTS!

Let's double-check every single limit and apply it directly to the user's **exact setup** (`AI-Studio-pdf-worker`, **Private** repo, `ubuntu-latest`, `GITHUB_TOKEN`, Google Apps Script pushing `jobs/*.json` and triggering `workflow_dispatch`):

1. **Monthly Minutes & Storage (GitHub Free, Private Repo) [3.1.1, 3.2.1, 3.3.1]:**
   - **Included minutes:** **2,000 minutes/month** for **private** repositories on GitHub Free (reset monthly) [3.1.1, 3.2.1]. *(Public repositories have unlimited free minutes for standard runners, though your `AI-Studio-pdf-worker` repo is **Private**—which you definitely want to keep Private so your chat contents in `jobs/` stay private!)*
   - **OS multiplier:** Standard Linux (`ubuntu-latest`) counts as **1×** (1 minute used = 1 minute deducted) [3.1.1]. *(Windows = 2×, macOS = 10× [3.1.1].)*
   - **Storage:** **500 MB** of Actions Artifacts & Packages storage [3.1.1, 3.2.1]. *(Note: Your workflow doesn't upload Artifacts and deletes `jobs/*.json` after completion, so your Actions artifact storage stays near **0 MB**!)*
   - **Spending limit:** By default on GitHub Free, the Actions spending limit is **$0**, meaning if you ever exceed 2,000 minutes in a month, GitHub simply pauses Actions until next month (you won't get surprise charges unless you explicitly add a payment method and raise the budget) [3.1.1, 3.2.1].

2. **Job & Workflow Runtime Limits [1.1.1, 1.3.2]:**
   - **Max time per single job:** **6 hours** (360 minutes) [1.1.1, 1.3.2] — though in your `build-pdfs.yml`, you set `timeout-minutes: 30`, so GitHub will cancel a single run after 30 minutes if it ever hangs.
   - **Max time per workflow run (including waiting/queued):** **35 days** [1.1.1].
   - **Queueing / Concurrency:** On GitHub Free, you can run up to **20 concurrent jobs** total across your account (up to 5 macOS jobs) [1.2.1]. Your workflow also explicitly sets `concurrency: group: ai-studio-pdf-renderer` with `cancel-in-progress: false`, which means only **1** `render` job runs at a time and a second triggered run queues cleanly behind it.

3. **GitHub REST API Limits (important for your `jobs/` queue!) [1.1.1, 2.2.1]:**
   - **Inside `render.py` (`GITHUB_TOKEN`):** **1,000 requests per hour per repository** [2.2.1].
     - Each delivered PDF in `render.py` uses **2 API calls** (`GET` SHA + `DELETE` `jobs/{id}.json`). That supports up to **500 PDFs/hour**!
   - **From Google Apps Script (`Personal Access Token`):** **5,000 requests per hour** per GitHub user account.
     - Each queued chat uses 2 API calls (`GET` + `PUT`), plus 1 call to `triggerGitHubWorkflow_` — plenty for 117 chats!
   - **Workflow dispatch / API request rate:** Up to **1,000 API requests in 1 hour** across all actions in a repo for `GITHUB_TOKEN` [2.2.1], and **max 500 queued/running workflow runs per 10 seconds** per repo (you'll never hit that with 15-minute triggers).
   - **Note on `jobs/` commit history:** Every `PUT` and `DELETE` via Contents API adds a commit to `main` (GitHub soft-recommends keeping repo size well under **1 GB–5 GB**; deleting `jobs/*.json` keeps the working tree small, and your text/PDF job files are deleted right after rendering, though note that deleted `jobs/*.json` base64 images stay in Git history—good to keep in mind long-term if you ever have huge image chats, though for normal chats it's tiny).

4. **How much of your 2,000 minutes/month will this PDF pipeline actually use?**
   Let's do the real math based on their **observed run times** in their own screenshots!
   - In Run `#43` (`1 job`): **36 seconds** total (~20s setup/install + ~16s render — note `Install MathJax` adds ~5–8s, so ~25–30s fixed setup per run).
   - In the `9:36` run (~50 jobs in `4m 19s`): **~5 seconds per PDF**.
   - **Math for your backfill of ~117 chats:**
     - Setup (~30s) + 117 PDFs × ~5s ≈ **~10 minutes total** (even split across 2–3 batches, maybe **11–13 minutes total** — under **1%** of your 2,000 free monthly minutes!).
   - **Math for ongoing daily use:**
     - Suppose you create/update **5 chats/day** (triggered once per chat or batched every 15 mins):
     - ~5 runs × ~40s ≈ **3.5 minutes/day** → **~100 minutes/month** (only **5%** of your 2,000-minute Free tier!).
   - *(Tip: Notice `syncCleanMarkdown` only triggers GitHub Actions when `queuedCount > 0`! So your 15-minute Apps Script trigger does **NOT** waste GitHub Actions minutes when there are no new/updated chats!)*

5. **Also mention where to check remaining minutes anytime on GitHub:**
   - **Profile icon → Settings → Billing & licensing → Usage** (or **Billing and plans**) shows exact Actions minutes used out of 2,000 in real time!

Everything is grounded in verified GitHub documentation (`[1.1.1, 1.2.1, 2.2.1, 3.1.1, 3.2.1]`) and directly tailored to their exact repo and observed numbers! Let's write a clear, concise, practical breakdown.For a **private repository** on the **GitHub Free** plan (`AI-Studio-pdf-worker`), here are the exact limits and what they mean for your PDF pipeline:

---

### 1. Monthly Usage Quotas (GitHub Free — Private Repo)
* **2,000 Actions minutes / month** (resets every month) [3.1.1, 3.2.1].
  * Your workflow uses `ubuntu-latest` (Linux), which counts at **1×** (1 real minute = 1 minute deducted) [3.1.1]. *(Windows counts as 2× and macOS as 10× [3.1.1].)*
* **500 MB of Artifacts & Packages storage** [3.1.1, 3.2.1].
  * Your workflow doesn't save build artifacts and deletes `jobs/*.json` after delivery, so this stays near **0 MB**.
* **$0 default spending limit:** If you ever hit 2,000 minutes in a month, GitHub simply pauses Actions until the next billing cycle — **you won't be charged automatically** unless you add a payment method and raise the limit [3.1.1, 3.2.1].

*(Note: Public repositories get unlimited Linux minutes, but keeping your repo **Private** is important so your personal AI Studio chats in `jobs/` aren't publicly visible.)*

---

### 2. Per-Run & Concurrency Limits
* **Max time per single job:** **6 hours (360 minutes)** [1.1.1, 1.3.2]. 
  * Your `build-pdfs.yml` caps each run at `timeout-minutes: 30` (30 minutes), which is plenty.
* **Max concurrent jobs:** **20 jobs at the same time** across your Free account [1.2.1].
  * Your `build-pdfs.yml` uses `concurrency: group: ai-studio-pdf-renderer` with `cancel-in-progress: false`, so runs cleanly queue 1-at-a-time instead of colliding.
* **API rate limits:**
  * Inside `render.py` (`GITHUB_TOKEN`): **1,000 API requests/hour** per repo [2.2.1] (each PDF uses 2 calls to `GET` + `DELETE` its job file → supports up to **~500 PDFs/hour**).
  * From Google Apps Script (your Personal Access Token): **5,000 API requests/hour** (each queued chat uses 2 calls → easily handles thousands of chats/hour).

---

### 3. How much of the 2,000 minutes your workflow actually uses
Based on your run logs (`~25–30s` setup per run + `~5s` per PDF):
* **Initial backfill (~117 past chats):** Roughly **10–13 minutes total** (< 1% of your 2,000 monthly minutes).
* **Normal daily usage:** Because Apps Script only triggers GitHub when `queuedCount > 0`, idle 15-minute checks use **0 GitHub minutes**. Even if you convert **10 chats every single day**, that's only around **~200 minutes/month (~10% of the Free tier)**.

### Where to check your live usage
Tap your GitHub profile picture → **Settings → Billing & licensing → Usage** to see how many of your 2,000 monthly minutes have been used so far.

---

## User

Does it affect long session chats differently?

---

## Model
