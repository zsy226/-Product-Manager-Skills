---
name: feasibility-report-writer
description: Draft, compare, expand, or revise Chinese government and public-sector feasibility reports, especially政务信息化建设、升级改造、系统集成、数据治理、运维服务、综合保障项目可研。 Use when the user provides project facts, policy basis, current-state materials, bid or procurement files, budget inputs, sample reports, or wants a structured feasibility report with compliant outline, evidence-backed section drafting, investment estimates, implementation governance, and wording aligned to formal government IT feasibility-report style.
---

# Feasibility Report Writer

Write feasibility reports from parsed source evidence, not from generic proposal language or raw procurement wording. When the user's target style is “可研骨架 + 系统需求说明导向”, prefer requirement-oriented chapter writing over macro management rhetoric.

## Mandatory Workflow

### CRITICAL: Auto-continuation is the default behavior

**For any long report (expected > 10,000 Chinese characters), you MUST execute the following loop until completion:**

```
LOOP (repeat until report is complete):
  1. Check round-status to find NEXT_UNWRITTEN_HEADING
  2. If no unwritten heading → EXIT LOOP (report complete)
  3. Draft content for the next bounded scope (2000-4000 chars)
  4. Append to report.md
  5. Briefly log progress (every 5 rounds)
  6. IMMEDIATELY continue to next iteration (do NOT wait for user)
```

**You must NOT stop after one round. You must NOT ask "Should I continue?". You must keep going automatically.**

### Long-report default

- Any request for `完整可研`, `整篇报告`, `全文`, `一次性出完整报告`, or a report benchmarked against sample-report scale must default to staged append-only drafting.
- Do not treat "请输出完整可研" as permission to emit the whole document in one response.
- **After Round 0 (baseline package), immediately continue to Round 1, then Round 2, and so on, without stopping.**
- The baseline package is mandatory for long reports, even when the user primarily wants the final full report.
- For long reports, completion means `deliver all rounds in sequence until the report is complete`, not `compress the report into one response`.
- If the user does not specify where to start, the first prose round after Round 0 should default to `Chapter 1-3` for thin evidence cases or the first clearly bounded chapter family supported by the fact base.
- Treat long-form generation as a `file-accumulation workflow`, not a `single-response workflow`.
- The expected output location for long reports is `workspace/report.md` plus `workspace/generated-sections/*`, not the chat window.
- For reference-scale reports, the assistant must prefer `many bounded rounds` over `fewer larger rounds`; quality and continuity are more important than round count.

### Operational profile for very long reports

- Long reports are constrained by single-response token limits, so they must scale via repeated append rounds.
- Recommended round payload target:
  - dense technical chapters (Chapter 4/6): about `2,000-3,500` Chinese characters per round
  - governance/budget chapters: about `1,500-2,500` Chinese characters per round
  - do not intentionally exceed roughly `4,000` Chinese characters in one drafting payload unless the user explicitly asks for larger chunks
- Recommended target cadence:
  - Round 0 = baseline package only
  - Round 1+ = one bounded chapter/subchapter/system/module package per round
  - every `3-5` drafting rounds, run a light review pass before continuing
- Completion criterion for very long reports:
  - all planned chapter/module packages have been appended
  - Stage 5 review-to-revision loop has been completed
  - `export-final` output is generated

1. Classify the report before outlining.
   - Determine whether the report is a建设型可研, 升级改造型可研, or 运维/综合保障型可研.
   - Do not reuse the same chapter depth blindly across these three categories.
2. Run the bundled parser before any drafting when source files are provided.
   - If the user provides `.pdf`, `.docx`, `.txt`, or `.md` source materials, you must run `scripts/parse_source_materials.py` first.
   - For PDF procurement or tender files, also use [$pdf](/Users/nicole/.codex/skills/pdf/SKILL.md) as the supporting file-reading workflow.
   - Do not begin outlining or prose drafting until you have read the generated fact-base output.
3. Read the generated fact base.
   - Review the generated `fact-base.md` or `fact-base.json` before deciding the report type, chapter skeleton, or major claims.
   - Treat the fact base as the default evidence source for the report.
   - If the parser prints a `READ_THIS_FIRST:` line, use that file path first.
   - If the parser prints a `NEXT_STEP:` line, follow that instruction before outlining or drafting.
   - Also read the extracted chapter-writing directions and system-writing directions when present. Treat them as the bridge between source facts and long-form drafting.
4. Lock the writing directions before drafting.
   - Before writing any outline, chapter, or subsection, explicitly determine which chapter-writing directions and which system-writing directions apply to the current unit of drafting.
   - Treat these directions as the immediate drafting brief for the current chapter or system.
   - If a chapter-writing direction and a generic writing habit conflict, follow the extracted writing direction.
   - If module-writing directions are present for the current system, lock those too before drafting Chapter 4 or Chapter 6 content.
5. Inventory available inputs.
   - Prefer source materials in this order: approved project background, policy basis, current-state survey, business requirements, system inventory, data inventory, budget basis, schedule constraints, security requirements, procurement files, and prior sample reports.
   - If inputs are thin, state the missing items and write conservative draft text with explicit placeholders rather than inventing facts.
   - Distinguish evidence about `procurement scope` from evidence about `project feasibility`. A tender or procurement file can support scope, cycle, budget cap, acceptance, staffing, and security clauses, but it rarely supports a full current-state diagnosis, business-process redesign, technical architecture decision, or investment-estimate logic on its own.
