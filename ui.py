
import tkinter as tk
import uuid
from tkinter import ttk, filedialog
import os
import sys
import shutil
import json

from parser import *
from pathlib import Path
from config import *
from data import load_tasks, save_tasks, load_report, save_report


class TaskApp:
    def __init__(self, root):

        self.root = root
        self.root.title("Task Manager")
        self.root.geometry("1200x600")

        self.tasks = load_tasks()
        for task in self.tasks:
            self.ensure_folder_id(task)

        save_tasks(self.tasks)

        self.segment_filter = set()
        self.setup_styles()


        self.build_ui()
        self.refresh_table()


    def ensure_folder_id(self, task):
        if "folder_id" not in task or not task["folder_id"]:
            task["folder_id"] = str(uuid.uuid4())

    def open_task_folder(self, task):
        folder_id = task.get("folder_id")

        if not folder_id:
            return

        path = Path("tasks") / folder_id
        abs_path = os.path.abspath(path)


        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            save_tasks(self.tasks)

        if sys.platform == "win32":
            os.startfile(abs_path)

        elif sys.platform == "darwin":
            os.system(f'open "{abs_path}"')

        else:
            os.system(f'xdg-open "{abs_path}"')

    def setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except:
            pass

        style.configure(".", font=default_font)
        style.configure("Treeview.Heading", font=bold_font)


        self.root.configure(bg=bg)

        style.configure("Treeview",
                        background=field_bg,
                        foreground=fg,
                        fieldbackground=field_bg,
                        rowheight=35)

        style.map("Treeview",
                  background=[("selected", "#2f4f4f")],
                  foreground=[("selected", "#ffffff")]
                  )

        style.map("Treeview.Heading",
                  background=[
                      ("active", "#2b2b2b"),
                      ("pressed", "#1f1f1f")
                  ],
                  foreground=[
                      ("active", "#cccccc"),
                      ("pressed", "#ffffff")
                  ]
                  )

        style.configure("TCombobox",
                        fieldbackground=field_bg,
                        background=field_bg,
                        foreground=bg,
                        bordercolor=field_bg,
                        lightcolor=field_bg,
                        darkcolor=field_bg,
                        arrowcolor=fg
                        )
        style.map("TCombobox",
                  fieldbackground=[("readonly", field_bg)],
                  background=[("readonly", field_bg)],
                  foreground=[("readonly", fg)]
                  )

        style.configure("Colored.TCombobox",
                        fieldbackground=field_bg,
                        background=field_bg,
                        foreground=fg)

        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=fg)
        style.configure("TButton", background=bg, foreground=fg)
        style.configure("TEntry", fieldbackground=field_bg, foreground=fg)
        style.configure("TPanedwindow", background=bg)



    def get_row_tag(self, task):
        values = [
            task.get("pentest/audit", "").lower(),
            task.get("compliance", "").lower()
        ]

        if any(v == "не запущен" for v in values):
            return "red"
        elif any(v == "запущен" for v in values):
            return "yellow"
        elif all(v == "отчет готов" for v in values if v):
            return "green"

        return ""

    def auto_fill_from_system(self, task):
        for t in self.tasks:
            if t is task:
                continue

            if t["name"].strip().lower() == task["name"].strip().lower():
                task["secure"] = t.get("secure", "")
                task["full_name"] = t.get("full_name", "")
                break

    def open_report(self):
        win = tk.Toplevel(self.root)
        win.title("Отчет")
        win.geometry("600x600")
        win.configure(bg=bg)

        columns = ("week", "scans", "closed")

        tree = ttk.Treeview(win, columns=columns, show="headings")
        tree.heading("week", text="Неделя")
        tree.heading("scans", text="Сканы")
        tree.heading("closed", text="Закрытые")
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        from datetime import datetime, timedelta

        report_data = load_report()

        def get_week_range(offset=0):
            today = datetime.now()


            friday = today - timedelta(days=(today.weekday() - 4) % 7)

            friday = friday + timedelta(days=7 * offset)

            thursday = friday + timedelta(days=6)

            return f"{friday.strftime('%d.%m')} - {thursday.strftime('%d.%m')}"

        def refresh():
            tree.delete(*tree.get_children())
            for row in report_data:
                tree.insert("", tk.END, values=(row["week"], row["scans"], row["closed"]))

        def add_week():
            current_week = get_week_range(0)
            next_week = get_week_range(1)

            existing_weeks = {row["week"] for row in report_data}


            if current_week in existing_weeks and next_week in existing_weeks:
                return

            if current_week not in existing_weeks:
                new_week = current_week
            else:
                new_week = next_week

            report_data.append({
                "week": new_week,
                "scans": 0,
                "closed": 0
            })

            save_report(report_data)
            refresh()

        def change_value(field, delta):
            selected = tree.selection()
            if not selected:
                return

            index = tree.index(selected[0])
            report_data[index][field] += delta

            if report_data[index][field] < 0:
                report_data[index][field] = 0

            save_report(report_data)
            refresh()


        btn_frame = tk.Frame(win, bg=bg)
        btn_frame.pack(fill=tk.X, pady=5)

        tk.Button(btn_frame, text="+ Сканы", command=lambda: change_value("scans", 1)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="- Сканы", command=lambda: change_value("scans", -1)).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="+ Закрытые", command=lambda: change_value("closed", 1)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="- Закрытые", command=lambda: change_value("closed", -1)).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="Добавить неделю", command=add_week).pack(side=tk.RIGHT, padx=5)

        refresh()
    def get_selected_task(self):
        sel = self.tree.selection()
        if not sel:
            return None

        item = sel[0]
        tag = self.tree.item(item, "tags")[0]

        for task in self.tasks:
            if str(id(task)) == tag:
                return task

        return None

    def load_docx(self):
        task = self.get_selected_task()
        if not task:
            return

        path = filedialog.askopenfilename(
            filetypes=[("Word files", "*.docx")]
        )
        if not path:
            return

        rows = extract_docx_table(path)

        filtered = []
        for r in rows[1:]:
            if len(r) >= 8:
                filtered.append([r[1], r[2], r[3], r[5], r[6], r[8]])

        self.table.delete(*self.table.get_children())

        for row in filtered:
            self.table.insert("", tk.END, values=row)

        self.save_table_to_task(filtered)
        self.apply_segment_filter()
        self.update_ip_count()

    def add_task(self):
        folder_id = str(uuid.uuid4())

        task = {
            "id": "RF",
            "name": "АС",
            "type": "",
            "mp8": "",
            "secure": "Не задан",
            "status": "В работе",
            "full_name": "",
            "second_id": "SD",
            "pentest/audit": "Не запущен",
            "compliance": "Не запущен",
            "comment": "",
            "folder_id": folder_id
        }

        self.tasks.append(task)

        folder_path = Path("tasks") / folder_id
        folder_path.mkdir(parents=True, exist_ok=True)

        save_tasks(self.tasks)
        self.refresh_table()

    def delete_task(self):
        sel = self.tree.selection()
        if not sel:
            return

        task = self.get_selected_task()
        if not task:
            return

        self.ensure_folder_id(task)

        folder_path = Path("tasks") / task["folder_id"]

        if folder_path.exists():
            shutil.rmtree(folder_path)

        self.tasks.remove(task)

        save_tasks(self.tasks)
        self.refresh_table()

    def copy_to_clipboard(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()

    def copy_all_ips(self):
        if not hasattr(self, "table"):
            return

        ips = []


        for item in self.table.get_children():
            row = self.table.item(item)["values"]

            if len(row) >= 5:
                ip = row[4]  # IP колонка
                if ip:
                    ips.append(str(ip))

        if not ips:
            return

        text = "\n".join(ips)

        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()

    def open_segment_filter(self):
        if not hasattr(self, "table"):
            return

        win = tk.Toplevel(self.root)
        win.title("Фильтр Segment")
        win.geometry("300x400")

        segments = set()

        for item in self.table.get_children():
            row = self.table.item(item)["values"]
            if len(row) >= 6 and row[5]:
                segments.add(str(row[5]))

        segments = sorted(list(segments))

        vars_map = {}

        frame = tk.Frame(win)
        frame.pack(fill=tk.BOTH, expand=True)

        for seg in segments:
            var = tk.BooleanVar(value=(seg in self.segment_filter))

            chk = tk.Checkbutton(frame, text=seg, variable=var)
            chk.pack(anchor="w")

            vars_map[seg] = var

        def apply():
            self.segment_filter = {
                seg for seg, var in vars_map.items() if var.get()
            }

            self.apply_segment_filter()
            win.destroy()

        tk.Button(win, text="Apply", command=apply).pack(fill=tk.X)

    def apply_segment_filter(self):
        if not hasattr(self, "table"):
            return

        self.table.delete(*self.table.get_children())

        task = self.get_selected_task()
        if not task:
            return

        path = Path("tasks") / task["folder_id"] / "table.json"

        if not path.exists():
            return

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for row in data:
            segment = str(row[5]) if len(row) >= 6 else ""

            if self.segment_filter and segment not in self.segment_filter:
                continue

            self.table.insert("", tk.END, values=row)
        self.update_ip_count()


    def build_ui(self):
        self.paned = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)

        self.left = ttk.Frame(self.paned, )
        self.right = ttk.Frame(self.paned, width=320)

        self.paned.add(self.left, weight=1)
        self.paned.add(self.right, weight=11)


        self.filter_frame = ttk.Frame(self.left)
        self.filter_frame.pack(fill=tk.X)

        self.filter_name = tk.StringVar()
        self.filter_status = tk.StringVar()

        tk.Label(self.filter_frame, text="Поиск:").pack(side=tk.LEFT, padx=5, pady=5)
        tk.Entry(self.filter_frame, textvariable=self.filter_name).pack(side=tk.LEFT, padx=5, pady=5)

        tk.Label(self.filter_frame, text="Статус:").pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Combobox(
            self.filter_frame,
            textvariable=self.filter_status,
            values=["", "В работе", "Ожидание", "Закрыто"],
            state="readonly",
            width=15
        ).pack(side=tk.LEFT)

        tk.Button(self.filter_frame, text="+", command=self.add_task).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(self.filter_frame, text="-", command=self.delete_task).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(self.filter_frame, text="Отчет", command=self.open_report).pack(side=tk.LEFT, padx=5, pady=5)


        self.tree = ttk.Treeview(self.left, columns=("ID", "Name", "Status"), show="headings")
        self.tree.heading("ID", text="Номер")
        self.tree.heading("Name", text="Система")
        self.tree.heading("Status", text="Статус")
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.details_frame = ttk.Frame(self.right)
        self.details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.bottom_panel = ttk.Frame(self.right)
        self.bottom_panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # фрейм для кнопок
        self.buttons_row = ttk.Frame(self.bottom_panel)
        self.buttons_row.pack(fill=tk.X, pady=5)

        btn_load = tk.Button(
            self.buttons_row,
            text="Загрузить DOCX",
            command=self.load_docx
        )
        btn_load.pack(side=tk.LEFT, padx=5)

        btn_copy_ip = tk.Button(
            self.buttons_row,
            text="Скопировать IP",
            command=self.copy_all_ips
        )
        btn_copy_ip.pack(side=tk.LEFT, padx=5)

        btn_filt_segment = tk.Button(
            self.buttons_row,
            text="Фильтр Segment",
            command=self.open_segment_filter
        )
        btn_filt_segment.pack(side=tk.LEFT, padx=5)

        self.table = ttk.Treeview(
            self.bottom_panel,
            columns=("c1", "c2", "c3", "c4", "c5", "c6"),
            show="headings",
            height=10,
            selectmode="extended"
        )

        headers = ["OS", "DB", "Instances", "Window", "IP", "Segment"]

        for i, h in enumerate(headers):
            self.table.heading(f"c{i + 1}", text=h)
            self.table.column(f"c{i + 1}", width=120)

        self.ip_count_label = tk.Label(
            self.bottom_panel,
            text="IP: 0",
            bg=bg,
            fg=fg,
            anchor="w"
        )
        self.ip_count_label.pack(fill=tk.X, pady=5)


        self.table.pack(fill=tk.BOTH, expand=True)




        # events
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<Double-1>", lambda e: self.edit_any_cell(e, self.tree))



        self.filter_name.trace_add("write", lambda *args: self.refresh_table())
        self.filter_status.trace_add("write", lambda *args: self.refresh_table())

    def update_ip_count(self):
        if not hasattr(self, "table"):
            return

        count = 0

        for item in self.table.get_children():
            row = self.table.item(item)["values"]

            if len(row) >= 5:
                ip = str(row[4]).strip()
                if ip:
                    count += 1

        self.ip_count_label.config(text=f"IP: {count}")

    def refresh_table(self):
        self.tree.delete(*self.tree.get_children())

        search = self.filter_name.get().lower()
        status = self.filter_status.get()

        for task in self.tasks:
            if search:
                if search not in task["name"].lower() and search not in task["id"].lower():
                    continue

            if status and task.get("status") != status:
                continue

            tag = self.get_row_tag(task)

            self.tree.insert(
                "",
                tk.END,
                values=(
                    task["id"],
                    task["name"],
                    task.get("status", "")
                ),
                tags=(str(id(task)), tag)
            )

    def update_status(self, task, status):
        task["status"] = status
        save_tasks(self.tasks)
        self.refresh_table()
        self.on_select(None)


    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return

        task = self.get_selected_task()
        if not task:
            return

        for widget in self.details_frame.winfo_children():
            if widget != getattr(self, "bottom_panel", None):
                widget.destroy()


        tk.Label(self.details_frame,
                 text=f"{task['id']} — {task['name']}",
                 bg=field_bg, fg=fg, font=bold_font
                 ).pack(anchor="w", pady=5)

        def editable_field(title, key):
            bg_color = field_bg


            frame = tk.Frame(self.details_frame, bg=bg_color)
            frame.pack(fill=tk.X, pady=2)

            def get_color(value):
                v = value.lower()

                if v == "не запущен":
                    return "#8b2e2e"
                elif v == "запущен":
                    return "#8b7a1a"
                elif v == "отчет готов":
                    return "#2e6b3a"

                return field_bg

            value = task.get(key, "")

            label_bg = field_bg
            if key in ["pentest/audit", "compliance"]:
                label_bg = get_color(value)

            label = tk.Label(
                frame,
                text=title,
                bg=label_bg,
                fg=fg,
                width=18,
                anchor="w"
            )
            label.pack(side=tk.LEFT)

            value = task.get(key, "")

            if title in FIELD_OPTIONS:
                entry = ttk.Combobox(
                    frame,
                    values=FIELD_OPTIONS[title],
                    state="readonly"
                )
                entry.set(value)

            else:
                entry = tk.Entry(frame, bg=bg_color, fg=fg, insertbackground=fg)
                entry.insert(0, value)

            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

            def save(event=None):
                task[key] = entry.get()
                save_tasks(self.tasks)
                self.on_select(None)


            entry.bind("<FocusOut>", save)
            entry.bind("<Return>", save)

            if title in ["Номер RF", "Номер SD", "Полное имя"]:
                btn = tk.Button(
                    frame,
                    text="📋",
                    command=lambda v=value: self.copy_to_clipboard(v),
                    bg=field_bg,
                    fg=fg,
                    relief="flat",
                    width=2
                )
                btn.pack(side=tk.RIGHT, padx=5)

        editable_field("Название АС", "name")
        editable_field("Тип работ", "type")
        editable_field("Номер задачи MP8", "mp8")
        editable_field("PCI DSS", "secure")
        editable_field("Номер RF", "id")
        editable_field("Статус", "status")
        editable_field("Пентест/Аудит", "pentest/audit")
        editable_field("СКИБ", "compliance")
        editable_field("Полное имя", "full_name")
        editable_field("Номер SD", "second_id")
        editable_field("Комментарий", "comment")

        tk.Label(self.details_frame,
                 text="Комментарий:",
                 bg=field_bg, fg=fg, font=bold_font
                 ).pack(anchor="w", pady=(10, 2))

        comment = tk.Text(self.details_frame,
                          height=6,
                          wrap="word",
                          bg=field_bg,
                          fg=fg,
                          insertbackground=fg)

        comment.insert("1.0", task["comment"])
        comment.pack(fill=tk.BOTH)

        def save_comment(event=None):
            task["comment"] = comment.get("1.0", tk.END).strip()
            save_tasks(self.tasks)

        comment.bind("<FocusOut>", save_comment)

        btns = tk.Frame(self.details_frame, bg=field_bg)
        btns.pack(fill=tk.X, pady=10)

        tk.Button(
            btns,
            text="Папка",
            command=lambda: self.open_task_folder(task)
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(btns, text="В работу",
                  command=lambda: self.update_status(task, "В работе")
                  ).pack(side=tk.LEFT, padx=2)

        tk.Button(btns, text="Ожидание",
                  command=lambda: self.update_status(task, "Ожидание")
                  ).pack(side=tk.LEFT, padx=2)

        tk.Button(btns, text="Закрыто",
                  command=lambda: self.update_status(task, "Закрыто")
                  ).pack(side=tk.LEFT, padx=2)
        self.segment_filter = set()
        self.load_task_table(task)

    def load_task_table(self, task):
        folder = Path("tasks") / task["folder_id"]
        path = folder / "table.json"

        self.table.delete(*self.table.get_children())

        if not path.exists():
            return

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for row in data:
            self.table.insert("", tk.END, values=row)
        self.update_ip_count()

    def edit_any_cell(self, event, table):
        region = table.identify("region", event.x, event.y)
        if region != "cell":
            return

        row = table.identify_row(event.y)
        col = table.identify_column(event.x)

        x, y, w, h = table.bbox(row, col)

        item = table.item(row)
        values = list(item["values"])
        col_i = int(col[1:]) - 1

        field = None

        entry = tk.Entry(table)
        entry.place(x=x, y=y, width=w, height=h)
        entry.insert(0, values[col_i])
        entry.focus()

        def save(event=None):
            new = entry.get()
            values[col_i] = new
            table.item(row, values=values)

            sel = self.tree.selection()
            if not sel:
                entry.destroy()
                return

            task = self.get_selected_task()
            if not task:
                entry.destroy()
                return

            if table == self.tree:
                if col_i == 0:
                    task["id"] = new
                elif col_i == 1:
                    task["name"] = new
                    self.auto_fill_from_system(task)
                elif col_i == 2:
                    task["status"] = new


            else:

                if field == "Название АС":
                    task["name"] = new
                elif field == "Тип работ":
                    task["type"] = new
                elif field == "PCI DSS":
                    task["secure"] = new
                elif field == "Номер RF":
                    task["id"] = new
                elif field == "Номер задачи MP8":
                    task["mp8"] = new
                elif field == "Статус":
                    task["status"] = new
                elif field == "Полное имя":
                    task["full_name"] = new
                elif field == "Номер SD":
                    task["second_id"] = new
                elif field == "Пентест/Аудит":
                    task["pentest/audit"] = new
                elif field == "СКИБ":
                    task["compliance"] = new
                elif field == "Комментарий":
                    task["comment"] = new

            save_tasks(self.tasks)
            self.refresh_table()
            self.on_select(None)
            entry.destroy()

        entry.bind("<Return>", save)
        entry.bind("<FocusOut>", save)

    def save_table_to_task(self, data):
        task = self.get_selected_task()
        if not task:
            return

        folder = Path("tasks") / task["folder_id"]
        folder.mkdir(parents=True, exist_ok=True)

        path = folder / "table.json"

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

