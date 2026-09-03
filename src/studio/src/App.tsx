import { useEffect, useRef, useState } from "react";
import {
  PRIORITIES,
  PRIORITY_ICON,
  type Priority,
  type Task,
  cyclePriority,
  dueLabel,
  sortTasks,
  startLabel,
  validDate,
} from "./todo";
import { ContextMenu, DateDialog, EditDialog } from "./dialogs";

const STORAGE_KEY = "qt-todo-tasks-v1";

interface Flash {
  text: string;
  id: number;
}

export default function App() {
  const [tasks, setTasks] = useState<Task[]>(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? (JSON.parse(raw) as Task[]) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks));
  }, [tasks]);

  // 新建任务的输入栏
  const [text, setText] = useState("");
  const [priority, setPriority] = useState<Priority>("中");
  const [start, setStart] = useState("");
  const [due, setDue] = useState("");

  const [flash, setFlash] = useState<Flash | null>(null);
  const flashTimer = useRef<number | undefined>(undefined);

  // 右键菜单
  const [menu, setMenu] = useState<{ x: number; y: number; task: Task } | null>(
    null,
  );

  // 对话框（编辑 / 设置开始日期）
  const [editing, setEditing] = useState<Task | null>(null);
  const [dating, setDating] = useState<Task | null>(null);

  function flashStatus(msg: string) {
    setFlash({ text: msg, id: Date.now() });
    window.clearTimeout(flashTimer.current);
    flashTimer.current = window.setTimeout(() => setFlash(null), 2500);
  }

  function nextId(): number {
    return tasks.reduce((m, t) => Math.max(m, t.id), 0) + 1;
  }

  function addTask() {
    const t = text.trim();
    if (!t) return;
    if (start && !validDate(start)) {
      flashStatus("日期格式无效，请用 YYYY-MM-DD");
      return;
    }
    if (due && !validDate(due)) {
      flashStatus("日期格式无效，请用 YYYY-MM-DD");
      return;
    }
    setTasks((prev) => [
      ...prev,
      { id: nextId(), text: t, done: false, priority, start: start.trim(), due: due.trim() },
    ]);
    setText("");
    setStart("");
    setDue("");
  }

  function patchTask(id: number, patch: Partial<Task>) {
    setTasks((prev) => prev.map((t) => (t.id === id ? { ...t, ...patch } : t)));
  }

  function clearDone() {
    setTasks((prev) => prev.filter((t) => !t.done));
  }

  function handleDateDialogSave(value: string) {
    if (!dating) return;
    if (value && !validDate(value)) {
      flashStatus("日期格式无效，请用 YYYY-MM-DD");
      return;
    }
    patchTask(dating.id, { start: value });
    setDating(null);
  }

  function handleEditSave(value: string) {
    if (!editing) return;
    const v = value.trim();
    if (!v) {
      flashStatus("内容不能为空");
      return;
    }
    patchTask(editing.id, { text: v });
    setEditing(null);
  }

  // 点击空白处 / Escape 关闭菜单与对话框
  useEffect(() => {
    if (!menu && !editing && !dating) return;
    const close = () => {
      setMenu(null);
      setEditing(null);
      setDating(null);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    window.addEventListener("click", close);
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("click", close);
      window.removeEventListener("keydown", onKey);
    };
  }, [menu, editing, dating]);

  const total = tasks.length;
  const doneCount = tasks.filter((t) => t.done).length;
  const allDone = total > 0 && doneCount === total;

  return (
    <div className="app">
      <header className="title-bar">
        <span className="title">📌 待办清单</span>
        <span className="title-tag">lite · web</span>
      </header>

      <main className="list" onContextMenu={(e) => e.preventDefault()}>
        {tasks.length === 0 ? (
          <div className="empty">
            <p>还没有任务</p>
            <p className="empty-hint">在下方输入，回车添加 ✨</p>
          </div>
        ) : (
          <ul>
            {sortTasks(tasks).map((task) => (
              <TaskRow
                key={task.id}
                task={task}
                onToggle={() => patchTask(task.id, { done: !task.done })}
                onDelete={() => setTasks((prev) => prev.filter((t) => t.id !== task.id))}
                onEdit={() => setEditing(task)}
                onCyclePriority={() =>
                  patchTask(task.id, { priority: cyclePriority(task.priority) })
                }
                onContextMenu={(e) => {
                  e.preventDefault();
                  setMenu({ x: e.clientX, y: e.clientY, task });
                }}
              />
            ))}
          </ul>
        )}
      </main>

      <section className="input-bar">
        <input
          className="text-input"
          placeholder="添加任务，回车确认"
          value={text}
          autoFocus
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") addTask();
          }}
        />
        <button className="btn-add" title="添加" onClick={addTask}>
          ＋
        </button>
      </section>

      <section className="toolbar">
        <select
          className="pri-select"
          value={priority}
          onChange={(e) => setPriority(e.target.value as Priority)}
        >
          {PRIORITIES.map((p) => (
            <option key={p} value={p}>
              {PRIORITY_ICON[p]} {p}
            </option>
          ))}
        </select>
        <span className="date-icon">🕐</span>
        <input
          className="date-input"
          placeholder="开始日期 YYYY-MM-DD"
          value={start}
          onChange={(e) => setStart(e.target.value)}
        />
        <span className="date-icon">📅</span>
        <input
          className="date-input"
          placeholder="截止日期 YYYY-MM-DD"
          value={due}
          onChange={(e) => setDue(e.target.value)}
        />
        <button className="btn-clear" title="清理已完成" onClick={clearDone}>
          🗑 清理完成
        </button>
      </section>

      <footer className={`status-bar${allDone ? " all-done" : ""}`}>
        {flash ? (
          <span className="flash">{flash.text}</span>
        ) : (
          <span>
            共 {total} 项 · 完成 {doneCount} 项{allDone ? " · 🎉" : ""}
          </span>
        )}
      </footer>

      {menu && (
        <ContextMenu
          x={menu.x}
          y={menu.y}
          task={menu.task}
          onToggle={() => patchTask(menu.task.id, { done: !menu.task.done })}
          onPriority={(p) => patchTask(menu.task.id, { priority: p })}
          onSetStart={() => {
            setMenu(null);
            setDating(menu.task);
          }}
          onEdit={() => {
            setMenu(null);
            setEditing(menu.task);
          }}
          onDelete={() => {
            setMenu(null);
            setTasks((prev) => prev.filter((t) => t.id !== menu.task.id));
          }}
        />
      )}

      {editing && (
        <EditDialog
          initial={editing.text}
          onSave={handleEditSave}
          onCancel={() => setEditing(null)}
        />
      )}
      {dating && (
        <DateDialog
          title="设置开始日期"
          initial={dating.start}
          onSave={handleDateDialogSave}
          onCancel={() => setDating(null)}
        />
      )}
    </div>
  );
}