6. Select the right outline family.
  - Use the standard建设型 skeleton in `references/structure-analysis.md` for new-build or upgrade projects with substantial design and construction content.
  - Use the运维型 skeleton in `references/source-intake.md` for service-heavy, operations-heavy, or保障类 projects.
  - Trim or merge chapters only when the source materials clearly do not support the full depth.
  - If the user wants a requirements-led report, keep the formal chapter skeleton but tilt the middle chapters toward `业务需求梳理、功能说明、流程说明、接口与数据要求、性能要求、安全要求、运维与验收要求`.
  - Use the chapter narrative traits from `references/structure-analysis.md` to decide how each chapter should read, not just what its title is.
7. Pass the pre-drafting checklist.
   - Before writing any outline or正文, confirm all of the following are true:
     - the bundled parser has been run, or a valid exception has been stated
     - the generated fact-base output has been read
     - the relevant chapter-writing directions have been read for the current drafting unit
     - the relevant system-writing directions have been read for the current drafting unit when system-level expansion is involved
     - the relevant module-writing directions have been read when module-level expansion is supported by the baseline fact base
     - the project has been classified as建设型, 升级改造型, or运维/综合保障型
     - the outline family has been selected from the references
     - if this is not the first drafting round, the current accumulated draft has been read first
   - If any item is false, stop and complete it first.
8. Write chapter by chapter from evidence.
  - Keep each section tied to extracted facts.
  - Make section goals explicit: overview states scope and basis, current state explains what exists, necessity explains gaps, design explains service or construction logic, budget explains how the amount is formed, governance explains delivery and control.
  - Write argument chains, not clause summaries. Every major chapter should connect `current state -> problem/gap -> reason for change -> proposed approach -> expected result`.
  - When the source evidence supports only procurement facts, downgrade the output to a conservative draft with explicit evidence gaps instead of fabricating a fully elaborated feasibility narrative.
   - When the source contains detailed system requirements, write the middle chapters like a requirement specification inside the feasibility-report skeleton:
     - explain each system's purpose, service object, business scope, function set, process support, data handling, interface requirements, performance constraints, security obligations, and acceptance expectations
     - do not stop at listing system names or repeating “负责维护/升级”
   - When module-level information is available, do not stop at the system level:
     - explain the module's business purpose
     - explain the module's specific function points or handled事项
     - explain the module's workflow, data, interface, reporting, or control logic
     - explain the module's expected support effect
   - Before drafting each chapter, decide its narrative mission from the reference sample:
     - Chapter 1 = organizational context
     - Chapter 2 = full-project compressed expansion
     - Chapter 3 = current-state inventory and bounded diagnosis
     - Chapter 4 = deepest requirement and demand analysis
     - Chapter 5 = requirement-to-solution mapping
     - Chapter 6 = deepest subsystem/module expansion
     - Chapter 7 = scope-aligned budget explanation
     - Chapter 8 = implementation and governance control
     - Chapter 9 = supporting materials and evidentiary appendices
   - Draft long reports incrementally. Do not compress a reference-sized report into a single short response.
   - Treat any report that is expected to approach sample-report scale, or clearly exceeds a normal single-response length, as a multi-round drafting task by default.
   - In multi-round drafting, each round must produce an append-only chapter package or subsection package.
   - Never regenerate the whole document when the task is to continue drafting later chapters or later subchapters.
   - The unit of output in later rounds is `new content to append after an existing anchor`, not `replacement full document`.
   - For every continuation round, structure the work internally as:
     - anchor = the last confirmed heading or subsection already present in the accumulated draft
     - scope = the next bounded chapter/subchapter/module package only
     - output = only the newly drafted prose under that scope
   - Do not include earlier chapter text in the continuation output, even for context-setting, unless the user explicitly requests revision.
   - In every continuation round, first decide whether the task is `append` or `revise`.
     - `append` means only drafting the next bounded section after the current anchor
     - `revise` means rewriting an explicitly named existing section
   - Unless the user explicitly asks for revision, continuation defaults to `append`.
   - When continuing a long report, never output a fresh full-report body. Output only:
     - the next heading block that starts exactly where the accumulated draft ended, plus
     - the new paragraphs belonging to that heading block
    - If you find yourself restating prior chapter background before entering the new heading, stop and remove that carry-over text.
    - **CRITICAL: After completing one chapter/section, immediately check for the next unwritten heading and continue drafting. Do NOT stop. Do NOT wait for user input. Keep writing until all chapters are complete.**
 9. Normalize tone and consistency.
    - Use formal, prudent, official wording.
    - Keep names, figures, subsystem labels, periods, budget numbers, staffing, and service indicators consistent across chapters.
 10. Loop until complete, then validate.
    - **After each round, run `manage_long_report.py round-status` to check if there are more unwritten headings.**
    - **If NEXT_UNWRITTEN_HEADING exists, immediately continue to the next round. Do NOT validate yet.**
    - **Only validate when round-status shows no more unwritten headings.**
    - Check that every major建设内容 or服务包 appears in necessity, design or service scheme, budget, schedule, governance, and assessment sections.
    - Flag unsupported claims, missing budgets, vague benefits, mismatched timelines, and sections that look like bid-response text rather than feasibility analysis.

## Bundled Script

