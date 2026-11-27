# Subject Pack: ch03-defeat-stale-caching-with-commit (Part 1/1)


---
## FILE: `chats/Optimizing Two-Step LLM Routing.md` [Part 3/17 — 3. Defeat Stale Caching with Commit-Pinned URLs]

#### 3. Defeat Stale Caching with Commit-Pinned URLs
Because URL Context checks Google's internal index cache before doing a live fetch (and GitHub's raw CDN caches `/main/` links for ~5 minutes), editing a file doesn't always show up immediately if the URL string stays identical.
* **The Fix:** Have your GitHub Action write **commit-SHA URLs** inside `llms.txt`:
  `https://raw.githubusercontent.com/<user>/<repo>/<COMMIT_SHA>/bundle-auth.md`
* Every time a file changes, its URL in `llms.txt` changes. Google sees a brand-new URL, skips any stale index cache, and live-fetches your exact latest version. *(For `llms.txt` itself in System Instructions, you still point to `main/llms.txt`.)*
