# ROADMAP

> `execute-distill` skill 的代码化实验。
>
> 目的：把 SKILL 中的 LLM 驱动的蒸馏流程翻译成可重复执行的 Python 脚本，验证 chunk → extract → diff → output 闭环。

---

## 设计约束

- **无规则引擎**：分类、优先级、去重、对比全部由 LLM 完成
- **通过 `quanttide-agent` 调用 LLM**，不直接调用 API
- **默认收录**：journal 中的内容已是用户筛选过的，不确定时与用户讨论，不擅自跳过
- **范围**：包含业务拓展、获客等事项（不限于内部团队协作）

## 架构

```
journal file
     │
     ▼
  chunk()   ──→ 按空行分割段落（启发式，遇到问题再迭代）
     │
     ▼
  extract() ──→ 按文件一次调用 LLM，返回候选条目 + 待讨论条目
     │
     ▼
  diff()    ──→ 一次 LLM 调用，对比候选条目 + 现有 profile
                输出：新增 / 合并 / 移动 / 待讨论
     │
     ▼
  输出提案 (stdout) → 用户确认 → apply() 写入
```

一次语义 diff：去重合并和对比清单在同一 prompt 中完成，不再分两步。

## 阶段一：基础骨架

**目标**：搭出最小可用流程，验证 chunk → extract → diff → output 闭环。

- [x] 实验目录结构确立（`examples/default/`）
- [x] 实验数据准备（journal + profile 基线）
- [x] ROADMAP
- [ ] `distill.py`：argparse + dry-run 模式
- [ ] `prompts/extract.md`：文件级提取 prompt（含类型推定、优先级推定、待讨论标记）
- [ ] `prompts/diff.md`：语义 diff prompt（去重 + 对比清单，一次完成）
- [ ] `evaluate.py`：接受提案输出 + baseline，打印指标（召回率、精确率、分类一致率）
- [ ] `requirements.txt`：`quanttide-agent`
- [ ] `.gitignore`：排除 `__pycache__`、`.venv`

**产出**：能跑通一条 journal 文件，输出结构化变更提案，evaluate 可对比 baseline。

## 阶段二：基于真实数据验证

**目标**：用已有 journal 反复调 prompt，直到 LLM 的输出与用户手动整理一致。

子阶段：先固定 extract，再调 diff（避免级联干扰）。

### 2a — 调优 extract

- [ ] 用 7/14 执行日志跑一轮，看 extract 输出是否覆盖基线中的所有条目
- [ ] 用 7/15 跑一轮，验证 asset-audit + 接新单能否被识别
- [ ] 调优 extract prompt：提高候选条目召回率
- [ ] 验证待讨论通道：边界案例能否被正确标记为"待讨论"而非跳过

### 2b — 调优 diff

- [ ] 固定 extract 输出后，调优 diff prompt
- [ ] 验证：新增/合并/移动/待讨论的判定与用户手动整理一致率 ≥ 80%

## 阶段三：集成与提交

**目标**：脚本能直接写入 profile 并 commit。

- [ ] `--apply` 模式：写入 `data/profile/index.md`
- [ ] 写入格式契约（对应 SKILL 输出格式约束）：
  - 板块顺序：日程 → 下一步行动 → 等待回复 → 悬而未决
  - 优先级文字标注：`> 优先级：高/中/低`，不用符号
  - 各板块内按优先级降序排列（高 → 中 → 低）
  - 空提案处理：若无新条目告知用户，不做变更
- [ ] 处理子模组路径（`data/profile/`）
- [ ] 可选 `--commit` flag 自动 commit

## 非目标

- 不做测试框架（`evaluate.py` 是评测工具，不是测试框架）
- 不做 pip 包发布
- 不包装成 agent skill（原 skill 已存在且够用）
- 不处理嵌套子模组以外的 git 工作流

## 评估标准

| 指标 | 达成条件 |
|---|---|
| 提案准确 | LLM 输出的条目与用户手动整理差异 ≤ 1 条 |
| 分类一致 | 类型和优先级判定与用户标注一致率 ≥ 80% |
| 不丢事项 | journal 中所有可执行事项都被识别（召回率 ≥ 90%，完美目标 100%） |
| 不引入噪音 | 不输出明显不属于待办的内容 |
