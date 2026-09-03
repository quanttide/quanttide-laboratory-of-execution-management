# 待办清单 · Studio

> 常驻桌面待办清单（[`lite/`](../lite/)）的 Web 版 —— 参考 tkinter 原版，使用 React 实现。
> 还原交互与猫猫配色（Catppuccin Mocha），数据保存在浏览器 localStorage。

## 功能对照（vs lite 桌面版）

| lite（tkinter） | studio（React Web） | 说明 |
| --- | --- | --- |
| 回车 / ＋ 添加任务 | 同 | 回车或「＋」 |
| 优先级 高/中/低 | 同 | 工具栏下拉选择 |
| 开始 / 截止日期 YYYY-MM-DD | 同 | 文本输入 + 格式校验，状态栏闪烁提示 |
| 未完成置前（优先级 → 截止日期），完成置后 | 同 | `sortTasks()` |
| ☐/☑ 勾选、✎ 编辑、✕ 删除 | 同 | 编辑为对话框（Ctrl/⌘+Enter 保存，Esc 取消） |
| 右键菜单：标记完成 / 优先级 / 设置开始日期 / 编辑 / 删除 | 同 | 自定义 ContextMenu，自适应视口边缘 |
| 🕐 今天开始 / N天后开始 / M月D日开始 | 同 | `startLabel()` |
| ⏰ 逾期N天（红）/ 今天截止 / 剩N天 / M月D日 | 同 | `dueLabel()`，逾期红色加粗 |
| 一键清理已完成 | 同 | 🗑 清理完成 |
| 状态栏 共 N 项 · 完成 M 项 · 🎉 | 同 | 全完成绿色高亮 |
| tasks.json 本地持久化 | localStorage | 键 `qt-todo-tasks-v1` |
| 窗口置顶 / 拖拽 / 缩放 / 半透明 | — | Web 无对应，省略 |

## 开发

```bash
npm install
npm run dev      # http://localhost:5173
npm run lint     # oxlint
npm run build    # tsc + vite build → dist/
```

## 结构

```
src/
├── main.tsx     # 入口
├── App.tsx      # 主界面与任务状态逻辑
├── dialogs.tsx  # 右键菜单 / 编辑对话框 / 日期对话框
├── todo.ts      # 任务类型、排序与日期标签纯函数
└── styles.css   # Catppuccin Mocha 主题
```
