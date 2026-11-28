# Subject Pack: chat-fixing-github-actions-workflow-error (Part 2/10)


---
## FILE: `chats/Fixing GitHub Actions Workflow Errors.md` [Part 2/10]

Once I see lines 1–125 of `render.py`, I'll give you an updated `render.py` (and workflow update if needed) that:
* Fixes the `$` / `**$S$**` corruption,
* Repairs the missing-newline `:* ` and `.* ` bullets cleanly, and
* Renders every `$...$` and `$$...$$` LaTeX formula (`\text{}`, `\mathbf{}`, `\frac{}{}`, `\implies`, `\dots`, etc.) as **crisp vector math equations** in the PDF instead of raw code!**search**
"mathjax-full" liteAdaptor TeX SVG convert svg node.js weasyprint inline svg vertical-align mathjax Look at `1.2.1`, `1.2.2`, `1.2.5`, and `2.1.4`!! Let's check every detail from those docs:
1. **`mathjax-full` Node.js API (`1.2.2`, `1.2.5`):**
   ```js
   const { mathjax } = require('mathjax-full/js/mathjax.js');
   const { TeX } = require('mathjax-full/js/input/tex.js');
   const { SVG } = require('mathjax-full/js/output/svg.js');
   const { liteAdaptor } = require('mathjax-full/js/adaptors/liteAdaptor.js');
   const { RegisterHTMLHandler } = require('mathjax-full/js/handlers/html.js');
   const { AllPackages } = require('mathjax-full/js/input/tex/AllPackages.js');
   ```
   - `const adaptor = liteAdaptor();`
   - `RegisterHTMLHandler(adaptor);`
   - `const tex = new TeX({ packages: AllPackages });`
   - `const svg = new SVG({ fontCache: 'none' });` *(Crucial! `fontCache: 'none'` embeds the exact `<path>` definitions inside each `<svg>` so WeasyPrint doesn't lose glyphs or require shared `<defs>` across `<svg>` elements!)* [1.2.2, 1.2.5]
   - `const html = mathjax.document('', { InputJax: tex, OutputJax: svg });` [1.2.2, 1.2.5]
   - `const node = html.convert(texStr, { display: isDisplay });` [1.2.2, 1.2.5]
   - `adaptor.innerHTML(node)` gives `<svg style="vertical-align: -0.xxxex;" width="...ex" height="...ex" ...>...</svg>`! [1.2.2, 2.1.4]
2. **WAIT — Check WeasyPrint compatibility with MathJax `<svg>`!**
   Look at `2.1.4` (`GitHub Kozea/WeasyPrint#1773`) and `2.2.1`: In MathJax SVG output:
   - MathJax sets `width="...ex" height="...ex"` and `style="vertical-align: -0.xxxex;"` on the `<svg>`, AND uses `stroke="currentColor" fill="currentColor"` (which WeasyPrint supports — or explicitly inherits `color`).
   -Wait: look at `2.1.4` carefully! Let's check if WeasyPrint has ANY quirk with MathJax SVG `ex` units or `mjx-container`! Let's run one targeted search on `WeasyPrint MathJax SVG` (`Kozea/WeasyPrint#1773` or `mathjax svg weasyprint`).**search** "WeasyPrint" mathjax svg "ex" OR "vertical-align" OR "mjx-container" Look at `1.2.1` (`WeasyPrint#1773`!) and `1.2.3`:
- In WeasyPrint, `<mjx-container>` can be styled cleanly as `display: inline-block;` (for inline math) or `display: block; text-align: center; margin: 8px 0;` (for display math `$$...$$`)!
- Even more important: notice in our `render.py` right now:
  ```css
  .diagram svg, img { max-width: 100%; max-height: 520px; height: auto; }
  ```
  Notice the selector `.diagram svg, img` ONLY targets `.diagram svg` and `img` (NOT `svg` globally — good! Never apply `height: auto` to inline math `<svg>`s because `height: auto` breaks MathJax's `height="...ex"` sizing!). Putting math `<svg>`s inside `<span class="math-inline">...</span>` and `<div class="math-display">...</div>` keeps them completely isolated from `.diagram svg`!
- Also note `1.2.3`: in WeasyPrint, `vertical-align` works on inline `<svg>` directly inside `<span class="math-inline">`! Adding `overflow: visible;` on `svg` and preserving MathJax's `style="vertical-align: ..."` ensures superscripts/subscripts/fractions align cleanly with surrounding text!

WAIT — BEFORE WE WRITE ANY CODE, STOP AND CHECK **ALL FOUR** THINGS IN `render.py` AND THE SOURCE `.md`!

Let's examine **WHY** the user's PDF had ALL the weird artifacts on Pages 1–4:
1. **Why were raw `$...$`, `$$...$$`, `\text{}`, `\mathbf{}`, `\frac{}{}`, `\implies`, `\dots`, `\times` printed as raw text?**
   Because `render.py` used `MarkdownIt('commonmark')` with **no math extraction/rendering**! Look at `render.py` line 34:
   `md = MarkdownIt('commonmark', {'html': False, 'linkify': False, 'highlight': render_code}).enable(['table', 'strikethrough'])`
   AND look at what happens when **CommonMark** parses raw LaTeX BEFORE math is protected:
   - CommonMark eats `*`, `_`, `\`, etc. **inside** `$...$` and `$$...$$`!!
   - For example: if a formula has `$a_1 + a_2$` or `$\mathbf{x}$` or `$a * b$`, CommonMark turns `_1 ... _2` into `<em>1 ... </em>2` and strips backslashes (`\\` → `\`), breaking LaTeX!
   - **Solution:** Extract and protect **fenced code blocks / inline code first**, THEN extract `$$...$$` and `$...$` math blocks **into placeholder tokens (`@@MATH_0@@`) BEFORE running `md.render(...)`**, render those math expressions via MathJax SVG, and substitute the `<svg>` HTML back in AFTER `BeautifulSoup` finishes!

2. **WAIT — NOW LOOK AGAIN AT THE MYSTERY WE NOTICED EARLIER:**
   Why did the user's PDF screenshot have:
   - `Notice that the variable $$$ appears` (when `.md` had `**$S$**`)
   - `1. Find $HS:` (when `.md` had `1. **Find $H$:**`)
   - `using $LS:` (when `.md` had `**$L$:**`)
   - `coefficient of $$S$$` (when `.md` had `$S$`)
   - `Find what $MS contains:` (when `.md` had `**$M$**`)
   WAIT A SECOND!! We ALREADY saw EVERY line of `render.py` (`lines 1–177`). `render.py` has **NO** code that turns `$H$` into `$HS` or `$S$` into `$$$`/`$$S$$`! **WHERE DID THAT HAPPEN?!** Look at the two possibilities:
   - Either **Google Apps Script** (when creating the `.json` job in `jobs/` from the `.md` file!) ran a buggy regex / `replace()` (remember in JavaScript `str.replace(pattern, replacement)`: if `replacement` contains `$`, e.g., `$$` → `$` or `$&` → matched text, or a custom math sanitizer in GAS!), **OR**
   - When the `.md` file was originally created/edited before the user copied it!
   **HOLD ON!** Let's tell the user **plainly**:
   - We inspected every single line of `render.py` (lines 1–177), and `render.py` itself is **not** changing `$H$` to `$HS` or `$S$` to `$$S$$` — so that specific `$HS`/`$$S$$`/`$$$` mangling is coming from **Google Apps Script** (when it converts `.md` → `jobs/*.json`) or from an older copy of the `.md` in Drive!
   - **Ask them to check/paste the Apps Script code** that reads `.md` and creates the `.json` job (or inspect one `.json` in `jobs/`), **AND** we can EVEN add a small defensive repair rule in `render.py`? Wait: be very careful with guessing `$$$` -> `$S$`! Don't silently corrupt valid `$$`! Better to find and fix the exact line in Google Apps Script if it's doing a `.replace()` on `mdText`, AND check why `**$H$:**` became `$HS:`!
   - **WAIT A SECOND!!** Look again at why `**$S$**` → `$$$` and `**$H$**` → `$HS`!!
     WHAT IF IN `render.py` IT WASN'T APPS SCRIPT — WAIT... COULD **WEASYPRINT** OR **`**$H$**`** HAVE SOMETHING ELSE?! No! Let's verify: In `render.py`:
     - `md = MarkdownIt('commonmark', ...)` parses `1. **Find $H$:**` into `<ol><li><strong>Find $H$:</strong>...`
     - `BeautifulSoup(..., 'html.parser')` parses `<strong>Find $H$:</strong>`.
     - `WeasyPrint` renders `<strong>Find $H$:</strong>` using `"Liberation Sans"`.
     WAIT... COULD `"Liberation Sans"` Bold HAVE AN ISSUE? NO, in `"Liberation Sans"` Bold, `$` is `$` (look at `**$3S$**`, `**$6$**`, `**$6S$**` on Page 1 & 2 — those ALL rendered `$` cleanly in bold!). AND in **`In this question, $S$ appeared` -> `$$S$$`** on Page 3, it wasn't even bold! So it **100% happened BEFORE `render.py`**, inside **Google Apps Script** when converting `.md` → `.json` (OR the `.json` job in `jobs/` came from an earlier version of the `.md` file)! WAIT — THINK ABOUT WHAT IN GOOGLE APPS SCRIPT TURNS:
     - `**$H$**` -> `$HS`
     - `**$L$**` -> `$LS`
     - `**$M$**` -> `$MS`
     - `**$S$**` -> `$$$` (or `$$S$$`)
     - `$S$` -> `$$S$$`
     Wait: could Google Apps Script be using `String.replace(..., ...)` where `$` is a special pattern in JS?! Think: if someone wrote in Apps Script `mdText.replace(/\*\*(.*?)\*\*/g, ...)` or tried to convert something with `replace()`, `$'` inserts everything after the match, `` $` `` inserts before, `$&` inserts match, `$$` inserts `$`! No wait: `$H$` has `$H` (not special in JS `replace`, only `$1`–`$99`, `$&`, `` $` ``, `$'`, `$$`). What if in `Apps Script` (or a Chrome extension that saved the chat!), someone used an expression or regex? Checking Apps Script's `.md` → `.json` function will reveal it immediately!

3. **Look at Bug 3 (the stray `:*` and `.*` bullets AND `Lowest $= L$`):**
   Look at the `.md` file the user pasted:
   - `Now, track only the coefficient of **$S$**:* $H = ...`
   - `Look at the given statements:* **I.**`
   - `Let the three numbers in ascending order be:* Lowest $= L$`
   - `In algebra, a **coefficient** is simply the number multiplied by a variable.* In $3S$, the coefficient of $S$ is **$3$**.* In $6S$, the coefficient of $S$ is **$6$**.* In $-3S$, the coefficient of $S$ is **$-3$**.`
   - `Look at the options given in your question:* Statement I has: **$3S$**`
   - `Let the three numbers be:* $L$ = Lowest`
   - `Look at the options first (take 2 seconds).* If Option I has $3S$`
   - `did not contain $S$ at all.* This means`
   - `distinguish between them.* *What to do:*`
   - `trap shortcut users.* *Rule of thumb:*`
   - `If equations involve terms like $\frac{S}{K}$, $S \times K$, or $S^2$:* Tracking`
   - `scale with each other.* Use the shortcut`
   - `$3S - 3S = 0$).* In such dense systems`

   **LOOK AT THAT PATTERN!!** Every single `:* ` and `.* ` and `).* ` followed by a space (and outside `$...$` math / code blocks!) is a **missing newline before a `* ` bullet item**! Look at WHY that happens in Google AI Studio: When AI Studio streams or exports bulleted lists after bold/inline math, it sometimes joins the previous line's ending (`:`, `.`, `)`) directly to the first bullet `* ` without `\n\n* `! Look what happens when we normalize that in `render.py` **before** parsing Markdown (outside code blocks & math!):
   - `statements:* **I.**` → `statements:\n\n* **I.**`
   - `variable.* In $3S$, the coefficient of $S$ is **$3$**.* In $6S$...` →
     ```markdown
     variable.

     * In $3S$, the coefficient of $S$ is **$3$**.
     * In $6S$, the coefficient of $S$ is **$6$**.
     * In $-3S$, the coefficient of $S$ is **$-3$**.
     ```
   - `distinguish between them.* *What to do:*` →
     ```markdown
     distinguish between them.

     * *What to do:*
     ```
   Wait: check for false positives! Could `.* ` or `:* ` ever appear legitimately in normal Markdown prose?
   - What about `*italic*`? Wait: in `*italic*` ending at a sentence: `*This is italic.* Next sentence.` -> THAT HAS `.* `!!
   **WHOA!! GOOD CATCH!!** Think about `*italic.* Next sentence` vs `variable.* In $3S$`!! Look at the `.md` file the user pasted:
   - `is **$6$**.*` -> `**$6$**` is bold, then `.`, then `* ` (an UNPAIRED `*` followed by space!)
   - `Look at the options first (take 2 seconds).* If Option I...` -> NO opening `*` on that line!
   - `did not contain $S$ at all.* This means...` -> NO opening `*` on that line!
   - `distinguish between them.* *What to do:*` -> NO opening `*` before `them.*`!
   - Look! In Markdown, `*italic.* Next` ONLY happens if there is an opening `*` earlier in that paragraph (so the `*` after `.` is a **closing** emphasis delimiter, NOT an opening bullet)! Whereas in EVERY broken bullet case:
     1. It's `:* ` (colon + `* ` — almost NEVER closing italics!)
     2. Or it's `.* ` / `).* ` where the line/paragraph **has an odd/unmatched number of `*`** or is followed by another `.* ` or `\n* `!
     Even better: check if the **next lines** start with `* ` (like `Look at the given statements:* **I.** ...\n* **II.** ...`) OR if there is no matching opening `*` earlier on the line (ignoring `**`)! Let's trace that rule on EVERY single example in the user's `.md` file!
     - `Now, track only the coefficient of **$S$**:* $H = ...` → `:* ` (after stripping `**`, zero unpaired `*` before `:* `) → turns into `:\n\n* $H = ...`!
     - `In algebra, a **coefficient** is simply the number multiplied by a variable.* In $3S$...` → zero unpaired `*` before `.* `, and multiple `.* ` on the line → turns each into `\n* `!
     - `*(contains no $S$)*` → HAS opening `*` before `(contains`! Because there's an opening `*`, the closing `*` is NOT followed by `.` anyway (`)*`), and even if it were `*(note).* Next`, tracking open `*` prevents splitting real italics!
     - `*What to do:*` → starts with `*` (opening italic), ends with `:* ` — wait: `*What to do:* You would` IS real italics (`<em>What to do:</em>`)!!
       **WHAT A CATCH!!** Look at Page 4 of the user's `.md` file:
       `* If Statement I was ... distinguish between them.* *What to do:* You would then need...`
       `*What to do:*` starts with `*` and ends with `:*`! If we blindly split ALL `:* `, we would break `*What to do:* You would...`! **HOW TO AVOID BREAKING `*What to do:*`:** Count **single `*`** (ignoring `**`) on the current line from left to right!
       - At `them.*`: single-`*` count before `them.` is `1` (the line started with `* If Statement...`—wait: a leading `* ` bullet at index 0 is a bullet marker, NOT italics!). Once you ignore a leading bullet `* `, single-`*` count before `them.*` is **0 (even)**! So `.* ` IS a missing-newline bullet!
       - Then at `*What to do:*`: the `*` before `What` opens italics (`count = 1`, odd!), so at `:* ` after `do`, `count` is **odd (`1`)** → that `*` **closes italics**, so do NOT split it!
       - Look at `Rule of thumb:` right below it:
         `to trap shortcut users.* *Rule of thumb:* In Banking Mains`
         - Leading `* ` is bullet marker (doesn't toggle italic).
         - At `users.*`: `in_italic` is `False` → split into `\n* ` (`\n* *Rule of thumb:*`)!
         - At `*Rule`: `in_italic` becomes `True`!
         - At `thumb:*`: `in_italic` is `True` → do NOT split! Closes italic (`in_italic = False`)!
       - Look at `or $S^2$:* Tracking coefficients`:
         - `in_italic` is `False` → splits `:* ` into `:\n\n* Tracking...`!
       - Look at `scale with each other.* Use the shortcut`:
         - `in_italic` is `False` → splits `.* ` into `.\n\n* Use the shortcut...`!
       THAT STATE-MACHINE CHECK (`in_italic` ignoring leading `^\s*\* ` and `**`) HANDLES 100% OF BOTH CASES WITH ZERO FALSE POSITIVES!!

4. **AND look at one more detail in the `.md` file + Page 1:**
   Look at Page 1 of the `.md` file:
   `Let the three numbers in ascending order be:* Lowest $= L$`
   Notice `Lowest $= L$` — there the LLM itself wrote `$= L$` instead of `= $L$`, which renders cleanly once MathJax renders `$= L$` as `= L`! And look at `$$$` / `$HS` / `$LS` / `$MS` / `$$S$$`: Wait — **WHY** did `**$S$**` become `$$$` / `$$S$$` and `**$H$**` become `$HS`? Let's make sure we tell the user clearly:
   - We checked **every single line of `render.py`**, and `render.py` has **nothing** that converts `$H$` to `$HS` or `$S$` to `$$S$$`.
   - That means that specific corruption (`$HS`, `$LS`, `$MS`, `$$$`, `$$S$$`) happened **inside Google Apps Script** (when creating the `.json` file in `jobs/`) OR the `.json` job came from a modified version of the `.md`!
   - If they share the part of their **Google Apps Script** that reads `.md` files and pushes `.json` to GitHub (or inspect one `.json` in `jobs/`), we can pinpoint the exact line doing that too!

5. **Wait — check Page 5 of the PDF (`assets`)!**
   Look at Page 5 in the screenshot: The user attached a tall mobile phone screenshot (`720x1600` aspect ratio), and in `render.py` CSS:
   `.diagram svg, img { max-width: 100%; max-height: 520px; height: auto; }`
   Actually Page 5 looks pretty clean, though wait: `max-height: 520px` on a `9:20` portrait phone screenshot shrinks it to a small centered image at the top of Page 5 (around `234px` wide), which is totally fine (`height: auto` preserves aspect ratio). Just make sure our MathJax `<svg>` CSS does **NOT** match `img` or `.diagram svg`! Using `.math-inline svg` and `.math-display svg` keeps them completely separate.

6. **Let's check `build-pdfs.yml` + `render.py` for MathJax v3 SVG rendering!**
   Let's verify EVERY detail of adding `mathjax-full` to `build-pdfs.yml` and `render.py`:
   - In **`.github/workflows/build-pdfs.yml`**:
     GitHub Actions `ubuntu-latest` (Ubuntu 26.04) has **Node.js** preinstalled! (Let's double-check Ubuntu 26.04 GitHub runner README if needed, or even better: `actions/setup-node@v4` or `node` preinstalled—wait: let's check our earlier search result `Ubuntu2604-Readme.md` or search if `node` and `npm` are preinstalled on `ubuntu-26.04`!). Let's do a quick search on `Ubuntu2604-Readme.md` for `Node.js` / `npm` so we don't assume anything unverified!**search** site:github.com/actions/runner-images "Ubuntu2604-Readme.md" "Node" Let's check! Look at `1.2.1` (`Ubuntu2604-Readme.md`):
- `Node 20.20.2` / `Node 24.14.1` and `npm 11.11.0` are preinstalled directly on `ubuntu-26.04`!
So in `.github/workflows/build-pdfs.yml`, a single line:
```yaml
      - name: Install MathJax (for LaTeX equations)
        run: npm install --no-save --prefix /tmp/mj mathjax-full
