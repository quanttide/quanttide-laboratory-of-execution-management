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
  chunk()   ──→ 按空行分割段落
     │
     ▼
  extract() ──→ 一次 LLM 调用 → JSON 候选条目（含分类/优先级/待讨论）
     │
     ▼
  diff()    ──→ 一次 LLM 调用 → JSON patch（additions / merges / discussions）
     │
     ▼
  apply()   ──→ 解析现有 profile → apply_patch → render_profile → 写入
```

patch 模式而非全量替换：diff 输出结构化变更指令，apply 做增量合并，避免 LLM 丢条目。

## 阶段一：基础骨架

**目标**：搭出最小可用流程，验证 chunk → extract → diff → output 闭环。

- [x] 实验目录结构确立（`examples/default/`）
- [x] 实验数据准备（journal + profile 基线）
- [x] ROADMAP
- [x] `.gitignore`：排除 `__pycache__`、`.venv`
- [x] `requirements.txt`：`quanttide-agent`
- [x] `prompts/extract.md`：文件级提取 prompt（含类型推定、优先级推定、待讨论标记、时间感知）
- [x] `prompts/diff.md`：语义 diff prompt（去重 + 对比，输出结构化 JSON patch）
- [x] `distill.py`：argparse + dry-run / apply / commit 模式，chunk → extract → diff → apply 闭环
- [x] `evaluate.py`：对比 baseline 与提案，打印召回率/精确率/F1/分类一致率/优先级一致率

**产出**：能跑通 journal 文件，输出结构化变更提案，evaluate 可对比 baseline。

## 阶段二：基于真实数据验证

**目标**：用已有 journal 反复调 prompt，直到 LLM 输出与用户手动整理一致。

### 2a — 调优 extract

- [x] 用 7/14 执行日志跑一轮，验证 extract 覆盖基线条目
- [x] 用 7/15 跑一轮，验证 asset-audit + 接新单的识别与分类
- [x] 调优 extract prompt：时间感知（已完成/已决策不做的排除）、分类规则（含典型错误示例）
- [ ] 验证待讨论通道：边界案例能否被正确标记为"待讨论"而非跳过

### 2b — 调优 diff

- [x] 固定 extract 输出后，调优 diff prompt：合并逻辑加强（语义匹配而非精确匹配）
- [ ] 验证：新增/合并/待讨论的判定与用户手动整理一致率 ≥ 80%

### 剩余问题

- extract 对日志内部时间线的理解已基本到位，但偶有遗漏（如已完成的"审查脚本"仍会在部分 run 中出现）
- diff 合并率从 0% 提升至 75%（v3 合并 3/4 条基线），但偶有因 LLM 非确定性导致的波动
- 待讨论通道尚未系统验证——当前输出中待讨论标记的出现与否存在随机性

## 阶段三：集成与提交

- [x] `--apply` 模式：写入 `data/profile/index.md`
- [x] 写入格式契约：
  - 板块顺序：日程 → 下一步行动 → 等待回复 → 悬而未决
  - 优先级文字标注：`> 优先级：高/中/低`，不用符号
  - 各板块内按优先级降序排列（高 → 中 → 低）
  - 空提案处理：若无新条目告知用户，不做变更
- [x] `commit()`：在子模组目录内用 subprocess 执行 git add + commit
- [x] `--commit` flag 自动 commit

## 非目标

- 不做测试框架（`evaluate.py` 是评测工具，不是测试框架）
- 不做 pip 包发布
- 不包装成 agent skill（原 skill 已存在且够用）
- 不处理嵌套子模组以外的 git 工作流

## 评估标准

| 指标 | 达成条件 | v3 表现 |
|---|---|---|
| 提案准确 | LLM 输出的条目与用户手动整理差异 ≤ 1 条 | 基线 4 条全部保留，新增 3 条无噪音 ≈ ✅ |
| 分类一致 | 类型和优先级判定与用户标注一致率 ≥ 80% | 3/3 新增条目分类正确，基线 4 条位置不变 |
| 不丢事项 | journal 中所有可执行事项都被识别（召回率 ≥ 90%） | 7/14 中 3 条全部识别，7/15 中 3 条全部识别 |
| 不引入噪音 | 不输出明显不属于待办的内容 | v3 输出 0 噪音 |
