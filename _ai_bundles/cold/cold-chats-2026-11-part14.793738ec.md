# Cold Knowledge Bundle: chats-2026-11-part14


---
## FILE: `chats/Optimizing Two-Step LLM Routing.md` [Part 4/14]

written.append( { "url": f"{RAW_BASE}/_ai_bundles/cold/{filename}", "group": f"{group_name}{suffix}", "titles": titles, "prompts": list(dict.fromkeys(prompts))[:10], "sections": list(dict.fromkeys(sections))[:16], "summaries": list(dict.fromkeys(summaries)), "keywords": list(dict.fromkeys(keywords)), } ) return written

def main: scan_dirs = [d for d in (Path("core"), Path("chats"), Path("kb")) if d.exists] if not scan_dirs: raise SystemExit("Missing 'chats/' or 'core/' directory.")

    OUT_DIR.mkdir(parents=True, exist_ok=True) shutil.rmtree(COLD_DIR, ignore_errors=True) COLD_DIR.mkdir(parents=True, exist_ok=True)

    git_recent = get_git_recent_files(RECENT_DAYS) hot_core_blocks = [] recent_candidates = [] # (sort_date, block, byte_size) cold_groups: dict[str, list[dict]] = {}

    for root_dir in scan_dirs: for path in sorted(root_dir.rglob("*")): if not path.is_file or path.suffix.lower not in ALLOWED_EXTS: continue

            raw_text = path.read_text(encoding="utf-8", errors="ignore") meta, body = parse_frontmatter(raw_text) body = clean_chat_wrapper(body) top_info = extract_doc_info(path, body) parts = path.parts

            is_hot = ( root_dir.name == "core" or (root_dir.name == "kb" and len(parts) > 2 and parts == "core") or meta.get("tier") == "hot" )

            if is_hot: hot_core_blocks.append(format_file_block(path, body)) continue

            # Tier 1 Recent check (only compact files <= MAX_RECENT_FILE_BYTES)
            body_bytes = len(body.encode("utf-8")) if top_info["updated_date"] is not None: is_recent = (TODAY - top_info["updated_date"]).days <= RECENT_DAYS sort_d = top_info["updated_date"] else: is_recent = path in git_recent sort_d = TODAY if is_recent else date.min

            if is_recent and body_bytes <= MAX_RECENT_FILE_BYTES: blk = format_file_block(path, body) recent_candidates.append((sort_d, blk, len(blk.encode("utf-8"))))

            # Determine Tier 2 Cold group
            if root_dir.name == "chats": if len(parts) > 2: group_key = sanitize_slug(parts) elif top_info["updated_date"] is not None: group_key = f"chats-{top_info['updated_date'].strftime('%Y-%m')}" else: group_key = "chats-general" else: raw_sub = parts if len(parts) > 2 else "general" group_key = sanitize_slug(raw_sub) if group_key == "chats" and top_info["updated_date"] is not None: group_key = f"chats-{top_info['updated_date'].strftime('%Y-%m')}"

            # Split giant files into <65 KB parts and index each part's own headings
            body_parts = split_large_body(body, MAX_COLD_BYTES - 1500) total_parts = len(body_parts) for idx, part_body in enumerate(body_parts, start=1): part_label = f"[Part {idx}/{total_parts}]" if total_parts > 1 else "" part_info = extract_doc_info(path, part_body, fallback_title=top_info["title"]) cold_groups.setdefault(group_key, []).append( { "path": path, "body": part_body, "part_label": part_label, "title": top_info["title"], "updated_date": top_info["updated_date"], "prompts": part_info["prompts"], "sections": part_info["sections"], "summary": meta.get("summary", ""), "keywords": meta.get("keywords", ""), } )

    # Write Tier 1 Core
    core_text = ( "# Tier 1: Core Knowledge\n" + "".join(hot_core_blocks) if hot_core_blocks else "# Tier 1: Core Knowledge\nNo core files configured yet." ) (OUT_DIR / "hot-core.md").write_text(core_text, encoding="utf-8")

    # Write Tier 1 Recent (newest first, capped at MAX_RECENT_TOTAL_BYTES)
    recent_candidates.sort(key=lambda x: x, reverse=True) selected_recent, recent_bytes = [], 0 for _, blk, b_size in recent_candidates: if selected_recent and (recent_bytes + b_size > MAX_RECENT_TOTAL_BYTES): break selected_recent.append(blk) recent_bytes += b_size

    recent_text = ( f"# Tier 1: Recent Compact Chats (Last {RECENT_DAYS} Days)\n" + "".join(selected_recent) if selected_recent else f"# Tier 1: Recent Changes\nNo compact chats updated in the last {RECENT_DAYS} days (large compendiums are indexed in llms.txt)." ) (OUT_DIR / "hot-recent.md").write_text(recent_text, encoding="utf-8")

    # Write Tier 2 Cold Bundles & llms.txt
    index_entries = [] for group_name, items in sorted(cold_groups.items): index_entries.extend(write_cold_chunks(group_name, items))

    lines = [ "# Knowledge Base Index (Tier 2 Cold Bundles)", "# Note: Core docs and recent compact chats are pre-loaded in Tier 1. Large compendiums are split into full-read Cold parts below.", "", ] for entry in index_entries: lines.append(f"- URL: {entry['url']}") lines.append(f" Topic Group: {entry['group']}") lines.append(f" Files/Parts: {' | '.join(entry['titles'])}") if entry["prompts"]: lines.append(f" User Questions: {' | '.join(entry['prompts'])}") if entry["sections"]: lines.append(f" Topics/Chapters: {' | '.join(entry['sections'])}") if entry["summaries"]: lines.append(f" Summary: {' | '.join(entry['summaries'])}") if entry["keywords"]: lines.append(f" Keywords: {' | '.join(entry['keywords'])}") lines.append("")

    (OUT_DIR / "llms.txt").write_text("\n".join(lines), encoding="utf-8") print(f"Built {len(index_entries)} cold bundle(s) and updated Tier 1 + llms.txt.")