```
Wait — why `--prefix /tmp/mj`?!
- Installing into `/tmp/mj` keeps the git working directory **100% clean** (`git status` doesn't get polluted with `node_modules/` or `package.json`, and `actions/checkout` + `delete_github_job` stay spotless!).
- And then in `render.py`, we either call `/tmp/mj/node_modules/mathjax-full` (and if running outside that workflow where `/tmp/mj` doesn't exist, check `./node_modules` or fallback gracefully without crashing)!

Let's design the **exact** Node helper + Python math extractor carefully so there are **zero** edge-case bugs!

### Designing the Math + Markdown pipeline in `render.py`:

Let's trace EVERY step carefully on real Gemini / AI Studio Markdown:

1. **Step A: Fix missing-newline bullets (`:* `, `.* `, `).* `) BEFORE math extraction** — wait: should we fix missing-newline bullets BEFORE or AFTER protecting code & math?
   **AFTER protecting fenced code blocks (` ```...``` `), inline code (`` `...` ``), and math (`$$...$$`, `$...$`)!** Why?
   - Inside code blocks, `:* ` or `.* ` is code (`foo.* bar`), NOT a bullet!
   - Inside math, `$S^2$:* Tracking` has `:* ` **right after** the closing `$` of `$S^2$` (now placeholder `@@MATH_5@@`), so `@@MATH_5@@:* Tracking` STILL triggers cleanly right after `@@MATH_5@@`!
   - Let's verify that!
     Look at the `.md` file:
     - `Now, track only the coefficient of **$S$**:* $H = ...` → after math placeholder: `**@@MATH_0@@**:* @@MATH_1@@` → `:* ` is right outside `**...**`!
     - `If equations involve terms like $\frac{S}{K}$, $S \times K$, or $S^2$:* Tracking...` → after math placeholder: `or @@MATH_2@@:* Tracking...` → `:* ` is right outside `@@MATH_2@@`!
     - `$3S - 3S = 0$).* In such dense systems...` → after math placeholder: `@@MATH_3@@).* In such dense systems` → `).* ` is right outside `@@MATH_3@@`!
     - `is **$6$**.* In $6S$` → after math placeholder: `is **@@MATH_4@@**.* In @@MATH_5@@` → `.* ` is right outside `**...**`!
     - **Wait:** what if a line in `.md` is `statements:* **I.**`?
       After `:* ` is replaced with `\n\n* ` (the first item in a list needs `\n\n* ` if previous line was a paragraph, and subsequent `.* ` items on the same line need `\n* `!), let's check CommonMark! In **CommonMark** (`MarkdownIt('commonmark')`): Look! In CommonMark, a list CAN interrupt a paragraph with a single `\n* ` (except empty list items or ordered lists starting != 1), **AND** using `\n\n* ` for the first break and `\n* ` for subsequent ones — OR just `\n* ` after a paragraph (wait: if `statements:\n* **I.**` is in CommonMark, let's check! Yes, in CommonMark `text\n* item` starts a `<ul>`, though if the previous line ended with `1.` or something, `\n\n* ` is ALWAYS safe after `:* ` or `.* ` — wait: if you put `\n\n* ` between `item1` and `item2`, CommonMark creates a *loose* list with `<p>` inside `<li>` and slightly larger spacing, whereas `\n* ` creates a *tight* list! So `\n\n* ` if the current line wasn't already a list item, or simply `\n* ` works in CommonMark when the item has non-empty content!). Wait: what if `Now, track only the coefficient of **$S$**:* $H = ...` is followed on the next line by `* $L = ...`? Look at the `.md` file:
       ```markdown
       Now, track only the coefficient of **$S$**:* $H = ...
       * $L = ...
       * $M = ...
       ```
       If `:* ` becomes `\n\n* `, then:
       ```markdown
       Now, track only the coefficient of **$S$**:

       * $H = ...
       * $L = ...
       * $M = ...
       ```
       ALL THREE bullets (`$H`, `$L`, `$M`) join into ONE tight `<ul>` list!! AND what about:
       ```markdown
       In algebra, a **coefficient** is simply the number multiplied by a variable.* In $3S$, the coefficient of $S$ is **$3$**.* In $6S$, the coefficient of $S$ is **$6$**.* In $-3S$, the coefficient of $S$ is **$-3$**.
       ```
       If the FIRST replacement on a non-list line uses `\n\n* ` and subsequent ones on the same paragraph use `\n* `, then ALL THREE bullets (`In $3S$...`, `In $6S$...`, `In $-3S$...`) form ONE clean tight `<ul>` list!! Let's also check: what if a bullet line ALREADY starts with `* ` (like `* If Statement I was ... distinguish between them.* *What to do:*`)? Since the line ALREADY starts with `* `, splitting `.* ` with `\n* ` keeps both bullets in the SAME tight `<ul>` list!

2. **Step B: How to extract `$...$` and `$$...$$` cleanly WITHOUT false positives on currency like `$50` or `$100`!**
   THIS IS SUPER IMPORTANT! In Banking/Quant exams (like SBI Clerk Mains!), currency like `$50` and `$100` can appear in word problems (`He bought 2 shirts for $50 and sold them for $75`)! Let's make sure our LaTeX regex does **NOT** treat `$50 and sold them for $75` as a math block! Check standard Pandoc / KaTeX / MathJax `$...$` rules:
   - **Code blocks & inline code first:** Protect ```` ```...``` ```` (fenced code) and `` `...` `` (inline code) first with placeholders so `$PATH` or `$variable` in code is NEVER treated as LaTeX!
   - **Display math `$$...$$` (and `\[...\]`):**
     `(?<!\\)\$\$(.+?)(?<!\\)\$\$` (`re.DOTALL`) — matches multi-line or single-line `$$...$$`. *(Wait: in the user's `.md` file, notice lines like `$$\text{Average} = S - 6$$ $$\text{Total} (L + M + H) = 3 \times (S - 6) = \mathbf{3S} - 18$$` have TWO `$$...$$` blocks on the same line! Using non-greedy `.+?` matches each separately! And if someone wrote `\[ ... \]`, we can support `(?<!\\)\\\[(.+?)(?<!\\)\\\]` too!)*
   - **Inline math `$...$` (and `\(...\)`):**
     What defines valid Pandoc/AI Studio inline math `$...$` vs currency `$50 ... $75`?
     - Cannot span across blank lines (no `\n\n` inside `$...$`, and usually single-line `[^\n]+?`).
     - Opening `$` must NOT be preceded by `\` (escaped `\$`) or `$` (`$$`), and must NOT be followed by whitespace (`$ 50` is currency, not math!).
     - Closing `$` must NOT be preceded by whitespace (`50 $`), must NOT be preceded by `\` (`\$`), and must NOT be immediately followed by a digit (`$50$5` or `$50` followed by `0`). Wait: what about `$3S$`? `3` is inside, closing `$` is followed by punctuation `,`, `.`, `:`, space, `)`, etc., NOT a digit! What about `$50 and $75`? Opening `$` is followed by `5` and closing `$` is followed by `7`? Wait: in `$50 and $75`, the second `$` is followed by `7` (a digit!) AND preceded by a space (`and `)! Because the closing `$` of `$...$` cannot be preceded by a space (`and `) and cannot be followed by a digit (`75`), `$50 and $75` will **NOT** match as math!!
     - Let's double check: what about `($3S$)` or `**$S$**` or `$3$:` or `$H - L = N - 10$`?
       - `**$S$**`: opening `$` not preceded by `\`, followed by `S` (not space); closing `$` preceded by `S` (not space), followed by `*` (not digit) → **MATCHES!**
       - `$3S$`: opening `$` followed by `3`, closing `$` preceded by `S`, followed by `,`/space → **MATCHES!**
       - `**$3$**`: opening `$` followed by `3`, closing `$` preceded by `3`, followed by `*` → **MATCHES!**
       - `$50 and $75`: at `$50 `, after `and ` there is a space before `$75` so `$75`'s `$` is preceded by space → NOT a closing `$`! Wait: what about `$50 to $75`? Same! What about `costs $50-$75`? Look: in `$50-$75`, `-` is before `$`, and `7` is after `$`! Adding `(?!\d)` after the closing `$` rejects `$50-$75` because `7` follows the closing `$`!
       - What about `$$` empty? Rejected because inner content is non-empty (`[^\s$]` or `(?!\s)...(?<!\s)`).
       - Let's check: single-character `$S$`!
         If inline math is only 1 char (`$S$`, `$L$`, `$H$`, `$3$`): Pattern: `(?<!\\)\$(?!\s)((?:\\\$|[^$\n])+?)(?<!\s)(?<!\\)\$(?!\d)` Wait: test that on `$S$`:
         - `(?<!\\)\$` matches first `$`
         - `(?!\s)` checks `S` is not whitespace
         - `((?:\\\$|[^$\n])+?)` matches `S`
         - `(?<!\s)(?<!\\)` checks `S` is not whitespace or `\`
         - `\$` matches closing `$`
         - `(?!\d)` checks char after closing `$` is not a digit!
         Wait: what if inside `(?:\\\$|[^$\n])+?` there's `\text{a}` ending in `}`? Works! What if it's `$100` (only ONE `$` on the line)? No closing `$`, doesn't match! What if there are TWO currency amounts on one line like `between $50 and $100`? First `$` has no closing `$` before a non-digit because the second `$` is preceded by a space AND followed by `1`! Wait: what if someone writes `I paid $50, and he paid $100`? Still space before second `$` AND digit after second `$` -> doesn't match! What if someone writes `I paid $50 and got $100 back`? Same! What if someone writes `I paid $50. Also $100.`? Same! What if someone writes `$3$`, `$6$`, `$-3$`? Matches! What if someone writes `\$$50$` (an escaped dollar sign followed by math)? `(?<!\\)\$` skips `\$`! (And then in unescaping `\$` outside math, we can turn `\$` into `$`!) Wait: what if `math_expr` is `3S` vs `x \text{ is } 5`? What if a single line has `Price is $50 and tax is $5` where `50` has a typo `$50and$5`? Won't match because `5` is after `$`! Wait: what if `**$S$**` vs `$50 (or $100)`? Space before `$100` and `1` after `$100` -> won't match!

3. **Step C: Wait — What happens when `**$S$**` or `**$\mathbf{3S}$**` is bolded in Markdown (`**$...$**`)?**
   - In `Solving Math Questions Under 30s.md`, notice lines like `**$S$**` or `**$+3S$**` or `**$6S$**`!
   - When we replace `$S$` with `@@MATH_0@@`, the Markdown becomes `**@@MATH_0@@**`!
   - `MarkdownIt` turns `**@@MATH_0@@**` into `<strong>@@MATH_0@@</strong>`.
   - Then `@@MATH_0@@` is replaced by `<span class="math-inline"><svg>...</svg></span>`.
   - Notice: inside `<svg>`, MathJax paths have their own stroke/fill (`currentColor`), so inside `<strong>` it inherits `#0f172a`/`#1e293b` cleanly!
   - Wait: what about **`**Find $H$:**`**?
     It becomes `**Find @@MATH_0@@:**` → `<strong>Find <span class="math-inline"><svg>...</svg></span>:</strong>`! Looks completely natural!

