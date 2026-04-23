# Source Intake And Operations-Style Feasibility Writing

Use this reference when the report is based on procurement files, tender PDFs, service requirements, or mixed source packages rather than a prior approved可研.

## 1. Non-Negotiable Intake Rule

When the user provides `.pdf`, `.docx`, `.txt`, or `.md` source materials, you must run the bundled parser first:

```bash
python3 scripts/parse_source_materials.py /path/to/source.pdf
```

Do this before:

- drafting any outline
- writing any chapter prose
- making any major claim about budget, staffing, service scope, or payment

Do not replace this with a newly written ad hoc parser unless the bundled script is blocked by a concrete failure.

## 2. Fixed Output Contract

Unless the user explicitly requests another destination, always use the parser's default output names:

- `<source>.fact-base.md`
- `<source>.fact-base.json`

Example:

- input: `采购文件.pdf`
- outputs:
  - `采购文件.fact-base.md`
  - `采购文件.fact-base.json`

After the parser runs:

- read the `.fact-base.md` file first
- use the `.fact-base.json` file for structured lookup and consistency checks
- if the terminal prints `READ_THIS_FIRST: /abs/path/...fact-base.md`, use that exact file first
- if the terminal prints `JSON_FACT_BASE: /abs/path/...fact-base.json`, use that exact file for structured checks
- if the terminal prints `NEXT_STEP: ...`, do that next before outlining or drafting

If you cannot find these default outputs after running the parser, stop and resolve the path issue before drafting.

Treat these terminal lines as workflow gates when they are present:

- `PARSE_STATUS: success`
- `READ_THIS_FIRST: /abs/path/...fact-base.md`
- `JSON_FACT_BASE: /abs/path/...fact-base.json`
- `NEXT_STEP: Read the markdown fact base before outlining or drafting.`

## 3. Pre-Drafting Checklist

Before writing any outline or正文, confirm all of the following:

- the bundled parser has been run, or a valid exception has been stated
- the generated `fact-base.md` or `fact-base.json` has been read
- the project has been classified as建设型, 升级改造型, or运维/综合保障型
- the outline family has been selected
- if this is not the first prose round, the current accumulated draft has been read and the append anchor has been identified
- the chapter-writing direction for the current scope has been locked
- the system-writing direction for the current scope has been locked when system expansion is involved
- the module-writing direction for the current scope has been locked when module information exists

If any item is false, stop and complete it first.

## 4. Allowed Exceptions

You may bypass the bundled parser only if:

- the file format is unsupported
- the script fails at runtime
- the script output is clearly inadequate for the required task and cannot be repaired by re-running or small local cleanup

If you bypass the parser:

- say why first
- prefer fixing the bundled script
- only then write minimal one-off extraction code if needed

## 5. Why This Intake Step Matters

The current failure pattern is drafting directly from procurement text. That usually causes:

- report structure drifting toward service plan or bid response
- overexpansion of repeated service items
- missing formal可研 chapters such as单位概况, 招标方案, 其他
- unsupported statements like “已批复” or “具备实施条件”
- generic current-state diagnosis that is not actually evidenced
- generic design prose that could fit almost any informationization project
- placeholder tables and empty shells that look formal but contain no feasibility reasoning

Always parse first, then draft.

## 6. Source Parsing Workflow

### PDF procurement or tender files

- Use [$pdf](/Users/nicole/.codex/skills/pdf/SKILL.md).
- Run `scripts/parse_source_materials.py`.
- Let it write default fact-base outputs unless the user requires otherwise.
- Prefer `pdftotext` for quick full-text extraction.
- Use `pdfplumber` when tables or fragmented text need structured extraction.
- Render pages when layout or table headers matter.

Extract at minimum:

- project name
- project number
- purchaser and demand unit
- agent and contacts
- budget amount and highest limit
- contract period
- service location
- procurement method
- service scope
- system list
- hardware or device list
- staffing requirements
- SLA and response time
- assessment indicators
- payment terms
- security, confidentiality, and compliance clauses
- acceptance and final-deliverable requirements

If the procurement file contains per-system requirement sections, also extract:

- each system's functional定位或服务范围
- each system's功能模块或功能点
- each system's具体建设/运维要求
- data, interface, monitoring, backup, reporting, and emergency-support requirements
- cross-system common requirements such as SLA,巡检,值班,数据库维护,资产维护,安全整改,验收文档

### DOCX sample reports or previous drafts

- Use the DOCX workflow from `/Users/nicole/.codex/skills/doc/SKILL.md`.
- Run `scripts/parse_source_materials.py` if the task is still source-intake oriented.
- Let it write default fact-base outputs unless the user requires otherwise.
- Extract:
  - chapter skeleton
  - heading depth
  - table types
  - official wording patterns
  - sections that are always present versus project-specific

### Build a fact base

Normalize the extracted information into a structured note with headings such as:

- 项目基本信息
- 采购与预算信息
- 服务范围
- 系统与资产清单
- 服务指标与考核
- 人员配置
- 安全与保密要求
- 付款与验收
- 待补充事实

Do not start the report until this fact base is reasonably complete.

## 7. Comparison Findings From The Two Reports

Original sample: `【可研】市发改委综合管理大系统（2026年升级改造）项目.docx`

Generated draft: `市发改委 2026 年数字化项目运维和综合保障项目可行性研究报告.md`

### Structural gaps in the generated draft

- The original uses a 9-chapter formal backbone. The generated draft compresses it into 8 chapters plus “结论与建议”.
- The generated draft omits the dedicated `单位概况` chapter.
- The generated draft renames `数字化现状` to `现状分析`, weakening alignment with the formal sample.
- The generated draft renames `项目设计方案` to `总体设计方案`, which is acceptable in isolation, but the content leans more like a service plan than a feasibility design chapter.
- The generated draft lacks a dedicated `项目建设与运行管理` chapter title and instead uses `治理与实施方案`, which weakens the official-document pattern.
- The generated draft lacks the final `其他` chapter structure used in the sample for budget basis, drawings, and related materials.
- The generated draft does not preserve `招标方案` as a stable chapter block even though the procurement file contains strong tendering, payment, and assessment content.

### Content-style gaps

- The sample moves from administrative context to present state, then to necessity, then to design, then to detailed construction, then to budget and governance.
- The generated draft moves too quickly into service breakdown and repeats similar subtrees for many systems.
- The generated draft is more list-like and procurement-driven, while the sample is more chapter-disciplined and analytical.
- The generated draft includes statements such as “项目已批复，资金已落实，采购文件已编制完成，具备实施条件”, which are not safely inferable from the procurement file alone.
- The sample uses paired “风险 + 控制措施” logic and more formal government-report pacing; the generated draft is closer to a detailed service response document.

### Evidence-source lesson

- The procurement PDF strongly supports service scope, systems, budget cap, service period, staffing, SLAs, assessment, payment, and security requirements.
- It does not by itself fully support administrative approval conclusions, broad social and economic effect claims, or deep current-state architecture narratives.
- Therefore the skill must distinguish:
  - facts directly extractable from procurement files
  - facts requiring additional internal materials
  - cautious placeholders

## 8. Recommended Operations-Style Skeleton

For运维和综合保障类项目, prefer this formal skeleton:

1. 单位概况
2. 项目概述
3. 数字化与运维现状
4. 项目必要性及服务需求分析
5. 项目服务方案
6. 项目服务内容
7. 项目预算
8. 项目实施与运行管理
9. 其他

Suggested emphasis by chapter:

- 单位概况: 建设单位, 需求单位, 职责边界
- 项目概述: 项目背景, 依据, 范围, 预算, 周期, 总体目标
- 数字化与运维现状: existing systems, assets, platform foundation, current service pain points
- 必要性及需求分析: policy need, continuity need, compliance need, SLA need, staffing and service demand
- 服务方案: service architecture, response mechanism, tool route, standards
- 服务内容: system services, hardware services, database services, security services, emergency services, asset management
- 项目预算: basis, estimates, summaries, payment plan
- 项目实施与运行管理: organization, tendering, schedule, quality, assessment, acceptance, security, confidentiality
- 其他: policy basis, source tables, supplementary lists