- You must use `scripts/parse_source_materials.py` before drafting when the user provides PDF procurement files, DOCX sample reports, or raw text source packs.
- For long reports, you must then use `scripts/manage_long_report.py` to initialize the staged workflow workspace and manage append-only drafting against the cumulative report file.
- Unless the user explicitly specifies another path, always let the script write to its default outputs:
  - `<source>.fact-base.md`
  - `<source>.fact-base.json`
- After the script runs:
  - read the `.fact-base.md` file first
  - use the `.fact-base.json` file for structured lookup, consistency checks, or downstream automation
  - if present, trust the `READ_THIS_FIRST:` terminal line as the primary pointer to the markdown fact base
  - if present, trust the `NEXT_STEP:` terminal line as the required immediate action
- Typical usage:

```bash
python3 scripts/parse_source_materials.py /path/to/source.pdf
python3 scripts/parse_source_materials.py /path/to/source.docx
python3 scripts/manage_long_report.py init --fact-base-json /path/to/source.fact-base.json --workspace /path/to/report-workflow
python3 scripts/manage_long_report.py task-pack --workspace /path/to/report-workflow --phase-id phase_2_chapter_draft
python3 scripts/manage_long_report.py append --draft /path/to/report-workflow/report.md --heading "第四章 项目建设必要性及需求分析" --content-file /path/to/round-b.md
python3 scripts/manage_long_report.py mark-phase --workspace /path/to/report-workflow --phase-id phase_2_chapter_draft --status completed
python3 scripts/manage_long_report.py review --draft /path/to/report-workflow/report.md --outline /path/to/report-workflow/01-outline.md
python3 scripts/manage_long_report.py revise-from-review --workspace /path/to/report-workflow --review-json /path/to/report-workflow/review-notes.json
python3 scripts/manage_long_report.py batch-revisions --workspace /path/to/report-workflow --targets-json /path/to/report-workflow/task-packs/phase_5_review_adjust.targets.json --group-by chapter
python3 scripts/manage_long_report.py prompt-packs --workspace /path/to/report-workflow --batches-json /path/to/report-workflow/task-packs/phase_5_review_adjust.batched-by-chapter.json
python3 scripts/manage_long_report.py draft-templates --workspace /path/to/report-workflow --prompt-pack-dir /path/to/report-workflow/task-packs/prompt-packs
python3 scripts/manage_long_report.py apply-draft-template --draft /path/to/report-workflow/report.md --template /path/to/report-workflow/task-packs/draft-templates/batch_001.filled.md
python3 scripts/manage_long_report.py ledger-doctor --draft /path/to/report-workflow/report.md --ledger-dir /path/to/report-workflow/generated-sections --fail-on-issues
python3 scripts/manage_long_report.py export-final --draft /path/to/report-workflow/report.md --output /path/to/report-workflow/final-report.md
```

- Only pass `-o` or `--json-output` when the user explicitly requests a non-default destination.

## Output Contract

- The parser's default output contract is part of this skill's workflow.
- When the input file is `foo.pdf`, the default outputs are:
  - `foo.fact-base.md`
  - `foo.fact-base.json`
- When locating parser results, check these default files first before searching elsewhere.
- Do not invent alternate fact-base filenames unless the user requested custom paths.
- If the parser prints `READ_THIS_FIRST: /abs/path/foo.fact-base.md`, read that exact file next.
- If the parser prints `PARSE_STATUS: success`, treat the parsing stage as complete and move directly to reading the fact base.
- If the parser prints `JSON_FACT_BASE: /abs/path/foo.fact-base.json`, use that path for structured lookup instead of searching for another JSON file.
- If the parser prints `NEXT_STEP: Read ...`, perform that step before drafting.
- If the parser provides chapter-writing directions or system-writing directions inside the fact base, use them to build the baseline document package before starting chapter prose.
- If the parser provides chapter-writing directions or system-writing directions inside the fact base, treat them as high-priority drafting instructions rather than optional reference notes.
- If the parser provides module-writing directions inside the fact base, treat them as required drilling instructions for Chapter 4 and Chapter 6 rather than optional fine detail.

## Exception Rules

- Only skip the bundled parser if one of these is true:
  - the input format is not supported by the script
  - the script fails at runtime
  - the script output is missing key facts and cannot be repaired with a second run or minor cleanup
- If you skip the parser, you must say why before doing anything else.
- If the parser fails, prefer fixing or re-running the bundled script before writing one-off parsing code.
- Do not create a new ad hoc parser for normal procurement-file parsing when the bundled script is applicable.
- Do not start report prose from raw source files unless the parser path is blocked for a stated reason.

## Stop Conditions

**Important**: "Stop" in this section means "stop the current round and fix the issue", NOT "stop the entire report generation". After fixing, you must continue with auto-continuation.

