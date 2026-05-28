import tkinter as tk
from tkinter import ttk

from config import *
from data import load_tasks, save_tasks, load_report, save_report


class TaskApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Task Manager")
        self.root.geometry("1200x600")

        self.tasks = load_tasks()

        self.setup_styles()

        self.build_ui()
        self.refresh_table()

    # ---------------- STYLES ----------------

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

        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=fg)
        style.configure("TButton", background=bg, foreground=fg)
        style.configure("TEntry", fieldbackground=field_bg, foreground=fg)
        style.configure("TCombobox", fieldbackground=field_bg, foreground=fg)
        style.configure("TPanedwindow", background=bg)



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

        def get_week_range():
            today = datetime.now()
            friday = today - timedelta(days=(today.weekday() - 4) % 7)
            thursday = friday + timedelta(days=6)
            return f"{friday.strftime('%d.%m')} - {thursday.strftime('%d.%m')}"

        def refresh():
            tree.delete(*tree.get_children())
            for row in report_data:
                tree.insert("", tk.END, values=(row["week"], row["scans"], row["closed"]))

        def add_week():
            week = get_week_range()

            for row in report_data:
                if row["week"] == week:
                    return

            report_data.append({
                "week": week,
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

    def add_task(self):
        self.tasks.append({
            "id": "RF",
            "name": "АС",
            "type": "",
            "mp8":"",
            "secure": "Не задан",
            "status": "В работе",
            "full_name": "",
            "second_id": "SD",
            "pentest/audit": "Не запущен",
            "compliance": "Не запущен",
            "comment": ""
        })
        save_tasks(self.tasks)
        self.refresh_table()

    def delete_task(self):
        sel = self.tree.selection()
        if not sel:
            return

        task = self.get_selected_task()
        if not task:
            return
        self.tasks.remove(task)

        save_tasks(self.tasks)
        self.refresh_table()

    def set_status(self, status):
        sel = self.tree.selection()
        if not sel:
            return

        task = self.get_selected_task()
        if not task:
            return
        task["status"] = status

        save_tasks(self.tasks)
        self.refresh_table()


    def build_ui(self):
        self.paned = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)

        self.left = ttk.Frame(self.paned, )
        self.right = ttk.Frame(self.paned, width=320)

        self.paned.add(self.left, weight=3)
        self.paned.add(self.right, weight=1)

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

        tk.Button(self.filter_frame, text="Добавить", command=self.add_task).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(self.filter_frame, text="Удалить", command=self.delete_task).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(self.filter_frame, text="Для отчета", command=self.open_report).pack(side=tk.LEFT, padx=5, pady=5)


        self.tree = ttk.Treeview(self.left, columns=("ID", "Name", "Status"), show="headings")
        self.tree.heading("ID", text="Номер")
        self.tree.heading("Name", text="Система")
        self.tree.heading("Status", text="Статус")
        self.tree.pack(fill=tk.BOTH, expand=True)

        # details
        self.details = ttk.Treeview(self.right, columns=("F", "V"), show="headings")
        self.details.heading("F", text="Поле")
        self.details.heading("V", text="Значение")
        self.details.pack(fill=tk.BOTH, expand=True)

        # buttons
        btn = ttk.Frame(self.right)
        btn.pack(fill=tk.X, padx=10, pady=10)


        tk.Button(btn, text="В работу", command=lambda: self.set_status("В работе")).pack(fill=tk.X, pady=2)
        tk.Button(btn, text="Ожидание", command=lambda: self.set_status("Ожидание")).pack(fill=tk.X, pady=2)
        tk.Button(btn, text="Закрыто", command=lambda: self.set_status("Закрыто")).pack(fill=tk.X, pady=2)

        # events
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<Double-1>", lambda e: self.edit_any_cell(e, self.tree))
        self.details.bind("<Double-1>", lambda e: self.edit_any_cell(e, self.details))

        self.filter_name.trace_add("write", lambda *args: self.refresh_table())
        self.filter_status.trace_add("write", lambda *args: self.refresh_table())

    # ---------------- TABLE ----------------

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

            self.tree.insert("", tk.END, values=(
                task["id"],
                task["name"],
                task.get("status", "")
            ), tags=(str(id(task)),))

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return

        task = self.get_selected_task()
        if not task:
            return

        self.details.delete(*self.details.get_children())

        self.details.insert("", tk.END, values=("Название АС", task["name"]))
        self.details.insert("", tk.END, values=("Тип работ", task["type"]))
        self.details.insert("", tk.END, values=("Номер задачи MP8", task["mp8"]))
        self.details.insert("", tk.END, values=("PCI DSS", task["secure"]))
        self.details.insert("", tk.END, values=("Номер RF", task["id"]))
        self.details.insert("", tk.END, values=("Статус", task["status"]))
        self.details.insert("", tk.END, values=("Пентест/Аудит", task["pentest/audit"]))
        self.details.insert("", tk.END, values=("СКИБ", task["compliance"]))
        self.details.insert("", tk.END, values=("Полное имя", task["full_name"]))
        self.details.insert("", tk.END, values=("Номер SD", task["second_id"]))
        self.details.insert("", tk.END, values=("Комментарий", task["comment"]))



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

        field = values[0] if table == self.details else None

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

            task = self.tasks[self.tree.index(sel[0])]

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
                elif field == "SD":
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