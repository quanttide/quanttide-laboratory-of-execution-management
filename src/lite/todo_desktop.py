import json
import os
import tkinter as tk
from tkinter import ttk, font, simpledialog
from datetime import datetime, date

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(APP_DIR, "tasks.json")

BG = "#1e1e2e"
BG2 = "#27293d"
BG3 = "#313244"
FG = "#cdd6f4"
FG_MUTED = "#7f849c"
ACCENT = "#cba6f7"
GREEN = "#a6e3a1"
RED = "#f38ba8"
YELLOW = "#f9e2af"
BLUE = "#89b4fa"


class TodoApp:
    def __init__(self, root):
        self.root = root
        self.tasks = self.load_tasks()
        self.drag_data = None
        self.resize_data = None
        self.always_on_top = True

        self.font_body = font.Font(family="Microsoft YaHei UI", size=11)
        self.font_small = font.Font(family="Microsoft YaHei UI", size=9)
        self.font_strike = font.Font(family="Microsoft YaHei UI", size=11, overstrike=1)

        self.setup_window()
        self.build_ui()
        self.render()

    def setup_window(self):
        self.root.title("桌面待办清单")
        self.root.geometry("380x460")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.92)
        self.root.configure(bg=BG)
        self.position_at_right()

    def position_at_right(self):
        w = self.root.winfo_screenwidth()
        h = self.root.winfo_screenheight()
        self.root.geometry(f"+{w - 410}+{h - 600}")

    def build_ui(self):
        self.title_bar = tk.Frame(self.root, bg=BG3, height=38)
        self.title_bar.pack(fill="x")
        self.title_bar.pack_propagate(False)

        self.title_label = tk.Label(
            self.title_bar, text="📌 桌面待办", bg=BG3, fg=FG, font=self.font_body
        )
        self.title_label.pack(side="left", padx=12)

        self.btn_pin = tk.Button(
            self.title_bar,
            text="📌",
            bg=BG3,
            fg=FG_MUTED,
            relief="flat",
            activebackground=BG3,
            activeforeground=FG,
            cursor="hand2",
            bd=0,
            command=self.toggle_pin,
        )
        self.btn_pin.pack(side="right", padx=4, pady=4)

        self.btn_close = tk.Button(
            self.title_bar,
            text="✕",
            bg=BG3,
            fg=FG_MUTED,
            relief="flat",
            activebackground=RED,
            activeforeground="#ffffff",
            cursor="hand2",
            bd=0,
            command=self.root.destroy,
        )
        self.btn_close.pack(side="right", padx=6, pady=4)

        self.title_bar.bind("<Button-1>", self.start_drag)
        self.title_bar.bind("<B1-Motion>", self.on_drag)
        self.title_label.bind("<Button-1>", self.start_drag)
        self.title_label.bind("<B1-Motion>", self.on_drag)

        self.list_container = tk.Frame(self.root, bg=BG)
        self.list_container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(
            self.list_container, bg=BG, highlightthickness=0, bd=0
        )
        self.scrollbar = ttk.Scrollbar(
            self.list_container, orient="vertical", command=self.canvas.yview
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.task_frame = tk.Frame(self.canvas, bg=BG)
        self.task_window = self.canvas.create_window(
            (0, 0), window=self.task_frame, anchor="nw"
        )
        self.task_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.task_window, width=e.width),
        )
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.bind_mousewheel(self.list_container)
        self.bind_mousewheel(self.task_frame)

        self.input_frame = tk.Frame(self.root, bg=BG2)
        self.input_frame.pack(fill="x", side="bottom")

        self.entry = tk.Entry(
            self.input_frame,
            bg=BG3,
            fg=FG,
            insertbackground=FG,
            relief="flat",
            font=self.font_body,
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(10, 4), pady=8, ipady=5)
        self.entry.bind("<Return>", lambda e: self.add_task())

        self.btn_add = tk.Button(
            self.input_frame,
            text="＋",
            bg=ACCENT,
            fg="#1e1e2e",
            relief="flat",
            font=self.font_body,
            activebackground="#b4befe",
            activeforeground="#1e1e2e",
            cursor="hand2",
            bd=0,
            width=3,
            command=self.add_task,
        )
        self.btn_add.pack(side="right", padx=(0, 10), pady=8)

        self.toolbar = tk.Frame(self.root, bg=BG2)
        self.toolbar.pack(fill="x", side="bottom")

        self.pri_var = tk.StringVar(value="中")
        self.pri_menu = ttk.Combobox(
            self.toolbar,
            textvariable=self.pri_var,
            values=["高", "中", "低"],
            width=3,
            state="readonly",
            font=self.font_small,
        )
        self.pri_menu.pack(side="left", padx=(10, 4), pady=6)

        self.start_var = tk.StringVar(value="")
        self.btn_start = tk.Button(
            self.toolbar,
            text="🕐",
            bg=BG2,
            fg=GREEN,
            relief="flat",
            activebackground=BG3,
            cursor="hand2",
            bd=0,
            font=self.font_small,
            command=self.set_start_hint,
        )
        self.btn_start.pack(side="left", padx=2, pady=6)

        self.start_entry = tk.Entry(
            self.toolbar,
            bg=BG3,
            fg=YELLOW,
            insertbackground=FG,
            relief="flat",
            font=self.font_small,
            width=9,
        )
        self.start_entry.insert(0, "开始日期 YYYY-MM-DD")
        self.start_entry.config(fg=FG_MUTED)
        self.start_entry.bind("<FocusIn>", self.on_start_focus_in)
        self.start_entry.bind("<FocusOut>", self.on_start_focus_out)
        self.start_entry.pack(side="left", padx=4, pady=6)

        self.due_var = tk.StringVar(value="")
        self.btn_due = tk.Button(
            self.toolbar,
            text="📅",
            bg=BG2,
            fg=BLUE,
            relief="flat",
            activebackground=BG3,
            cursor="hand2",
            bd=0,
            font=self.font_small,
            command=self.set_due_dialog,
        )
        self.btn_due.pack(side="left", padx=2, pady=6)

        self.due_entry = tk.Entry(
            self.toolbar,
            bg=BG3,
            fg=YELLOW,
            insertbackground=FG,
            relief="flat",
            font=self.font_small,
            width=9,
        )
        self.due_entry.insert(0, "截止日期 YYYY-MM-DD")
        self.due_entry.config(fg=FG_MUTED)
        self.due_entry.bind("<FocusIn>", self.on_due_focus_in)
        self.due_entry.bind("<FocusOut>", self.on_due_focus_out)
        self.due_entry.pack(side="left", padx=4, pady=6)

        self.btn_clear_done = tk.Button(
            self.toolbar,
            text="🗑 清理完成",
            bg=BG2,
            fg=FG_MUTED,
            relief="flat",
            activebackground=BG3,
            activeforeground=RED,
            cursor="hand2",
            bd=0,
            font=self.font_small,
            command=self.clear_done,
        )
        self.btn_clear_done.pack(side="right", padx=10, pady=6)

        self.status_bar = tk.Label(
            self.root, text="", bg=BG2, fg=FG_MUTED, font=self.font_small, anchor="w"
        )
        self.status_bar.pack(fill="x", side="bottom")

        grip = tk.Frame(self.root, bg=BG2, width=14, height=14, cursor="size_nw_se")
        grip.pack(side="bottom", anchor="se", padx=0, pady=0)
        grip.bind("<Button-1>", self.start_resize)
        grip.bind("<B1-Motion>", self.on_resize)

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def bind_mousewheel(self, widget):
        widget.bind("<MouseWheel>", self.on_mousewheel)
        for child in widget.winfo_children():
            self.bind_mousewheel(child)

    def load_tasks(self):
        if not os.path.exists(DATA_FILE):
            return []
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def save_tasks(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=2)

    def add_task(self):
        text = self.entry.get().strip()
        if not text:
            return
        task = {
            "id": self.next_id(),
            "text": text,
            "done": False,
            "priority": self.pri_var.get(),
            "start": self.start_entry.get().strip() or "",
            "due": self.due_entry.get().strip() or "",
        }
        if task["start"] and not self.valid_date(task["start"]):
            self.flash_status("日期格式无效，请用 YYYY-MM-DD")
            return
        if task["due"] and not self.valid_date(task["due"]):
            self.flash_status("日期格式无效，请用 YYYY-MM-DD")
            return
        self.tasks.append(task)
        self.entry.delete(0, "end")
        self.save_tasks()
        self.render()

    def next_id(self):
        ids = [t["id"] for t in self.tasks]
        return max(ids, default=0) + 1

    def valid_date(self, s):
        try:
            datetime.strptime(s, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def toggle_done(self, task_id):
        for t in self.tasks:
            if t["id"] == task_id:
                t["done"] = not t["done"]
                break
        self.save_tasks()
        self.render()

    def delete_task(self, task_id):
        self.tasks = [t for t in self.tasks if t["id"] != task_id]
        self.save_tasks()
        self.render()

    def edit_task(self, task_id):
        t = next((x for x in self.tasks if x["id"] == task_id), None)
        if not t:
            return
        dlg = tk.Toplevel(self.root)
        dlg.title("编辑任务")
        dlg.configure(bg=BG2)
        dlg.transient(self.root)
        dlg.attributes("-topmost", True)
        dlg.grab_set()
        w = max(self.root.winfo_width(), 320)
        x = self.root.winfo_x() + (self.root.winfo_width() - w) // 2
        y = self.root.winfo_y() + 60
        dlg.geometry(f"{w}x240+{x}+{y}")

        lab = tk.Label(dlg, text="任务内容", bg=BG2, fg=FG, font=self.font_small, anchor="w")
        lab.pack(fill="x", padx=12, pady=(12, 4))
        box = tk.Text(
            dlg,
            bg=BG3,
            fg=FG,
            insertbackground=FG,
            relief="flat",
            font=self.font_body,
            wrap="word",
            height=6,
        )
        box.insert("1.0", t["text"])
        box.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        box.focus_set()

        def on_ok():
            val = box.get("1.0", "end-1c").strip()
            if not val:
                self.flash_status("内容不能为空")
                return
            t["text"] = val
            self.save_tasks()
            self.render()
            dlg.destroy()

        btn_frame = tk.Frame(dlg, bg=BG2)
        btn_frame.pack(fill="x", padx=12, pady=(0, 12))
        tk.Button(
            btn_frame,
            text="保存",
            bg=ACCENT,
            fg="#1e1e2e",
            relief="flat",
            activebackground="#b4befe",
            activeforeground="#1e1e2e",
            cursor="hand2",
            bd=0,
            font=self.font_small,
            command=on_ok,
        ).pack(side="right")
        tk.Button(
            btn_frame,
            text="取消",
            bg=BG3,
            fg=FG,
            relief="flat",
            activebackground=BG2,
            cursor="hand2",
            bd=0,
            font=self.font_small,
            command=dlg.destroy,
        ).pack(side="right", padx=(0, 8))
        dlg.bind("<Return>", lambda e: on_ok())
        dlg.bind("<Escape>", lambda e: dlg.destroy())

    def clear_done(self):
        self.tasks = [t for t in self.tasks if not t["done"]]
        self.save_tasks()
        self.render()

    def set_start_hint(self):
        text = self.start_entry.get().strip()
        if text and text != "开始日期 YYYY-MM-DD" and self.valid_date(text):
            self.flash_status(f"开始日期：{text}，回车或直接输入即可")
        else:
            self.flash_status("请在输入框输入 YYYY-MM-DD 格式日期")

    def on_start_focus_in(self, _):
        if self.start_entry.get() == "开始日期 YYYY-MM-DD":
            self.start_entry.delete(0, "end")
            self.start_entry.config(fg=FG)

    def on_start_focus_out(self, _):
        if not self.start_entry.get().strip():
            self.start_entry.insert(0, "开始日期 YYYY-MM-DD")
            self.start_entry.config(fg=FG_MUTED)

    def set_start_date(self, task_id):
        t = next((x for x in self.tasks if x["id"] == task_id), None)
        if not t:
            return
        current = t.get("start", "")
        val = simpledialog.askstring(
            "设置开始日期", "格式 YYYY-MM-DD，留空清除", initialvalue=current, parent=self.root
        )
        if val is None:
            return
        val = val.strip()
        if val and not self.valid_date(val):
            self.flash_status("日期格式无效，请用 YYYY-MM-DD")
            return
        t["start"] = val
        self.save_tasks()
        self.render()

    def set_due_dialog(self):
        text = self.due_entry.get().strip()
        if text and text != "截止日期 YYYY-MM-DD" and self.valid_date(text):
            self.flash_status(f"截止日期：{text}，回车或直接输入即可")
        else:
            self.flash_status("请在左侧输入框输入 YYYY-MM-DD 格式日期")

    def on_due_focus_in(self, _):
        if self.due_entry.get() == "截止日期 YYYY-MM-DD":
            self.due_entry.delete(0, "end")
            self.due_entry.config(fg=FG)

    def on_due_focus_out(self, _):
        if not self.due_entry.get().strip():
            self.due_entry.insert(0, "截止日期 YYYY-MM-DD")
            self.due_entry.config(fg=FG_MUTED)

    def change_priority(self, task_id, value):
        for t in self.tasks:
            if t["id"] == task_id:
                t["priority"] = value
                break
        self.save_tasks()
        self.render()

    def flash_status(self, msg):
        self.status_bar.config(text=msg)
        self.root.after(2500, lambda: self.status_bar.config(text=""))

    def priority_color(self, p):
        return {"高": RED, "中": YELLOW, "低": BLUE}.get(p, FG_MUTED)

    def priority_icon(self, p):
        return {"高": "🔴", "中": "🟡", "低": "🔵"}.get(p, "⚪")

    def start_label(self, start):
        if not start:
            return ""
        try:
            d = datetime.strptime(start, "%Y-%m-%d").date()
            today = date.today()
            delta = (d - today).days
            if delta == 0:
                return "今天开始"
            if delta > 0 and delta <= 3:
                return f"{delta}天后开始"
            return f"{d.month}月{d.day}日开始"
        except ValueError:
            return start

    def due_label(self, due):
        if not due:
            return ""
        try:
            d = datetime.strptime(due, "%Y-%m-%d").date()
            today = date.today()
            delta = (d - today).days
            if delta < 0:
                return f"逾期{days_label(-delta)}"
            if delta == 0:
                return "今天截止"
            if delta <= 3:
                return f"剩{delta}天"
            return f"{d.month}月{d.day}日"
        except ValueError:
            return due

    def render(self):
        for w in self.task_frame.winfo_children():
            w.destroy()

        active = [t for t in self.tasks if not t["done"]]
        done_list = [t for t in self.tasks if t["done"]]

        order_map = {"高": 0, "中": 1, "低": 2}
        active.sort(key=lambda t: (order_map.get(t["priority"], 9), t.get("due", "")))
        done_list.sort(key=lambda t: t["id"], reverse=True)

        all_tasks = active + done_list

        if not all_tasks:
            empty = tk.Label(
                self.task_frame,
                text="还没有任务\n在下方输入，回车添加 ✨",
                bg=BG,
                fg=FG_MUTED,
                font=self.font_body,
                justify="center",
            )
            empty.pack(pady=40)
            self.bind_mousewheel(empty)
            self.update_status()
            return

        for t in all_tasks:
            row = tk.Frame(self.task_frame, bg=BG)
            row.pack(fill="x", padx=8, pady=3)

            card = tk.Frame(row, bg=BG2)
            card.pack(fill="x")
            card.bind("<Button-3>", lambda e, tid=t["id"]: self.show_context_menu(e, tid))

            text_font = self.font_strike if t["done"] else self.font_body
            text_color = FG_MUTED if t["done"] else FG

            pri_lbl = tk.Label(
                card,
                text=self.priority_icon(t["priority"]),
                bg=BG2,
                fg=self.priority_color(t["priority"]),
                font=self.font_small,
            )
            pri_lbl.pack(side="left", padx=(8, 4), pady=6)
            pri_lbl.bind("<Button-3>", lambda e, tid=t["id"]: self.show_context_menu(e, tid))

            check_var = tk.StringVar(value="☑" if t["done"] else "☐")
            check_btn = tk.Button(
                card,
                textvariable=check_var,
                bg=BG2,
                fg=GREEN if t["done"] else FG_MUTED,
                relief="flat",
                activebackground=BG3,
                cursor="hand2",
                bd=0,
                font=self.font_body,
                command=lambda tid=t["id"]: self.toggle_done(tid),
            )
            check_btn.pack(side="left", padx=(0, 2), pady=6)

            text_lbl = tk.Label(
                card,
                text=t["text"],
                bg=BG2,
                fg=text_color,
                font=text_font,
                anchor="w",
                justify="left",
                wraplength=180,
            )
            text_lbl.pack(side="left", fill="x", expand=True, pady=6)
            text_lbl.bind("<Button-3>", lambda e, tid=t["id"]: self.show_context_menu(e, tid))

            start_text = self.start_label(t.get("start", ""))
            if start_text:
                start_lbl = tk.Label(
                    card,
                    text=f"🕐{start_text}",
                    bg=BG2,
                    fg=GREEN,
                    font=self.font_small,
                )
                start_lbl.pack(side="right", padx=(4, 0), pady=6)
                start_lbl.bind("<Button-3>", lambda e, tid=t["id"]: self.show_context_menu(e, tid))

            due_text = self.due_label(t.get("due", ""))
            if due_text:
                overdue = due_text.startswith("逾期") and not t["done"]
                due_lbl = tk.Label(
                    card,
                    text=f"⏰{due_text}",
                    bg=BG2,
                    fg=RED if overdue else FG_MUTED,
                    font=self.font_small,
                )
                due_lbl.pack(side="right", padx=(4, 8), pady=6)
                due_lbl.bind("<Button-3>", lambda e, tid=t["id"]: self.show_context_menu(e, tid))

            del_btn = tk.Button(
                card,
                text="✕",
                bg=BG2,
                fg=FG_MUTED,
                relief="flat",
                activebackground=BG3,
                activeforeground=RED,
                cursor="hand2",
                bd=0,
                font=self.font_small,
                command=lambda tid=t["id"]: self.delete_task(tid),
            )
            del_btn.pack(side="right", padx=(0, 6), pady=6)

            edit_btn = tk.Button(
                card,
                text="✎",
                bg=BG2,
                fg=BLUE,
                relief="flat",
                activebackground=BG3,
                activeforeground=BLUE,
                cursor="hand2",
                bd=0,
                font=self.font_small,
                command=lambda tid=t["id"]: self.edit_task(tid),
            )
            edit_btn.pack(side="right", padx=(0, 2), pady=6)

            self.bind_mousewheel(row)

        self.update_status()

    def update_status(self):
        total = len(self.tasks)
        done = sum(1 for t in self.tasks if t["done"])
        self.status_bar.config(text=f"共 {total} 项 · 完成 {done} 项" + (" · 🎉" if total and done == total else ""))

    def show_context_menu(self, event, task_id):
        menu = tk.Menu(self.root, tearoff=0)
        t = next((x for x in self.tasks if x["id"] == task_id), None)
        if not t:
            return
        if t["done"]:
            menu.add_command(label="✔ 标记未完成", command=lambda: self.toggle_done(task_id))
        else:
            menu.add_command(label="✔ 标记完成", command=lambda: self.toggle_done(task_id))
        menu.add_separator()
        pri_menu = tk.Menu(menu, tearoff=0)
        for p in ["高", "中", "低"]:
            pri_menu.add_command(
                label=f"{self.priority_icon(p)} {p}优先级",
                command=lambda v=p: self.change_priority(task_id, v),
            )
        menu.add_cascade(label="⚡ 优先级", menu=pri_menu)
        menu.add_command(label="🕐 设置开始日期", command=lambda: self.set_start_date(task_id))
        menu.add_command(label="✎ 编辑任务", command=lambda: self.edit_task(task_id))
        menu.add_separator()
        menu.add_command(label="🗑 删除任务", command=lambda: self.delete_task(task_id))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def start_drag(self, event):
        self.drag_data = (event.x_root - self.root.winfo_x(), event.y_root - self.root.winfo_y())

    def on_drag(self, event):
        if self.drag_data:
            x = event.x_root - self.drag_data[0]
            y = event.y_root - self.drag_data[1]
            self.root.geometry(f"+{x}+{y}")

    def start_resize(self, event):
        self.resize_data = (
            event.x_root,
            event.y_root,
            self.root.winfo_width(),
            self.root.winfo_height(),
        )

    def on_resize(self, event):
        if self.resize_data:
            dx = event.x_root - self.resize_data[0]
            dy = event.y_root - self.resize_data[1]
            w = max(self.resize_data[2] + dx, 260)
            h = max(self.resize_data[3] + dy, 300)
            self.root.geometry(f"{int(w)}x{int(h)}")

    def toggle_pin(self):
        self.always_on_top = not self.always_on_top
        self.root.attributes("-topmost", self.always_on_top)
        self.btn_pin.config(text="📌" if self.always_on_top else "📍", fg=ACCENT if self.always_on_top else FG_MUTED)


def days_label(n):
    return f"{n}天"


def main():
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