- Stop immediately if you are about to draft without a fact base.
- Stop immediately if you cannot locate the default fact-base outputs after running the parser; resolve the path issue first.
- Stop immediately if you are about to make a budget, staffing, payment, SLA, or implementation claim that is not supported by the fact base or an explicitly cited source file.
- Stop immediately if you notice yourself writing a temporary parser for a standard procurement document while the bundled script still applies.
- Stop immediately if a construction or upgrade report is drifting into generic filler such as “采用主流技术框架”“优化用户体验”“提升系统性能” without project-specific evidence.
- Stop immediately if you are about to fill a chapter with `待补充`, `待评估`, or empty indicator tables instead of either supplying supported content or explicitly marking the whole subsection as evidence-insufficient.
- Stop immediately if the建设内容或服务内容 chapter is turning into consecutive lists, tables, or bullet points without paragraph-level explanation for each major system or module.
- Stop immediately if you are attempting to output a reference-scale report in one pass and the result is collapsing into a short generalized summary.
- Stop immediately if a later drafting round is about to overwrite, restate, or replace previously completed chapters instead of appending new content.
- Stop immediately if you are about to answer a long-report request with a single full-report generation attempt. Switch to staged drafting instead.
- Stop immediately if you are about to draft a chapter or system section without first applying its corresponding chapter-writing direction or system-writing direction.
- Stop immediately if module information exists in the baseline fact base but the draft stays only at system-level description.
- Stop immediately if a continuation round starts reprinting already completed headings or paragraphs instead of only drafting the next bounded section.
- Stop immediately if the text is drifting into consecutive short bullet-like sentences, checklist phrasing, or summary labels without sustained analytical paragraphs.
- Stop immediately if a continuation draft begins with Chapter 1, Chapter 2, “项目概述”, or other already completed chapter labels when the task was to continue later sections.
- Stop immediately if the continuation output contains more old text than new text. Continuation rounds must be dominated by newly added material.
- Stop immediately if a section is being expanded only at system-name level while the evidence supports module-level or function-point-level expansion.

## Core Rules

- Prefer objective statements over sales language.
- Do not write bid-response language such as “我方”, “投标人”, “完全满足”.
- Do not overclaim effects. Use “预计”, “可实现”, “有助于”, “支撑”.
- Keep chapter numbering strict and hierarchical.
- Use tables for indicators, inventories, budgets, schedules, user roles, staffing, responsibility matrices, SLAs, and assessment rules.
- Use prose for background, necessity, risks, governance rules, and benefit analysis.
- Do not confuse `formal structure` with `substantive content`. A report that has the right chapters but only generic bullets, placeholder tables, or rewritten procurement clauses is not an acceptable feasibility report.
- Do not produce placeholder-heavy tables. If a table would mostly contain `待补充`, omit it and explain what evidence is missing.
- Do not use generic technical filler such as “主流前端框架”, “微服务架构”, “关系型数据库”, “提升用户体验”, or “优化业务流程” unless the source materials clearly justify those exact choices.
- For建设型或升级改造型项目, prioritize narrative diagnosis, construction rationale, target-state description, and construction scope logic over checklist-style requirement restatement.
- If the user wants a系统需求说明书导向的可研, prioritize requirement extraction and requirement explanation over macro policy prose.
- Treat system-level requirements as first-class evidence. If the source file contains per-system functions, daily maintenance actions, interface work, data handling, SLA, monitoring, backup, security, or acceptance duties, extract and use them directly in chapter writing.
- Treat chapter-writing directions and system-writing directions as first-class drafting inputs. They should be created before long-form writing begins.
- Drafting priority order is:
  - current chapter-writing direction
  - current system-writing direction
  - current module-writing direction
  - extracted fact base and requirement evidence
  - outline family and reference chapter traits
  - generic style rules
- This means the back-half guidance in the baseline fact base is higher priority than generic stock writing patterns.
- Treat the current accumulated draft as the source of truth in later rounds. New output must preserve prior chapter numbering, wording conventions, names, and already drafted content.
- In long-form drafting, the operative prompt for each round is not “write the report”, but “append the next bounded section under the current writing direction”.
- When the source gives only a module or service name, expand cautiously into responsibilities, users, process steps, data sources, outputs, service frequency, or control points.
- When writing investment sections, separate software development, service work, AI or model capability, security work, hardware if any, and contingency or supporting costs if supplied.
- Do not force “deep function tree” writing for运维服务项目 when the source is organized by service package, staffing, SLA, and work item.
- Richness means evidence-based expansion, not filler. Expand from concrete requirements into concrete explanatory dimensions.
- For any major system, module, or requirement cluster, try to cover as many of these dimensions as the evidence supports:
  - service object or user group
  - business scenario or trigger condition
  - current pain point or management difficulty
  - function or capability to be built, optimized, or guaranteed
  - workflow step or handling process
  - data object, data source, interface, or document flow
  - monitoring, feedback, reporting, or control mechanism
  - performance, availability, security, or compliance constraint
  - expected support effect, management value, or risk-control effect
- If a paragraph only restates the requirement item without adding these dimensions, it is under-expanded.
- Prefer paragraph-first writing. Lists and tables may summarize, but the core explanation must live in prose paragraphs.
- A good deep paragraph usually combines at least 3-4 concrete dimensions from the evidence, rather than one label plus one generic consequence.
- Treat each important system as a mini-specification unit, and each important module as a mini-requirement unit inside that system.
- For Chapter 4 and Chapter 6, simple “system name + one sentence” treatment is not enough when the fact base contains module names, handled items, business objects, or work tasks.
- A strong subsection usually expands through this ladder:
  - system mission and service object
  - current problem or trigger scenario
  - module set and module division of responsibility
  - concrete function points or handled事项
  - workflow, data, interface, monitoring, reporting, or control logic
  - expected support effect or management improvement
- If a subsection only enumerates modules or service items without turning them into explanatory paragraphs, it is not deep enough.

## Long-Form Continuation Protocol

Use this protocol whenever the report is too long for one high-quality response.

### Round 0: baseline package

- Produce the baseline package first:
  - report classification
  - selected outline family
  - chapter-writing directions
  - system-writing directions
  - module-writing directions when available
  - staged drafting plan