## 9. Drafting Rules For Procurement-Derived Reports

- Convert clauses into report prose; do not paste tender wording unchanged.
- Keep procurement facts traceable to chapter claims.
- Use tables for system list, device list, staffing, SLA, assessment, and payment terms.
- Avoid deep module decomposition unless the file actually provides detailed module logic.
- When a chapter lacks supporting source evidence, write a bounded summary and explicitly note the need for supplementary materials.
- Do not treat procurement scope as sufficient evidence for a full建设型或升级改造型可研.
- If the source pack lacks current-state survey, business-process diagnosis, target-state scheme, or investment-estimate basis, do not fabricate them with generic consulting language.
- Do not output placeholder-heavy tables such as `待补充 / 待统计 / 待评估` in a supposed completed report. Either omit the table or mark the subsection as preliminary.
- For upgrade projects, write around the chain `existing limitation -> upgrade objective -> construction task -> expected improvement`. If this chain cannot be supported, say so.
- If the user wants a requirements-oriented report, keep the formal可研 structure but make the middle chapters read like a system requirements specification:
  - per-system function summary
  - per-system建设/运维要求
  - business process support points
  - data and interface requirements
  - performance, availability, backup, emergency, and security requirements
  - acceptance and output-document requirements
- When the source supports module-level detail, continue downward:
  - per-module business purpose
  - per-module handled items or function points
  - per-module workflow or coordination logic
  - per-module data, reporting, interface, monitoring, or control requirements
  - per-module expected support effect
- Do not stop at “系统包括A、B、C模块”. That is only the opening sentence of a subsection, not the subsection itself.
- Use lists and tables only as a summary layer. The main explanation must be paragraph-led.
- If the prose begins to look like a procurement requirement digest or checklist, rewrite the section into causal explanatory paragraphs.

## 10. Specific Failure Pattern Seen In The Latest Draft

Observed draft: `市发改委信息化升级改造项目可行性研究报告.md`

Key problems:

- It reads like a procurement-derived interpretation memo, not a true feasibility report.
- It uses many generic statements such as “采用主流前端框架”“采用微服务架构”“优化用户体验”“提升系统性能”, none of which are evidenced by the source pack.
- It contains visible placeholders and shell tables such as `待补充`, `待统计`, `待评估`.
- It substitutes abstract checklist sections for actual diagnosis, such as broad policy, business, and technical “needs” that are not tied to the present-state evidence.
- It creates a formal chapter shell for current state, design, and construction content without sufficient project-specific substance.

Required correction:

- For similar source conditions, prefer a conservative formal draft with explicit evidence gaps over a falsely complete report.
- Reduce empty tables and generic requirement lists.
- Increase analytical prose that explains what is known, what is inferred, and what still needs authoritative supplement.

## 11. New Writing Direction: Skeleton Plus Requirements

For some users, the target is not a macro feasibility memo, but a `formal可研框架 + 系统需求说明书式正文`.

In that mode:

- Chapter 2 and 3 still establish project background and current state.
- Chapter 4 and Chapter 6 become the main requirement-expansion zones and should usually be the longest parts of the report.
- Each important system should be expanded beyond its name and scope into its module set and concrete function points when the evidence supports that level.
- Each important module should be written as a small explanatory unit:
  - what business problem it serves
  - what users or roles use it
  - what tasks or事项 it handles
  - what data, interface, reporting, or control relationships it must support
  - what improvement or support effect it is expected to produce
- If the generated text still looks like “module list + short gloss”, the expansion is insufficient.

## 12. Append-Only Long-Form Rule

Long reports should be drafted as cumulative documents, not repeatedly regenerated documents.

- Round 0 produces only the baseline package and staged plan.
- Round 1 writes only the first bounded prose package.
- Round 2 and later must:
  - read the current accumulated draft
  - locate the append anchor
  - write only the next bounded section
  - return only the new content to append

Do not:

- restart from Chapter 1 in later rounds
- rebuild the table of contents in later rounds
- restate previous chapters for context
- return a whole new full-report body when the task is continuation

