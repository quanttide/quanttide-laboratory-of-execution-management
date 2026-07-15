#!/usr/bin/env python3
"""评估 distill 输出与 baseline 的差异。

从 profile 中解析已有条目作为 baseline，与 distill 输出的提案对比，
计算召回率、精确率、F1。

Usage:
    python evaluate.py <proposal.md> [--baseline data/profile/index.md]
"""

import argparse
import re
import sys


def parse_profile_items(text: str) -> list[dict]:
    items = []
    current_category = None
    for line in text.split("\n"):
        m = re.match(r"^## (.+)", line)
        if m:
            current_category = m.group(1).strip()
            continue
        m = re.match(r"^- (?:\*\*)?\[?]?\*?(.+?)\*?(?:\]\(.*?\))?", line)
        if m and current_category:
            items.append({"title": m.group(1).strip(), "category": current_category})
    return items


def normalize_title(title: str) -> str:
    return title.strip().rstrip("）)").strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="评估 distill 输出")
    parser.add_argument("proposal_file", help="distill 输出的提案文件路径")
    parser.add_argument(
        "--baseline",
        default="data/profile/index.md",
        help="baseline profile 路径",
    )
    args = parser.parse_args()

    with open(args.proposal_file) as f:
        proposal_text = f.read()
    with open(args.baseline) as f:
        baseline_text = f.read()

    proposal_items = parse_profile_items(proposal_text)
    baseline_items = parse_profile_items(baseline_text)

    prop_by_title = {normalize_title(i["title"]): i for i in proposal_items}
    base_by_title = {normalize_title(i["title"]): i for i in baseline_items}

    proposal_titles = set(prop_by_title.keys())
    baseline_titles = set(base_by_title.keys())

    true_positives = proposal_titles & baseline_titles
    false_positives = proposal_titles - baseline_titles
    false_negatives = baseline_titles - proposal_titles

    recall = len(true_positives) / len(baseline_titles) if baseline_titles else 0.0
    precision = (
        len(true_positives) / len(proposal_titles) if proposal_titles else 0.0
    )
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    # 分类一致率
    matched = 0
    for title in true_positives:
        if prop_by_title[title]["category"] == base_by_title[title]["category"]:
            matched += 1
    cat_consistency = matched / len(true_positives) if true_positives else 0.0

    print(f"Baseline 条目数:   {len(baseline_titles)}")
    print(f"提案条目数:       {len(proposal_titles)}")
    print(f"匹配:             {len(true_positives)}")
    print(f"新增（可能噪音）: {len(false_positives)}")
    print(f"遗漏:             {len(false_negatives)}")
    print()
    print(f"召回率 (Recall):             {recall:.1%}")
    print(f"精确率 (Precision):          {precision:.1%}")
    print(f"F1:                          {f1:.1%}")
    print(f"分类一致率:                  {cat_consistency:.1%}")
    print()

    # 输出 ROADMAP 评估标准对齐
    print("--- 评估标准对照 ---")
    print(f"提案准确（差异 ≤ 1 条）: {'✓' if len(false_positives) + len(false_negatives) <= 1 else '✗'}")
    print(f"分类一致率 ≥ 80%:        {'✓' if cat_consistency >= 0.8 else '✗'}")
    print(f"召回率 ≥ 90%:            {'✓' if recall >= 0.9 else '✗'}")
    print(f"不引入噪音:              {'✓' if len(false_positives) == 0 else '✗'}")
    print()

    if false_negatives:
        print("遗漏条目:")
        for t in sorted(false_negatives):
            print(f"  - {t}")
    if false_positives:
        print("新增条目（可能噪音）:")
        for t in sorted(false_positives):
            print(f"  - {t}")


if __name__ == "__main__":
    main()