- Initialize a workflow workspace with `scripts/manage_long_report.py init`, and treat the generated `report.md` as the cumulative source of truth for all later rounds.
- Do not treat the baseline package as chapter prose.

### Round N: append-only drafting

- Every drafting round after the baseline package must internally lock:
  - `mode = append` unless the user explicitly requested revision
  - `current accumulated draft`
  - `append anchor`
  - `next bounded scope`
  - `chapter/system/module writing direction for this scope`
- Output only the new section content for that scope.
- After generating the new section content, append it into the cumulative `report.md` under the correct heading anchor with `scripts/manage_long_report.py append`.
- Do not reissue previous chapters, previous summaries, or a rebuilt table of contents.
- If the next bounded scope is still too large, split again by subsystem, module cluster, or heading family.

### Five-stage execution workflow (AUTO-CONTINUE between stages)

**IMPORTANT: After completing each stage, immediately proceed to the next stage without waiting for user input.**

- Stage 1: build baseline package, factual ground draft, and chapter/subchapter skeleton
  - run the parser
  - read the fact base
  - run `manage_long_report.py init`
  - lock `00-baseline-package.md`, `01-outline.md`, and the empty cumulative `report.md`
  - **Then immediately continue to Stage 2**
- Stage 2: write the first chapter package from chapter-writing directions
  - run `manage_long_report.py task-pack --phase-id phase_2_chapter_draft`
  - choose the next bounded chapter family
  - generate only that chapter package
  - append it under the corresponding headings in `report.md`
  - **After each chapter, check round-status. If more chapters remain, continue drafting. Do NOT stop.**
  - mark the phase completed after all chapters are done
  - **Then immediately continue to Stage 3**
- Stage 3: append system-level expansion from system-writing directions
  - run `manage_long_report.py task-pack --phase-id phase_3_system_append`
  - reopen the cumulative `report.md`
  - find the target chapter or system anchor
  - append only the new system-level expansion without replacing prior text
  - **After each system, check round-status. If more systems remain, continue drafting. Do NOT stop.**
  - **Then immediately continue to Stage 4**
- Stage 4: append module-level expansion from module-writing directions
  - run `manage_long_report.py task-pack --phase-id phase_4_module_append`
  - reopen the cumulative `report.md`
  - find the target system or module anchor
  - append only the new module-level expansion without replacing prior text
  - **After each module, check round-status. If more modules remain, continue drafting. Do NOT stop.**
  - **Then immediately continue to Stage 5**
- Stage 5: review and corrective append
  - run `manage_long_report.py task-pack --phase-id phase_5_review_adjust`
  - run `manage_long_report.py review` against the cumulative `report.md`
  - run `manage_long_report.py revise-from-review` to convert review findings into targeted revision tasks
  - if the revision targets are numerous, run `manage_long_report.py batch-revisions` to aggregate them into chapter-level or system-level repair batches
  - run `manage_long_report.py prompt-packs` to generate ready-to-write prompt packs for each repair batch
  - run `manage_long_report.py draft-templates` to generate editable repair draft templates and append maps
  - fill one or more draft templates, then run `manage_long_report.py apply-draft-template` for semi-automatic anchor-based appending
  - read the generated revision task pack, target JSON, and append map
  - prefer working from the draft templates when the report is large or the findings count is high
  - add corrective text under the affected heading anchors through template application or manual append
  - prefer localized append or narrow revision over whole-document regeneration
  - after all phases are complete, export the clean deliverable with `manage_long_report.py export-final`

### Round execution loop (mandatory for long reports)

- Use this loop for every Round N after baseline:
  - Step A: reopen `report.md` and locate the current append anchor
  - Step B: lock one bounded scope only (one chapter family, one subsystem cluster, or one module cluster)
  - Step C: draft only new prose for that scope
  - Step D: append to `report.md` using `manage_long_report.py append`
  - Step E: record phase progress with `mark-phase` when a phase boundary is reached
  - Step F: continue to next bounded scope; do not regenerate prior scope text
- If a round is interrupted, resume from `report.md` and ledger state; do not restart from Round 0.
- If two consecutive rounds fail to increase depth (for example, repeated system-name summaries), force scope split to a smaller module-level unit before continuing.

### Auto-continuation rule (mandatory for long reports)

- **You must NOT stop after completing one round.** For long reports, continuation is automatic, not user-triggered.
- After appending content for the current bounded scope, immediately run `manage_long_report.py round-status` to check:
  - Is there a `NEXT_UNWRITTEN_HEADING`?
  - Is there a `NEXT_UNWRITTEN_CHAPTER`?
- If any unwritten heading exists, you must immediately proceed to the next round without waiting for user input.
- The auto-continuation loop continues until one of these conditions is met:
  - `round-status` shows `NEXT_UNWRITTEN_HEADING: N/A`
  - All phases in `workflow-state.json` are marked `completed`
  - The user explicitly says "stop" or "pause"
- Do not ask "Should I continue?" or "Do you want me to proceed?" — just continue automatically.
- For very long reports (targeting 100,000+ Chinese characters), expect 25-50+ rounds. This is normal. Keep going.
- Progress indicator: After every 5 rounds, briefly report progress (e.g., "已完成 5/9 章，累计 12,000 字，继续下一轮...") then immediately continue.
- The only valid reasons to pause mid-report are:
  - User explicitly requests a pause
  - A blocking error in the script or fact base
  - You need clarification on a critical fact that affects the entire report structure
- If you pause for any reason other than user request, you must explain why and what is needed to resume.

### Auto-continuation implementation