4. **Step D: Test EVERY LaTeX construct from `Solving Math Questions Under 30s.md` through MathJax v3 (`AllPackages`)!**
   Let's check every single one in the user's `.md` file:
   - `\text{Sum}(L + M + H) = 3(S - 6) = \mathbf{3S} - 18` → valid TeX!
   - `H - L = N - 10 \implies L = H - (N - 10)` → `\implies` is in `ams` (included in `AllPackages`)!
   - `\dots` → valid!
   - `\times` → valid!
   - `\frac{S}{K}` → valid!
   - `S^2` → valid!
   - `3S - 6K - N - 23` → valid!
   - What if some future AI Studio chat has a weird broken LaTeX expression that throws a TeX error in MathJax?
     In our tiny Node script, wrap `html.convert(...)` in `try { ... } catch (e) { ... }` per expression! If MathJax ever throws on a bizarre expression (or if `mathjax-full` isn't installed), return `null` so Python falls back cleanly to escaped HTML text instead of crashing the whole PDF build!

5. **Step E: Look closely at `CSS` and Math SVG sizing in WeasyPrint!**
   Wait: MathJax v3 SVG generates `<svg style="vertical-align: -0.566ex;" xmlns="http://www.w3.org/2000/svg" width="12.345ex" height="2.123ex" viewBox="0 -750 5456 938" ...>`! Let's verify how WeasyPrint renders `<svg width="...ex" height="...ex" style="vertical-align: -0.566ex;">`:
   - In CSS, `1ex` is roughly half of `1em` (`~0.5em`, i.e., `x-height`), matching MathJax's font-metric `ex` units!
   - In `.math-display`, wrapping the `<svg>` in `<div class="math-display">...</div>` with:
     ```css
     .math-inline {
       display: inline;
       white-space: nowrap;
     }
     .math-inline svg {
       display: inline;
       overflow: visible;
       max-width: 100%;
     }
     .math-display {
       display: block;
       text-align: center;
       margin: 8px 0 10px;
       overflow-x: visible;
       break-inside: avoid;
     }
     .math-display svg {
       display: inline-block;
       max-width: 100%;
       overflow: visible;
     }
     ```
   - Wait: in `render.py` lines 55–56:
     ```css
     .diagram svg, img { max-width: 100%; max-height: 520px; height: auto; }
     ```
     Notice `.diagram svg` only matches `<svg>` inside `.diagram`, NOT `.math-inline svg` or `.math-display svg`! AND notice `overflow: visible;` ensures accents/superscripts aren't clipped at SVG bounding boxes in WeasyPrint!
   - Wait: what if `math-display` is very wide? `max-width: 100%;` keeps it from overflowing the page width! (Though if `max-width: 100%` shrinks width without `height: auto`, wait: if an SVG has both `width="80ex"` and `height="3ex"` and gets constrained by `max-width: 100%`, `preserveAspectRatio="xMidYMid meet"` is standard in SVG so WeasyPrint scales proportionally inside the box, though setting `max-width: 100%;` on display math is safe.)
   - Wait: what about `<mjx-container>` vs inner `<svg>`?
     In our Node script, `adaptor.innerHTML(node)` returns the `<svg ...>...</svg>` directly (without needing `<mjx-container>` custom tags!). Wait: let's double-check whether `html.convert(texStr, { display: isDisplay })` returns `<mjx-container><svg>...</svg></mjx-container>` so `adaptor.innerHTML(node)` is `<svg ...>...</svg>`! YES! Look at result `1.2.2`: `const node = html.convert(tex, { display }); return adaptor.innerHTML(node);` returns `<svg ...>...</svg>` directly!

6. **Step F: Check `render.py` for how `@@MATH_0@@` interacts with `BeautifulSoup` and `<table>`!**
   Look at `render.py` lines 75–116:
   - `soup = BeautifulSoup(md.render(md_text), 'html.parser')`
   - In `<table>`, `render.py` loops over `cell.find_all(string=True)` to replace `<br>` and measure `len(seg.strip())` for column widths!
   - **Notice how nice our order is:**
     If we keep `@@MATH_0@@` as placeholders during `md.render(...)` and `BeautifulSoup` table calculation, OR substitute `<span class="math-inline">...</span>` **after** `str(soup)` (Wait: if we replace `@@MATH_0@@` *after* `str(soup)`, then `len(seg.strip())` sees `"@@MATH_0@@"` (10 chars) instead of the raw `\mathbf{...}` string — which is actually much closer to the rendered width than 50 chars of LaTeX markup! Even better, we can estimate display width or replace `@@MATH_0@@` right after `str(soup)` so `BeautifulSoup` doesn't waste time parsing thousands of SVG `<path>` tags!).
   - Wait: what if a placeholder string like `@@MATH_0@@` gets wrapped by `MarkdownIt` inside `<strong>`, `<td>`, `<li>`, `<p>`, `<h3>`?
     **WAIT A SECOND — CHECK THIS EDGE CASE!!** Does `MarkdownIt('commonmark')` treat `@@MATH_0@@` as plain text, with NO special Markdown meaning?
     - `@` has NO special meaning in CommonMark!
     - `_` DOES have special meaning in CommonMark (`_0_` could become `<em>0</em>` if there are two underscores like `@@MATH_0@@ ... @@MATH_1@@`!!)!
     **WHOA!! WHAT A CATCH!!** STOP AND TRACE WHAT WOULD HAPPEN IF PLACEHOLDERS WERE `@@MATH_0@@` AND A LINE HAD TWO FORMULAS: `Compare @@MATH_0@@ and @@MATH_1@@`!! In CommonMark, `_0@@ and @@MATH_` would turn into `<em>0@@ and @@MATH</em>`!! That would DESTROY both placeholders!! **THANK GOODNESS WE CAUGHT THAT!!** Use **ZERO underscores, asterisks, brackets, or punctuation** in placeholder tokens — use pure alphanumeric + Unicode private-use sentinel or `XMATHTOKEN0X` / `\uE000MATH0\uE001` (Private Use Area Unicode characters `\uE000` and `\uE001` + uppercase letters + digits: `\uE000M0\uE001`, `\uE000C0\uE001`)! Let's check:
     - Can `\uE000M0\uE001` EVER collide with anything in CommonMark (`*`, `_`, `[`, `]`, `<`, `>`, `\`, `` ` ``, `$`)? **NEVER!**
     - Can `\uE000M0\uE001` EVER be escaped by `html.escape` or `MarkdownIt`? **NEVER!**
     - Can `\uE000M0\uE001` EVER appear naturally in a user's AI Studio chat? **Practically ZERO chance** (and even if it did, only our own generated index keys `0..N-1` are substituted)!
     - Can `BeautifulSoup(..., 'html.parser')` preserve `\uE000M0\uE001` cleanly? **YES!**
