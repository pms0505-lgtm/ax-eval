#!/usr/bin/env python3
"""
AX-Eval: Claude Code 세션 JSONL → Markdown 변환기
- 프로젝트별로 대화를 읽기 좋은 Markdown으로 변환
- AX 평가용 지표(요청력/검증력/활용력/판단력) 자동 추출
- vibe-sunsang convert_sessions.py 기반, ax-eval 출력 경로로 수정
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"
DEFAULT_OUTPUT_DIR = Path.home() / "ax-eval" / "conversations"
DEFAULT_NAMES_FILE = Path.home() / "ax-eval" / "config" / "project_names.json"

# 검증 키워드: 사용자가 AI 결과를 검토하는 패턴
VERIFY_KEYWORDS = [
    "확인", "검토", "맞아", "맞나요", "맞는지", "틀렸", "틀린",
    "다시", "수정", "고쳐", "바꿔", "잘못", "아니야", "아닌데",
    "왜", "이게 맞아", "검증", "체크"
]

# 전략 키워드: 메타인지, 비교, 대안 사고
STRAT_KEYWORDS = [
    "왜", "이유", "대안", "비교", "차이", "장단점", "어떤 게 나",
    "더 좋은", "효율", "전략", "계획", "방향", "목적", "목표"
]

# Tool formatters
TOOL_FORMATTERS = {
    "Read":      lambda i: f"*[Tool: Read → `{i.get('file_path', '?')}`]*",
    "Write":     lambda i: f"*[Tool: Write → `{i.get('file_path', '?')}`]*",
    "Edit":      lambda i: f"*[Tool: Edit → `{i.get('file_path', '?')}`]*",
    "Bash":      lambda i: f"*[Tool: Bash → `{i.get('command', '?')[:80]}`]*",
    "Grep":      lambda i: f"*[Tool: Grep → `{i.get('pattern', '?')}`]*",
    "Glob":      lambda i: f"*[Tool: Glob → `{i.get('pattern', '?')}`]*",
    "WebSearch": lambda i: f"*[Tool: WebSearch → `{i.get('query', '?')}`]*",
    "WebFetch":  lambda i: f"*[Tool: WebFetch → `{i.get('url', '?')}`]*",
    "Task":      lambda i: f"*[Tool: Task → `{i.get('description', '?')}`]*",
    "Agent":     lambda i: f"*[Tool: Agent → `{i.get('description', '?')}`]*",
}


def load_project_names(names_file: Path) -> dict:
    if names_file.exists():
        try:
            with open(names_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def get_project_name(dir_name: str, project_names: dict) -> str:
    if dir_name in project_names:
        return project_names[dir_name]
    name = re.sub(r"^-Users-[^-]+-", "", dir_name).replace("-", "_").lower()
    return name or "unknown"


def extract_text_content(content, verbose: bool = False) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    texts.append(block.get("text", ""))
                elif block.get("type") == "tool_use":
                    tool_name = block.get("name", "unknown")
                    tool_input = block.get("input", {})
                    formatter = TOOL_FORMATTERS.get(tool_name)
                    if formatter:
                        texts.append(formatter(tool_input))
                    else:
                        texts.append(f"*[Tool: {tool_name}]*")
                elif block.get("type") == "tool_result":
                    result_content = block.get("content", "")
                    if isinstance(result_content, str) and result_content.strip():
                        if verbose:
                            texts.append(f"\n> *[Result]:*\n> {result_content}\n")
                        else:
                            preview = result_content[:200].replace("\n", " ")
                            if len(result_content) > 200:
                                preview += "..."
                            texts.append(f"\n> *[Result]: {preview}*\n")
        return "\n".join(texts)
    return str(content)


def format_timestamp(ts) -> str:
    if isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return ts
    if isinstance(ts, (int, float)):
        try:
            if ts > 1e12:
                dt = datetime.utcfromtimestamp(ts / 1000)
            else:
                dt = datetime.utcfromtimestamp(ts)
            return dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return str(ts)
    return str(ts)


def get_session_date(ts) -> str:
    if isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return "unknown-date"
    if isinstance(ts, (int, float)):
        try:
            if ts > 1e12:
                dt = datetime.utcfromtimestamp(ts / 1000)
            else:
                dt = datetime.utcfromtimestamp(ts)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return "unknown-date"
    return "unknown-date"


def count_keywords(text: str, keywords: list) -> int:
    """텍스트에서 키워드 등장 횟수 합산"""
    count = 0
    for kw in keywords:
        count += text.count(kw)
    return count


def has_context_specificity(text: str) -> bool:
    """파일명, 숫자, 구체적 명사 포함 여부 (맥락 구체성)"""
    # 파일 경로 패턴
    has_path = bool(re.search(r'[\w\-]+\.\w{2,5}', text))
    # 숫자 포함 (날짜, 금액, 비율 등)
    has_number = bool(re.search(r'\d+', text))
    # 따옴표로 감싼 구체적 용어
    has_quoted = bool(re.search(r'["\'「」]', text))
    return has_path or (has_number and len(text) > 50) or has_quoted


def convert_session(jsonl_path: Path, verbose: bool = False) -> dict:
    """단일 세션 JSONL을 파싱 + AX 지표 추출"""
    messages = []
    metadata = {
        "session_id": jsonl_path.stem,
        "models_used": set(),
        "tools_used": set(),
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "start_time": None,
        "end_time": None,
        "git_branch": None,
        "cwd": None,
    }

    # 기본 P0 카운터
    ORCH_TOOLS = {"Task", "Agent", "SendMessage"}
    user_msg_lengths = []
    user_turn_count = 0
    bypass_count = 0
    total_entry_count = 0
    orch_tool_count = 0
    tool_error_count = 0
    compact_boundary_count = 0
    assistant_turn_count = 0
    thinking_turn_count = 0

    # AX 추가 카운터
    verify_keyword_count = 0    # 검증 키워드 합산 (검증력)
    strat_keyword_count = 0     # 전략 키워드 합산 (판단력)
    specific_context_count = 0  # 맥락 구체성 (요청력)
    user_msgs_raw = []          # 원본 사용자 메시지 (분석용)

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            entry_type = entry.get("type", "")
            timestamp = entry.get("timestamp", "")
            total_entry_count += 1

            if metadata["start_time"] is None and timestamp:
                metadata["start_time"] = timestamp
            if timestamp:
                metadata["end_time"] = timestamp

            if entry.get("gitBranch"):
                metadata["git_branch"] = entry["gitBranch"]
            if entry.get("cwd"):
                metadata["cwd"] = entry["cwd"]

            if entry.get("permissionMode") == "bypassPermissions":
                bypass_count += 1

            if entry_type == "system" and entry.get("subtype") == "compact_boundary":
                compact_boundary_count += 1

            msg = entry.get("message", {})
            role = msg.get("role", entry_type)
            model = msg.get("model", "")

            if model:
                metadata["models_used"].add(model)

            usage = msg.get("usage", {})
            metadata["total_input_tokens"] += usage.get("input_tokens", 0)
            metadata["total_output_tokens"] += usage.get("output_tokens", 0)

            content = msg.get("content", "")
            if not content:
                continue

            if role in ("user", "human"):
                if isinstance(content, str) and content.strip():
                    user_turn_count += 1
                    user_msg_lengths.append(len(content))
                    user_msgs_raw.append(content)

                    # AX 지표: 검증력 키워드
                    verify_keyword_count += count_keywords(content, VERIFY_KEYWORDS)
                    # AX 지표: 판단력 키워드
                    strat_keyword_count += count_keywords(content, STRAT_KEYWORDS)
                    # AX 지표: 맥락 구체성
                    if has_context_specificity(content):
                        specific_context_count += 1

                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("is_error"):
                            tool_error_count += 1

            if role == "assistant" and isinstance(content, list):
                assistant_turn_count += 1
                has_thinking = False
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "tool_use":
                            tool_name = block.get("name", "")
                            if tool_name in ORCH_TOOLS:
                                orch_tool_count += 1
                        if block.get("type") == "thinking":
                            has_thinking = True
                if has_thinking:
                    thinking_turn_count += 1
            elif role == "assistant" and isinstance(content, str) and content.strip():
                assistant_turn_count += 1

            text = extract_text_content(content, verbose=verbose)
            if not text or not text.strip():
                continue

            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        metadata["tools_used"].add(block.get("name", "unknown"))

            if role in ("user", "human"):
                messages.append({"role": "user", "content": text, "time": format_timestamp(timestamp)})
            elif role == "assistant":
                messages.append({"role": "assistant", "content": text, "time": format_timestamp(timestamp)})

    metadata["models_used"] = sorted(metadata["models_used"])
    metadata["tools_used"] = sorted(metadata["tools_used"])
    metadata["message_count"] = len(messages)

    # 기본 P0 지표
    metadata["avg_user_msg_len"] = (
        round(sum(user_msg_lengths) / len(user_msg_lengths)) if user_msg_lengths else 0
    )
    metadata["user_turn_count"] = user_turn_count
    metadata["bypass_permission_ratio"] = (
        round(bypass_count / total_entry_count, 2) if total_entry_count > 0 else 0.0
    )
    metadata["has_orchestration"] = orch_tool_count > 0
    metadata["orch_tool_count"] = orch_tool_count
    metadata["tool_error_count"] = tool_error_count
    metadata["compact_boundaries"] = compact_boundary_count
    metadata["thinking_turn_ratio"] = (
        round(thinking_turn_count / assistant_turn_count, 2) if assistant_turn_count > 0 else 0.0
    )

    # AX 전용 지표
    metadata["tool_diversity"] = len(metadata["tools_used"])
    metadata["verify_keyword_count"] = verify_keyword_count
    metadata["strat_keyword_count"] = strat_keyword_count
    metadata["specific_context_ratio"] = (
        round(specific_context_count / user_turn_count, 2) if user_turn_count > 0 else 0.0
    )
    metadata["verify_ratio"] = (
        round(verify_keyword_count / user_turn_count, 2) if user_turn_count > 0 else 0.0
    )
    metadata["strat_ratio"] = (
        round(strat_keyword_count / user_turn_count, 2) if user_turn_count > 0 else 0.0
    )

    return {"messages": messages, "metadata": metadata}


def session_to_markdown(session_data: dict, project_name: str) -> str:
    """파싱된 세션을 Markdown으로 변환"""
    meta = session_data["metadata"]
    messages = session_data["messages"]

    if not messages:
        return ""

    date = get_session_date(meta["start_time"])
    lines = []

    # 프론트매터
    lines.append("---")
    lines.append(f"project: {project_name}")
    lines.append(f"session_id: {meta['session_id']}")
    lines.append(f"date: {date}")
    lines.append(f"start: {format_timestamp(meta['start_time'])}")
    lines.append(f"end: {format_timestamp(meta['end_time'])}")
    lines.append(f"tags:")
    lines.append(f"  - ax-eval")
    lines.append(f"  - {project_name}")

    if meta["models_used"]:
        lines.append("models:")
        for m in meta["models_used"]:
            lines.append(f"  - {m}")
    else:
        lines.append("models: unknown")

    if meta["tools_used"]:
        lines.append("tools:")
        for t in meta["tools_used"]:
            lines.append(f"  - {t}")
    else:
        lines.append("tools: none")

    lines.append(f"messages: {meta['message_count']}")
    lines.append(f"input_tokens: {meta['total_input_tokens']}")
    lines.append(f"output_tokens: {meta['total_output_tokens']}")
    if meta["git_branch"]:
        lines.append(f"git_branch: {meta['git_branch']}")
    if meta["cwd"]:
        lines.append(f"working_dir: {meta['cwd']}")

    # AX 지표
    lines.append("# AX 지표")
    lines.append(f"avg_user_msg_len: {meta['avg_user_msg_len']}")
    lines.append(f"user_turn_count: {meta['user_turn_count']}")
    lines.append(f"tool_diversity: {meta['tool_diversity']}")
    lines.append(f"specific_context_ratio: {meta['specific_context_ratio']}")
    lines.append(f"verify_ratio: {meta['verify_ratio']}")
    lines.append(f"strat_ratio: {meta['strat_ratio']}")
    lines.append(f"orch_tool_count: {meta['orch_tool_count']}")
    lines.append(f"has_orchestration: {str(meta['has_orchestration']).lower()}")
    lines.append(f"tool_error_count: {meta['tool_error_count']}")
    lines.append(f"thinking_turn_ratio: {meta['thinking_turn_ratio']}")
    lines.append("---")
    lines.append("")

    first_msg = messages[0]["content"][:80].replace("\n", " ")
    lines.append(f"# {date} | {project_name}")
    lines.append(f"> 첫 메시지: {first_msg}...")
    lines.append("")

    for msg in messages:
        if msg["role"] == "user":
            lines.append(f"## User ({msg['time']})")
        else:
            lines.append(f"## Assistant ({msg['time']})")
        lines.append("")
        lines.append(msg["content"])
        lines.append("")

    return "\n".join(lines)


def _find_existing_output(output_dir: Path, short_id: str) -> Path | None:
    for f in output_dir.glob(f"*_{short_id}.md"):
        return f
    return None


def convert_project(
    project_dir: str,
    output_base: Path,
    project_names: dict,
    project_name: str = None,
    force: bool = False,
    verbose: bool = False,
):
    project_path = CLAUDE_PROJECTS_DIR / project_dir
    if not project_path.exists():
        print(f"  [SKIP] {project_dir} - 디렉토리 없음")
        return 0

    if project_name is None:
        project_name = get_project_name(project_dir, project_names)

    output_dir = output_base / project_name
    dir_created = False

    jsonl_files = sorted(project_path.glob("*.jsonl"))
    converted = 0
    skipped = 0

    for jsonl_file in jsonl_files:
        try:
            short_id = jsonl_file.stem[:8]

            if not force and output_dir.exists():
                existing = _find_existing_output(output_dir, short_id)
                if existing and existing.stat().st_mtime >= jsonl_file.stat().st_mtime:
                    skipped += 1
                    continue

            session_data = convert_session(jsonl_file, verbose=verbose)
            if not session_data["messages"]:
                continue

            md_content = session_to_markdown(session_data, project_name)
            if not md_content:
                continue

            if not dir_created:
                output_dir.mkdir(parents=True, exist_ok=True)
                dir_created = True

            date = get_session_date(session_data["metadata"]["start_time"])
            output_file = output_dir / f"{date}_{short_id}.md"
            output_file.write_text(md_content, encoding="utf-8")
            converted += 1
        except Exception as e:
            print(f"  [ERROR] {jsonl_file.name}: {e}")

    if output_dir.exists() and not any(output_dir.iterdir()):
        output_dir.rmdir()

    skip_msg = f", {skipped} skipped (최신)" if skipped else ""
    print(f"  [{project_name}] {converted}/{len(jsonl_files)} 세션 변환 완료{skip_msg}")
    return converted


def generate_index(output_base: Path):
    if not output_base.exists():
        print("\n[INDEX] 출력 디렉토리 없음, 인덱스 생성 건너뜀.")
        return

    lines = []
    lines.append("---")
    lines.append("tags:")
    lines.append("  - ax-eval")
    lines.append("  - index")
    lines.append(f"updated: '{datetime.now().strftime('%Y-%m-%d %H:%M')}'")
    lines.append("---")
    lines.append("")
    lines.append("# AX-Eval 대화 인덱스")
    lines.append(f"\n생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    total_sessions = 0
    project_stats = []

    for project_dir in sorted(output_base.iterdir()):
        if not project_dir.is_dir():
            continue
        md_files = sorted(project_dir.glob("*.md"))
        if not md_files:
            continue
        total_sessions += len(md_files)
        dates = [f.stem[:10] for f in md_files]
        project_stats.append({
            "name": project_dir.name,
            "count": len(md_files),
            "first": min(dates),
            "last": max(dates),
        })

    lines.append(f"**총 {total_sessions}개 세션** | {len(project_stats)}개 프로젝트\n")
    lines.append("| 프로젝트 | 세션 수 | 기간 |")
    lines.append("|----------|---------|------|")

    for stat in sorted(project_stats, key=lambda x: -x["count"]):
        lines.append(
            f"| [{stat['name']}](./{stat['name']}/) | {stat['count']} | {stat['first']} ~ {stat['last']} |"
        )

    lines.append("\n---\n")
    lines.append("AX-Eval로 과거 대화를 분석하고 성장을 추적하세요.")

    index_path = output_base / "INDEX.md"
    index_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[INDEX] {index_path} 생성 완료 (총 {total_sessions}개 세션)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AX-Eval: Claude Code 세션 → Markdown 변환기")
    parser.add_argument("projects", nargs="*", help="특정 프로젝트 디렉토리명 (미지정 시 전체)")
    parser.add_argument("--force", action="store_true", help="전체 재변환 (캐시 무시)")
    parser.add_argument("--verbose", action="store_true", help="도구 결과 전문 포함")
    parser.add_argument("--output-dir", type=Path, default=None, help="출력 디렉토리")
    parser.add_argument("--names-file", type=Path, default=None, help="project_names.json 경로")
    parser.add_argument("--project", type=str, default=None, help="특정 프로젝트만 변환")
    return parser.parse_args()


def main():
    args = parse_args()

    output_dir = args.output_dir if args.output_dir else DEFAULT_OUTPUT_DIR
    names_file = args.names_file if args.names_file else DEFAULT_NAMES_FILE

    project_names = load_project_names(names_file)

    if args.project:
        targets = [args.project]
    elif args.projects:
        targets = args.projects
    else:
        targets = [d.name for d in CLAUDE_PROJECTS_DIR.iterdir() if d.is_dir()]

    print(f"=== AX-Eval: Claude Code 세션 → Markdown 변환 ===")
    print(f"소스: {CLAUDE_PROJECTS_DIR}")
    print(f"출력: {output_dir}")
    print(f"대상: {len(targets)}개 프로젝트")
    if args.force:
        print(f"모드: --force (전체 재변환)")
    print()

    total = 0
    for target in sorted(targets):
        total += convert_project(target, output_dir, project_names, force=args.force, verbose=args.verbose)

    generate_index(output_dir)
    print(f"\n=== 완료: 총 {total}개 세션 변환 ===")


if __name__ == "__main__":
    main()