if __name__ == "__main__": main ```

3. Tap **Commit changes...**.

---

### Quick Test After Commit
1. Wait ~15 seconds (check **More ▾ → Actions** until green ✅).
2. In Google AI Studio, turn **Grounding with Google Search → OFF** (leave only **URL context → ON**).
3. Start a **fresh chat**, paste your **3 pinned URLs + a question about Chapter 4 of `document.md`** (e.g., *"Which exact Cold Bundle has Chapter 4 Government Schemes, and what topics/years are inside it?"*), and watch it route cleanly to the exact `<65 KB` part!

---

## User

# Untitled prompt

---

## You

Read every URL above via URL context and answer my previous question with exact FILE citations. Comprehensive analysis of the examiner's question setting pattern for scheme questions

---

## AI Studio

Tier 1 contains no relevant compendium files, so I am requesting Part 1 (the only bundle in `llms.txt` listing `Included Topic Chapters`) alongside evenly spaced Parts 4, 8, and 12 to map the archive and locate all scheme questions.

```text
https://raw.githubusercontent.com/inikashx-hub/ai-kb/main/_ai_bundles/cold/cold-chats-general-part1.b4ef2929.md
https://raw.githubusercontent.com/inikashx-hub/ai-kb/main/_ai_bundles/cold/cold-chats-general-part4.c8517c24.md
https://raw.githubusercontent.com/inikashx-hub/ai-kb/main/_ai_bundles/cold/cold-chats-general-part8.1bd816b5.md
https://raw.githubusercontent.com/inikashx-hub/ai-kb/main/_ai_bundles/cold/cold-chats-general-part12.c260178d.md
Read every URL above via URL context and answer my previous question with exact FILE citations.
```

---

## You

Read every URL above via URL context and answer my previous question with exact FILE citations.

---

## AI Studio

Part 1 identifies Chapter 4 (*Government Schemes & Initiatives*, 342 questions) and Chapter 3 (*Indian Economy & Union Budget*, 156 questions), which fall between Part 4 (Chapter 2) and Part 8 (Chapter 7), so please load Parts 5, 6, and 7 to read those chapters in full.

```text
https://raw.githubusercontent.com/inikashx-hub/ai-kb/main/_ai_bundles/cold/cold-chats-general-part5.5b52c641.md
https://raw.githubusercontent.com/inikashx-hub/ai-kb/main/_ai_bundles/cold/cold-chats-general-part6.2c69a78c.md
https://raw.githubusercontent.com/inikashx-hub/ai-kb/main/_ai_bundles/cold/cold-chats-general-part7.a6658fe9.md
Read every URL above via URL context and answer my previous question with exact FILE citations.
```

---

## You

Read every URL above via URL context and answer my previous question with exact FILE citations.

---

## AI Studio

### Evidence Scope & Archive Structure

This analysis is grounded in `FILE: chats/document.md [Part 5/13]`, `FILE: chats/document.md [Part 6/13]`, and `FILE: chats/document.md [Part 7/13]`:
- **`FILE: chats/document.md [Part 5/13]`** contains the tail of Chapter 2 (*Banking & Financial Awareness*, Q593–Q642), the entire Chapter 3 (*Indian Economy & Union Budget*, 156 Qs: Q1–Q156), and the start of Chapter 4 (*Government Schemes & Initiatives*, 342 Qs: Q1–Q19 retrieved before browse snippet truncation).
- **`FILE: chats/document.md [Part 6/13]`** contains Chapter 4 (*Government Schemes & Initiatives*) Q72–Q286 retrieved before browse snippet truncation.
- **`FILE: chats/document.md [Part 7/13]`** begins in Chapter 5 (*Appointments & Resignations*) and continues into Chapter 6 (*Awards & Honours*), confirming that Chapter 4 ends inside Part 6. *(Note: Chapter 4 Q20–Q71 in Part 5 and Q287–Q342 in Part 6 fall beyond the URL-context browse snippet length limit and are excluded from sample counts below.)*

---

### 1. Volume, Year-Wise Consistency & Cross-Chapter Distribution

- **Sustained High Weightage:** Chapter 4 (*Government Schemes & Initiatives*) comprises **342 questions** across 2019–2026: **2019 (70)**, **2020 (13)**, **2021 (53)**, **2022 (44)**, **2023 (50)**, **2024 (48)**, **2025 (48)**, and **2026 (16, partial year)**. Excluding the pandemic-disrupted 2020 cycle, Mains papers consistently draw **44–53 dedicated scheme questions per year**.
- **Schemes Leak Across Three Chapters:** Examiners do not restrict scheme testing to Chapter 4:
  - **Budget-linked Funds & Production Schemes (Chapter 3):** Examples include **PLI** domestic electronics output jumping from Rs 1.90 lakh cr to Rs 9.52 lakh cr (Q22), the **Urban Challenge Fund** of Rs 1 lakh cr (Q23), **RoDTEP** deadline extension (Q21), Kharif P&K fertiliser subsidy of Rs 37,216 cr (Q25), **UIDF** statement testing (Q39), Budget 2023–24 **Agricultural Accelerator Fund / EMRS / DigiLocker** (Q46–Q48), **Sovereign Green Bonds** of Rs 16,000 cr (Q71), **10,000 FPOs** in Budget 2020 (Q101), and **Carbon Credit Trading Scheme (CCTS)** administration by BEE (Q2).
  - **Bank-Routed / Small Savings Schemes (Chapter 2):** Examples include **Sovereign Gold Bonds (SGB)** eligible investors (Q637), quarterly interest-rate review of **Small Savings Schemes** (Q641), and commercial bank deposit schemes like Axis Bank's *Express Fixed Scheme* (Q593) and ICICI's *FD Health* (Q599).

---

### 2. The Nine Recurring Question-Setting Hooks

Across the **234 directly observed Chapter 4 questions** (Q1–Q19 in `[Part 5/13]` and Q72–Q286 in `[Part 6/13]`) plus scheme items in Chapters 2–3, examiners rely on nine repeatable "angle triggers":

#### (1) Hyper-Specific Numerical Parameters & Sub-Component Figures (Dominant Hook)
Examiners test exact numbers—and increasingly ask for **sub-shares, revised caps, and multi-tier brackets** rather than just headline outlays:
- **Outlays & Corpus:** PMAY-G total outlay Rs 3,06,137 cr specifically asking for the **state share** (`Rs 1 Lakh crore`, Ch 4 Q78); 7 farmer schemes Rs 14,235.30 cr asking for **1st and 2nd highest allocations** (*Crop science for food and nutritional security* & *Digital Agriculture Mission*, Ch 4 Q77); Fund of Funds for Startups (`Rs 10,000 cr`, Ch 4 Q87); PLI Semiconductor (`Rs 76,000 cr`, Ch 4 Q182) and enhanced Solar PLI (`Rs 24,000 cr`, Ch 4 Q172); PMGKAY total spend across phases (`Rs 3.91 lakh cr`, Ch 4 Q148); Atmanirbhar Bharat Rozgar Yojana (`Rs 22,810 cr`, Ch 4 Q213); AIF corpus (`Rs 1 lakh cr`, Ch 4 Q115, Q247, Q259); RuPay/BHIM-UPI incentive (`Rs 1,300 cr`, Ch 4 Q178); BharatNet (`Rs 6,000 cr`, Ch 4 Q269).
- **Loan Limits, Guarantees, Subsidies & Withdrawal Caps:** MSME **TREAD** grant (`30%`, Ch 4 Q88); **MSSC** partial withdrawal (`40%`, Ch 4 Q110); **VGF** GoI share (`40%`, Ch 4 Q122); **CGSS** guarantee (`75%` for loans above Rs 3 cr up to Rs 5 cr, Ch 4 Q144); **PMEGP** manufacturing cap (`Rs 50 lakh`, Ch 4 Q145); **ECLGS** aviation ceiling raised from Rs 400 cr to `Rs 1,500 cr` (Ch 4 Q146); **CBFTE** max reimbursement (`Rs 10,000`, Ch 4 Q149); **SIDBI ARISE** (`Rs 3 cr`, Ch 4 Q200) & **SFURTI** (`Rs 8 cr`, Ch 4 Q205); **DAY-NULM** SHG max loan (`Rs 20 lakh`, Ch 4 Q216); **PMJDY** overdraft (`Rs 10,000`, Ch 4 Q221, Q243); **MUDRA** *Kishore* (`Rs 5 lakh`, Ch 4 Q262) & *Tarun* (`>5 to 10 lakh`, Ch 4 Q238); **PSB Loans in 59 minutes** (`Rs 1 lakh to Rs 5 cr`, Ch 4 Q240); **CLCSS** subsidy (`up to Rs 1 cr` across `51 sub-sectors`, Ch 4 Q263–Q264); ethanol interest subvention (`6% p.a.`, Ch 4 Q255); **MPLAD** (`Rs 5 cr/yr`, Ch 4 Q108); **IREDA** Navratna cap without GoI nod (`Rs 1,000 cr`, Ch 4 Q85).
- **Insurance & Pension Mechanics:** **PMSBY** partial disability cover (`Rs 1 lakh`, Ch 4 Q118); **PMJJBY** premium hike (`Rs 330 to Rs 436`, Ch 4 Q191); **PM-SYM** monthly contribution for <40 yrs (`Rs 200`, Ch 4 Q142) and income cap (`< Rs 15,000`, Ch 4 Q215); **PMFBY** Kharif premium (`2%`, Ch 4 Q222); **APY** plan count (`5 plans`, Ch 4 Q248); **PM-KISAN** payout cadence (`3 installments in 4 quarters`, Ch 4 Q261).
- **Scheme Scope Counts & Exception Rules:** **PLI** (`14 sectors`, Ch 4 Q155); **PM-MITRA** (`7` states/parks, Ch 4 Q139, Q203); **PM-JANMAN** (`73` ST communities across `18` states, Ch 4 Q105); **PM Gati Shakti** (`7 Engines`, Ch 4 Q81); **DAY-NRLM** minimum SHG size in **remote/tribal/difficult areas** (`5 members`, Ch 4 Q6—testing an exception rule rather than the standard 10–20 norm).

#### (2) Single-Letter Acronym Expansion ("What does X stand for?")
Examiners avoid asking for full expansions and instead isolate **one middle or final letter**, especially on newly coined schemes (persisting straight through 2026):
- **2026:** `SHATAYU` -> `'H'` = *Holistic* (Ch 4 Q2, IBPS PO Mains 2026); `BHAVYA` -> `'V'` = *Vikas* (Ch 4 Q15, SBI PO Mains 2026).
- **2024:** `Project PRAYAS` -> `'R'` = *Regular* (Ch 4 Q94, IBPS RRB Clerk Mains 2024).
- **2023:** `SHRESHTA` -> `'T'` = *Targeted* (Ch 4 Q147, SBI Clerk Mains 2023); `ACABC` -> `'C'` = *Clinic* (Ch 4 Q156, SBI PO Mains 2023).
- **2022–2021:** `MMF` under textile PLI -> **second `'M'`** = *Made* (Ch 4 Q202, SBI PO Mains 2022); `ASHA` -> `'A'` = *Accredited* (Ch 4 Q225); `RAFTAAR` -> **last `'R'`** = *Rejuvenation* (Ch 4 Q231); `TOPS` -> `'P'` = *Podium* (Ch 4 Q242). *(Ch 3 also tests `NCAER` `'A'` = Applied, Q24; `HAM` `'A'` = Annuity, Q87; `OPC` `'P'` = Person, Q88.)*

#### (3) Four-Part Timeline Testing (Launch Year, Duration, Extensions, Target Years)
Every exam year tests four distinct date angles:
1. **Static Launch Years (revived sharply in 2026):** `AIF` (`2020`, Ch 4 Q7, RRB Clerk Mains 2025–26); `PMKVY` (`2015`, Ch 4 Q13, SBI PO Mains 2026); `Khelo India` (`2017`, Ch 4 Q195); `NITI Aayog` (`Jan 1, 2015`, Ch 4 Q282).
2. **Scheme Tenure / Period:** `One Scientist One Product` (`5 years`, Ch 4 Q95); `National Quantum Mission` (`8 years`, Ch 4 Q106); `PRITHVI` (`2021–2026`, Ch 4 Q111); `AIF` (`2020–2025` / `FY 2020–2029`, Ch 4 Q115, Q258); `PLI` (`5 years`, Ch 4 Q249).
3. **Cabinet Extension Deadlines:** `PM-SGMBY` till `March 2027` (Ch 4 Q11); `RoDTEP` till `Sep 30, 2025` / `March 31, 2026` (Ch 4 Q75; Ch 3 Q21); `Project Unnati` till `March 2025` (Ch 4 Q96); `PMEGP` till `FY 2025–26` (Ch 4 Q145); `PM SVANidhi` till `Dec 2024` (Ch 4 Q167); `FAME India II` till `March 2024` (Ch 4 Q217); `PMGKAY` extensions (Ch 4 Q173, Q218).
4. **Effective Dates & Policy Target Years:** `SCSS` Rs 30L effective date (`1st April 2023`, Ch 4 Q159); `Bima Vahaks` gram panchayat deadline (`31 Dec 2024`, Ch 4 Q140); `Green Hydrogen` (`2029–30` / `5 MMT by 2030`, Ch 4 Q72, Q137); `Indian Railways` net-zero (`2030`, Ch 4 Q120); `National Logistics Policy` top-25 LPI (`2030`, Ch 4 Q150, Q175); `15% ethanol` (`2023–24`, Ch 4 Q157); `175 GW` renewables (`2022`, Ch 4 Q260, Q281).

#### (4) Non-Obvious Nodal Ministries, Implementing Agencies & Exclusions
Examiners deliberately pick schemes whose ministry or executing agency differs from surface intuition:
- **Nodal Ministry Traps:** `'Samudra Manthan'` -> `Ministry of Petroleum and Natural Gas` (Ch 4 Q3); `SMILE` & `SHATAYU` -> `Ministry of Social Justice and Empowerment` (Ch 4 Q2, Q8); `Viksit Bharat Sankalp Yatra` -> joint `MoIB & MoHUA` (Ch 4 Q112); `FAME India` -> `Ministry of Heavy Industries` (Ch 4 Q114); `GOBARDHAN` -> `Ministry of Jal Shakti` (Ch 4 Q128); `APY` -> `MoF (DFS)` (Ch 4 Q129); `RuPay/BHIM-UPI Incentive` -> `MeitY` (Ch 4 Q178); `Solar Charkha Mission`, `PMEGP`, `FFDC` -> `Ministry of MSME` (Ch 4 Q171, Q184, Q244); `PM-FME` working capital partner -> `Ministry of Rural Development` (Ch 4 Q219).
- **Implementing / Channelizing / Administering Bodies:** `PACT` under `e-FAST India` -> `NITI Aayog` (Ch 4 Q1); `ICM/CCTS` -> `BEE` (Ch 3 Q2); `Saubhagya` -> `REC Ltd` (Ch 4 Q168, Q226—asked twice); `e-NAM` -> `SFAC` (Ch 4 Q229); `National SC/ST Hub` -> `NSIC` (Ch 4 Q234); `ACABC` subsidy channel -> `NABARD` (Ch 4 Q156); `PM Kisan` pension fund manager -> `LIC` (Ch 4 Q277).
- **Negative / Exclusion List:** *"Which of the following Banks does not issue the Mahila Samman Savings Certificate?"* (`Bandhan, IDBI, Axis, HDFC, ICICI`, Ch 4 Q116).

#### (5) Digital Portals, Apps & Brand Names (Major 2021–2026 Trend)
Scheme delivery mechanisms—especially apps, portals, and language counts—form a dedicated sub-genre:
- **2025–2026:** `Mobile Seva` (govt SMS platform, Ch 4 Q10); `SARAS / e-SARAS` (SHG product brand, Ch 4 Q12); `DigiLocker` (Ch 4 Q16; also Ch 3 Q46 in 2023); `SHATAYU` dashboard (Ch 4 Q2); `Jeevan Pramaan` (digital life certificate, Ch 4 Q17); `NITI NCAER States Economic Forum` (Ch 3 Q24).
- **2021–2024:** `e-Jagriti` (Ch 4 Q82), `CDP-SURAKSHA` (Ch 4 Q89), `Saksham App` (Ch 4 Q101), `SAKSHAM` MoHFW (Ch 4 Q113), `ULLAS` (Ch 4 Q117), `Sanchar Saathi` (Ch 4 Q125), `Digi Yatra` (Ch 4 Q135), `Kisan eMitra` (**5 languages**, Ch 4 Q141), `PRANA` (Ch 4 Q162), `Jan Samarth` (Ch 4 Q188), `MSME Sambandh` (Ch 4 Q201), `CHAMPIONS` (Ch 4 Q235), `SWAYAM` (Ch 4 Q251), `Mera Ration` (Ch 4 Q253).

#### (6) Eligibility Boundaries, Age Brackets & Legal Qualifiers
- **Age Cut-offs:** `RBSK 2.0` (`0–18 yrs`, Ch 4 Q5); `PMJJBY` upper limit (`50 yrs`, Ch 4 Q19); `NEP` Grade 1 min (`6 yrs`, Ch 4 Q138); `DDU-GKY` (`15–35 yrs`, Ch 4 Q152, Q214, Q220—asked three times); `RSETI` (`18–45 yrs`, Ch 4 Q223); `PM Laghu Vyapari Maan Dhan` (`18–40 yrs`, Ch 4 Q276); `Saksham App` (`85+ yrs` & `40%` PwD, Ch 4 Q101).
- **Beneficiary & Qualifier Precision:** `PMMY` extends credit to *individuals and **non-corporate, non-farm** micro and small enterprises* (Ch 4 Q4); `SMILE` (*Transgender welfare*, Ch 4 Q8); `PM Vishwakarma` coir weavers (*Artisans*, Ch 4 Q91); `Donate-a-Pension` worker list (Ch 4 Q194); `Poshan Abhiyan` (`Children, Pregnant women and lactating mothers`, Ch 4 Q227); small farmer definition (`upto 2.0 hectares`, Ch 3 Q103).

#### (7) Multi-Statement / "NOT True" / Component Elimination Questions
Rather than asking one fact, higher-tier papers bundle 3–4 facts (outlay + start date + duration + ministry) into one item:
- `RuPay & BHIM-UPI Incentive Scheme` testing duration (`1 year w.e.f. April 01, 2021`), outlay (`Rs 1,300 cr`), and ministry (`MeitY`) together (*Only A & C are correct*, Ch 4 Q177–Q178).
- *"Which of the following is NOT a component of PMKSY 2016–17?"* (Ch 4 Q176); *"Green Credit Program & Ecomark Scheme — Which among the following was not True?"* (Ch 4 Q158); *"Which scheme is not related to education?"* (`PRASAD`, Ch 4 Q236).
- Dedicated statement-based questions on `UIDF` (Ch 3 Q39), `PM-KISAN` (Ch 4 Q83), `PMGSY` (Ch 4 Q98), `PMFBY` land tenancy eligibility (Ch 4 Q131), `PM CARES for Children` (Ch 4 Q151), `GeM` (Ch 4 Q154), `NRLM SHG` (Ch 4 Q189), `7 PM MITRA parks` (Ch 4 Q203), `PMAY` (Ch 4 Q204), and `PMMVY` (Ch 4 Q257).

#### (8) "First State / City" & Geographic Cluster Pinning
- **Adoption Firsts:** `Himachal Pradesh` (1st state for Aadhaar FaceAuth in PDS, Ch 4 Q9); `Andhra Pradesh` (1st state Gender Budget, Ch 3 Q98); `Gujarat` (1st domestic emissions trading scheme, Ch 3 Q148); `Puri` (1st city 24x7 drinking water, Ch 4 Q246); `Rajasthan` (1st biofuel policy, Ch 4 Q279); `Tripura` (7th Economic Census launch, Ch 4 Q278); `Uttar Pradesh` (1st agri export policy, Ch 4 Q275).
- **Location-Specific Clusters & State Schemes:** `Rajasthan` (*Indira Gandhi Urban Employment Guarantee Scheme*, Ch 4 Q187), `Koppal, Karnataka` (1st toy cluster, Ch 4 Q209), `Kalol, Gujarat` (1st nano urea plant, Ch 4 Q183), `Gwalior, MP` (1st Drone School, Ch 4 Q198), `Dholera, Gujarat` (Greenfield airport, Ch 4 Q193), `Ken-Betwa` (`MP & UP`, Ch 4 Q192), `6 Lighthouse projects` (Ch 4 Q210).

#### (9) Objective Matching & Indirect Policy Linkages (SDGs, Brand Ambassadors, Committees)
Examiners ask second-order linkages around schemes: `LiFE initiative` mapped to **SDG 12** (Ch 4 Q161); *Viksit Bharat Buildathon 2025* Brand Ambassador **Shubhanshu Shukla** (Ch 4 Q18); *NEP* draft committee **K. Kasturirangan** (Ch 4 Q274); *PM Surya Sarovar Yojana* purpose (*floating solar on water bodies*, Ch 4 Q14); *SATAT* (*Compressed Biogas*, Ch 4 Q109); *Svamitva* (*Record of Rights*, Ch 4 Q104); *AVSAR* (*SHG space at airports*, Ch 4 Q185); *NIRVIK* (*Exports*, Ch 4 Q245).

---

### 3. Chronological Evolution (2019 -> 2026) & Exam-Tier Split

#### Evolution Across Cycles
1. **2019–2020 (Direct Headline Recall):** Short, single-fact questions on purpose, basic age caps, and "first state" milestones (e.g., `AMRUT` Q272, `Mission Karmayogi` Q267, `PM Laghu Vyapari Maan Dhan` Q276, `Rajasthan` Q279).
2. **2021–2023 (Statement Bundles + Amendments + Evergreen Mechanics):** Surge in multi-statement/negative-elimination questions (`PMKSY`, `RuPay/BHIM`, `Green Credit`, `GeM`, `PMFBY`), active testing of revised ceilings/premiums (`PMJJBY` Rs 330->436, `SCSS` Rs 15L->30L, `PMEGP` Rs 50L, `ECLGS` Rs 1,500 cr), and repeated re-testing of legacy schemes (`PMJDY`, `APY`, `MUDRA`, `Saubhagya`, `DDU-GKY`).
3. **2024–2026 (Sub-Component Granularity + Digital Platforms + Static Revival):**
   - **2026 shows a dual pattern:** testing **brand-new 2026 launches/guidelines** up to the exam window (`PACT` Sept 2026, `Samudra Manthan` July 2026, `SHATAYU` May 2026, `RBSK 2.0` May 2026, `BHAVYA`, `PM Surya Sarovar`) **alongside a sharp revival of static origin/rule questions on 2015–2020 schemes** (`PMKVY` 2015, `AIF` 2020, `PMMY` non-corporate/non-farm scope, `DAY-NRLM` 5-member tribal SHG exception, `PMJJBY` age 50).
   - **Budget/Scheme allocation questions** shifted from headline totals to **sub-shares and internal rankings** (PMAY-G state share Q78; top-2 of 7 agri schemes Q77; specific HSR corridor pair in Budget 2026–27 Ch 3 Q3).

#### Exam-Tier Differentiation
- **IBPS PO Mains & SBI PO Mains:** Heavily favor **multi-statement/NOT-true elimination** (`Q158`, `Q176`, `Q177–178`, `Q203`, `Q204`, `Q257`), **subtle legal/eligibility qualifiers** (`non-corporate, non-farm` Q4; remote SHG `5 members` Q6), **sub-allocations** (`Q77`, `Q78`), **middle-letter acronyms** (`SHATAYU` Q2, `BHAVYA` Q15; `ACABC` Q156, `MMF` Q202), **SDG links** (`Q161`), and **current-year new launches** (`Q1–Q5`, `Q14`).
- **IBPS Clerk / SBI Clerk / RRB Clerk Mains:** Concentrate on **numerical caps, extensions, portals/apps, non-issuing bank exclusions, and single-fact ministry/beneficiary matches** (e.g., `Mobile Seva` Q10, `PM-SGMBY` March 2027 Q11, `e-SARAS` Q12, `Jeevan Pramaan` Q17, `PMJJBY` age 50 Q19; `FFS` Q87, `TREAD` Q88, `MSSC` Q110 & Q116, `PM-SYM` Q142, `PMEGP` Q145, `ECLGS` Q146, `PMGKAY` Q148).
- **RRB PO / Scale 1 & Insurance (LIC / ESIC / EPFO):** Weight toward **rural/agri/cooperative/social-security** (`PMFBY` Q131, `PM Vishwakarma` Q133, `Sahkar se Samriddhi` Q134, `Svamitva` Q104, `GOBARDHAN` Q128, `e-NAM` Q229) and **insurance/pension/welfare timelines** (`Bima Vahaks` Q140, `PM-MITRA` Q139, `PM Laghu Vyapari Maan Dhan` Q276).

---

### 4. Practical Takeaways: The Examiner's 8-Field Scheme Checklist

To match how questions are actually constructed in `FILE: chats/document.md [Part 5/13]` and `FILE: chats/document.md [Part 6/13]`, notes for any government scheme (new or evergreen) must capture these 8 specific fields:
1. **Exact Acronym Expansion** (watch the middle/last letters, e.g., `SHATAYU`, `BHAVYA`, `PRAYAS`, `SHRESHTA`).
2. **Nodal Ministry + Implementing/Channelizing Agency** (flag non-obvious pairings like `GOBARDHAN -> Jal Shakti`, `FAME -> Heavy Industries`, `e-NAM -> SFAC`, `Saubhagya -> REC`, `CCTS -> BEE`).
3. **Origin Year + Tenure + Latest Extension / Effective Date / Target Year** (`2015–2020` launch years are actively re-tested in 2026).
4. **Total Outlay + Sub-Allocations / Centre-State Share** (do not stop at headline outlay—note state share and top-ranked sub-schemes).
5. **Revised Financial Caps, Interest/Premiums & Sub-Categories** (capture *before vs. after* values, e.g., `PMJJBY` 330->436, `SCSS` 15L->30L, `ECLGS` 400->1,500 cr).
6. **Eligibility Qualifiers, Age Brackets & Exception Rules** (e.g., *non-corporate/non-farm*, `0–18` vs `15–35` vs `18–50`, remote-area `5-member` SHG rule, non-issuing bank exclusions).
7. **Associated Portal / Mobile App / Brand Name (+ Language Count)** (`Mobile Seva`, `e-SARAS`, `Jeevan Pramaan`, `e-Jagriti`, `CDP-SURAKSHA`, `Kisan eMitra`).
8. **First Adopting State/City, Cluster Locations & Multi-Statement Components** (especially for PO Mains component/exclusion traps).

---

## Model

That output is impressive—and your transcript just revealed **the exact two bottlenecks** keeping your hybrid from hitting 100% recall in 1–2 hops:

### What Your Transcript Just Proved
1. **The Exact Truncation Ceiling (~40–45 KB per URL):**
   Look at AI Studio's own note:
   > *"Chapter 4 Q20–Q71 in Part 5 and Q287–Q342 in Part 6 fall beyond the URL-context browse snippet length limit."*
   
   Our 65 KB chunks (`MAX_COLD_BYTES = 65_000`) were ~20 KB too big—Playground's URL-context tool clipped the bottom ~20% of both files! Dropping the limit to **35 KB per chunk** means Gemini reads **every single question** with **zero truncation** (and since you can request up to 20 URLs per turn, pulling 4–5 chunks of 35 KB in one message works cleanly).

2. **Why Gemini Had to Binary-Search (`Parts 1, 4, 8, 12` → `Parts 5, 6, 7`):**
   * `Part 6` was a mid-chapter continuation of Chapter 4, so the *"04. Government Schemes"* heading only appeared back in `Part 5` (and was crowded out of `llms.txt` by earlier subheadings).
   * If `build-kb.py` **carries forward the active chapter name** (`## [Chapter Context: 04. Government Schemes & Initiatives (342)]`) onto every continuation chunk and prioritizes chapter headers in `llms.txt`, Gemini will jump **straight to every Chapter 4 part on Turn 2** without wasting a turn probing `Parts 1, 4, 8, 12`.