Use this loop structure for automatic continuation:

```
while True:
    1. Run round-status to get NEXT_UNWRITTEN_HEADING
    2. If no unwritten heading: break (report complete)
    3. Draft content for the next scope
    4. Append to report.md
    5. If round count % 5 == 0: print brief progress
    6. Continue to step 1
```

- This loop must execute within a single session until completion.
- Do not output "I'll continue in the next message" — continue in the current response.
- If you reach a token limit mid-draft, complete the current append, then immediately start a new response continuing from where you left off.

### One-command-per-round template

Use this shell template to enforce append-only behavior:

```bash
# 0) inspect round progress and auto-suggest next bounded scope
python3 scripts/manage_long_report.py round-status --workspace /path/to/report-workflow
python3 scripts/manage_long_report.py next-scope --workspace /path/to/report-workflow --prefer auto --content-file /tmp/round-N.md

# 1) prepare next scope content as /tmp/round-N.md (new prose only)
python3 scripts/manage_long_report.py append \
  --draft /path/to/report-workflow/report.md \
  --heading "第X章 或具体锚点标题" \
  --content-file /tmp/round-N.md

# 2) optional but recommended at phase boundaries
python3 scripts/manage_long_report.py mark-phase \
  --workspace /path/to/report-workflow \
  --phase-id phase_2_chapter_draft \
  --status in_progress
```

- `round-status` is used to display the current active phase, last appended heading, and next unwritten heading.
- `next-scope` is used to generate a next-scope suggestion and a ready-to-run append command template.

### Anti-regeneration gate

- Before any long-report response, run this decision gate mentally:
  - Is this request long-form and reference-scale? If yes, do not output full report in one response.
  - Is this a continuation request? If yes, default mode is append, not rewrite.
  - Is the output starting with already completed chapter headings? If yes, stop and rewrite the round as new-content-only.
- Any round that reprints prior chapter text by default is a workflow violation and must be regenerated before delivery.

### Review-to-revision rule

- `review` is only the detection step.
- `revise-from-review` is the routing step that maps review findings to concrete heading anchors and revision actions.
- `batch-revisions` is the aggregation step that compresses many small revision actions into a manageable number of chapter-level or system-level repair batches.
- `prompt-packs` is the execution-brief step that turns each repair batch into a ready-to-write writing prompt pack with anchors, issues, and relevant writing directions.
- `draft-templates` is the pre-append step that turns each prompt pack into an editable draft template plus append-anchor map.
- `apply-draft-template` is the semi-automatic落稿 step that reads filled templates and appends each target block into the cumulative draft at the mapped heading.
- Every append/apply operation should also be treated as an append-only generated-content record in the workflow ledger directory (default: `generated-sections` beside `report.md`).
- `export-final` should prefer merging from the append-only ledger when it exists, so final output is resilient even if `report.md` was accidentally overwritten during drafting.
- For Stage 5, do not stop after producing `review-notes.md` or `review-notes.json`.
- You must continue by generating the revision task pack, batching it when needed, generating prompt packs, generating draft templates, and then applying localized fixes to the cumulative `report.md`.
- If a finding is only about anchor leakage or empty skeleton residue, prefer solving it through `export-final` rather than polluting the cumulative draft with cleanup prose.

### Continuation depth rule

- For long formal reports, length growth should come from deeper evidence-backed expansion, not from repeating chapter summaries.
- The main depth-bearing zones are usually:
  - Chapter 4 requirement analysis
  - Chapter 6 construction or service content
- These zones should often be split across several rounds by system family, then by module family when available.

### Continuation self-check

Before returning a continuation round, check all of the following:

- the first heading in this output is the next heading after the append anchor
- no completed chapter text has been reprinted
- the new section follows the active chapter/system/module writing direction
- the new section is paragraph-led, not checklist-led
- the new section goes deeper than system naming and reaches module or function-point explanation when the evidence supports it

If any check fails, rewrite the round before returning it.

## Outline Selection

### Construction and upgrade reports

- Retain the stronger “单位概况 - 项目概述 - 数字化现状 - 必要性及需求分析 - 项目设计方案 - 项目建设内容 - 项目预算 - 项目建设与运行管理 - 其他” main line.
- Use deeper heading levels in “需求分析” and “建设内容” when the source supports subsystem and module decomposition.
- Do not write a full construction or upgrade report from procurement scope alone. If only procurement facts are available, produce:
  - a formal outline
  - conservative chapter summaries tied to known facts
  - an explicit “待补充材料/待补充事实” list for current state, target architecture, detailed modules, workload, and budget basis
- The design chapter must explain why the chosen construction route fits the diagnosed problems. It must not default to generic architecture diagrams or textbook technology stacks.
- For reference-scale reports, Chapter 4 and Chapter 6 should be expanded in multiple rounds, not collapsed into one short chapter draft.

### Operations and support reports

- Keep the formal chapter backbone, but adapt the middle chapters to service logic instead of construction logic.
- Recommended backbone:
  - 单位概况
  - 项目概述
  - 数字化与运维现状
  - 项目必要性及服务需求分析
  - 项目服务方案或实施方案
  - 项目服务内容
  - 项目预算
  - 项目实施与运行管理
  - 其他
- Preserve chapters for招标方案, 考核机制, 付款安排, and相关管理制度 when the source is a government procurement file.
- Do not collapse the report into a generic 8-chapter consulting memo if the target style is a formal可研.

## Section Guidance

### Unit and project overview

