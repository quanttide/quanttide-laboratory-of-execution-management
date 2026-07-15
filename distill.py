#!/usr/bin/env python3
"""从执行日志蒸馏出 GTD 清单条目到执行档案。

Usage:
    python distill.py --dry-run
    python distill.py ../../data/journal/2026-07-14.md --dry-run
    python distill.py --apply
"""

import argparse
import json
import os
import sys

from quanttide_agent.llm import LLM, Message

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(REPO_ROOT, "data")
JOURNAL_DIR = os.path.join(DATA_DIR, "journal")
PROMPTS_DIR = os.path.join(REPO_ROOT, "prompts")
PROFILE_PATH = os.path.join(DATA_DIR, "profile", "index.md")


def load_prompt(name: str) -> str:
    path = os.path.join(PROMPTS_DIR, name)
    with open(path) as f:
        return f.read()


def chunk(text: str) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    return paragraphs


def extract(
    llm: LLM, paragraphs: list[str], journal_name: str
) -> dict:
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


def diff(llm: LLM, candidates: dict, existing_profile: str | None) -> str:
    prompt = load_prompt("diff.md")
    content = json.dumps(
        {
            "candidates": candidates,
            "existing_profile": existing_profile or "（尚无清单）",
        },
        ensure_ascii=False,
        indent=2,
    )
    messages = [
        Message(role="system", content=prompt),
        Message(role="user", content=content),
    ]
    resp = llm.complete(messages)
    return resp.content


def apply(proposal: str) -> None:
    os.makedirs(os.path.dirname(PROFILE_PATH), exist_ok=True)
    with open(PROFILE_PATH, "w") as f:
        f.write(proposal)
    print(f"已写入 {PROFILE_PATH}")


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

    existing_profile = read_profile()
    print(f"\n正在比对现有清单…")
    proposal = diff(llm, all_candidates, existing_profile)

    print("\n" + "=" * 60)
    print("变更提案")
    print("=" * 60)
    print(proposal)

    if args.dry_run:
        print("\n--- dry-run 模式，未做任何修改 ---")
    elif args.apply:
        apply(proposal)
        if args.commit:
            os.system("git add -A && git commit -m 'distill: 更新 GTD 清单'")
    else:
        print("\n提示: 使用 --dry-run 仅查看，使用 --apply 写入文件")


if __name__ == "__main__":
    main()