If the next target scope is too large, split it again by system family, module family, or heading family rather than broadening the output.
- Chapter 4 should focus on requirement梳理 rather than broad slogan-style necessity.
- Chapter 5 should explain how the requirement set is translated into solution boundaries and design principles.
- Chapter 6 should become the most detailed chapter, organized by system or service domain, and should explain what each system must support, maintain, process, integrate, secure, monitor, and deliver.
- Chapter 7 and 8 should still exist, but they should align with the extracted requirement set, SLA, acceptance, and document outputs.
- Inside Chapter 6, do not leave the content at the level of requirement bullets or summary tables. Expand each major system or module into paragraph text that explains:
  - the business or management problem being addressed
  - the function or maintenance capability that must be provided
  - how the requirement supports workflow, data handling, or service continuity
  - what effect the建设或运维内容 should achieve after implementation

This means the parser should not stop at system names. It should surface the actual requirement-bearing text that later chapters can be written from.

## 12. Procurement Extraction Must Produce Chapter Writing Directions

When the source package is a procurement or tender file, extraction must not stop at factual fields and system lists.

It must also produce chapter-oriented writing guidance, at minimum:

- Chapter 2 direction:
  - project scope
  - construction or service objects
  - overall goals
  - cycle and budget cap
  - high-level expected benefits and constraints
- Chapter 3 direction:
  - what existing systems, devices, data, and security foundation can be evidenced
  - what current-state information is still missing and must not be fabricated
- Chapter 4 direction:
  - per-system business needs
  - per-system functional needs
  - workflow, data, interface, performance, security, and service-level needs
  - user roles, business volume, or asset volume if extractable
- Chapter 5 direction:
  - how extracted needs imply solution boundaries, design principles, integration direction, data route, or management mechanism
- Chapter 6 direction:
  - per-system writing direction
  - per-module or per-service writing direction
  - what paragraph expansions should explain beyond the checklist
- Chapter 7 direction:
  - what budget categories are evidenced
  - what workload or procurement categories can support estimates
- Chapter 8 direction:
  - staffing, duty roster, response SLA, assessment, acceptance, security, and document-delivery rules

If the parser cannot produce chapter directions, the later drafting step will tend to fall back to generic writing.

These chapter directions are not optional notes. They are the primary drafting brief for the corresponding chapter.

## 13. Per-System Writing Direction

For each system extracted from the procurement file, produce a writing direction note, not just a name.

Each note should answer:

- this system mainly supports which business or management scenario
- this system's extracted functions or maintenance scope
- this system's likely pain point or operational value as implied by the source
- this system's interface, data, monitoring, reporting, backup, or safety obligations if any
- this system should be written in Chapter 4 as what kind of requirement
- this system should be written in Chapter 6 as what kind of construction or maintenance narrative

This is especially important for long reports, because the report length mainly comes from per-system and per-module expansion.

These system directions are not secondary metadata. When drafting Chapter 4 or Chapter 6, they should outrank generic writing habits and generic technology boilerplate.

## 13B. Per-Module Writing Direction

If the source file already implies modules, handled事项, or function points under a system, extraction must continue one layer deeper.

For each module or function cluster, produce writing guidance that answers:

- this module serves which concrete business action or management action
- this module handles which information, document, interface, or reporting flow
- this module solves which local pain point inside the larger system
- this module should be written in Chapter 4 as what kind of requirement point
- this module should be written in Chapter 6 as what kind of建设或运维内容

If this layer is missing from the baseline fact base, later drafting will remain too abstract even when the system-level writing direction is correct.

When module-writing directions exist, Chapter 4 and Chapter 6 should normally continue from:

- chapter direction
- system direction
- module direction

rather than stopping at the system overview level.

## 13A. Requirement-To-Prose Expansion Rule

When the source provides a requirement item, maintenance item, or module name, do not stop at rewriting it once in prose.

Expand it using the strongest evidence-supported dimensions available:

- who uses or depends on it
- in what business or management scenario it appears
- what current problem, delay, blind spot, or control difficulty it addresses
- what capability, function, or保障机制 is required
- what process, data flow, interface flow, or document flow is involved
- what monitoring, reporting, feedback, or control loop is needed
- what result, management value, or risk-control effect is expected

This is the main way to increase depth and useful length without writing filler.

If a generated paragraph only rephrases the requirement item and does not add these dimensions, treat it as under-expanded.

If generated text turns into many short checklist-like sentences, treat that as another failure mode even when the facts are technically correct.

## 14. Long-Form Delivery Workflow

The reference report is about 150,000 Chinese characters, while a single model response is much shorter. Therefore the skill must not try to generate the whole report in one shot.

This is a hard rule, not a preference.

If the requested report is likely to approach reference scale:

- do not attempt one-shot generation
- do not interpret “请输出完整可研” as permission to emit the whole document in one response
- instead switch automatically to staged append-only drafting

Use this staged workflow:

1. Build baseline document package
- source fact base
- chapter writing directions
- per-system writing directions
- outline with depth to at least chapter/subchapter/module level where supported

2. Draft by chapter family
- Round A: Chapter 1-3
- Round B: Chapter 4 necessity and requirement analysis
- Round C: Chapter 5 design scheme
- Round D: Chapter 6 construction content, split by subsystem or module cluster
- Round E: Chapter 7-9

Important:

- each round produces only the new chapter package for that round
- do not re-output prior rounds in full
- do not replace the accumulated draft with the latest round's text
- the accumulated draft should grow by appending new sections after the correct chapter anchor
- each continuation round should be mentally framed as:
  - read current accumulated draft
  - locate append anchor
  - draft next bounded section only
  - append only that new section

3. Expand heavy chapters in multiple passes
- Chapter 4: split by subsystem or analysis topic
- Chapter 6: split by subsystem first, then by module cluster
- after each pass, append into the baseline document before continuing
- before the next pass, read the accumulated draft so the new section continues the existing numbering and style

4. Perform consistency pass
- names
- quantities
- roles
- data objects
- security constraints
- SLA and acceptance rules
- budget-to-scope alignment

5. Produce final stitched report
- only after all chapter pieces are drafted and normalized

## 16. Append-Only Rule For Long Reports

Long-form drafting must follow an append-only rule.

That means:

- Round 1 creates the baseline draft file or baseline text package.
- Round 2 writes only the next chapter family and appends it after the existing content.
- Round 3 writes only the next bounded section and appends it after the proper anchor.
- Later rounds must read the current accumulated draft before writing.

Do not do these things unless the user explicitly asks for revision:

- regenerate the whole report from the beginning
- replace old chapters with a newly generated full version
- output a later round as though it were a fresh complete report

The safe mental model is:

- current accumulated draft = source of truth
- next round output = incremental addition
- final stitched report = accumulated draft plus consistency cleanup
- continuation output must not contain already completed chapter text

## 18. Writing-Direction Priority Rule

When the baseline fact base contains:

- chapter-writing directions
- system-writing directions

then drafting must follow this priority order:

1. current chapter-writing direction
2. current system-writing direction
3. current module-writing direction
4. extracted requirement and fact evidence
5. outline family and sample-derived chapter traits
6. generic style habits

If the generated text follows generic habits but ignores the chapter or system directions, that is a workflow failure.

## 17. One-Shot Long-Report Generation Is Disallowed

For long feasibility reports, especially those benchmarked against reports around 100k+ Chinese characters:

- one-shot full-report generation is disallowed
- the correct behavior is staged output
- if a user asks for a “full report”, interpret that as “deliver the report through multiple append-only rounds until complete”

The only time a one-shot response is acceptable is when the target report is obviously short enough to fit within a normal high-quality single response.

## 15. Target Output Length Strategy

To approach the length and density of the reference report:

- do not aim for one response = one full report
- aim for one response = one bounded chapter cluster or one subsystem package
- Chapter 4 and Chapter 6 should be the most detailed and may need several rounds each
- if the user requests a full report, explain or internally follow a multi-round writing sequence rather than compressing all content into a short generic summary
