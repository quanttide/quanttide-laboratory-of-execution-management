export type Priority = "高" | "中" | "低";

export const PRIORITIES: Priority[] = ["高", "中", "低"];

export interface Task {
  id: number;
  text: string;
  done: boolean;
  priority: Priority;
  /** YYYY-MM-DD 或空串 */
  start: string;
  /** YYYY-MM-DD 或空串 */
  due: string;
}

export const PRIORITY_ICON: Record<Priority, string> = {
  高: "🔴",
  中: "🟡",
  低: "🔵",
};

const PRIORITY_ORDER: Record<Priority, number> = { 高: 0, 中: 1, 低: 2 };

/** 未完成在前（高→中→低，同级按截止日期升序），完成在后（新→旧） */
export function sortTasks(tasks: Task[]): Task[] {
  const active = tasks
    .filter((t) => !t.done)
    .sort(
      (a, b) =>
        PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority] ||
        a.due.localeCompare(b.due),
    );
  const done = tasks
    .filter((t) => t.done)
    .sort((a, b) => b.id - a.id);
  return [...active, ...done];
}

/** 本地时区的今天，格式 YYYY-MM-DD */
export function todayStr(): string {
  const d = new Date();
  const m = `${d.getMonth() + 1}`.padStart(2, "0");
  const day = `${d.getDate()}`.padStart(2, "0");
  return `${d.getFullYear()}-${m}-${day}`;
}

export function validDate(s: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(s)) return false;
  const d = new Date(`${s}T00:00:00`);
  return !Number.isNaN(d.getTime());
}

function daysDiff(dateStr: string): number {
  const d = new Date(`${dateStr}T00:00:00`);
  const t = new Date(`${todayStr()}T00:00:00`);
  return Math.round((d.getTime() - t.getTime()) / 86_400_000);
}

function monthDay(dateStr: string): string {
  const [, m, day] = dateStr.split("-");
  return `${Number(m)}月${Number(day)}日`;
}

/** 开始日期提示：今天开始 / N天后开始（≤3 天）/ M月D日开始 */
export function startLabel(start: string): string {
  if (!start) return "";
  if (!validDate(start)) return start;
  const delta = daysDiff(start);
  if (delta === 0) return "今天开始";
  if (delta > 0 && delta <= 3) return `${delta}天后开始`;
  return `${monthDay(start)}开始`;
}

/** 截止日期提示：逾期N天 / 今天截止 / 剩N天（≤3 天）/ M月D日 */
export function dueLabel(due: string): string {
  if (!due) return "";
  if (!validDate(due)) return due;
  const delta = daysDiff(due);
  if (delta < 0) return `逾期${-delta}天`;
  if (delta === 0) return "今天截止";
  if (delta <= 3) return `剩${delta}天`;
  return monthDay(due);
}
