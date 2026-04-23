#!/usr/bin/env python3
"""
Build a feasibility-report fact base from procurement/source files.

Supported inputs:
- PDF files via pdftotext fallback
- TXT / MD files
- DOCX files via python-docx

Default outputs:
- <source>.fact-base.md
- <source>.fact-base.json
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


FIELD_PATTERNS: Sequence[Tuple[str, Sequence[str]]] = (
    ("项目名称", (r"项目名称[:：]\s*(.+)",)),
    ("项目编号", (r"项目编号[:：]\s*([A-Za-z0-9\-]+)",)),
    ("预算编号", (r"预算编号[:：]\s*([A-Za-z0-9\-]+)",)),
    ("采购单位", (r"采\s*购\s*单\s*位[:：]\s*(.+)", r"采购人信息[\s\S]{0,30}?名\s*称[:：]?\s*(.+)")),
    ("需求单位", (r"需求单位[:：]\s*(.+)",)),
    ("采购代理机构", (r"采购代理机构[:：]\s*(.+)",)),
    ("预算金额", (r"预算金额[（(]元[）)][:：]?\s*([^\n]+)", r"预算总金额[:：]\s*([^\n]+)")),
    ("最高限价", (r"最高限价[（(]元[）)][:：]?\s*([^\n]+)", r"采购金额[（(]最高限价[）)][:：]\s*([^\n]+)")),
    ("合同履行期限", (r"合同履行期限[:：]\s*([^\n]+)", r"运维期限[:：]\s*([^\n]+)")),
    ("运维地点", (r"运维地点[:：]\s*([^\n]+)", r"项目建设地点[:：]\s*([^\n]+)")),
    ("采购方式", (r"采购方式[:：]\s*([^\n]+)",)),
    ("联系方式", (r"联系方式[:：]\s*([^\n]+)",)),
)


SECTION_PATTERNS: Sequence[Tuple[str, Sequence[str]]] = (
    ("服务范围", ("服务范围", "采购需求", "项目需求", "主要工作内容")),
    ("系统与资产清单", ("维护清单", "软件系统维护服务清单", "桌面运维设备维护清单", "系统重要等级")),
    ("人员配置", ("人员要求", "项目团队", "运维服务团队", "人员配置")),
    ("服务指标与考核", ("服务质量考核要求", "考核标准", "响应时间", "非设备故障解决率")),
    ("付款与验收", ("付款方式", "服务费支付方式", "验收", "支付合同总价款")),
    ("安全与保密要求", ("保密", "安全", "无犯罪记录证明", "背景调查", "漏洞", "密码应用")),
)


def compact(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" ：:")


def compact_text_block(value: str) -> str:
    text = value.replace("\x0c", " ")
    text = re.sub(r"\s*\n\s*", "", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(?<=[\u4e00-\u9fff])\d{1,3}(?=[\u4e00-\u9fff])", "", text)
    return text.strip()


def normalize_lines(text: str) -> List[str]:
    out: List[str] = []
    for raw in text.splitlines():
        line = compact(raw.replace("\x0c", " "))
        if line:
            out.append(line)
    return out


def read_pdf(path: Path) -> str:
    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        raise RuntimeError("pdftotext is required to parse PDF files")

    result = subprocess.run([pdftotext, str(path), "-"], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "pdftotext failed")
    return result.stdout


def read_docx(path: Path) -> str:
    try:
        from docx import Document  # type: ignore
    except ImportError as exc:
        raise RuntimeError("python-docx is required to parse DOCX files") from exc

    doc = Document(path)
    parts: List[str] = []
    for p in doc.paragraphs:
        text = (p.text or "").strip()
        if text:
            parts.append(text)
    for table in doc.tables:
        for row in table.rows:
            cells = [compact(cell.text.replace("\n", " / ")) for cell in row.cells]
            if any(cells):
                parts.append(" | ".join(cells))
    return "\n".join(parts)


def read_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return read_pdf(path)
    if suffix == ".docx":
        return read_docx(path)
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8")
    raise RuntimeError(f"Unsupported file type: {suffix}")


def first_match(text: str, patterns: Sequence[str]) -> Optional[str]:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.MULTILINE)
        if match:
            return compact(match.group(1))
    return None


def collect_fields(text: str) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    for label, patterns in FIELD_PATTERNS:
        value = first_match(text, patterns)
        if value:
            fields[label] = value
    return fields


def extract_lines_with_keywords(lines: Sequence[str], keywords: Sequence[str], limit: int = 12) -> List[str]:
    hits: List[str] = []
    for line in lines:
        if any(keyword in line for keyword in keywords):
            hits.append(line)
    deduped: List[str] = []
    seen = set()
    for item in hits:
        if item not in seen:
            deduped.append(item)
            seen.add(item)
        if len(deduped) >= limit:
            break
    return deduped


def collect_sections(lines: Sequence[str]) -> Dict[str, List[str]]:
    sections: Dict[str, List[str]] = {}
    for label, keywords in SECTION_PATTERNS:
        sections[label] = extract_lines_with_keywords(lines, keywords)
    return sections


def normalize_heading_title(title: str) -> str:
    value = compact(title)
    if value in {"统）", "目）"}:
        return value
    if value.endswith("系") or value.endswith("项"):
        return value
    return value


def find_line_index(lines: Sequence[str], needle: str) -> int:
    for idx, line in enumerate(lines):
        if needle in line:
            return idx
    return -1


def slice_until_next_major_heading(lines: Sequence[str], start_idx: int, max_lines: int = 180) -> List[str]:
    if start_idx < 0:
        return []
    chunk: List[str] = []
    for line in lines[start_idx : start_idx + max_lines]:
        if chunk and re.match(r"^[一二三四五六七八九十]+、", line):
            break
        chunk.append(line)
    return chunk


def slice_between(lines: Sequence[str], start_needle: str, end_needle: str, max_lines: int = 220) -> List[str]:
    start = find_line_index(lines, start_needle)
    if start == -1:
        return []
    end = find_line_index(lines[start + 1 :], end_needle)
    if end == -1:
        return lines[start : start + max_lines]
    absolute_end = start + 1 + end
    return lines[start:absolute_end]


def merge_wrapped_lines(lines: Sequence[str]) -> List[str]:
    merged: List[str] = []
    pending = ""
    for line in lines:
        value = compact(line)
        if not value:
            continue
        if re.match(r"^3\.1\.\d+\s+", value):
            if pending:
                merged.append(pending)
                pending = ""
            merged.append(value)
            continue
        if pending:
            value = pending + value
            pending = ""
        if value.endswith(("系", "统", "项", "护", "模", "维", "块", "容", "办", "景", "应", "况")) and not re.search(r"[。；：]$", value):
            pending = value
            continue
        merged.append(value)
    if pending:
        merged.append(pending)
    return merged


def cleanup_list_items(items: Sequence[str]) -> List[str]:
    cleaned: List[str] = []
    seen = set()
    for item in items:
        value = compact(item)
        if not value:
            continue
        if value.endswith("（2026 年运维项"):
            value = value + "目）"
        if re.fullmatch(r"[\d.]+", value):
            continue
        if value in {"软件系统维护", "服务", "硬件维护服务", "桌面终端运维", "视频会议运维"}:
            continue
        if value in {"序号", "项目名称", "系统名称", "数量", "单位", "服务名称", "名称", "类别", "品牌", "型号"}:
            continue
        if len(value) <= 2:
            continue
        if value.startswith("第") and "章" in value:
            continue
        if value.startswith("项目需求") or value.startswith("采购需求"):
            continue
        if value.startswith("详见附件") or value.startswith("详见第四章"):
            continue
        if value.startswith("成交办法") or value.startswith("磋商小组"):
            continue
        if value in {"（2026 年运维项目）", "目）", "统）"}:
            continue
        if value.startswith("员会") or value.startswith("统事业单位") or value.startswith("保护信息系统"):
            continue
        if value.endswith("招"):
            continue
        if value not in seen:
            cleaned.append(value)
            seen.add(value)
    return cleaned


def merge_parenthetical_suffix(items: Sequence[str]) -> List[str]:
    merged: List[str] = []
    for item in items:
        value = compact(item)
        if not value:
            continue
        if value.startswith("（") and merged:
            merged[-1] = compact(merged[-1] + value)
            continue
        merged.append(value)
    return merged


def split_repeated_shanghai_prefix(item: str) -> List[str]:
    marker = "上海市"
    first = item.find(marker)
    second = item.find(marker, first + len(marker)) if first != -1 else -1
    if first != -1 and second != -1:
        return [compact(item[:second]), compact(item[second:])]
    return [item]


def extract_sentence_items(text: str, start_marker: str, end_marker: str) -> List[str]:
    pattern = re.escape(start_marker) + r"([\s\S]+?)" + re.escape(end_marker)
    match = re.search(pattern, text)
    if not match:
        return []
    block = compact_text_block(match.group(1))
    parts = [compact(part) for part in re.split(r"[、，]", block)]
    return cleanup_list_items(parts)


def extract_service_scope(lines: Sequence[str]) -> List[str]:
    chunk = slice_between(lines, "二、服务范围", "2.1 系统重要等级", max_lines=100)
    results: List[str] = []
    for line in chunk:
        if line in {"二、服务范围", "序号", "服务项目", "软件系统维护", "硬件维护服务"}:
            continue
        if any(token in line for token in ("升级改造项目", "升级改造）", "运维项目", "子系统", "门户网站", "数据中台", "服务", "通用业务办理系统", "通用业务办理平台", "招聘平台", "项目管理系统", "考核系统")):
            results.append(line)
    return cleanup_list_items(merge_parenthetical_suffix(results))


def extract_system_list(text: str, lines: Sequence[str]) -> List[str]:
    paragraph_items: List[str] = []
    paragraph_items.extend(extract_sentence_items(text, "本项目重要信息系统清单为：", "。"))
    paragraph_items.extend(extract_sentence_items(text, "本项目一般信息系统清单为：", "。"))
    paragraph_items.extend(extract_service_scope(lines))

    chunk = slice_between(lines, "1、软件系统维护服务清单", "2、硬件维护服务清单", max_lines=160)
    if not chunk:
        start = find_line_index(lines, "1、软件系统维护服务清单")
        if start == -1:
            start = find_line_index(lines, "软件系统维护服务清单")
        chunk = slice_until_next_major_heading(lines, start, max_lines=140)
    results: List[str] = []
    pending = ""
    for line in chunk:
        if line in {"1、软件系统维护服务清单", "序号", "项目名称", "系统名称", "数量", "单位"}:
            continue
        if re.fullmatch(r"\d+(\.\d+)?", line) or re.fullmatch(r"\d+(\.\d+)?\s*人月", line) or line == "人月":
            continue
        candidate = line
        if pending:
            candidate = pending + line
            pending = ""
        if any(token in candidate for token in ("系统", "平台", "网站", "子系统", "数据中台")):
            results.append(candidate)
        elif any(line.endswith(suffix) for suffix in ("服务热", "招聘", "项目管", "办理", "员会课题申报", "评估", "决策支撑", "项", "系")):
            pending = line
    seed_items = paragraph_items if paragraph_items else results
    merged = cleanup_list_items(merge_parenthetical_suffix(seed_items))
    normalized: List[str] = []
    seen = set()
    for item in merged:
        for part in split_repeated_shanghai_prefix(item):
            part = re.sub(r"(?<=[\u4e00-\u9fff])\d{1,3}(?=[\u4e00-\u9fff])", "", part)
            if part.endswith("（2026 年运维项"):
                part = part + "目）"
            if part in {"办理平台（升级改造）", "评估系统", "考核系统", "热线系统（社情民意调查系统）", "项目管理系统（2026 年运维项目）", "办理系统（2026 年运维项目）"}:
                continue
            if part in {"上海市发展改革委系统", "上海市各区节能降碳考核系统（2026"}:
                continue
            if part.endswith("（2026") or part.endswith("招"):
                continue
            if not (part.startswith("上海市") or part.startswith("上海石油") or part.startswith("进博")):
                continue
            if part not in seen:
                normalized.append(part)
                seen.add(part)
    return normalized


def extract_device_list(lines: Sequence[str]) -> List[str]:
    chunk = slice_between(lines, "3、桌面运维设备维护清单", "三、软件系统运维需求", max_lines=80)
    if not chunk:
        start = find_line_index(lines, "3、桌面运维设备维护清单")
        if start == -1:
            start = find_line_index(lines, "桌面运维设备维护清单")
        chunk = slice_until_next_major_heading(lines, start, max_lines=80)
    results: List[str] = []
    current: List[str] = []
    for line in chunk:
        if line in {"3、桌面运维设备维护清单", "序号", "名称", "类别", "品牌", "型号", "数量"}:
            continue
        if re.fullmatch(r"\d+", line):
            if current:
                results.append(" ".join(current))
                current = []
            continue
        if any(token in line for token in ("PC 机", "打印机", "联想", "惠普", "光电通", "M630Z", "M613B-D326", "Laserjet", "OEP400DN")):
            current.append(line)
    if current:
        results.append(" ".join(current))
    return cleanup_list_items(results)


def extract_basis_list(lines: Sequence[str]) -> List[str]:
    start = find_line_index(lines, "1.3 编制依据")
    if start == -1:
        return []
    chunk = lines[start : start + 80]
    results: List[str] = []
    for line in chunk:
        if re.match(r"^\d+[.、]\s*", line):
            results.append(re.sub(r"^\d+[.、]\s*", "", line))
    return cleanup_list_items(results)


def split_cn_enumeration(text: str) -> List[str]:
    parts = re.split(r"[一二三四五六七八九十]+是", text)
    cleaned = [compact(part.strip(" 。；;")) for part in parts if compact(part)]
    return cleaned


def split_feature_items(text: str) -> List[str]:
    value = compact_text_block(text)
    value = re.sub(r"^(包括|主要提供)", "", value)
    value = re.sub(r"(等模块功能|等功能|模块功能维护|功能维护|相关内容的维护|相关内容|内容的维护|内容维护|日常维护)$", "", value)
    parts = [compact(part) for part in re.split(r"[、，,；;]", value)]
    cleaned: List[str] = []
    seen = set()
    for part in parts:
        if not part or len(part) <= 1:
            continue
        if part in {"主要提供", "包括", "形成", "维护"}:
            continue
        if part not in seen:
            cleaned.append(part)
            seen.add(part)
    return cleaned


def split_function_points(items: Sequence[str]) -> List[str]:
    points: List[str] = []
    seen = set()
    for item in items:
        fragments = re.split(r"[、，,；;]", compact_text_block(item))
        for fragment in fragments:
            value = compact(fragment)
            if not value or len(value) <= 1:
                continue
            if value in {"四项维护内容", "三块维护内容", "两块维护内容", "两项维护内容", "三项维护内容"}:
                continue
            if value not in seen:
                points.append(value)
                seen.add(value)
    return points


def extract_system_requirement_blocks(lines: Sequence[str]) -> Dict[str, Dict[str, object]]:
    chunk = slice_between(lines, "3.1 应用系统维护内容", "3.2 日常维护业务需求", max_lines=260)
    if not chunk:
        return {}
    merged_chunk = merge_wrapped_lines(chunk)
    blocks: Dict[str, List[str]] = {}
    current_name: Optional[str] = None
    i = 0
    while i < len(merged_chunk):
        line = merged_chunk[i]
        match = re.match(r"^3\.1\.\d+\s+(.+)$", line)
        if match:
            current_name = normalize_heading_title(match.group(1))
            if current_name.endswith(("系", "项")) and i + 1 < len(merged_chunk):
                next_line = merged_chunk[i + 1]
                if len(next_line) <= 8 and not re.match(r"^3\.", next_line):
                    current_name = compact(current_name + next_line)
                    i += 1
            blocks[current_name] = []
            i += 1
            continue
        if current_name:
            blocks[current_name].append(line)
        i += 1

    result: Dict[str, Dict[str, object]] = {}
    for name, block_lines in blocks.items():
        inferred_summary = ""
        if "主要提供" in name:
            pure_name, inferred_summary = name.split("主要提供", 1)
            name = compact(pure_name)
            inferred_summary = compact(inferred_summary.strip("。"))
        block_text = compact_text_block(" ".join(block_lines))
        summary_match = re.search(r"主要提供(.+?)[。；]", block_text)
        summary = compact(summary_match.group(1)) if summary_match else inferred_summary
        detail_text = ""
        detail_match = re.search(r"具体包括(.+)", block_text)
        if detail_match:
            detail_text = compact(detail_match.group(1))
        requirement_items = split_cn_enumeration(detail_text) if detail_text else []
        if not requirement_items and block_text:
            requirement_items = [block_text]
        module_items = split_feature_items(summary) if summary else []
        function_points = split_function_points(requirement_items)
        result[name] = {
            "功能定位": summary,
            "功能模块": module_items[:10],
            "功能点或事项": function_points[:12],
            "运维或建设要求": requirement_items[:6],
        }
    return result


def extract_requirement_bucket(lines: Sequence[str], start: str, end: str, limit: int = 10) -> List[str]:
    chunk = merge_wrapped_lines(slice_between(lines, start, end, max_lines=120))
    if not chunk:
        return []
    items: List[str] = []
    for line in chunk[1:]:
        if re.match(r"^\d+(\.\d+)?", line):
            continue
        if line in {start, end}:
            continue
        items.append(line)
    return cleanup_list_items(items)[:limit]


def collect_requirement_views(lines: Sequence[str]) -> Dict[str, object]:
    return {
        "系统级要求": extract_system_requirement_blocks(lines),
        "通用要求": {
            "日常维护与支持": extract_requirement_bucket(lines, "3.2 日常维护业务需求", "3.3 数据库维护需求"),
            "数据库维护": extract_requirement_bucket(lines, "3.3 数据库维护需求", "3.4 信息化资产维护需求"),
            "资产维护": extract_requirement_bucket(lines, "3.4 信息化资产维护需求", "四、硬件维护服务需求"),
            "硬件与现场保障": extract_requirement_bucket(lines, "4.4 日常维护需求", "4.5 其他要求"),
            "考核要求": extract_requirement_bucket(lines, "5.1 考核标准", "5.2 考核方式"),
            "验收要求": extract_requirement_bucket(lines, "六、验收要求", "七、付款方式"),
            "安全与数据要求": extract_requirement_bucket(lines, "十二、网络和数据安全管理要求", "十三、网络和数据安全处罚措施"),
        },
    }


def build_chapter_writing_directions(fields: Dict[str, str], lists: Dict[str, List[str]], requirements: Dict[str, object]) -> Dict[str, List[str]]:
    systems = lists.get("系统清单", [])[:12]
    common = requirements.get("通用要求", {}) if isinstance(requirements.get("通用要求", {}), dict) else {}
    directions: Dict[str, List[str]] = {
        "第一章 单位概况": [
            "交代业务需求单位、建设单位、采购单位之间的职责关系与项目牵头关系。",
            "用行政职责和业务范围说明项目为何由该单位提出，不展开技术方案。"
        ],
        "第二章 项目概述": [
            f"围绕项目名称、采购方式、履行周期、预算上限、服务范围和涉及系统进行总览性展开。",
            "对项目目标、主要内容、实施周期、预期效益、风险和考核指标做压缩展开，而不是只列字段。"
        ],
        "第三章 数字化现状": [
            "根据现有系统清单、设备清单、数据与安全要求，写已有基础、现有资源和当前支撑格局。",
            "不能臆造过深架构；要明确哪些现状来自采购文件，哪些仍需调研补充。"
        ],
        "第四章 项目建设必要性及需求分析": [
            "把已提取的系统级要求改写为业务需求、功能需求、流程需求、接口需求、性能需求、安全需求和验收需求。",
            "这一章应是需求说明最强的一章，按系统或主题簇逐层展开。"
        ],
        "第五章 项目设计方案": [
            "围绕已提取需求说明方案边界、支撑机制、接口与数据路线、运维与保障机制。",
            "不要写通用技术栈，要写为什么这些方案能够支撑前述需求。"
        ],
        "第六章 项目建设内容": [
            "按系统、模块或能力域展开建设内容；每个对象都要写业务问题、建设内容、支撑效果。",
            "表格只能做摘要，正文必须展开到段落级。"
        ],
        "第七章 项目预算": [
            "预算应与已提取的系统范围、数据库维护、资产维护、安全整改、SLA和验收要求对应。",
            "先写预算编制依据，再写分类测算和汇总使用计划。"
        ],
        "第八章 项目建设与运行管理": [
            "结合通用要求中的值班、巡检、监控、考核、验收、安全与数据要求，展开组织、进度、质量、制度、验收和运行管理。",
            "重点写怎么保障项目建设和长期稳定运行。"
        ],
        "第九章 其他": [
            "汇总预算依据、验收文档要求、制度依据、相关技术经济资料等补证材料。",
            "作为前文论证的支撑附件，不应空缺。"
        ],
    }
    if systems:
        directions["第二章 项目概述"].append("项目概述中应点明涉及的主要系统或子系统：" + "、".join(systems[:6]) + "。")
        directions["第四章 项目建设必要性及需求分析"].append("需求分析优先围绕以下系统展开：" + "、".join(systems[:8]) + "。")
        directions["第六章 项目建设内容"].append("建设内容可优先按以下系统分节：" + "、".join(systems[:8]) + "。")
    if common:
        directions["第八章 项目建设与运行管理"].append("运行管理还应覆盖：" + "、".join([k for k, v in common.items() if isinstance(v, list) and v][:5]) + "。")
    return directions


def build_system_writing_directions(requirements: Dict[str, object]) -> Dict[str, List[str]]:
    result: Dict[str, List[str]] = {}
    systems = requirements.get("系统级要求", {})
    if not isinstance(systems, dict):
        return result
    for system_name, payload in systems.items():
        if not isinstance(payload, dict):
            continue
        summary = str(payload.get("功能定位") or "").strip()
        modules = payload.get("功能模块", [])
        module_list = [str(item).strip() for item in modules if str(item).strip()] if isinstance(modules, list) else []
        points = payload.get("功能点或事项", [])
        point_list = [str(item).strip() for item in points if str(item).strip()] if isinstance(points, list) else []
        reqs = payload.get("运维或建设要求", [])
        req_list = [str(item).strip() for item in reqs if str(item).strip()] if isinstance(reqs, list) else []
        items = []
        if summary:
            items.append(f"先交代该系统支撑的业务场景或服务对象：{summary}")
        if module_list:
            items.append("该系统可优先按以下功能模块展开：" + "、".join(module_list[:8]) + "。")
        if point_list:
            items.append("模块下可继续落到这些功能点或事项：" + "；".join(point_list[:6]) + "。")
        items.append("说明该系统当前需要被建设、优化或保障的核心能力，而不是只列系统名称。")
        if req_list:
            items.append("可围绕以下要求扩写建设内容：" + "；".join(req_list[:4]) + "。")
        items.append("在第四章中将其写成需求，在第六章中将其写成建设或运维能力说明；如有功能模块和功能点，应继续下钻到模块级。")
        result[system_name] = items
    return result


def build_module_writing_directions(requirements: Dict[str, object]) -> Dict[str, Dict[str, List[str]]]:
    result: Dict[str, Dict[str, List[str]]] = {}
    systems = requirements.get("系统级要求", {})
    if not isinstance(systems, dict):
        return result
    for system_name, payload in systems.items():
        if not isinstance(payload, dict):
            continue
        modules = payload.get("功能模块", [])
        points = payload.get("功能点或事项", [])
        module_list = [str(item).strip() for item in modules if str(item).strip()] if isinstance(modules, list) else []
        point_list = [str(item).strip() for item in points if str(item).strip()] if isinstance(points, list) else []
        if not module_list:
            continue
        result[system_name] = {}
        for module_name in module_list[:10]:
            items = [
                f"说明模块“{module_name}”面向的具体业务动作、办理环节或服务场景。",
                f"解释模块“{module_name}”需要承载的能力边界，而不是只写名称。",
                f"说明模块“{module_name}”涉及的处理流程、数据对象、接口协同、报表或监测逻辑。",
                f"补出模块“{module_name}”在管理、服务、监管或风险控制方面的预期作用。"
            ]
            related_points = [p for p in point_list if module_name in p or any(token in p for token in module_name.split())]
            if related_points:
                items.append("可结合这些功能点或事项继续展开：" + "；".join(related_points[:4]) + "。")
            result[system_name][module_name] = items
    return result


def collect_lists(text: str, lines: Sequence[str]) -> Dict[str, List[str]]:
    return {
        "服务范围清单": extract_service_scope(lines),
        "系统清单": extract_system_list(text, lines),
        "硬件与设备清单": extract_device_list(lines),
        "编制依据或法规": extract_basis_list(lines),
    }


def build_missing(fields: Dict[str, str], lists: Dict[str, List[str]]) -> List[str]:
    required = ["项目名称", "采购单位", "预算金额", "最高限价", "合同履行期限", "采购方式"]
    missing = [field for field in required if field not in fields]
    if not lists.get("系统清单"):
        missing.append("系统清单")
    if not lists.get("硬件与设备清单"):
        missing.append("硬件与设备清单")
    return missing


def default_output_paths(source_path: Path) -> Tuple[Path, Path]:
    return (
        source_path.with_name(source_path.stem + ".fact-base.md"),
        source_path.with_name(source_path.stem + ".fact-base.json"),
    )


def build_json_payload(
    source_path: Path,
    fields: Dict[str, str],
    sections: Dict[str, List[str]],
    lists: Dict[str, List[str]],
    requirements: Dict[str, object],
    chapter_directions: Dict[str, List[str]],
    system_directions: Dict[str, List[str]],
    module_directions: Dict[str, Dict[str, List[str]]],
    missing: List[str],
    output_path: Path,
    json_path: Path,
) -> Dict[str, object]:
    default_md, default_json = default_output_paths(source_path)
    return {
        "source_file": str(source_path),
        "default_outputs": {"markdown": str(default_md), "json": str(default_json)},
        "actual_outputs": {"markdown": str(output_path), "json": str(json_path)},
        "read_this_first": str(output_path),
        "project_info": {k: v for k, v in fields.items() if k in {"项目名称", "项目编号", "预算编号", "采购单位", "需求单位", "采购代理机构", "采购方式", "运维地点", "合同履行期限"}},
        "budget_info": {k: v for k, v in fields.items() if k in {"预算金额", "最高限价", "联系方式"}},
        "lists": lists,
        "sections": sections,
        "requirements": requirements,
        "chapter_writing_directions": chapter_directions,
        "system_writing_directions": system_directions,
        "module_writing_directions": module_directions,
        "missing_facts": missing,
    }


def render_markdown(
    source_path: Path,
    fields: Dict[str, str],
    sections: Dict[str, List[str]],
    lists: Dict[str, List[str]],
    requirements: Dict[str, object],
    chapter_directions: Dict[str, List[str]],
    system_directions: Dict[str, List[str]],
    module_directions: Dict[str, Dict[str, List[str]]],
    missing: List[str],
    output_path: Path,
    json_path: Path,
) -> str:
    lines: List[str] = []
    lines.append("# 可研写作事实底稿")
    lines.append("")
    lines.append(f"- 来源文件: `{source_path.name}`")
    lines.append(f"- Markdown 输出: `{output_path.name}`")
    lines.append(f"- JSON 输出: `{json_path.name}`")
    lines.append("- 下一步: 先阅读本 Markdown 底稿，再进入可研目录设计和正文写作。")
    lines.append("")

    lines.append("## 项目基本信息")
    lines.append("")
    for key in ("项目名称", "项目编号", "预算编号", "采购单位", "需求单位", "采购代理机构", "采购方式", "运维地点", "合同履行期限"):
        lines.append(f"- {key}: {fields.get(key, '待补充')}")
    lines.append("")

    lines.append("## 采购与预算信息")
    lines.append("")
    for key in ("预算金额", "最高限价", "联系方式"):
        lines.append(f"- {key}: {fields.get(key, '待补充')}")
    lines.append("")

    for title in ("服务范围清单", "系统清单", "硬件与设备清单", "编制依据或法规"):
        lines.append(f"## {title}")
        lines.append("")
        items = lists.get(title, [])
        if items:
            for item in items:
                lines.append(f"- {item}")
        else:
            lines.append("- 待补充")
        lines.append("")

    for title in ("服务范围", "系统与资产清单", "人员配置", "服务指标与考核", "付款与验收", "安全与保密要求"):
        lines.append(f"## {title}")
        lines.append("")
        items = sections.get(title, [])
        if items:
            for item in items:
                lines.append(f"- {item}")
        else:
            lines.append("- 待补充")
        lines.append("")

    lines.append("## 系统级建设或运维要求提要")
    lines.append("")
    system_requirements = requirements.get("系统级要求", {})
    if isinstance(system_requirements, dict) and system_requirements:
        for system_name, payload in system_requirements.items():
            if not isinstance(payload, dict):
                continue
            lines.append(f"### {system_name}")
            lines.append("")
            lines.append(f"- 功能定位: {payload.get('功能定位') or '待补充'}")
            modules = payload.get("功能模块", [])
            if isinstance(modules, list) and modules:
                lines.append("- 功能模块: " + "、".join(str(item) for item in modules))
            points = payload.get("功能点或事项", [])
            if isinstance(points, list) and points:
                lines.append("- 功能点或事项: " + "；".join(str(item) for item in points[:8]))
            reqs = payload.get("运维或建设要求", [])
            if isinstance(reqs, list) and reqs:
                for req in reqs:
                    lines.append(f"- 要求: {req}")
            else:
                lines.append("- 要求: 待补充")
            lines.append("")
    else:
        lines.append("- 待补充")
        lines.append("")

    lines.append("## 通用建设与运维要求")
    lines.append("")
    common_requirements = requirements.get("通用要求", {})
    if isinstance(common_requirements, dict):
        for title, items in common_requirements.items():
            lines.append(f"### {title}")
            lines.append("")
            if isinstance(items, list) and items:
                for item in items:
                    lines.append(f"- {item}")
            else:
                lines.append("- 待补充")
            lines.append("")

    lines.append("## 章节写作方向")
    lines.append("")
    for chapter, items in chapter_directions.items():
        lines.append(f"### {chapter}")
        lines.append("")
        for item in items:
            lines.append(f"- {item}")
        lines.append("")

    lines.append("## 系统写作方向")
    lines.append("")
    for system_name, items in system_directions.items():
        lines.append(f"### {system_name}")
        lines.append("")
        for item in items:
            lines.append(f"- {item}")
        lines.append("")

    lines.append("## 模块写作方向")
    lines.append("")
    if module_directions:
        for system_name, module_map in module_directions.items():
            lines.append(f"### {system_name}")
            lines.append("")
            for module_name, items in module_map.items():
                lines.append(f"#### {module_name}")
                lines.append("")
                for item in items:
                    lines.append(f"- {item}")
                lines.append("")
    else:
        lines.append("- 待补充")
        lines.append("")

    lines.append("## 待补充事实")
    lines.append("")
    if missing:
        for item in missing:
            lines.append(f"- {item}")
    else:
        lines.append("- 当前关键字段已提取，可进入可研大纲设计与章节写作。")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Parse source files into a feasibility-report fact base.",
        epilog="Default outputs: <source>.fact-base.md and <source>.fact-base.json",
    )
    parser.add_argument("input", help="Input source file (.pdf, .docx, .txt, .md)")
    parser.add_argument("-o", "--output", help="Output markdown path. Defaults to <input>.fact-base.md")
    parser.add_argument("--json-output", help="Output JSON path. Defaults to <input>.fact-base.json")
    args = parser.parse_args()

    source_path = Path(args.input).expanduser().resolve()
    if not source_path.exists():
        print(f"Input file not found: {source_path}", file=sys.stderr)
        return 1

    default_md, default_json = default_output_paths(source_path)
    output_path = Path(args.output).expanduser().resolve() if args.output else default_md
    json_path = Path(args.json_output).expanduser().resolve() if args.json_output else default_json

    try:
        text = read_text(source_path)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    lines = normalize_lines(text)
    fields = collect_fields(text)
    sections = collect_sections(lines)
    lists = collect_lists(text, lines)
    requirements = collect_requirement_views(lines)
    chapter_directions = build_chapter_writing_directions(fields, lists, requirements)
    system_directions = build_system_writing_directions(requirements)
    module_directions = build_module_writing_directions(requirements)
    missing = build_missing(fields, lists)

    markdown = render_markdown(source_path, fields, sections, lists, requirements, chapter_directions, system_directions, module_directions, missing, output_path, json_path)
    output_path.write_text(markdown, encoding="utf-8")

    json_payload = build_json_payload(source_path, fields, sections, lists, requirements, chapter_directions, system_directions, module_directions, missing, output_path, json_path)
    json_path.write_text(json.dumps(json_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(output_path)
    print(json_path)
    print("PARSE_STATUS: success")
    print(f"READ_THIS_FIRST: {output_path}")
    print(f"JSON_FACT_BASE: {json_path}")
    print("NEXT_STEP: Read the markdown fact base before outlining or drafting.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
