# Subject Pack: ch02-context-pollution-speed (Part 1/1)


---
## FILE: `chats/Optimizing Two-Step LLM Routing.md` [Part 2/17 — 2. Context Pollution & Speed]

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
