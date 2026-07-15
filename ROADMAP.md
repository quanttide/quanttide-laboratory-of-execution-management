# ROADMAP

> `execute-distill` skill 的代码化实验。
>
> 目的：把 SKILL 中的 LLM 驱动的蒸馏流程翻译成可重复执行的 Python 脚本，验证分块提取 + 合并 + diff 的可行性。

---

## 阶段一：基础骨架

**目标**：搭出最小可用流程，验证 chunk → extract → merge → diff 闭环。

- [x] 实验目录结构确立（`experiments/default/`）
- [ ] `distill.py` 骨架：argparse + dry-run 模式
- [ ] `prompts/extract.md`：单段提取 prompt
- [ ] `prompts/merge.md`：去重合并 prompt
- [ ] `prompts/diff.md`：对比清单 prompt
- [ ] `requirements.txt`：`quanttide-agent`

**产出**：能跑通一条 journal 文件，输出提案。

---

## 阶段二：基于真实数据验证

**目标**：用已有 journal 反复调 prompt，直到 LLM 的分类和用户标注一致。

- [ ] 用 7/14 execution 日志跑一轮，看输出是否符合用户手动整理的清单
- [ ] 用 7/15 跑一轮，验证新条目能否被正确识别
- [ ] 调优 extract prompt：过滤"纯思考"、准确识别团队协作事项
- [ ] 调优 merge prompt：消除跨段落的重复候选
- [ ] 调优 diff prompt：正确区分新增/合并/移动/跳过

---

## 阶段三：集成与提交

**目标**：脚本能直接写入 profile 并 commit。

- [ ] `--apply` 模式：写入 `profile/index.md`
- [ ] 写入格式与现有 GTD 清单风格一致（板块顺序、优先级文字标注）
- [ ] 处理子模组路径（`data/profile/`）
- [ ] 可选 `--commit` flag 自动 commit

---

## 非目标

- 不做测试框架（实验阶段手动验证即可）
- 不做 pip 包发布
- 不包装成 agent skill（原 skill 已存在且够用）
- 不处理嵌套子模组以外的 git 工作流

---

## 评估标准

| 指标 | 达成条件 |
|---|---|
| 提案准确 | LLM 输出的条目与用户手动整理差异 ≤ 1 条 |
| 分类一致 | 类型和优先级判定与用户标注一致率 ≥ 80% |
| 不丢事项 | journal 中所有可执行事项都被识别（召回率 100%） |
| 不引入噪音 | 不输出明显不属于待办的内容 |