- State the建设单位,需求单位,编制单位, project name, responsible persons, background, basis, objectives, scope, cycle, benefits, risks, and planning indicators.
- For运维类项目, still include单位概况 rather than jumping directly into service scope.
- Open with facts and administrative context, not solution detail.

### Current-state chapter

- Describe existing systems, networks, devices, data resources, security posture,运营平台基础, and current service arrangement if relevant.
- For运维类项目, add current service pain points, current support model, existing asset base, and critical service targets.
- Use inventories and summary tables wherever the source has system lists, asset lists, or service lists.
- Do not infer a detailed current-state architecture merely from procurement scope. If the source lacks current-state evidence, write a bounded summary and explicitly identify the missing survey inputs.

### Necessity and demand analysis

- Split “why do this project” from “what the project requires”.
- Cover policy drivers, business pain points, workflow bottlenecks, user roles, workload, performance, security, data demands, and service-level expectations.
- For运维类项目, demand analysis should emphasize service continuity, SLA, asset visibility, emergency support, staffing, compliance, and assessment.
- Necessity analysis must diagnose concrete contradictions or gaps. It is not enough to restate “国家要求”“业务需要”“技术需要” in abstract slogans.
- For upgrade reports, tie every major necessity point to an observed limitation of the current systems, management model, data use pattern, or user experience.
- Demand analysis should be requirement-led when evidence allows:
  - business scenarios
  - function modules
  - workflow steps
  - interface or data exchange needs
  - performance and availability targets
  - security and compliance constraints
  - operation and acceptance requirements
- If a system already has identifiable功能模块或功能点, Chapter 4 should descend to that module layer instead of summarizing only at system level.
- In rich reports, this chapter should not stop at category labels. Each demand cluster should be expanded into:
  - who uses it
  - in what business situation it is triggered
  - what problem is occurring now
  - what capability is required
  - what processing or data flow is involved
  - what target state or control effect is expected

### Design or service-scheme chapter

- Describe construction goals, service goals, scope, overall architecture, technical route, service route, standards, and management mechanism.
- For运维类项目, this chapter should describe service体系,支撑架构,响应分级,工作机制, and platform/tool route rather than pretending there is a large new technical architecture.
- For建设型或升级改造型项目, the design chapter must be project-specific. Avoid canned architecture stacks unless the source actually names them or the report clearly labels them as recommended assumptions.
- For requirement-led reports, this chapter should translate extracted requirements into solution boundaries and design principles, not generic technology stacks.

### Construction-content or service-content chapter

- Expand by subsystem, service package, module, and submodule as the evidence allows.
- For each major item, explain function or service content, users, process, data, outputs, frequency, and control points.
- Use deeper heading levels only when the source material actually supports that depth.
- Avoid generating repetitive “系统概述/运维内容/运维工作量” subtrees for every system unless the source truly distinguishes them; summarize repeated patterns in shared tables where possible.
- Do not pad this chapter with empty module tables or generic work packages. If module-level evidence is absent, summarize construction boundaries at system level and state what detailed design inputs are still needed.
- Prefer per-system requirement summaries such as:
  - system purpose and service object
  - functional modules or service items
  - daily maintenance or construction tasks
  - interface and data requirements
  - monitoring, backup, and emergency support requirements
  - acceptance and deliverable expectations
- Do not stop at requirement lists. For each major system, subsystem, or module, convert the extracted requirement items into narrative paragraphs that answer:
  - what business problem or operational pain point this item addresses
  - what capability needs to be built, optimized, maintained, or guaranteed
  - how the function or service supports the actual workflow, data flow, or management process
  - what improvement or control effect is expected after construction or maintenance
- In this chapter, tables are only summaries. They cannot replace the main explanatory prose.
- Preferred writing unit for each system/module:
  - paragraph 1: current issue or business context
  - paragraph 2: construction or maintenance content
  - paragraph 3: expected support effect, management value, or control value
- If the source gives module names only, make cautious paragraph-level expansions from the known function, users, data, process, and maintenance duties. Do not leave the chapter as a bare checklist.
- If the source gives daily maintenance duties, rewrite them into “系统能力保障” language instead of listing task verbs one by one.
- Use the sample report's depth pattern as a target: Chapter 6 is normally the longest chapter and should expand by subsystem, functional module, feature cluster, and key function point where evidence supports it.
- If the baseline fact base has `功能模块` or `功能点或事项`, Chapter 6 should normally use them as the next level of headings or paragraph clusters.
- Minimum expansion rule for major modules:
  - first explain the business or governance problem
  - then explain the function/capability boundary
  - then explain the workflow, data, interface, or handling logic
  - then explain the output, service result, or control result
- If one module is described in only one short paragraph or one small table, assume the depth is probably insufficient unless the evidence is truly minimal.
- Prefer using multiple short-to-medium analytical paragraphs over one generic summary paragraph.
- When a module has extracted功能点或事项, use them to build paragraph substance, not bullet accumulation:
  - integrate several points into a coherent narrative about how the module works
  - explain relationships among functions, data, and management actions
  - explain why these function points matter to the business process

### Budget chapter

- Explain basis first, then detailed estimates, then summary tables, then annual or phased use plan.
- Keep every amount traceable to a category and scope item.
- For procurement-driven reports, make budget sections line up with the procurement categories and payment terms rather than free-form consulting categories.

### Governance and implementation chapter

