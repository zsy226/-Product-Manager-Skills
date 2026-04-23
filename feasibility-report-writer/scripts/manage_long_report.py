#!/usr/bin/env python3
"""
Manage staged long-form feasibility-report drafting artifacts.

This script is intentionally text-first and markdown-first:
- initialize a workflow workspace from a fact base
- scaffold a cumulative report draft with stable heading anchors
- generate phase task packs and update workflow state
- append new content under an existing heading without replacing prior text
- review the cumulative draft for common long-report problems
- convert review findings into targeted revision actions
- batch targeted revision actions into chapter-level or system-level repair packs
- export a clean final report without anchor comments or empty placeholder headings
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


OPS_SKELETON: Sequence[Tuple[str, Sequence[str]]] = (
    ("第一章 单位概况", ("1.1 业务需求单位概况", "1.2 项目单位概况")),
    ("第二章 项目概述", ("2.1 项目名称", "2.2 项目建设单位及负责人", "2.3 项目建设的背景及依据", "2.4 项目建设目标、内容、建设周期", "2.5 项目效益、项目风险与对策", "2.6 项目成效考核目标（规划指标）", "2.7 投资概况")),
    ("第三章 数字化与运维现状", ("3.1 数字化建设基础情况", "3.2 现有应用系统情况", "3.3 现有网络设备及终端情况", "3.4 数据资源与运维支撑现状", "3.5 安全与保密现状")),
    ("第四章 项目必要性及服务需求分析", ("4.1 项目必要性", "4.2 服务目标需求分析", "4.3 业务功能与服务事项分析", "4.4 用户角色与服务对象分析", "4.5 信息量与资源使用分析", "4.6 系统功能与性能需求分析", "4.7 安全与保密需求分析", "4.8 运维与验收需求分析")),
    ("第五章 项目服务方案", ("5.1 服务目标、范围与内容", "5.2 服务体系与支撑架构", "5.3 标准规范与工作机制")),
    ("第六章 项目服务内容", ("6.1 应用系统服务内容", "6.2 数据与接口服务内容", "6.3 基础设施与终端保障内容", "6.4 安全与应急服务内容")),
    ("第七章 项目预算", ("7.1 预算编制说明", "7.2 项目预算测算", "7.3 项目预算分类汇总清单", "7.4 预算使用计划")),
    ("第八章 项目实施与运行管理", ("8.1 组织与管理机制", "8.2 项目招标方案", "8.3 项目实施周期", "8.4 质量、进度与资金管理", "8.5 考核验收与安全保密制度")),
    ("第九章 其他", ("9.1 项目预算编制依据", "9.2 相关支撑材料", "9.3 需补充的研究与证明材料")),
)


CONSTRUCTION_SKELETON: Sequence[Tuple[str, Sequence[str]]] = (
    ("第一章 单位概况", ("1.1 业务需求单位概况", "1.2 项目单位概况")),
    ("第二章 项目概述", ("2.1 项目名称", "2.2 项目建设单位及负责人", "2.3 项目建设背景及依据", "2.4 项目建设目标、内容、周期", "2.5 项目效益、风险与对策", "2.6 项目成效考核目标", "2.7 投资概况")),
    ("第三章 数字化现状", ("3.1 总体框架规划或设想", "3.2 现有应用系统情况", "3.3 现有网络、设备及其他信息资源情况", "3.4 数据资源现状", "3.5 安全建设现状")),
    ("第四章 项目建设必要性及需求分析", ("4.1 项目建设必要性", "4.2 建设目标需求分析", "4.3 业务功能、业务流程、业务量分析", "4.4 用户角色分析", "4.5 信息量分析与预测", "4.6 系统功能与性能需求分析", "4.7 安全需求分析", "4.8 数据需求分析")),
    ("第五章 项目设计方案", ("5.1 建设目标、规模与内容", "5.2 总体架构及技术路线", "5.3 标准规范设计")),
    ("第六章 项目建设内容", ("6.1 应用系统建设", "6.2 数据资源建设", "6.3 安全建设内容", "6.4 配套支撑建设内容")),
    ("第七章 项目预算", ("7.1 预算编制说明", "7.2 项目软硬件购置及应用系统开发投资估算", "7.3 项目预算分类汇总清单", "7.4 预算使用计划")),
    ("第八章 项目建设与运行管理", ("8.1 领导和管理机构", "8.2 项目招标方案", "8.3 项目建设周期", "8.4 项目实施进度、质量与资金管理方案", "8.5 相关管理制度")),
    ("第九章 其他", ("9.1 项目预算编制有关政策、技术、经济资料", "9.2 系统软硬件物理布置图", "9.3 相关研究成果")),
)


PHASES: Sequence[Tuple[str, str]] = (
    ("phase_1_baseline", "搭框架，沉淀基准事实底稿、目录结构和累计总稿骨架"),
    ("phase_2_chapter_draft", "按章节写作方向完成首轮章节写作"),
    ("phase_3_system_append", "按系统写作方向在对应章节下追加系统级扩写"),
    ("phase_4_module_append", "按模块写作方向在对应系统段落下追加模块级扩写"),
    ("phase_5_review_adjust", "对累计总稿进行回顾分析，并把修订内容追加到对应章节锚点"),
)


@dataclass
class Heading:
    level: int
    text: str
    start: int


def compact(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def read_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def normalize_heading_text(value: str) -> str:
    return compact(value).strip("#").strip()


def detect_report_type(payload: Dict[str, object]) -> str:
    project_name = str(((payload.get("project_info") or {}) if isinstance(payload.get("project_info"), dict) else {}).get("项目名称", ""))
    text_parts: List[str] = [project_name]
    for section_values in (payload.get("sections"), payload.get("lists"), payload.get("chapter_writing_directions")):
        if isinstance(section_values, dict):
            for key, value in section_values.items():
                text_parts.append(str(key))
                text_parts.append(json.dumps(value, ensure_ascii=False))
    merged = " ".join(text_parts)
    if any(token in merged for token in ("运维", "保障", "服务", "驻场", "SLA", "响应")):
        return "ops"
    if any(token in merged for token in ("升级", "改造")):
        return "upgrade"
    return "construction"


def skeleton_for(report_type: str) -> Sequence[Tuple[str, Sequence[str]]]:
    if report_type == "ops":
        return OPS_SKELETON
    return CONSTRUCTION_SKELETON


def build_outline_markdown(title: str, report_type: str) -> str:
    lines = [f"# {title} 目录结构", "", f"- 报告类型: `{report_type}`", ""]
    for chapter, subheads in skeleton_for(report_type):
        lines.append(f"## {chapter}")
        lines.append("")
        for subhead in subheads:
            lines.append(f"- {subhead}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_report_skeleton(title: str, report_type: str) -> str:
    lines = [f"# {title}", ""]
    for chapter, subheads in skeleton_for(report_type):
        lines.append(f"## {chapter}")
        lines.append("")
        lines.append(f"<!-- SECTION-ANCHOR: {chapter} -->")
        lines.append("")
        for subhead in subheads:
            lines.append(f"### {subhead}")
            lines.append("")
            lines.append(f"<!-- SECTION-ANCHOR: {subhead} -->")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_baseline_package(payload: Dict[str, object], report_type: str, title: str) -> str:
    project_info = payload.get("project_info") if isinstance(payload.get("project_info"), dict) else {}
    budget_info = payload.get("budget_info") if isinstance(payload.get("budget_info"), dict) else {}
    chapter_dirs = payload.get("chapter_writing_directions") if isinstance(payload.get("chapter_writing_directions"), dict) else {}
    system_dirs = payload.get("system_writing_directions") if isinstance(payload.get("system_writing_directions"), dict) else {}
    module_dirs = payload.get("module_writing_directions") if isinstance(payload.get("module_writing_directions"), dict) else {}
    missing = payload.get("missing_facts") if isinstance(payload.get("missing_facts"), list) else []

    lines = [f"# {title} 长文工作流基线包", ""]
    lines.append("## 1. 报告分类")
    lines.append("")
    lines.append(f"- 报告类型: `{report_type}`")
    lines.append(f"- 目录骨架: `{ '运维/综合保障型' if report_type == 'ops' else '建设/升级改造型' }`")
    lines.append("- 当前包用途: Round 0，仅用于锁定事实底稿、写作方向、阶段计划和累计总稿骨架。")
    lines.append("")

    lines.append("## 2. 基本事实")
    lines.append("")
    if project_info:
        for key, value in project_info.items():
            lines.append(f"- {key}: {value}")
    if budget_info:
        for key, value in budget_info.items():
            lines.append(f"- {key}: {value}")
    if not project_info and not budget_info:
        lines.append("- 待从事实底稿补充。")
    lines.append("")

    lines.append("## 3. 章节写作方向")
    lines.append("")
    if chapter_dirs:
        for chapter, items in chapter_dirs.items():
            lines.append(f"### {chapter}")
            lines.append("")
            if isinstance(items, list):
                for item in items:
                    lines.append(f"- {item}")
            lines.append("")
    else:
        lines.append("- 待补充")
        lines.append("")

    lines.append("## 4. 系统写作方向")
    lines.append("")
    if system_dirs:
        for system_name, items in system_dirs.items():
            lines.append(f"### {system_name}")
            lines.append("")
            if isinstance(items, list):
                for item in items:
                    lines.append(f"- {item}")
            lines.append("")
    else:
        lines.append("- 待补充")
        lines.append("")

    lines.append("## 5. 模块写作方向")
    lines.append("")
    if module_dirs:
        for system_name, module_map in module_dirs.items():
            lines.append(f"### {system_name}")
            lines.append("")
            if isinstance(module_map, dict):
                for module_name, items in module_map.items():
                    lines.append(f"#### {module_name}")
                    lines.append("")
                    if isinstance(items, list):
                        for item in items:
                            lines.append(f"- {item}")
                    lines.append("")
    else:
        lines.append("- 待补充")
        lines.append("")

    lines.append("## 6. 分阶段执行计划")
    lines.append("")
    for phase_id, desc in PHASES:
        lines.append(f"- `{phase_id}`: {desc}")
    lines.append("")

    lines.append("## 7. 待补充事实")
    lines.append("")
    if missing:
        for item in missing:
            lines.append(f"- {item}")
    else:
        lines.append("- 当前未发现必须立即补充的关键缺口，可进入章节分阶段写作。")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_state(title: str, report_type: str, fact_base_json: Path, workspace: Path) -> Dict[str, object]:
    return {
        "title": title,
        "report_type": report_type,
        "fact_base_json": str(fact_base_json),
        "workspace": str(workspace),
        "files": {
            "baseline_package": str((workspace / "00-baseline-package.md").resolve()),
            "outline": str((workspace / "01-outline.md").resolve()),
            "report": str((workspace / "report.md").resolve()),
            "review": str((workspace / "review-notes.md").resolve()),
            "final": str((workspace / "final-report.md").resolve()),
        },
        "phases": [{"id": phase_id, "description": desc, "status": "pending", "task_pack": None} for phase_id, desc in PHASES],
    }


def parse_headings(lines: Sequence[str]) -> List[Heading]:
    headings: List[Heading] = []
    for idx, line in enumerate(lines):
        match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if match:
            headings.append(Heading(level=len(match.group(1)), text=normalize_heading_text(match.group(2)), start=idx))
    return headings


def find_heading(lines: Sequence[str], heading_text: str) -> Heading:
    normalized = normalize_heading_text(heading_text)
    headings = parse_headings(lines)
    for heading in headings:
        if heading.text == normalized:
            return heading
    available = ", ".join(heading.text for heading in headings[:20])
    raise ValueError(f"Heading not found: {heading_text}. Available headings include: {available}")


def section_insert_index(lines: Sequence[str], target: Heading, position: str) -> int:
    if position == "after-heading":
        return target.start + 1

    headings = parse_headings(lines)
    for heading in headings:
        if heading.start <= target.start:
            continue
        if heading.level <= target.level:
            return heading.start
    return len(lines)


def append_under_heading(draft_path: Path, heading_text: str, content: str, position: str) -> None:
    original = draft_path.read_text(encoding="utf-8")
    lines = original.splitlines()
    target = find_heading(lines, heading_text)
    insert_at = section_insert_index(lines, target, position)

    payload = sanitize_append_payload(content, target.text).strip("\n")
    insert_lines = [""] + payload.splitlines() + [""]
    new_lines = lines[:insert_at] + insert_lines + lines[insert_at:]
    draft_path.write_text("\n".join(new_lines).rstrip() + "\n", encoding="utf-8")


def _sanitize_filename(value: str) -> str:
    cleaned = re.sub(r"[^\w\-.一-龥]+", "_", value.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "section"


def _next_ledger_id(ledger_dir: Path) -> int:
    counter_path = ledger_dir / "counter.txt"
    if counter_path.exists():
        try:
            current = int(counter_path.read_text(encoding="utf-8").strip() or "0")
        except ValueError:
            current = 0
    else:
        current = 0
    next_id = current + 1
    counter_path.write_text(str(next_id), encoding="utf-8")
    return next_id


def record_generated_content(ledger_dir: Path, heading_text: str, content: str, source: str) -> Path:
    ledger_dir.mkdir(parents=True, exist_ok=True)
    item_id = _next_ledger_id(ledger_dir)
    heading_slug = _sanitize_filename(heading_text)
    payload_path = ledger_dir / f"{item_id:06d}_{heading_slug}.md"
    index_path = ledger_dir / "index.jsonl"

    clean_content = content.strip()
    payload = [
        f"<!-- HEADING: {heading_text} -->",
        f"<!-- SOURCE: {source} -->",
        f"<!-- CREATED_AT: {datetime.utcnow().isoformat()}Z -->",
        "",
        clean_content,
        "",
    ]
    write_text(payload_path, "\n".join(payload))

    record = {
        "id": item_id,
        "heading": heading_text,
        "source": source,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "path": str(payload_path),
    }
    with index_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return payload_path


def sanitize_append_payload(content: str, target_heading: str) -> str:
    lines = content.strip().splitlines()
    while lines and not compact(lines[0]):
        lines.pop(0)
    while lines and not compact(lines[-1]):
        lines.pop()
    if not lines:
        return ""

    first = lines[0]
    match = re.match(r"^(#{1,6})\s+(.*)$", first)
    if match and normalize_heading_text(match.group(2)) == normalize_heading_text(target_heading):
        lines = lines[1:]
        while lines and not compact(lines[0]):
            lines.pop(0)
    return "\n".join(lines)


def collect_section_body(lines: Sequence[str], heading: Heading) -> List[str]:
    start = heading.start + 1
    end = section_insert_index(lines, heading, "end-of-section")
    return list(lines[start:end])


def review_report(draft_path: Path, outline_path: Optional[Path], min_nonempty_lines: int) -> Tuple[str, Dict[str, object]]:
    text = draft_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    headings = parse_headings(lines)
    issues: List[Dict[str, object]] = []

    outline_headings: List[str] = []
    if outline_path and outline_path.exists():
        outline_headings = [heading.text for heading in parse_headings(outline_path.read_text(encoding="utf-8").splitlines())]

    for heading in headings:
        if heading.level == 1:
            continue
        body = collect_section_body(lines, heading)
        nonempty = [line for line in body if compact(line)]
        body_text = "\n".join(nonempty)
        if len(nonempty) < min_nonempty_lines:
            issues.append({"heading": heading.text, "type": "thin_section", "detail": f"该节非空行数仅 {len(nonempty)}，建议补充段落级分析。"})
        if any(token in body_text for token in ("待补充", "待评估", "待统计")):
            issues.append({"heading": heading.text, "type": "placeholder", "detail": "该节仍包含明显占位词，需要补充事实或改为保守说明。"})
        if "<!-- SECTION-ANCHOR:" in body_text:
            issues.append({"heading": heading.text, "type": "anchor_leak", "detail": "该节正文区域出现锚点注释残留，导出终稿前应清理。"})
        if re.search(r"主流前端框架|微服务架构|优化用户体验|提升系统性能", body_text):
            issues.append({"heading": heading.text, "type": "generic_filler", "detail": "该节包含泛化技术表述，需核对是否有事实依据。"})

    if outline_headings:
        draft_heading_names = {heading.text for heading in headings}
        for heading_name in outline_headings:
            if heading_name not in draft_heading_names:
                issues.append({"heading": heading_name, "type": "missing_heading", "detail": "目录中已有该标题，但累计总稿中尚未出现。"})

    review_lines = [f"# {draft_path.stem} 回顾分析", ""]
    if not issues:
        review_lines.append("- 当前未发现结构性问题，可继续下一轮追加写作。")
        review_lines.append("")
    else:
        for idx, issue in enumerate(issues, start=1):
            review_lines.append(f"## 问题 {idx}: {issue['heading']}")
            review_lines.append("")
            review_lines.append(f"- 类型: `{issue['type']}`")
            review_lines.append(f"- 说明: {issue['detail']}")
            review_lines.append("")

    payload = {"draft": str(draft_path), "issue_count": len(issues), "issues": issues}
    return "\n".join(review_lines).rstrip() + "\n", payload


def find_nearest_existing_heading(heading_name: str, headings: Sequence[str]) -> str:
    normalized = normalize_heading_text(heading_name)
    if normalized in headings:
        return normalized
    for heading in headings:
        if heading.startswith(normalized[:3]) or normalized.startswith(heading[:3]):
            return heading
    return headings[0] if headings else heading_name


def parent_chapter_for_heading(heading_name: str, draft_path: Path) -> str:
    lines = draft_path.read_text(encoding="utf-8").splitlines()
    headings = parse_headings(lines)
    normalized = normalize_heading_text(heading_name)
    target_index = -1
    for idx, heading in enumerate(headings):
        if heading.text == normalized:
            target_index = idx
            break
    if target_index == -1:
        if re.match(r"^第[一二三四五六七八九十]+章", normalized):
            return normalized
        return "未定位章节"
    for idx in range(target_index, -1, -1):
        if headings[idx].level == 2:
            return headings[idx].text
    return "未定位章节"


def remediation_guidance(issue_type: str) -> List[str]:
    if issue_type == "thin_section":
        return [
            "补充该节的分析性正文，至少覆盖现状/问题、建设或服务要求、预期效果三个维度。",
            "避免只补一两句摘要，应形成成段说明。",
        ]
    if issue_type == "placeholder":
        return [
            "清理占位词，改为有事实支撑的正文，或明确说明该节证据不足。",
            "不要在终稿中保留“待补充/待评估/待统计”等显式占位表达。",
        ]
    if issue_type == "generic_filler":
        return [
            "删除泛化技术套话，改写为与当前项目直接相关的能力、流程、数据或控制要求。",
            "如无事实依据，不要保留技术选型判断句。",
        ]
    if issue_type == "missing_heading":
        return [
            "补齐该标题下的正文内容，至少先形成保守版章节说明。",
            "若证据不足，可写明已知事实和待补材料边界，但不能留空。",
        ]
    if issue_type == "anchor_leak":
        return [
            "该问题不需要回写正文，终稿导出时自动清理锚点注释即可。",
        ]
    return ["根据问题说明补充或修订对应章节内容。"]


def build_revision_targets(review_payload: Dict[str, object], draft_path: Path) -> List[Dict[str, object]]:
    issues = review_payload.get("issues")
    if not isinstance(issues, list):
        return []
    headings = list_headings_from_report(draft_path)
    targets: List[Dict[str, object]] = []
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        issue_type = str(issue.get("type", "unknown"))
        heading_name = str(issue.get("heading", "")).strip()
        if issue_type == "anchor_leak":
            targets.append(
                {
                    "type": "cleanup",
                    "heading": heading_name or "export-final",
                    "issue_type": issue_type,
                    "detail": str(issue.get("detail", "")),
                    "action": "run export-final",
                    "guidance": remediation_guidance(issue_type),
                }
            )
            continue
        mapped_heading = find_nearest_existing_heading(heading_name, headings)
        targets.append(
            {
                "type": "revision",
                "heading": mapped_heading,
                "issue_type": issue_type,
                "detail": str(issue.get("detail", "")),
                "action": "append_or_revise_locally",
                "guidance": remediation_guidance(issue_type),
            }
        )
    return targets


def build_revision_task_pack(workspace: Path, review_json_path: Path, output_path: Optional[Path] = None) -> Tuple[Path, Path]:
    state = load_state(workspace)
    files = state.get("files") if isinstance(state.get("files"), dict) else {}
    report_path = Path(str(files.get("report"))).resolve()
    review_payload = read_json(review_json_path)
    targets = build_revision_targets(review_payload, report_path)

    revision_json_path = output_path.with_suffix(".json") if output_path else (workspace / "task-packs" / "phase_5_review_adjust.targets.json")
    revision_md_path = output_path if output_path else (workspace / "task-packs" / "phase_5_review_adjust.generated.md")
    revision_md_path.parent.mkdir(parents=True, exist_ok=True)

    lines = ["# phase_5_review_adjust 修订任务包", ""]
    lines.append(f"- 累计总稿: `{report_path}`")
    lines.append(f"- 回顾结果: `{review_json_path}`")
    lines.append("- 处理原则: 逐条定位、局部修订、禁止整篇重写。")
    lines.append("")
    if targets:
        for idx, target in enumerate(targets, start=1):
            lines.append(f"## 修订任务 {idx}: {target['heading']}")
            lines.append("")
            lines.append(f"- 类型: `{target['type']}`")
            lines.append(f"- 问题类型: `{target['issue_type']}`")
            lines.append(f"- 动作: `{target['action']}`")
            lines.append(f"- 问题说明: {target['detail']}")
            lines.append("- 修订建议:")
            for item in target["guidance"]:
                lines.append(f"  - {item}")
            lines.append("")
    else:
        lines.append("- 当前 review 结果未生成可执行修订项。")
        lines.append("")

    write_text(revision_md_path, "\n".join(lines).rstrip() + "\n")
    write_text(revision_json_path, json.dumps({"review_json": str(review_json_path), "targets": targets}, ensure_ascii=False, indent=2) + "\n")

    phase = find_phase(state, "phase_5_review_adjust")
    phase["task_pack"] = str(revision_md_path)
    phase["status"] = "in_progress"
    save_state(workspace, state)
    return revision_md_path, revision_json_path


def build_batched_revision_pack(
    workspace: Path,
    targets_json_path: Path,
    group_by: str,
    max_items_per_batch: int,
    output_path: Optional[Path] = None,
) -> Tuple[Path, Path]:
    state = load_state(workspace)
    files = state.get("files") if isinstance(state.get("files"), dict) else {}
    report_path = Path(str(files.get("report"))).resolve()
    payload = read_json(targets_json_path)
    targets = payload.get("targets")
    if not isinstance(targets, list):
        targets = []

    grouped: Dict[str, List[Dict[str, object]]] = {}
    for target in targets:
        if not isinstance(target, dict):
            continue
        heading = str(target.get("heading", "")).strip() or "未命名修订项"
        if group_by == "chapter":
            group_key = parent_chapter_for_heading(heading, report_path)
        else:
            system_name = target.get("system")
            group_key = str(system_name).strip() if system_name else parent_chapter_for_heading(heading, report_path)
        grouped.setdefault(group_key, []).append(target)

    batches: List[Dict[str, object]] = []
    batch_index = 1
    for group_key, items in grouped.items():
        for start in range(0, len(items), max_items_per_batch):
            chunk = items[start : start + max_items_per_batch]
            batches.append({"batch_id": f"batch_{batch_index:03d}", "group": group_key, "items": chunk})
            batch_index += 1

    batch_md_path = output_path if output_path else (workspace / "task-packs" / f"phase_5_review_adjust.batched-by-{group_by}.md")
    batch_json_path = batch_md_path.with_suffix(".json")
    batch_md_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [f"# phase_5_review_adjust 批次修订包（按{group_by}聚合）", ""]
    lines.append(f"- 累计总稿: `{report_path}`")
    lines.append(f"- 修订目标来源: `{targets_json_path}`")
    lines.append(f"- 聚合方式: `{group_by}`")
    lines.append(f"- 每批最大项数: `{max_items_per_batch}`")
    lines.append("")
    if not batches:
        lines.append("- 当前没有可聚合的修订项。")
        lines.append("")
    else:
        for batch in batches:
            lines.append(f"## {batch['batch_id']} {batch['group']}")
            lines.append("")
            lines.append("- 处理原则: 本批次内的问题应尽量一次性统筹修订，避免逐条零散回写。")
            lines.append("- 涉及条目:")
            for item in batch["items"]:
                lines.append(f"  - heading=`{item.get('heading', '')}` issue_type=`{item.get('issue_type', '')}` action=`{item.get('action', '')}`")
                detail = str(item.get("detail", "")).strip()
                if detail:
                    lines.append(f"    说明: {detail}")
            lines.append("")

    write_text(batch_md_path, "\n".join(lines).rstrip() + "\n")
    write_text(batch_json_path, json.dumps({"group_by": group_by, "max_items_per_batch": max_items_per_batch, "batches": batches}, ensure_ascii=False, indent=2) + "\n")

    phase = find_phase(state, "phase_5_review_adjust")
    phase["batched_task_pack"] = str(batch_md_path)
    save_state(workspace, state)
    return batch_md_path, batch_json_path


def extract_system_or_module_names(text: str, fact_payload: Dict[str, object]) -> Tuple[List[str], List[Tuple[str, str]]]:
    systems: List[str] = []
    modules: List[Tuple[str, str]] = []
    sys_dirs = system_direction_map(fact_payload)
    mod_dirs = module_direction_map(fact_payload)
    for system_name in sys_dirs.keys():
        if system_name and system_name in text and system_name not in systems:
            systems.append(system_name)
    for system_name, module_map in mod_dirs.items():
        if isinstance(module_map, dict):
            for module_name in module_map.keys():
                if module_name and module_name in text:
                    modules.append((system_name, module_name))
                    if system_name not in systems:
                        systems.append(system_name)
    return systems, modules


def build_batch_prompt_pack(workspace: Path, batches_json_path: Path, output_dir: Optional[Path] = None) -> List[Path]:
    fact_payload = read_json(Path(str(load_state(workspace)["fact_base_json"])))
    batch_payload = read_json(batches_json_path)
    batches = batch_payload.get("batches")
    if not isinstance(batches, list):
        batches = []

    output_root = output_dir if output_dir else (workspace / "task-packs" / "prompt-packs")
    output_root.mkdir(parents=True, exist_ok=True)
    created: List[Path] = []

    chapter_dirs = chapter_direction_map(fact_payload)
    system_dirs = system_direction_map(fact_payload)
    module_dirs = module_direction_map(fact_payload)

    for batch in batches:
        if not isinstance(batch, dict):
            continue
        batch_id = str(batch.get("batch_id", "batch_unknown"))
        group_name = str(batch.get("group", "未分组"))
        items = batch.get("items")
        if not isinstance(items, list):
            items = []

        summary_text = " ".join(
            f"{item.get('heading', '')} {item.get('detail', '')}" for item in items if isinstance(item, dict)
        )
        systems, modules = extract_system_or_module_names(summary_text, fact_payload)

        lines = [f"# {batch_id} 写作提示包", ""]
        lines.append(f"- 批次分组: `{group_name}`")
        lines.append("- 用途: 直接作为本批次修订写作的输入说明。")
        lines.append("- 输出要求: 只生成本批次新增或局部修订内容，不重写整章。")
        lines.append("")

        lines.append("## 1. 目标锚点")
        lines.append("")
        seen_headings = set()
        for item in items:
            if not isinstance(item, dict):
                continue
            heading = str(item.get("heading", "")).strip()
            if heading and heading not in seen_headings:
                lines.append(f"- `{heading}`")
                seen_headings.add(heading)
        lines.append("")

        lines.append("## 2. 问题摘要")
        lines.append("")
        for item in items:
            if not isinstance(item, dict):
                continue
            lines.append(f"- heading=`{item.get('heading', '')}` type=`{item.get('issue_type', '')}`: {item.get('detail', '')}")
        lines.append("")

        if group_name in chapter_dirs:
            lines.append(f"## 3. 章节写作方向: {group_name}")
            lines.append("")
            for text in chapter_dirs[group_name]:
                lines.append(f"- {text}")
            lines.append("")

        if systems:
            lines.append("## 4. 相关系统写作方向")
            lines.append("")
            for system_name in systems:
                if system_name in system_dirs:
                    lines.append(f"### {system_name}")
                    lines.append("")
                    for text in system_dirs[system_name]:
                        lines.append(f"- {text}")
                    lines.append("")

        if modules:
            lines.append("## 5. 相关模块写作方向")
            lines.append("")
            for system_name, module_name in modules:
                if system_name in module_dirs and isinstance(module_dirs[system_name], dict) and module_name in module_dirs[system_name]:
                    lines.append(f"### {system_name} / {module_name}")
                    lines.append("")
                    for text in module_dirs[system_name][module_name]:
                        lines.append(f"- {text}")
                    lines.append("")

        lines.append("## 6. 本批次写作约束")
        lines.append("")
        lines.append("- 只修当前批次覆盖的锚点，不延伸重写其他章节。")
        lines.append("- 优先补足分析性正文，避免条目式回写。")
        lines.append("- 如果问题属于占位词或泛化表述，修订时应替换为证据支撑的表述。")
        lines.append("- 如果某个问题仅与终稿清理有关，不要往正文补清理性文字。")
        lines.append("")

        lines.append("## 7. 期望输出格式")
        lines.append("")
        lines.append("- 一个或多个可直接 append 的 Markdown 片段")
        lines.append("- 每个片段从目标锚点下的下一级标题或正文开始")
        lines.append("- 不重复输出已经存在的完整章节标题")
        lines.append("")

        pack_path = output_root / f"{batch_id}.md"
        write_text(pack_path, "\n".join(lines).rstrip() + "\n")
        created.append(pack_path)

    state = load_state(workspace)
    phase = find_phase(state, "phase_5_review_adjust")
    phase["prompt_pack_dir"] = str(output_root)
    save_state(workspace, state)
    return created


def parse_prompt_pack(prompt_pack_path: Path) -> Dict[str, object]:
    lines = prompt_pack_path.read_text(encoding="utf-8").splitlines()
    batch_id = ""
    targets: List[str] = []
    current_section = ""
    for line in lines:
        if line.startswith("# "):
            batch_id = line.replace("#", "", 1).strip().split(" ", 1)[0]
        elif line.startswith("## "):
            current_section = line.replace("##", "", 1).strip()
        elif current_section.startswith("1. 目标锚点") and line.strip().startswith("- `") and line.strip().endswith("`"):
            targets.append(line.strip()[3:-1])
    return {"batch_id": batch_id or prompt_pack_path.stem, "targets": targets}


def build_draft_templates_from_prompt_packs(workspace: Path, prompt_pack_dir: Path, output_dir: Optional[Path] = None) -> Tuple[List[Path], Path]:
    output_root = output_dir if output_dir else (workspace / "task-packs" / "draft-templates")
    output_root.mkdir(parents=True, exist_ok=True)
    append_map: Dict[str, object] = {"templates": []}
    created: List[Path] = []

    for prompt_pack_path in sorted(prompt_pack_dir.glob("*.md")):
        parsed = parse_prompt_pack(prompt_pack_path)
        batch_id = str(parsed["batch_id"])
        targets = parsed["targets"] if isinstance(parsed.get("targets"), list) else []
        template_lines = [f"# {batch_id} 修订草稿模板", ""]
        template_lines.append(f"- 来源提示包: `{prompt_pack_path}`")
        template_lines.append("- 使用方式: 直接在每个锚点下填写新增或局部修订内容，完成后可按锚点逐段 append。")
        template_lines.append("")

        for target in targets:
            template_lines.append(f"## TARGET: {target}")
            template_lines.append("")
            template_lines.append(f"<!-- APPEND-HEADING: {target} -->")
            template_lines.append("")
            template_lines.append("<!-- 在此填写该锚点下的新增或修订内容。不要重复整章标题。 -->")
            template_lines.append("")

        template_path = output_root / f"{batch_id}.md"
        write_text(template_path, "\n".join(template_lines).rstrip() + "\n")
        created.append(template_path)
        append_map["templates"].append(
            {
                "batch_id": batch_id,
                "prompt_pack": str(prompt_pack_path),
                "draft_template": str(template_path),
                "targets": [{"heading": target, "position": "end-of-section"} for target in targets],
            }
        )

    append_map_path = output_root / "append-map.json"
    write_text(append_map_path, json.dumps(append_map, ensure_ascii=False, indent=2) + "\n")

    state = load_state(workspace)
    phase = find_phase(state, "phase_5_review_adjust")
    phase["draft_template_dir"] = str(output_root)
    phase["append_map"] = str(append_map_path)
    save_state(workspace, state)
    return created, append_map_path


def parse_template_blocks(template_path: Path) -> List[Tuple[str, str]]:
    lines = template_path.read_text(encoding="utf-8").splitlines()
    blocks: List[Tuple[str, List[str]]] = []
    current_heading: Optional[str] = None
    current_lines: List[str] = []

    for line in lines:
        if line.startswith("## TARGET: "):
            if current_heading is not None:
                blocks.append((current_heading, current_lines))
            current_heading = line.replace("## TARGET: ", "", 1).strip()
            current_lines = []
            continue
        if current_heading is not None:
            current_lines.append(line)
    if current_heading is not None:
        blocks.append((current_heading, current_lines))

    parsed: List[Tuple[str, str]] = []
    for heading, raw_lines in blocks:
        cleaned = [line for line in raw_lines if not re.match(r"^\s*<!--.*-->\s*$", line)]
        while cleaned and not compact(cleaned[0]):
            cleaned.pop(0)
        while cleaned and not compact(cleaned[-1]):
            cleaned.pop()
        if cleaned:
            parsed.append((heading, "\n".join(cleaned)))
    return parsed


def apply_draft_template(draft_path: Path, template_path: Path, position: str = "end-of-section") -> Tuple[int, List[str]]:
    blocks = parse_template_blocks(template_path)
    applied = 0
    headings: List[str] = []
    for heading, content in blocks:
        append_under_heading(draft_path, heading, content, position)
        applied += 1
        headings.append(heading)
    return applied, headings


def command_init(args: argparse.Namespace) -> int:
    fact_base_json = Path(args.fact_base_json).expanduser().resolve()
    workspace = Path(args.workspace).expanduser().resolve()
    payload = read_json(fact_base_json)

    report_type = args.report_type or detect_report_type(payload)
    title = args.title or str(((payload.get("project_info") or {}) if isinstance(payload.get("project_info"), dict) else {}).get("项目名称", fact_base_json.stem))

    workspace.mkdir(parents=True, exist_ok=True)
    baseline_path = workspace / "00-baseline-package.md"
    outline_path = workspace / "01-outline.md"
    report_path = workspace / "report.md"
    state_path = workspace / "workflow-state.json"

    write_text(baseline_path, build_baseline_package(payload, report_type, title))
    write_text(outline_path, build_outline_markdown(title, report_type))
    write_text(report_path, build_report_skeleton(title, report_type))
    write_text(state_path, json.dumps(build_state(title, report_type, fact_base_json, workspace), ensure_ascii=False, indent=2) + "\n")

    print(f"WORKFLOW_DIR: {workspace}")
    print(f"BASELINE_PACKAGE: {baseline_path}")
    print(f"OUTLINE: {outline_path}")
    print(f"REPORT_DRAFT: {report_path}")
    print(f"WORKFLOW_STATE: {state_path}")
    print("NEXT_STEP: Fill the first bounded prose package and append it into report.md under the target heading.")
    return 0


def load_state(workspace: Path) -> Dict[str, object]:
    state_path = workspace / "workflow-state.json"
    if not state_path.exists():
        raise ValueError(f"workflow-state.json not found under {workspace}")
    state = read_json(state_path)
    files = state.get("files")
    if not isinstance(files, dict):
        files = {}
        state["files"] = files
    files.setdefault("baseline_package", str((workspace / "00-baseline-package.md").resolve()))
    files.setdefault("outline", str((workspace / "01-outline.md").resolve()))
    files.setdefault("report", str((workspace / "report.md").resolve()))
    files.setdefault("review", str((workspace / "review-notes.md").resolve()))
    files.setdefault("final", str((workspace / "final-report.md").resolve()))

    phases = state.get("phases")
    if not isinstance(phases, list):
        phases = []
        state["phases"] = phases
    known = {phase.get("id"): phase for phase in phases if isinstance(phase, dict)}
    normalized_phases: List[Dict[str, object]] = []
    for phase_id, desc in PHASES:
        current = known.get(phase_id, {})
        normalized_phases.append(
            {
                "id": phase_id,
                "description": current.get("description", desc),
                "status": current.get("status", "pending"),
                "task_pack": current.get("task_pack"),
                "note": current.get("note"),
                "batched_task_pack": current.get("batched_task_pack"),
                "prompt_pack_dir": current.get("prompt_pack_dir"),
                "draft_template_dir": current.get("draft_template_dir"),
                "append_map": current.get("append_map"),
            }
        )
    state["phases"] = normalized_phases
    return state


def save_state(workspace: Path, state: Dict[str, object]) -> Path:
    state_path = workspace / "workflow-state.json"
    write_text(state_path, json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    return state_path


def find_phase(state: Dict[str, object], phase_id: str) -> Dict[str, object]:
    phases = state.get("phases")
    if not isinstance(phases, list):
        raise ValueError("Invalid workflow state: phases missing")
    for phase in phases:
        if isinstance(phase, dict) and phase.get("id") == phase_id:
            return phase
    raise ValueError(f"Phase not found: {phase_id}")


def list_headings_from_report(report_path: Path) -> List[str]:
    return [heading.text for heading in parse_headings(report_path.read_text(encoding="utf-8").splitlines())]


def chapter_direction_map(payload: Dict[str, object]) -> Dict[str, List[str]]:
    value = payload.get("chapter_writing_directions")
    return value if isinstance(value, dict) else {}


def system_direction_map(payload: Dict[str, object]) -> Dict[str, List[str]]:
    value = payload.get("system_writing_directions")
    return value if isinstance(value, dict) else {}


def module_direction_map(payload: Dict[str, object]) -> Dict[str, Dict[str, List[str]]]:
    value = payload.get("module_writing_directions")
    return value if isinstance(value, dict) else {}


def infer_default_targets(phase_id: str, report_path: Path, fact_payload: Dict[str, object]) -> List[Dict[str, object]]:
    headings = list_headings_from_report(report_path)
    chapter_dirs = chapter_direction_map(fact_payload)
    system_dirs = system_direction_map(fact_payload)
    module_dirs = module_direction_map(fact_payload)

    if phase_id == "phase_2_chapter_draft":
        targets: List[Dict[str, object]] = []
        for heading in headings:
            if heading in chapter_dirs:
                targets.append({"heading": heading, "type": "chapter"})
        return targets[:3] if targets else [{"heading": "第一章 单位概况", "type": "chapter"}, {"heading": "第二章 项目概述", "type": "chapter"}, {"heading": "第三章 数字化与运维现状", "type": "chapter"}]

    if phase_id == "phase_3_system_append":
        targets = []
        preferred_heading = "第六章 项目服务内容" if "第六章 项目服务内容" in headings else "第六章 项目建设内容"
        for system_name in system_dirs.keys():
            targets.append({"heading": preferred_heading, "system": system_name, "type": "system"})
        return targets

    if phase_id == "phase_4_module_append":
        targets = []
        preferred_heading = "第六章 项目服务内容" if "第六章 项目服务内容" in headings else "第六章 项目建设内容"
        for system_name, modules in module_dirs.items():
            if isinstance(modules, dict):
                for module_name in modules.keys():
                    targets.append({"heading": preferred_heading, "system": system_name, "module": module_name, "type": "module"})
        return targets

    if phase_id == "phase_5_review_adjust":
        return [{"heading": "report-wide", "type": "review"}]

    return []


def build_task_pack(workspace: Path, phase_id: str, targets: Optional[List[Dict[str, object]]]) -> Path:
    state = load_state(workspace)
    fact_payload = read_json(Path(str(state["fact_base_json"])))
    files = state.get("files") if isinstance(state.get("files"), dict) else {}
    report_path = Path(str(files.get("report"))).resolve()
    baseline_path = Path(str(files.get("baseline_package"))).resolve()
    review_path = Path(str(files.get("review"))).resolve()
    phase = find_phase(state, phase_id)

    actual_targets = targets or infer_default_targets(phase_id, report_path, fact_payload)
    task_dir = workspace / "task-packs"
    task_dir.mkdir(parents=True, exist_ok=True)
    task_path = task_dir / f"{phase_id}.md"

    lines = [f"# {phase_id} 任务包", ""]
    lines.append(f"- 阶段说明: {phase.get('description')}")
    lines.append(f"- 累计总稿: `{report_path}`")
    lines.append(f"- 基线包: `{baseline_path}`")
    lines.append("- 输出规则: 只产出本轮新增内容，不要重写既有章节。")
    lines.append("- 交付格式: 生成单独 Markdown 内容文件，再通过 append 命令落入累计总稿。")
    lines.append("")

    if phase_id == "phase_5_review_adjust":
        lines.append("## 本轮输入")
        lines.append("")
        lines.append(f"- 回顾分析文件: `{review_path}`")
        lines.append("- 目标: 按问题定位进行局部补写或局部修订，避免整篇回写。")
        lines.append("")

    lines.append("## 目标锚点")
    lines.append("")
    if actual_targets:
        for item in actual_targets:
            parts = [f"`{item.get('type', 'task')}`"]
            if item.get("heading"):
                parts.append(f"heading=`{item['heading']}`")
            if item.get("system"):
                parts.append(f"system=`{item['system']}`")
            if item.get("module"):
                parts.append(f"module=`{item['module']}`")
            lines.append(f"- {'，'.join(parts)}")
    else:
        lines.append("- 本阶段暂未自动识别到目标锚点，请手工补充。")
    lines.append("")

    lines.append("## 写作依据")
    lines.append("")
    chapter_dirs = chapter_direction_map(fact_payload)
    system_dirs = system_direction_map(fact_payload)
    module_dirs = module_direction_map(fact_payload)
    for item in actual_targets:
        heading = item.get("heading")
        system_name = item.get("system")
        module_name = item.get("module")
        if heading and heading in chapter_dirs:
            lines.append(f"### 章节方向: {heading}")
            lines.append("")
            for text in chapter_dirs.get(heading, []):
                lines.append(f"- {text}")
            lines.append("")
        if system_name and system_name in system_dirs:
            lines.append(f"### 系统方向: {system_name}")
            lines.append("")
            for text in system_dirs.get(system_name, []):
                lines.append(f"- {text}")
            lines.append("")
        if system_name and module_name and system_name in module_dirs and isinstance(module_dirs[system_name], dict) and module_name in module_dirs[system_name]:
            lines.append(f"### 模块方向: {system_name} / {module_name}")
            lines.append("")
            for text in module_dirs[system_name].get(module_name, []):
                lines.append(f"- {text}")
            lines.append("")

    write_text(task_path, "\n".join(lines).rstrip() + "\n")
    phase["task_pack"] = str(task_path)
    phase["status"] = "in_progress"
    save_state(workspace, state)
    return task_path


def command_append(args: argparse.Namespace) -> int:
    draft_path = Path(args.draft).expanduser().resolve()
    content_path = Path(args.content_file).expanduser().resolve()
    content = content_path.read_text(encoding="utf-8")
    append_under_heading(draft_path, args.heading, content, args.position)
    ledger_dir = Path(args.ledger_dir).expanduser().resolve() if args.ledger_dir else draft_path.parent / "generated-sections"
    ledger_path = record_generated_content(ledger_dir, args.heading, content, f"append:{content_path.name}")
    print(f"UPDATED_DRAFT: {draft_path}")
    print(f"APPEND_HEADING: {args.heading}")
    print(f"CONTENT_FILE: {content_path}")
    print(f"LEDGER_ITEM: {ledger_path}")
    return 0


def command_task_pack(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).expanduser().resolve()
    targets = None
    if args.targets_json:
        targets = json.loads(Path(args.targets_json).expanduser().resolve().read_text(encoding="utf-8"))
    task_path = build_task_pack(workspace, args.phase_id, targets)
    print(f"TASK_PACK: {task_path}")
    print(f"PHASE_ID: {args.phase_id}")
    return 0


def command_revise_from_review(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).expanduser().resolve()
    review_json_path = Path(args.review_json).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve() if args.output else None
    revision_md_path, revision_json_path = build_revision_task_pack(workspace, review_json_path, output_path)
    print(f"REVISION_TASK_PACK: {revision_md_path}")
    print(f"REVISION_TARGETS_JSON: {revision_json_path}")
    return 0


def command_batch_revisions(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).expanduser().resolve()
    targets_json_path = Path(args.targets_json).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve() if args.output else None
    batch_md_path, batch_json_path = build_batched_revision_pack(workspace, targets_json_path, args.group_by, args.max_items_per_batch, output_path)
    print(f"BATCHED_REVISION_PACK: {batch_md_path}")
    print(f"BATCHED_REVISION_JSON: {batch_json_path}")
    return 0


def command_prompt_packs(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).expanduser().resolve()
    batches_json_path = Path(args.batches_json).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else None
    created = build_batch_prompt_pack(workspace, batches_json_path, output_dir)
    print(f"PROMPT_PACK_COUNT: {len(created)}")
    for path in created:
        print(f"PROMPT_PACK: {path}")
    return 0


def command_draft_templates(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).expanduser().resolve()
    prompt_pack_dir = Path(args.prompt_pack_dir).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else None
    created, append_map_path = build_draft_templates_from_prompt_packs(workspace, prompt_pack_dir, output_dir)
    print(f"DRAFT_TEMPLATE_COUNT: {len(created)}")
    for path in created:
        print(f"DRAFT_TEMPLATE: {path}")
    print(f"APPEND_MAP: {append_map_path}")
    return 0


def command_apply_draft_template(args: argparse.Namespace) -> int:
    draft_path = Path(args.draft).expanduser().resolve()
    template_path = Path(args.template).expanduser().resolve()
    applied, headings = apply_draft_template(draft_path, template_path, args.position)
    ledger_dir = Path(args.ledger_dir).expanduser().resolve() if args.ledger_dir else draft_path.parent / "generated-sections"
    blocks = parse_template_blocks(template_path)
    for heading, content in blocks:
        record_generated_content(ledger_dir, heading, content, f"apply-draft-template:{template_path.name}")
    print(f"UPDATED_DRAFT: {draft_path}")
    print(f"TEMPLATE: {template_path}")
    print(f"APPLIED_BLOCKS: {applied}")
    for heading in headings:
        print(f"APPLIED_HEADING: {heading}")
    return 0


def command_mark_phase(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).expanduser().resolve()
    state = load_state(workspace)
    phase = find_phase(state, args.phase_id)
    phase["status"] = args.status
    if args.note:
        phase["note"] = args.note
    state_path = save_state(workspace, state)
    print(f"WORKFLOW_STATE: {state_path}")
    print(f"PHASE_ID: {args.phase_id}")
    print(f"STATUS: {args.status}")
    return 0


def command_review(args: argparse.Namespace) -> int:
    draft_path = Path(args.draft).expanduser().resolve()
    outline_path = Path(args.outline).expanduser().resolve() if args.outline else None
    review_md, payload = review_report(draft_path, outline_path, args.min_nonempty_lines)
    review_path = Path(args.output).expanduser().resolve() if args.output else draft_path.with_name("review-notes.md")
    review_json = review_path.with_suffix(".json")
    write_text(review_path, review_md)
    write_text(review_json, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(f"REVIEW_MARKDOWN: {review_path}")
    print(f"REVIEW_JSON: {review_json}")
    print(f"ISSUE_COUNT: {payload['issue_count']}")
    return 0


def strip_anchor_comments(lines: Sequence[str]) -> List[str]:
    return [line for line in lines if not re.match(r"^\s*<!--\s*SECTION-ANCHOR:", line)]


def is_heading_line(line: str) -> bool:
    return bool(re.match(r"^(#{1,6})\s+.+$", line))


def clean_final_report_text(text: str) -> str:
    lines = strip_anchor_comments(text.splitlines())
    headings = parse_headings(lines)
    if not headings:
        return "\n".join(lines).rstrip() + "\n"

    keep_line_indexes = {0}
    for heading in headings:
        body = collect_section_body(lines, heading)
        meaningful = [line for line in body if compact(line) and not is_heading_line(line)]
        if meaningful:
            keep_line_indexes.add(heading.start)

    result: List[str] = []
    for idx, line in enumerate(lines):
        if is_heading_line(line) and idx not in keep_line_indexes:
            continue
        result.append(line)

    compacted: List[str] = []
    blank_run = 0
    for line in result:
        if compact(line):
            compacted.append(line)
            blank_run = 0
        else:
            blank_run += 1
            if blank_run <= 1:
                compacted.append("")
    return "\n".join(compacted).strip() + "\n"


def _read_ledger_index(ledger_dir: Path) -> List[Dict[str, object]]:
    index_path = ledger_dir / "index.jsonl"
    if not index_path.exists():
        return []
    entries: List[Dict[str, object]] = []
    for line in index_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
            if isinstance(item, dict):
                entries.append(item)
        except json.JSONDecodeError:
            continue
    entries.sort(key=lambda x: int(x.get("id", 0)))
    return entries


def _ledger_heading_counts(ledger_entries: Sequence[Dict[str, object]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for entry in ledger_entries:
        heading = str(entry.get("heading", "")).strip()
        if not heading:
            continue
        counts[heading] = counts.get(heading, 0) + 1
    return counts


def _last_ledger_heading(ledger_entries: Sequence[Dict[str, object]]) -> Optional[str]:
    if not ledger_entries:
        return None
    last = ledger_entries[-1]
    heading = str(last.get("heading", "")).strip()
    return heading or None


def _chapter_headings_in_order(headings: Sequence[Heading]) -> List[str]:
    return [heading.text for heading in headings if heading.level == 2 and re.match(r"^第[一二三四五六七八九十]+章", heading.text)]


def _all_non_title_headings_in_order(headings: Sequence[Heading]) -> List[str]:
    return [heading.text for heading in headings if heading.level >= 2]


def _detect_active_phase(state: Dict[str, object]) -> str:
    phases = state.get("phases")
    if isinstance(phases, list):
        for phase in phases:
            if isinstance(phase, dict) and phase.get("status") == "in_progress":
                phase_id = str(phase.get("id", "")).strip()
                if phase_id:
                    return phase_id
        for phase_id, _ in PHASES:
            try:
                phase = find_phase(state, phase_id)
            except ValueError:
                continue
            if str(phase.get("status", "pending")) == "pending":
                return phase_id
    return PHASES[0][0]


def _next_unwritten_heading(
    headings_in_order: Sequence[str],
    ledger_heading_counts: Dict[str, int],
    fallback_to_next_after_last: bool = True,
    last_heading: Optional[str] = None,
) -> Optional[str]:
    for heading in headings_in_order:
        if ledger_heading_counts.get(heading, 0) == 0:
            return heading
    if fallback_to_next_after_last and last_heading and last_heading in headings_in_order:
        idx = list(headings_in_order).index(last_heading)
        if idx + 1 < len(headings_in_order):
            return list(headings_in_order)[idx + 1]
    return None


def _section_meaningful_lines(lines: Sequence[str], heading: Heading) -> List[str]:
    body = collect_section_body(lines, heading)
    meaningful: List[str] = []
    for line in body:
        if not compact(line):
            continue
        if is_heading_line(line):
            continue
        if re.match(r"^\s*<!--.*-->\s*$", line):
            continue
        meaningful.append(line)
    return meaningful


def _heading_end_indices(headings: Sequence[Heading], total_lines: int) -> List[int]:
    ends: List[int] = []
    for idx, heading in enumerate(headings):
        end = total_lines
        for next_heading in headings[idx + 1 :]:
            if next_heading.level <= heading.level:
                end = next_heading.start
                break
        ends.append(end)
    return ends


def _heading_direct_meaningful_lines(lines: Sequence[str], headings: Sequence[Heading], ends: Sequence[int], idx: int) -> List[str]:
    heading = headings[idx]
    start = heading.start + 1
    end = ends[idx]
    child_ranges: List[Tuple[int, int]] = []
    for j in range(idx + 1, len(headings)):
        child = headings[j]
        if child.start >= end:
            break
        if child.level > heading.level:
            child_ranges.append((child.start, ends[j]))

    meaningful: List[str] = []
    for line_idx in range(start, end):
        if any(r_start <= line_idx < r_end for r_start, r_end in child_ranges):
            continue
        line = lines[line_idx]
        if not compact(line):
            continue
        if is_heading_line(line):
            continue
        if re.match(r"^\s*<!--.*-->\s*$", line):
            continue
        meaningful.append(line)
    return meaningful


def ledger_doctor_check(draft_path: Path, ledger_dir: Path) -> Tuple[str, Dict[str, object]]:
    report_lines = draft_path.read_text(encoding="utf-8").splitlines()
    headings = parse_headings(report_lines)
    ends = _heading_end_indices(headings, len(report_lines))
    report_headings = {heading.text for heading in headings}
    report_content_sections: Dict[str, List[str]] = {}
    for idx, heading in enumerate(headings):
        if heading.level == 1:
            continue
        meaningful = _heading_direct_meaningful_lines(report_lines, headings, ends, idx)
        if meaningful:
            report_content_sections[heading.text] = meaningful

    ledger_entries = _read_ledger_index(ledger_dir) if ledger_dir.exists() else []
    ledger_heading_counts: Dict[str, int] = {}
    for entry in ledger_entries:
        heading = str(entry.get("heading", "")).strip()
        if heading:
            ledger_heading_counts[heading] = ledger_heading_counts.get(heading, 0) + 1

    missing_ledger_for_report_content: List[Dict[str, object]] = []
    for heading, lines in report_content_sections.items():
        if ledger_heading_counts.get(heading, 0) == 0:
            missing_ledger_for_report_content.append(
                {
                    "heading": heading,
                    "sample": lines[0][:160],
                    "line_count": len(lines),
                }
            )

    ledger_heading_not_in_report: List[Dict[str, object]] = []
    for heading, count in ledger_heading_counts.items():
        if heading not in report_headings:
            ledger_heading_not_in_report.append({"heading": heading, "ledger_count": count})

    issues_total = len(missing_ledger_for_report_content) + len(ledger_heading_not_in_report)
    status = "ok" if issues_total == 0 else "issues_found"

    lines: List[str] = [f"# Ledger Doctor: {draft_path.name}", ""]
    lines.append(f"- 状态: `{status}`")
    lines.append(f"- report 有正文章节数: `{len(report_content_sections)}`")
    lines.append(f"- ledger 记录数: `{len(ledger_entries)}`")
    lines.append("")

    lines.append("## 缺失账本记录的章节")
    lines.append("")
    if missing_ledger_for_report_content:
        for item in missing_ledger_for_report_content:
            lines.append(f"- `{item['heading']}`: 正文行数 {item['line_count']}，示例: {item['sample']}")
    else:
        lines.append("- 未发现此类问题。")
    lines.append("")

    lines.append("## 账本中存在但 report 不存在的章节")
    lines.append("")
    if ledger_heading_not_in_report:
        for item in ledger_heading_not_in_report:
            lines.append(f"- `{item['heading']}`: ledger 记录 {item['ledger_count']} 条")
    else:
        lines.append("- 未发现此类问题。")
    lines.append("")

    payload = {
        "status": status,
        "draft": str(draft_path),
        "ledger_dir": str(ledger_dir),
        "report_content_section_count": len(report_content_sections),
        "ledger_entry_count": len(ledger_entries),
        "missing_ledger_for_report_content": missing_ledger_for_report_content,
        "ledger_heading_not_in_report": ledger_heading_not_in_report,
        "issue_count": issues_total,
    }
    return "\n".join(lines).rstrip() + "\n", payload


def _render_final_from_ledger(draft_path: Path, ledger_dir: Path) -> str:
    lines = draft_path.read_text(encoding="utf-8").splitlines()
    headings = parse_headings(lines)
    if not headings:
        return ""

    entries = _read_ledger_index(ledger_dir)
    by_heading: Dict[str, List[str]] = {}
    for entry in entries:
        heading = str(entry.get("heading", "")).strip()
        payload_path = Path(str(entry.get("path", "")))
        if not heading or not payload_path.exists():
            continue
        payload_lines = payload_path.read_text(encoding="utf-8").splitlines()
        content_lines = [ln for ln in payload_lines if not re.match(r"^\s*<!--.*-->\s*$", ln)]
        content = "\n".join(content_lines).strip()
        if content:
            by_heading.setdefault(heading, []).append(content)

    out: List[str] = []
    title = headings[0].text if headings[0].level == 1 else "可行性研究报告"
    out.append(f"# {title}")
    out.append("")

    for heading in headings:
        if heading.level == 1:
            continue
        bucket = by_heading.get(heading.text, [])
        if not bucket:
            continue
        out.append("#" * heading.level + f" {heading.text}")
        out.append("")
        for i, block in enumerate(bucket):
            out.append(block.strip())
            out.append("")
            if i != len(bucket) - 1:
                out.append("")

    return "\n".join(out).strip() + "\n"


def command_export_final(args: argparse.Namespace) -> int:
    draft_path = Path(args.draft).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve() if args.output else draft_path.with_name("final-report.md")
    ledger_dir = Path(args.ledger_dir).expanduser().resolve() if args.ledger_dir else draft_path.parent / "generated-sections"
    clean_text = ""
    if ledger_dir.exists():
        clean_text = _render_final_from_ledger(draft_path, ledger_dir)
    if not clean_text.strip():
        clean_text = clean_final_report_text(draft_path.read_text(encoding="utf-8"))
    write_text(output_path, clean_text)
    print(f"FINAL_REPORT: {output_path}")
    if ledger_dir.exists():
        print(f"LEDGER_DIR: {ledger_dir}")
    return 0


def command_ledger_doctor(args: argparse.Namespace) -> int:
    draft_path = Path(args.draft).expanduser().resolve()
    ledger_dir = Path(args.ledger_dir).expanduser().resolve() if args.ledger_dir else draft_path.parent / "generated-sections"
    output_path = Path(args.output).expanduser().resolve() if args.output else draft_path.with_name("ledger-doctor.md")
    json_path = Path(args.json_output).expanduser().resolve() if args.json_output else output_path.with_suffix(".json")

    report_md, payload = ledger_doctor_check(draft_path, ledger_dir)
    write_text(output_path, report_md)
    write_text(json_path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")

    print(f"LEDGER_DOCTOR_MARKDOWN: {output_path}")
    print(f"LEDGER_DOCTOR_JSON: {json_path}")
    print(f"STATUS: {payload['status']}")
    print(f"ISSUE_COUNT: {payload['issue_count']}")
    if args.fail_on_issues and int(payload["issue_count"]) > 0:
        return 2
    return 0


def command_round_status(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).expanduser().resolve()
    state = load_state(workspace)
    files = state.get("files") if isinstance(state.get("files"), dict) else {}
    report_path = Path(str(files.get("report"))).resolve()
    ledger_dir = Path(args.ledger_dir).expanduser().resolve() if args.ledger_dir else report_path.parent / "generated-sections"

    lines = report_path.read_text(encoding="utf-8").splitlines()
    headings = parse_headings(lines)
    chapter_headings = _chapter_headings_in_order(headings)
    all_headings = _all_non_title_headings_in_order(headings)

    ledger_entries = _read_ledger_index(ledger_dir) if ledger_dir.exists() else []
    counts = _ledger_heading_counts(ledger_entries)
    last_heading = _last_ledger_heading(ledger_entries)
    active_phase = args.phase_id or _detect_active_phase(state)

    next_chapter = _next_unwritten_heading(chapter_headings, counts, True, last_heading)
    next_any = _next_unwritten_heading(all_headings, counts, True, last_heading)

    print(f"WORKSPACE: {workspace}")
    print(f"REPORT_DRAFT: {report_path}")
    print(f"LEDGER_DIR: {ledger_dir}")
    print(f"ACTIVE_PHASE: {active_phase}")
    print(f"TOTAL_HEADINGS: {len(all_headings)}")
    print(f"TOTAL_CHAPTERS: {len(chapter_headings)}")
    print(f"LEDGER_ENTRIES: {len(ledger_entries)}")
    print(f"LAST_APPENDED_HEADING: {last_heading or 'N/A'}")
    print(f"NEXT_UNWRITTEN_CHAPTER: {next_chapter or 'N/A'}")
    print(f"NEXT_UNWRITTEN_HEADING: {next_any or 'N/A'}")
    return 0


def command_next_scope(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).expanduser().resolve()
    state = load_state(workspace)
    files = state.get("files") if isinstance(state.get("files"), dict) else {}
    report_path = Path(str(files.get("report"))).resolve()
    ledger_dir = Path(args.ledger_dir).expanduser().resolve() if args.ledger_dir else report_path.parent / "generated-sections"

    active_phase = args.phase_id or _detect_active_phase(state)
    headings = parse_headings(report_path.read_text(encoding="utf-8").splitlines())
    ledger_entries = _read_ledger_index(ledger_dir) if ledger_dir.exists() else []
    counts = _ledger_heading_counts(ledger_entries)
    last_heading = _last_ledger_heading(ledger_entries)

    if args.prefer == "chapter":
        scope_pool = _chapter_headings_in_order(headings)
    elif args.prefer == "heading":
        scope_pool = _all_non_title_headings_in_order(headings)
    else:
        scope_pool = _all_non_title_headings_in_order(headings)
        if active_phase in ("phase_2_chapter_draft", "phase_5_review_adjust"):
            scope_pool = _chapter_headings_in_order(headings)

    next_scope = _next_unwritten_heading(scope_pool, counts, True, last_heading)
    if not next_scope and scope_pool:
        next_scope = scope_pool[-1]

    if not next_scope:
        print("NEXT_SCOPE: N/A")
        print("NEXT_STEP: Run review and export-final, or verify outline/report consistency.")
        return 0

    temp_path = args.content_file or "/tmp/round-next.md"
    print(f"ACTIVE_PHASE: {active_phase}")
    print(f"LAST_APPENDED_HEADING: {last_heading or 'N/A'}")
    print(f"NEXT_SCOPE: {next_scope}")
    print(f"SUGGESTED_CONTENT_FILE: {temp_path}")
    print("SUGGESTED_APPEND_COMMAND:")
    print(
        f"python3 scripts/manage_long_report.py append --draft {report_path} "
        f"--heading \"{next_scope}\" --content-file {temp_path}"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage staged long-form feasibility-report drafting.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize long-report workflow artifacts from a fact-base JSON file.")
    init_parser.add_argument("--fact-base-json", required=True, help="Path to <source>.fact-base.json")
    init_parser.add_argument("--workspace", required=True, help="Output workflow directory")
    init_parser.add_argument("--report-type", choices=("ops", "construction", "upgrade"), help="Override detected report type")
    init_parser.add_argument("--title", help="Override report title")
    init_parser.set_defaults(func=command_init)

    append_parser = subparsers.add_parser("append", help="Append new content under an existing markdown heading.")
    append_parser.add_argument("--draft", required=True, help="Path to cumulative report draft markdown")
    append_parser.add_argument("--heading", required=True, help="Exact target heading text")
    append_parser.add_argument("--content-file", required=True, help="Markdown file containing only the new content to append")
    append_parser.add_argument("--position", choices=("end-of-section", "after-heading"), default="end-of-section", help="Insert position under the heading")
    append_parser.add_argument("--ledger-dir", help="Optional append-only generated-content ledger directory")
    append_parser.set_defaults(func=command_append)

    task_pack_parser = subparsers.add_parser("task-pack", help="Generate a task pack for a workflow phase and mark it in progress.")
    task_pack_parser.add_argument("--workspace", required=True, help="Workflow workspace directory")
    task_pack_parser.add_argument("--phase-id", required=True, choices=[phase_id for phase_id, _ in PHASES], help="Phase id to prepare")
    task_pack_parser.add_argument("--targets-json", help="Optional JSON file containing explicit targets")
    task_pack_parser.set_defaults(func=command_task_pack)

    mark_phase_parser = subparsers.add_parser("mark-phase", help="Update phase status in workflow-state.json.")
    mark_phase_parser.add_argument("--workspace", required=True, help="Workflow workspace directory")
    mark_phase_parser.add_argument("--phase-id", required=True, choices=[phase_id for phase_id, _ in PHASES], help="Phase id to update")
    mark_phase_parser.add_argument("--status", required=True, choices=("pending", "in_progress", "completed", "blocked"), help="New phase status")
    mark_phase_parser.add_argument("--note", help="Optional status note")
    mark_phase_parser.set_defaults(func=command_mark_phase)

    revise_parser = subparsers.add_parser("revise-from-review", help="Convert review JSON findings into targeted revision tasks.")
    revise_parser.add_argument("--workspace", required=True, help="Workflow workspace directory")
    revise_parser.add_argument("--review-json", required=True, help="Path to review-notes.json")
    revise_parser.add_argument("--output", help="Optional output markdown path for revision task pack")
    revise_parser.set_defaults(func=command_revise_from_review)

    batch_parser = subparsers.add_parser("batch-revisions", help="Group revision targets into batched repair packs.")
    batch_parser.add_argument("--workspace", required=True, help="Workflow workspace directory")
    batch_parser.add_argument("--targets-json", required=True, help="Path to phase_5_review_adjust.targets.json")
    batch_parser.add_argument("--group-by", choices=("chapter", "system"), default="chapter", help="How to group revision targets")
    batch_parser.add_argument("--max-items-per-batch", type=int, default=8, help="Maximum revision items in one batch")
    batch_parser.add_argument("--output", help="Optional output markdown path for batched pack")
    batch_parser.set_defaults(func=command_batch_revisions)

    prompt_pack_parser = subparsers.add_parser("prompt-packs", help="Generate ready-to-write prompt packs for each batched repair pack.")
    prompt_pack_parser.add_argument("--workspace", required=True, help="Workflow workspace directory")
    prompt_pack_parser.add_argument("--batches-json", required=True, help="Path to batched revision json")
    prompt_pack_parser.add_argument("--output-dir", help="Optional output directory for prompt packs")
    prompt_pack_parser.set_defaults(func=command_prompt_packs)

    draft_template_parser = subparsers.add_parser("draft-templates", help="Generate draft templates and append maps from prompt packs.")
    draft_template_parser.add_argument("--workspace", required=True, help="Workflow workspace directory")
    draft_template_parser.add_argument("--prompt-pack-dir", required=True, help="Directory containing prompt pack markdown files")
    draft_template_parser.add_argument("--output-dir", help="Optional output directory for draft templates")
    draft_template_parser.set_defaults(func=command_draft_templates)

    apply_template_parser = subparsers.add_parser("apply-draft-template", help="Apply a filled draft template into the cumulative report by APPEND-HEADING blocks.")
    apply_template_parser.add_argument("--draft", required=True, help="Path to cumulative report draft markdown")
    apply_template_parser.add_argument("--template", required=True, help="Path to a filled draft template markdown")
    apply_template_parser.add_argument("--position", choices=("end-of-section", "after-heading"), default="end-of-section", help="Insert position under each heading")
    apply_template_parser.add_argument("--ledger-dir", help="Optional append-only generated-content ledger directory")
    apply_template_parser.set_defaults(func=command_apply_draft_template)

    review_parser = subparsers.add_parser("review", help="Review the cumulative report for common long-report issues.")
    review_parser.add_argument("--draft", required=True, help="Path to cumulative report draft markdown")
    review_parser.add_argument("--outline", help="Optional outline markdown for heading completeness checks")
    review_parser.add_argument("--output", help="Optional output markdown path for review notes")
    review_parser.add_argument("--min-nonempty-lines", type=int, default=4, help="Minimum non-empty lines expected in a section before flagging it as thin")
    review_parser.set_defaults(func=command_review)

    export_parser = subparsers.add_parser("export-final", help="Export a clean final report without anchor comments or empty placeholder headings.")
    export_parser.add_argument("--draft", required=True, help="Path to cumulative report draft markdown")
    export_parser.add_argument("--output", help="Optional output path for final clean report")
    export_parser.add_argument("--ledger-dir", help="Optional generated-content ledger directory; if present export is merged from append-only ledger")
    export_parser.set_defaults(func=command_export_final)

    doctor_parser = subparsers.add_parser("ledger-doctor", help="Check for report content that is missing corresponding ledger records.")
    doctor_parser.add_argument("--draft", required=True, help="Path to cumulative report draft markdown")
    doctor_parser.add_argument("--ledger-dir", help="Optional generated-content ledger directory")
    doctor_parser.add_argument("--output", help="Optional markdown output path")
    doctor_parser.add_argument("--json-output", help="Optional json output path")
    doctor_parser.add_argument("--fail-on-issues", action="store_true", help="Exit non-zero when issues are found")
    doctor_parser.set_defaults(func=command_ledger_doctor)

    round_status_parser = subparsers.add_parser("round-status", help="Show current long-report drafting progress and next likely anchor.")
    round_status_parser.add_argument("--workspace", required=True, help="Workflow workspace directory")
    round_status_parser.add_argument("--phase-id", choices=[phase_id for phase_id, _ in PHASES], help="Optional phase override for status display")
    round_status_parser.add_argument("--ledger-dir", help="Optional generated-content ledger directory")
    round_status_parser.set_defaults(func=command_round_status)

    next_scope_parser = subparsers.add_parser("next-scope", help="Suggest the next bounded scope and a ready-to-run append command.")
    next_scope_parser.add_argument("--workspace", required=True, help="Workflow workspace directory")
    next_scope_parser.add_argument("--phase-id", choices=[phase_id for phase_id, _ in PHASES], help="Optional phase override for scope suggestion")
    next_scope_parser.add_argument("--ledger-dir", help="Optional generated-content ledger directory")
    next_scope_parser.add_argument("--prefer", choices=("auto", "chapter", "heading"), default="auto", help="Scope granularity preference")
    next_scope_parser.add_argument("--content-file", help="Optional suggested content file path shown in output")
    next_scope_parser.set_defaults(func=command_next_scope)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
