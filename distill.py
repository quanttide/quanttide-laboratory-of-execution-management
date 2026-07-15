#!/usr/bin/env python3
"""从执行日志蒸馏出 GTD 清单条目到执行档案。

Usage:
    python distill.py --dry-run
    python distill.py data/journal/2026-07-14.md --dry-run
    python distill.py --apply
    python distill.py --apply --commit
"""

import argparse
import json
import os
import re
import subprocess
import sys

from quanttide_agent.llm import LLM, Message

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(REPO_ROOT, "data")
JOURNAL_DIR = os.path.join(DATA_DIR, "journal")
PROMPTS_DIR = os.path.join(REPO_ROOT, "prompts")
PROFILE_PATH = os.path.join(DATA_DIR, "profile", "index.md")

SECTION_ORDER = ["日程", "下一步行动", "等待回复", "悬而未决"]
SECTION_TITLES = {
    "日程": "日程 📅",
    "下一步行动": "下一步行动",
    "等待回复": "等待回复",
    "悬而未决": "悬而未决",
}
PRIORITY_SORT = {"高": 0, "中": 1, "低": 2}

ITEM_RE = re.compile(
    r'^- (?:\[ \]\s+)?\*\*(.+?)\*\*(?:[—\-–]\s*(.*))?$'
)
PRIORITY_RE = re.compile(r'>\s*优先级：\s*(\S+)')
DISCUSSION_RE = re.compile(r'（待讨论）')


def load_prompt(name: str) -> str:
    path = os.path.join(PROMPTS_DIR, name)
    with open(path) as f:
        return f.read()


def chunk(text: str) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    return paragraphs


def extract(llm: LLM, paragraphs: list[str], journal_name: str) -> dict:
    prompt = load_prompt("extract.md")
    journal_text = (
        f"## {journal_name}\n\n"
        + "\n\n".join(
            f"### 段落 {i+1}\n{p}" for i, p in enumerate(paragraphs)
        )
    )
    messages = [
        Message(role="system", content=prompt),
        Message(role="user", content=journal_text),
    ]
    resp = llm.complete(messages, response_format={"type": "json_object"})
    return json.loads(resp.content)


def read_profile() -> str | None:
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH) as f:
            return f.read()
    return None


# ---------------------------------------------------------------------------
# Profile 解析 / 渲染
# ---------------------------------------------------------------------------

def parse_profile(text: str) -> dict[str, list[dict]]:
    sections: dict[str, list[dict]] = {s: [] for s in SECTION_ORDER}
    current_section = None
    cur_item = None

    for line in text.split("\n"):
        hdr = re.match(r"^## (.+)", line)
        if hdr:
            current_section = _match_section(hdr.group(1).strip())
            cur_item = None
            continue
        if current_section is None:
            continue

        m = ITEM_RE.match(line)
        if m:
            title = m.group(1).strip()
            description = (m.group(2) or "").strip()
            is_done = not line.lstrip().startswith("- [ ]")
            discussion = bool(DISCUSSION_RE.search(title))
            title = DISCUSSION_RE.sub("", title).strip()
            cur_item = {
                "title": title,
                "description": description,
                "category": current_section,
                "priority": "中",
                "is_done": is_done,
                "discussion": discussion,
                "detail": "",
            }
            sections.setdefault(current_section, []).append(cur_item)
            continue

        if cur_item and line.strip().startswith(">"):
            content = line.strip()[1:].strip()
            if PRIORITY_RE.search(line):
                cur_item["priority"] = PRIORITY_RE.search(line).group(1)
            elif content:
                cur_item["detail"] = (
                    cur_item["detail"] + " " + content
                    if cur_item["detail"]
                    else content
                )

    return sections


def _match_section(line: str) -> str | None:
    for s in SECTION_ORDER:
        if s in line:
            return s
    return None


def render_profile(sections: dict[str, list[dict]]) -> str:
    lines = ["# 量潮GTD清单"]
    for section_name in SECTION_ORDER:
        lines.append("")
        lines.append(f"## {SECTION_TITLES.get(section_name, section_name)}")
        lines.append("")
        items = sections.get(section_name, [])
        items = sorted(items, key=lambda x: PRIORITY_SORT.get(x["priority"], 1))
        for item in items:
            title = item["title"]
            if item.get("discussion"):
                title += "（待讨论）"
            desc = item.get("description", "")
            prefix = "" if item.get("is_done") else "[ ] "
            line = f"- {prefix}**{title}**"
            if desc:
                line += f" — {desc}"
            lines.append(line)
            if item.get("detail"):
                lines.append(f"  > {item['detail']}")
            lines.append(f"  > 优先级：{item['priority']}")
            lines.append("")
        lines.pop()
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Diff & Apply
# ---------------------------------------------------------------------------

def diff(llm: LLM, candidates: dict, sections: dict) -> dict:
    prompt = load_prompt("diff.md")
    content = json.dumps(
        {
            "candidates": candidates,
            "current_items": sections,
        },
        ensure_ascii=False,
        indent=2,
    )
    messages = [
        Message(role="system", content=prompt),
        Message(role="user", content=content),
    ]
    resp = llm.complete(messages, response_format={"type": "json_object"})
    return json.loads(resp.content)


def apply_patch(patch: dict, sections: dict) -> dict:
    for add in patch.get("additions", []):
        cat = _match_section(add.get("category", ""))
        if cat is None:
            print(f"  警告: 未知板块 '{add.get('category')}'，跳过新增", file=sys.stderr)
            continue
        sections.setdefault(cat, []).append({
            "title": add["title"],
            "description": add.get("description", ""),
            "category": cat,
            "priority": add.get("priority", "中"),
            "is_done": False,
            "discussion": False,
            "detail": "",
        })

    for merge in patch.get("merges", []):
        cat = _match_section(merge.get("category", ""))
        if cat is None:
            continue
        target = _find_item(sections, cat, merge["target_title"])
        if target:
            if "new_description" in merge:
                target["description"] = merge["new_description"]
            if "new_priority" in merge:
                target["priority"] = merge["new_priority"]

    for disc in patch.get("discussions", []):
        cat = _match_section(disc.get("category", ""))
        if cat is None:
            continue
        target = _find_item(sections, cat, disc["title"])
        if target:
            target["discussion"] = True

    return sections


def _find_item(sections: dict, category: str, title: str) -> dict | None:
    for item in sections.get(category, []):
        if item["title"] == title:
            return item
    return None


def commit() -> None:
    cwd = os.path.dirname(os.path.abspath(__file__))
    try:
        subprocess.run(
            ["git", "add", "-A"],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "distill: 更新 GTD 清单"],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
        print("已 commit")
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.strip()
        if "nothing to commit" in stderr:
            print("无变更，跳过 commit")
        else:
            print(f"commit 失败: {stderr}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="从执行日志蒸馏 GTD 条目")
    parser.add_argument(
        "journal", nargs="?", help="journal 文件路径，默认处理 data/journal/ 下所有文件"
    )
    parser.add_argument("--dry-run", action="store_true", help="仅输出提案，不写入文件")
    parser.add_argument("--apply", action="store_true", help="写入 data/profile/index.md")
    parser.add_argument(
        "--commit", action="store_true", help="自动 commit（需配合 --apply）"
    )
    args = parser.parse_args()

    if args.commit and not args.apply:
        parser.error("--commit 需配合 --apply 使用")

    if args.journal:
        journal_path = args.journal
        if not os.path.exists(journal_path):
            print(f"文件不存在: {journal_path}", file=sys.stderr)
            sys.exit(1)
        journal_files = [journal_path]
    else:
        if not os.path.isdir(JOURNAL_DIR):
            print(f"目录不存在: {JOURNAL_DIR}", file=sys.stderr)
            sys.exit(1)
        journal_files = sorted(
            os.path.join(JOURNAL_DIR, f)
            for f in os.listdir(JOURNAL_DIR)
            if f.endswith(".md")
        )
        if not journal_files:
            print("没有找到 journal 文件", file=sys.stderr)
            sys.exit(1)

    llm = LLM()
    all_candidates = {"items": []}

    for jf in journal_files:
        with open(jf) as f:
            text = f.read()
        paragraphs = chunk(text)
        jname = os.path.basename(jf)
        print(f"处理: {jname} ({len(paragraphs)} 段)")

        result = extract(llm, paragraphs, jname)
        items = result.get("items", [])
        all_candidates["items"].extend(items)

        print(f"  → 提取 {len(items)} 个候选条目")
        to_discuss = [i for i in items if i.get("needs_discussion")]
        if to_discuss:
            print(f"  → 其中 {len(to_discuss)} 个待讨论:")
            for item in to_discuss:
                print(f"    - {item['title']}")

    if not all_candidates["items"]:
        print("未提取到任何条目")
        return

    profile_text = read_profile()
    sections = parse_profile(profile_text) if profile_text else {s: [] for s in SECTION_ORDER}

    print(f"\n正在比对现有清单…")
    patch = diff(llm, all_candidates, sections)

    if patch.get("additions"):
        print(f"\n新增 {len(patch['additions'])} 条:")
        for a in patch["additions"]:
            print(f"  [{a['category']}] {a['title']}")
    if patch.get("merges"):
        print(f"\n合并 {len(patch['merges'])} 条:")
        for m in patch["merges"]:
            print(f"  [{m['category']}] {m['target_title']}")
    if patch.get("discussions"):
        print(f"\n待讨论 {len(patch['discussions'])} 条:")
        for d in patch["discussions"]:
            print(f"  [{d['category']}] {d['title']}: {d.get('reason', '')}")

    if args.dry_run:
        print("\n--- dry-run 模式，未做任何修改 ---")
        return

    if args.apply:
        sections = apply_patch(patch, sections)
        rendered = render_profile(sections)
        os.makedirs(os.path.dirname(PROFILE_PATH), exist_ok=True)
        with open(PROFILE_PATH, "w") as f:
            f.write(rendered)
        print(f"已写入 {PROFILE_PATH}")
        if args.commit:
            commit()
    else:
        print("\n提示: 使用 --dry-run 仅查看，使用 --apply 写入文件")


if __name__ == "__main__":
    main()