- Cover organization, tendering, schedule, quality, funding control, operations, assessment, security obligations, and management制度.
- For运维类项目, keep招标方案、考核机制、服务验收、人员管理、保密与安全要求 as explicit subtopics.
- Use responsibility matrices, phased plans,制度 lists, and SLA tables to keep this chapter concrete.

## Common Failure Modes

- Skipping the bundled parser and drafting directly from raw files.
- Writing a new one-off parser even though `scripts/parse_source_materials.py` is available.
- Passing into正文 without completing the pre-drafting checklist.
- Ignoring the default fact-base output names and then failing to read the parser results.
- Ignoring the `READ_THIS_FIRST:` pointer after parsing.
- Ignoring the parser's `PARSE_STATUS`, `JSON_FACT_BASE`, or `NEXT_STEP` lines and improvising the next action.
- Copying the sample chapter names too literally even when the project is service-oriented.
- Collapsing “单位概况” and “其他” chapters and weakening the official-document feel.
- Writing too much service decomposition and too little feasibility reasoning.
- Repeating procurement clauses verbatim instead of converting them into feasibility-report prose.
- Using conclusive claims such as “项目已批复、具备实施条件” without source support.
- Missing招标方案、考核支付机制、保密安全约束 even though they are central in government service procurements.
- Producing lots of headings with thin content and low analytical density.
- Producing a document that reads like a procurement-file interpretation memo rather than a feasibility report.
- Filling chapters with generic policy slogans, generic technology choices, and reusable consulting phrases that could apply to any project.
- Using formal chapter headings as camouflage for missing evidence and weak reasoning.
- Leaving behind visible placeholders such as `待补充`, `待统计`, `待评估`, or empty shell tables in a supposed full report.
- Extracting only system names and ignoring the per-system construction or运维要求 that actually make the report useful.
- Writing the middle chapters as framework summaries instead of requirement explanations when the source already contains detailed per-system duties and constraints.
- Writing the建设内容 chapter as a module checklist without any paragraph-level explanation of problems, capabilities, workflows, or expected effects.
- Letting tables dominate the chapter so the text reads like a requirement matrix instead of a feasibility-report explanation.
- In multi-round drafting, re-emitting earlier chapters instead of appending only the new requested section.
- Replacing the accumulated draft with the latest chapter package because the append boundary was not respected.
- Misreading “完整可研” as a request for one-shot full-document generation when the report is clearly reference-scale.
- Expanding word count by repeating generic management language instead of adding concrete demand dimensions, process logic, data logic, or control logic.
- Producing short under-expanded module descriptions that only restate a requirement item and do not explain the business problem, handling logic, and expected result.
- Stopping at the system layer even though the baseline fact base already extracted module names or function points.
- Producing “条条框框” prose: many short list-like statements, each saying one obvious thing, without weaving them into analytical paragraphs.

## Handling Missing Inputs

- If policy basis is missing, request it or mark the section as needing authoritative supplement.
- If current-state materials are missing, write only a bounded summary and mark inventories as incomplete.
- If budget basis is missing, produce a category framework and assumptions list, not fabricated totals.
- If schedule is missing, give a phase structure with placeholder dates or durations.
- If subsystem or service details are uneven, keep unsupported items at the same abstraction level instead of fabricating deep function trees.
- If the only source is a procurement file, explicitly say the report is procurement-derived and that administrative approval materials may still need supplement.
- If the only source is a procurement file for a建设型或升级改造型项目, do not output a “fully completed” report. Output a formal draft plus a required-materials list, and mark which chapters are only preliminarily inferred from procurement scope.

## Reference Use

- Read `references/structure-analysis.md` when you need the standard建设型 chapter map, heading depth, table patterns, or style cues extracted from the sample report.
- Read `references/source-intake.md` when you need the source-parsing workflow, procurement-to-fact-base extraction checklist, or运维型 skeleton.
- For long-form drafting, read both references before generating the outline and again before drafting Chapter 4 and Chapter 6.

## Deliverables

- Default output depends on scope:
  - if the user requests one or more specific chapters or a clearly bounded short task, output the requested outline fragment and chapter draft
  - if the user requests a full report that is not obviously short, output Round 0 baseline package first, then continue with append-only chapter packages
- If the user wants a full report and it is short enough for one response, produce it in chapter order with clear headings and tables where appropriate.
- If the user wants a full report and it is reference-scale, do not attempt a one-shot full-document response. Instead produce:
  - the baseline document package
  - the current round's append-only chapter package
  - the next-round continuation point
- If the user wants only partial help, still preserve the same style and numbering system so later chapters can be merged cleanly.
- For thin-evidence construction or upgrade cases, the preferred deliverable is:
  - complete formal outline
  - substantive text only where evidence exists
  - concise conservative drafting elsewhere
  - a closing list of required supplementary materials to turn the draft into a full formal可研
- For reference-scale reports, the preferred delivery pattern is:
  - Step 1: baseline document package
  - Step 2: chapter family drafts
  - Step 3: subsystem/module expansions for heavy chapters
  - Step 4: consistency pass and stitched final version
- For reference-scale reports, one-shot generation is not an allowed default path.
- For long reports, if a single response starts collapsing into a short generalized report, stop and shrink the scope of the current round instead of summarizing the whole document.
- In Step 2 and Step 3, every round should be produced as append-only output:
  - Round output = newly drafted chapters or subsections only
  - Existing drafted chapters must not be re-emitted unless the user explicitly asks for revision
  - When continuing, first read the accumulated draft, then append the next bounded section