---

### Patched `build-kb.py` (Zero Truncation + Direct Chapter Routing)

Replace **`build-kb.py`** with this updated version (`MAX_COLD_BYTES = 35_000` + chapter carry-forward):

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

def find_chapter_marker(line: str) -> str | None:
    s = line.strip()
    m = re.match(r"^#{1,2}\s+(.+)$", s)
    if m:
        txt = " ".join(m.group(1).split())
        if txt.lower() not in {"table of contents", "contents", "index", "user", "model"}:
            return txt[:90]
    m2 = re.match(r"^(?:#{3,4}\s+|\*\*)?((?:Chapter\s+\d+|\d{2}\.\s+[A-Z]).{5,85}?)(?:\*\*)?$", s)
    if m2:
        return " ".join(m2.group(1).split())[:90]
    return None

def split_by_heading_pattern(text: str, pattern: str) -> list[str]:
    regex = re.compile(pattern)
    sections, current = [], []
    in_fence = False

    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith("```"): in_fence = not in_fence if not in_fence and regex.match(line) and current: sections.append("".join(current).strip) current = [line] else: current.append(line)

    if current: sections.append("".join(current).strip) return [s for s in sections if s]

def split_large_body(body: str, max_bytes: int) -> list[str]: """Split huge files into <= max_bytes parts and carry forward active chapter headings.""" if len(body.encode("utf-8")) <= max_bytes: return [body]

    pieces = [] for sec in split_by_heading_pattern(body, r"^#{1,2}\s+"): if len(sec.encode("utf-8")) <= max_bytes: pieces.append(sec) continue

        for sub in split_by_heading_pattern(sec, r"^#{3}\s+"): if len(sub.encode("utf-8")) <= max_bytes: pieces.append(sub) continue

            buf, buf_bytes = [], 0 for para in sub.split("\n\n"): p_bytes = len(para.encode("utf-8")) + 2 if buf and (buf_bytes + p_bytes > max_bytes): pieces.append("\n\n".join(buf).strip) buf, buf_bytes = [], 0 buf.append(para) buf_bytes += p_bytes if buf: pieces.append("\n\n".join(buf).strip)

    # Track active chapter heading across pieces
    tagged_pieces = [] running_chapter = None for p in pieces: tagged_pieces.append((p, running_chapter)) in_fence = False for line in p.splitlines: if line.lstrip.startswith("```"):
                in_fence = not in_fence
            if not in_fence:
                ch = find_chapter_marker(line)
                if ch:
                    running_chapter = ch

    # Merge small pieces up to max_bytes, prepending chapter context on continuation chunks
    merged, cur, cur_bytes, chunk_chapter = [], [], 0, None
    for p, start_chapter in tagged_pieces:
        p_bytes = len(p.encode("utf-8")) + 2
        if cur and (cur_bytes + p_bytes > max_bytes):
            chunk_text = "\n\n".join(cur)
            first_line = chunk_text.lstrip().splitlines()[0] if chunk_text.strip() else ""
            if chunk_chapter and not find_chapter_marker(first_line):
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
        if chunk_chapter and not find_chapter_marker(first_line):
            chunk_text = f"## [Chapter Context: {chunk_chapter}]\n\n{chunk_text}"
        merged.append(chunk_text)

    return merged

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
