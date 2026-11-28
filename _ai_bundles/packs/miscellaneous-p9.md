# Subject Pack: miscellaneous (Part 9/24)


---
## FILE: `chats/Fixing GitHub Actions Workflow Errors.md` [Part 9/10]

def build_pdf_bytes(md_text, assets, footer_prefix='Page '):
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

    css = build_css(footer_prefix)
    full_html = f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>{css}</style></head><body>{body_html}{assets_html}</body></html>'
    return HTML(string=full_html).write_pdf()

def fetch_existing_pdf(file_id):
    for attempt in range(1, 4):
        try:
            resp = requests.post(
                GAS_WEBHOOK_URL,
                json={'secret': GAS_SECRET, 'action': 'get_pdf', 'fileId': file_id},
                timeout=120
            )
            try:
                res_json = resp.json()
            except Exception:
                raise RuntimeError(
                    f"Non-JSON get_pdf response (status={resp.status_code}): {resp.text[:400]}"
                )
            if not res_json.get('ok'):
                raise RuntimeError(f"get_pdf failed for {file_id}: {res_json}")
            return base64.b64decode(res_json['pdfB64'])
        except Exception as e:
            if attempt < 3 and 'timed out' in str(e).lower():
                time.sleep(attempt * 10)
                continue
            raise

def merge_pdfs(old_bytes, delta_bytes):
    writer = PdfWriter()
    writer.append(io.BytesIO(old_bytes))
    writer.append(io.BytesIO(delta_bytes))
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()

