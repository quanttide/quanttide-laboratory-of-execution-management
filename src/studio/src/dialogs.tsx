import { useEffect, useRef, useState } from "react";
import { PRIORITIES, PRIORITY_ICON, type Priority, type Task } from "./todo";

/** 右键菜单：标记完成 / 优先级 / 设置开始日期 / 编辑 / 删除 */
export function ContextMenu({
  x,
  y,
  task,
  onToggle,
  onPriority,
  onSetStart,
  onEdit,
  onDelete,
}: {
  x: number;
  y: number;
  task: Task;
  onToggle: () => void;
  onPriority: (p: Priority) => void;
  onSetStart: () => void;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);

  // 贴近视口边缘时翻转菜单方向
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const overRight = rect.right > window.innerWidth;
    const overBottom = rect.bottom > window.innerHeight;
    if (overRight) el.style.left = `${x - rect.width}px`;
    if (overBottom) el.style.top = `${y - rect.height}px`;
  }, [x, y]);

  return (
    <div
      ref={ref}
      className="ctx-menu"
      style={{ left: x, top: y }}
      onClick={(e) => e.stopPropagation()}
      onContextMenu={(e) => {
        e.preventDefault();
        e.stopPropagation();
      }}
    >
      <button onClick={onToggle}>{task.done ? "✔ 标记未完成" : "✔ 标记完成"}</button>
      <div className="ctx-sep" />
      <div className="ctx-sub">
        <span className="ctx-label">⚡ 优先级</span>
        <div className="ctx-sub-items">
          {PRIORITIES.map((p) => (
            <button key={p} onClick={() => onPriority(p)}>
              {PRIORITY_ICON[p]} {p}优先级
            </button>
          ))}
        </div>
      </div>
      <button onClick={onSetStart}>🕐 设置开始日期</button>
      <button onClick={onEdit}>✎ 编辑任务</button>
      <div className="ctx-sep" />
      <button className="danger" onClick={onDelete}>
        🗑 删除任务
      </button>
    </div>
  );
}

function Dialog({
  title,
  children,
  onSave,
  onCancel,
}: {
  title: string;
  children: React.ReactNode;
  onSave: () => void;
  onCancel: () => void;
}) {
  return (
    <div className="overlay" onMouseDown={(e) => e.target === e.currentTarget && onCancel()}>
      <div className="dialog">
        <h3>{title}</h3>
        {children}
        <div className="dialog-actions">
          <button className="btn-cancel" onClick={onCancel}>
            取消
          </button>
          <button className="btn-save" onClick={onSave}>
            保存
          </button>
        </div>
      </div>
    </div>
  );
}

/** 编辑任务内容 */
export function EditDialog({
  initial,
  onSave,
  onCancel,
}: {
  initial: string;
  onSave: (value: string) => void;
  onCancel: () => void;
}) {
  const [value, setValue] = useState(initial);
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    ref.current?.focus();
  }, []);

  return (
    <Dialog
      title="编辑任务"
      onSave={() => onSave(value)}
      onCancel={onCancel}
    >
      <textarea
        ref={ref}
        className="edit-box"
        rows={6}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) onSave(value);
          if (e.key === "Escape") onCancel();
        }}
      />
    </Dialog>
  );
}

/** 设置开始日期（YYYY-MM-DD，留空清除） */
export function DateDialog({
  title,
  initial,
  onSave,
  onCancel,
}: {
  title: string;
  initial: string;
  onSave: (value: string) => void;
  onCancel: () => void;
}) {
  const [value, setValue] = useState(initial);
  const ref = useRef<HTMLInputElement>(null);

  useEffect(() => {
    ref.current?.focus();
    ref.current?.select();
  }, []);

  return (
    <Dialog title={title} onSave={() => onSave(value)} onCancel={onCancel}>
      <input
        ref={ref}
        className="date-dialog-input"
        placeholder="YYYY-MM-DD，留空清除"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") onSave(value);
          if (e.key === "Escape") onCancel();
        }}
      />
    </Dialog>
  );
}
