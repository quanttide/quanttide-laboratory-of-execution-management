# ROADMAP

> `execute-distill` skill 的代码化实验。
>
> 目的：把 SKILL 中的 LLM 驱动的蒸馏流程翻译成可重复执行的 Python 脚本，验证 chunk → extract → merge → diff 闭环。

---

## 设计约束

- **无规则引擎**：分类、优先级、去重、对比全部由 LLM 完成
- **通过 `quanttide-agent` 调用 LLM**，不直接调用 API
- **默认收录**：journal 中的内容已是用户筛选过的，不确定时与用户讨论，不擅自跳过
- **范围**：包含业务拓展、获客等事项（不限于内部团队协作）

## 架构

```
journal text
     │
     ▼
  chunk()   ──→ 按空行分割段落
     │
     ▼
  extract() ──→ 每段调 LLM，判断是否含可执行事项
     │
     ▼
  merge()   ──→ LLM 去重合并
     │
     ▼
  diff()    ──→ LLM 对比现有 profile，生成变更提案
     │
     ▼
  输出提案 (stdout) → 用户确认 → apply() 写入
```

## 阶段一：基础骨架

**目标**：搭出最小可用流程，验证 chunk → extract → merge → diff → output 闭环。

- [x] 实验目录结构确立（`experiments/default/`）
- [x] 实验数据准备（journal + profile 基线）
- [x] ROADMAP
- [ ] `distill.py`：argparse + dry-run 模式
- [ ] `prompts/extract.md`：单段提取 prompt
- [ ] `prompts/merge.md`：去重合并 prompt
- [ ] `prompts/diff.md`：对比清单 prompt
- [ ] `requirements.txt`：`quanttide-agent`
- [ ] .gitignore：排除 __pycache__

**产出**：能跑通一条 journal 文件，输出结构化变更提案。

## 阶段二：基于真实数据验证

**目标**：用已有 journal 反复调 prompt，直到 LLM 的输出与用户手动整理一致。

- [ ] 用 7/14 execution 日志跑一轮，看输出是否符合用户手动整理的基线
- [ ] 用 7/15 跑一轮，验证 asset-audit + 接新单能否被正确识别为新增
- [ ] 调优 extract prompt：准确识别可执行事项
- [ ] 调优 merge prompt：消除跨段落的重复候选
- [ ] 调优 diff prompt：正确区分新增/合并/移动/跳过

## 阶段三：集成与提交

**目标**：脚本能直接写入 profile 并 commit。

- [ ] `--apply` 模式：写入 `data/profile/index.md`
- [ ] 写入格式与现有 GTD 清单风格一致（板块顺序、优先级文字标注）
- [ ] 处理子模组路径（`data/profile/`）
- [ ] 可选 `--commit` flag 自动 commit

## 非目标

- 不做测试框架（实验阶段手动验证即可）
- 不做 pip 包发布
- 不包装成 agent skill（原 skill 已存在且够用）
- 不处理嵌套子模组以外的 git 工作流

## 评估标准

| 指标 | 达成条件 |
|---|---|
| 提案准确 | LLM 输出的条目与用户手动整理差异 ≤ 1 条 |
| 分类一致 | 类型和优先级判定与用户标注一致率 ≥ 80% |
| 不丢事项 | journal 中所有可执行事项都被识别（召回率 100%） |
| 不引入噪音 | 不输出明显不属于待办的内容 |