def delete_github_job(rel_path):
    sha = None
    try:
        p = subprocess.run(['git', 'rev-parse', f'HEAD:{rel_path}'], text=True, capture_output=True, timeout=10)
        if p.returncode == 0:
            sha = p.stdout.strip()
    except Exception:
        pass

    url = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{rel_path}'
    headers = {'Authorization': f'Bearer {GITHUB_TOKEN}', 'Accept': 'application/vnd.github+json'}
    if not sha:
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code == 200:
            sha = r.json().get('sha')
    if sha:
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

        mode = job.get('mode', 'full')
        footer_prefix = 'Cont. · Page ' if mode in ('append', 'new_part') else 'Page '
        delta_bytes = build_pdf_bytes(job['mdText'], job.get('assets', []), footer_prefix=footer_prefix)

        if mode == 'append' and job.get('existingPdfId'):
            old_bytes = fetch_existing_pdf(job['existingPdfId'])
            final_pdf_bytes = merge_pdfs(old_bytes, delta_bytes)
        else:
            final_pdf_bytes = delta_bytes

        pdf_b64 = base64.b64encode(final_pdf_bytes).decode('ascii')
        pdf_name = job.get('pdfName') or f"{job['baseName']}.pdf"

        for attempt in range(1, 5):
            try:
                resp = requests.post(
                    GAS_WEBHOOK_URL,
                    json={
                        'secret': GAS_SECRET,
                        'mode': mode,
                        'sourceId': job['sourceId'],
                        'updatedMs': job['updatedMs'],
                        'pdfName': pdf_name,
                        'pdfB64': pdf_b64,
                        'expectedTc': job.get('expectedTc', 0),
                        'nextTc': job.get('nextTc'),
                        'nextTh': job.get('nextTh'),
                        'part': job.get('part', 1),
                        'partStartTc': job.get('partStartTc', 0)
                    },
                    timeout=180
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
        print(f"Delivered ({mode}): {pdf_name}")

if __name__ == '__main__':
    main()
```

---

### 3. Google Apps Script (`Code.gs`)

```javascript
/**
 * Syncs AI Studio chats -> Clean .md in Drive -> Private GitHub Actions -> Incremental PDFs via doPost()
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
  const cache = CacheService.getScriptCache();
  if (cache.get('gh_sync_running')) return;
  cache.put('gh_sync_running', '1', 300);

  const startTime = Date.now();

  try {
    const { token } = getSecrets_();
    const mdFolder = getOrCreateFolder_(CONFIG.MD_FOLDER_NAME);
    const pdfFolder = getOrCreateFolder_(CONFIG.PDF_FOLDER_NAME);
    const visited = new Set([mdFolder.getId(), pdfFolder.getId()]);

    const files = [];
    for (const f of getSourceFolders_()) collectFiles_(f, visited, files);

    const seen = new Set(files.map(f => f.getId()));
    try {
      const q = DriveApp.searchFiles('mimeType = "application/vnd.google-makersuite.prompt" and trashed = false');
      while (q.hasNext()) {
        const pf = q.next();
        if (!seen.has(pf.getId())) { seen.add(pf.getId()); files.push(pf); }
      }
    } catch (e) {}

    const props = PropertiesService.getScriptProperties();
    const stateMap = props.getProperties();
    let mdCount = 0, queuedCount = 0, paused = false;

    for (const file of files) {
      if (Date.now() - startTime > 220000) { paused = true; break; }
      if (file.isTrashed()) continue;
      const mime = file.getMimeType();
      if (mime.startsWith('application/vnd.google-apps.') || mime.startsWith('image/') ||
          mime.startsWith('video/') || mime.startsWith('audio/') || mime === 'application/pdf') continue;

      const id = file.getId();
      const updatedMs = file.getLastUpdated().getTime();
      const key = CONFIG.STATE_PREFIX + id;
      let prev = {};
      if (stateMap[key]) { try { prev = JSON.parse(stateMap[key]); } catch (e) {} }

      const needsMd = prev.t !== updatedMs || !prev.m;
      const jobInFlight = prev.qa && (Date.now() - prev.qa < 15 * 60 * 1000);
      const needsPdf = (prev.pt !== updatedMs || !prev.p) && !jobInFlight;

      if (!needsMd && !needsPdf) continue;
      if (file.getSize() > 15 * 1024 * 1024) continue;

      let data;
      try { data = JSON.parse(file.getBlob().getDataAsString('UTF-8')); } catch (e) { continue; }
      if (!data || (!data.chunkedPrompt && !data.contents && !data.runSettings)) continue;

      const chat = extractCleanChat_(data, file);
      const baseName = cleanName_(file.getName());
      const mdName = `${baseName}.md`;
      const fullMdText = renderCleanMd_(chat);

      let mdId = prev.m || null;
      if (needsMd) {
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

      if (needsPdf) {
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
    }

    console.log(paused
      ? `Paused at time guard. MD: ${mdCount}, Queued for PDF: ${queuedCount}. Run again to queue remaining.`
      : `Done! MD updated: ${mdCount}, Queued for GitHub PDF build: ${queuedCount}`);
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
  console.log(`Reset ${resetCount} chat(s). Running syncCleanMarkdown() now...`);
  syncCleanMarkdown();
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
function collectFiles_(folder, visited, out) {
  const id = folder.getId();
  if (visited.has(id)) return;
  visited.add(id);
  const fi = folder.getFiles(); while (fi.hasNext()) out.push(fi.next());
  const si = folder.getFolders(); while (si.hasNext()) { const s = si.next(); if (!s.isTrashed()) collectFiles_(s, visited, out); }
}
function cleanName_(raw) {
  return raw.replace(/\.(json|prompt|txt)$/i, '').replace(/[\\/:*?"<>|]/g, '_').trim() || 'Untitled prompt';
}
```

---

### Order to deploy
1. Commit **`.github/workflows/build-pdfs.yml`** and **`render.py`** on GitHub (`main`).
2. Paste **`Code.gs`** in Apps Script → **Save** → **Deploy → Manage deployments → Edit (✏️) → Version: New version → Deploy** *(important so `doPost` gets the new `get_pdf` action)*.
3. Run **`requeueAllPastChats`** (or **`syncCleanMarkdown`** if you already have jobs waiting) to build the initial baseline (`tc` / `th`) — from then on, any follow-up tokens added to an existing chat will only render the new turns!

---

## User

I updated all the three files. How much are we going to save in comparison with previous method especially for the free tier?

---

## Model

**search** site:developers.google.com/apps-script/guides/services/quotas "Triggers total runtime" "URL Fetch calls" Let's check `1.1.1` / `1.1.2` (`developers.google.com/apps-script/guides/services/quotas`)! Verified exact Apps Script consumer (`gmail.com`) quotas:
- **Triggers total runtime:** **90 min / day** (`1.1.1`)
- **URL Fetch calls:** **20,000 / day** (`1.1.1`)
- *(Also remember `Script runtime` is **6 min / execution** (`1.1.1`)!)*

Let's double-check all calculations so everything is crystal clear, honest, and easy to skim:
