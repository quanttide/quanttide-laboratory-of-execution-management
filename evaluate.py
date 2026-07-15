#!/usr/bin/env python3
"""评估 distill 输出与 baseline 的差异。

从 profile 中解析已有条目作为 baseline，与 distill 输出的提案对比，
计算召回率、精确率、F1、分类一致率、优先级一致率。

Usage:
    python evaluate.py <baseline.md> <proposal.md>
"""

import argparse
import re
import sys

ITEM_RE = re.compile(
    r'^- (?:\[ \]\s+)?\*\*(.+?)\*\*(?:\s*[—\-–]\s*(.*))?\s*$'
)
PRIORITY_RE = re.compile(r'>\s*优先级：\s*(\S+)')
DISCUSSION_RE = re.compile(r'（待讨论）')
PRIORITY_SORT = {"高": 0, "中": 1, "低": 2}


def parse_items(text: str) -> list[dict]:
    items = []
    current_category = None
    cur_item = None
    for line in text.split("\n"):
        hdr = re.match(r"^## (.+)", line)
        if hdr:
            current_category = hdr.group(1).strip()
            cur_item = None
            continue
        if current_category is None:
            continue
        m = ITEM_RE.match(line)
        if m and current_category:
            title = m.group(1).strip()
            title = DISCUSSION_RE.sub("", title).strip()
            description = (m.group(2) or "").strip()
            cur_item = {
                "title": title,
                "description": description,
                "category": current_category,
                "priority": "中",
            }
            items.append(cur_item)
            continue
        if cur_item and line.strip().startswith(">"):
            pm = PRIORITY_RE.search(line)
            if pm:
                cur_item["priority"] = pm.group(1)
    return items


def fmt(items: list[dict]) -> dict[str, dict]:
    return {i["title"]: i for i in items}


def main() -> None:
    parser = argparse.ArgumentParser(description="评估 distill 输出与 baseline 差异")
    parser.add_argument("baseline_file", help="baseline profile 路径")
    parser.add_argument("proposal_file", help="distill 输出的提案文件路径")
    args = parser.parse_args()

    with open(args.baseline_file) as f:
        baseline_text = f.read()
    with open(args.proposal_file) as f:
        proposal_text = f.read()

    baseline = parse_items(baseline_text)
    proposal = parse_items(proposal_text)

    base_idx = fmt(baseline)
    prop_idx = fmt(proposal)

    base_titles = set(base_idx.keys())
    prop_titles = set(prop_idx.keys())

    true_positives = base_titles & prop_titles
    false_positives = prop_titles - base_titles
    false_negatives = base_titles - prop_titles

    n_base = len(base_titles)
    n_prop = len(prop_titles)
    n_tp = len(true_positives)

    recall = n_tp / n_base if n_base else 0.0
    precision = n_tp / n_prop if n_prop else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    # 分类一致率 & 优先级一致率
    cat_matched = 0
    pri_matched = 0
    for t in true_positives:
        if base_idx[t]["category"] == prop_idx[t]["category"]:
            cat_matched += 1
        if base_idx[t]["priority"] == prop_idx[t]["priority"]:
            pri_matched += 1
    cat_consistency = cat_matched / n_tp if n_tp else 0.0
    pri_consistency = pri_matched / n_tp if n_tp else 0.0

    print("=" * 50)
    print("  评估报告")
    print("=" * 50)
    print()
    print(f"Baseline 条目数:  {n_base}")
    print(f"提案条目数:      {n_prop}")
    print(f"匹配:            {n_tp}")
    print(f"新增（可能噪音）: {len(false_positives)}")
    print(f"遗漏:            {len(false_negatives)}")
    print()
    print(f"召回率 (Recall):     {recall:.1%}")
    print(f"精确率 (Precision):  {precision:.1%}")
    print(f"F1:                  {f1:.1%}")
    print(f"分类一致率:          {cat_consistency:.1%}")
    print(f"优先级一致率:        {pri_consistency:.1%}")
    print()
    print("--- 评估标准对照 ---")
    print(f"提案准确（差异 ≤ 1 条）:  {'✓' if len(false_positives) + len(false_negatives) <= 1 else '✗'}")
    print(f"分类一致率 ≥ 80%:         {'✓' if cat_consistency >= 0.8 else '✗'}")
    print(f"召回率 ≥ 90%:             {'✓' if recall >= 0.9 else '✗'}")
    print(f"不引入噪音:               {'✓' if len(false_positives) == 0 else '✗'}")
    print()

    # 逐项分类/优先级偏差
    if true_positives:
        print("--- 匹配条目分类/优先级对比 ---")
        for t in sorted(true_positives, key=lambda x: (PRIORITY_SORT.get(base_idx[x].get("priority", "中"), 1), x)):
            b = base_idx[t]
            p = prop_idx[t]
            cat_ok = "✓" if b["category"] == p["category"] else f"✗ ({b['category']} → {p['category']})"
            pri_ok = "✓" if b["priority"] == p["priority"] else f"✗ ({b['priority']} → {p['priority']})"
            print(f"  {t}")
            print(f"    分类: {cat_ok}")
            print(f"    优先级: {pri_ok}")
        print()

    if false_negatives:
        print("--- 遗漏条目 ---")
        for t in sorted(false_negatives):
            item = base_idx[t]
            print(f"  [{item['category']}] {t} ({item['priority']})")
        print()

    if false_positives:
        print("--- 新增条目（可能噪音） ---")
        for t in sorted(false_positives):
            item = prop_idx[t]
            print(f"  [{item['category']}] {t} ({item['priority']})")
        print()


if __name__ == "__main__":
    main()