function TaskRow({
  task,
  onToggle,
  onDelete,
  onEdit,
  onCyclePriority,
  onContextMenu,
}: {
  task: Task;
  onToggle: () => void;
  onDelete: () => void;
  onEdit: () => void;
  onCyclePriority: () => void;
  onContextMenu: (e: React.MouseEvent) => void;
}) {
  const startText = startLabel(task.start);
  const dueText = dueLabel(task.due);
  const overdue = dueText.startsWith("逾期") && !task.done;

  return (
    <li className={`card${task.done ? " done" : ""}`} onContextMenu={onContextMenu}>
      <button
        className="pri-dot"
        title={`${task.priority}优先级（点击切换）`}
        onClick={onCyclePriority}
      >
        {PRIORITY_ICON[task.priority]}
      </button>
      <button className="check" title={task.done ? "标记未完成" : "标记完成"} onClick={onToggle}>
        {task.done ? "☑" : "☐"}
      </button>
      <span className="text">{task.text}</span>
      {startText && (
        <span className="tag start" title="开始日期">
          🕐{startText}
        </span>
      )}
      {dueText && (
        <span className={`tag due${overdue ? " overdue" : ""}`} title="截止日期">
          ⏰{dueText}
        </span>
      )}
      <span className="row-actions">
        <button className="act edit" title="编辑任务" onClick={onEdit}>
          ✎
        </button>
        <button className="act del" title="删除任务" onClick={onDelete}>
          ✕
        </button>
      </span>
    </li>
  );
}
