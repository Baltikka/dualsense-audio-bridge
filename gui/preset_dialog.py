"""Диалоги для работы с пресетами."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Optional, List


class PresetDialog:
    """Базовый класс для диалогов пресетов."""

    def __init__(self, parent, title: str):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x200")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.result = None
        self._build()

        # Центрирование
        self.dialog.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 400) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 200) // 2
        self.dialog.geometry(f"+{x}+{y}")

    def _build(self):
        pass

    def wait(self):
        self.dialog.wait_window()
        return self.result


class SavePresetDialog(PresetDialog):
    """Диалог сохранения пресета."""

    def __init__(self, parent, current_name: str = ""):
        self.current_name = current_name
        super().__init__(parent, "Сохранить пресет")

    def _build(self):
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Название пресета:", font=("", 10)).pack(anchor="w")

        self.name_var = tk.StringVar(value=self.current_name)
        self.name_entry = ttk.Entry(frame, textvariable=self.name_var, width=40, font=("", 10))
        self.name_entry.pack(fill="x", pady=(5, 15))
        self.name_entry.select_range(0, tk.END)
        self.name_entry.focus()

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x")

        ttk.Button(btn_frame, text="💾 Сохранить", command=self._save).pack(side="right", padx=3)
        ttk.Button(btn_frame, text="Отмена", command=self.dialog.destroy).pack(side="right", padx=3)

        self.name_entry.bind('<Return>', lambda e: self._save())
        self.name_entry.bind('<Escape>', lambda e: self.dialog.destroy())

    def _save(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Предупреждение", "Введите название пресета!", parent=self.dialog)
            return
        self.result = name
        self.dialog.destroy()


class LoadPresetDialog(PresetDialog):
    """Диалог загрузки/удаления пресетов."""

    def __init__(self, parent, presets: List[Dict], builtin_count: int):
        self.presets = presets
        self.builtin_count = builtin_count
        super().__init__(parent, "Управление пресетами")
        self.dialog.geometry("500x400")

    def _build(self):
        frame = ttk.Frame(self.dialog, padding="15")
        frame.pack(fill="both", expand=True)

        # Список пресетов
        ttk.Label(frame, text="Доступные пресеты:", font=("", 10, "bold")).pack(anchor="w")

        list_frame = ttk.Frame(frame)
        list_frame.pack(fill="both", expand=True, pady=(5, 10))

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        self.listbox = tk.Listbox(
            list_frame, yscrollcommand=scrollbar.set,
            font=("", 10), selectmode="single", activestyle="none"
        )
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)

        # Заполняем список
        for i, p in enumerate(self.presets):
            prefix = "[В] " if i < self.builtin_count else "[П] "
            self.listbox.insert(tk.END, f"{prefix}{p['name']}")

        self.listbox.bind('<Double-Button-1>', lambda e: self._load())

        # Кнопки
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x")

        ttk.Button(btn_frame, text="✅ Загрузить", command=self._load).pack(side="left", padx=3)
        ttk.Button(btn_frame, text="🗑 Удалить", command=self._delete).pack(side="left", padx=3)
        ttk.Button(btn_frame, text="📤 Экспорт", command=self._export).pack(side="left", padx=3)
        ttk.Button(btn_frame, text="📥 Импорт", command=self._import).pack(side="left", padx=3)
        ttk.Button(btn_frame, text="Отмена", command=self.dialog.destroy).pack(side="right", padx=3)

        self.listbox.bind('<Return>', lambda e: self._load())
        self.listbox.bind('<Delete>', lambda e: self._delete())
        self.listbox.bind('<Escape>', lambda e: self.dialog.destroy())

    def _get_selected(self) -> Optional[int]:
        sel = self.listbox.curselection()
        return sel[0] if sel else None

    def _load(self):
        idx = self._get_selected()
        if idx is not None:
            self.result = ('load', idx)
            self.dialog.destroy()

    def _delete(self):
        idx = self._get_selected()
        if idx is None:
            return
        if idx < self.builtin_count:
            messagebox.showinfo("Инфо", "Встроенные пресеты нельзя удалить.", parent=self.dialog)
            return

        name = self.presets[idx]['name']
        if messagebox.askyesno("Подтверждение", f"Удалить пресет «{name}»?", parent=self.dialog):
            self.result = ('delete', idx)
            self.dialog.destroy()

    def _export(self):
        idx = self._get_selected()
        if idx is None:
            return

        preset = self.presets[idx]
        path = filedialog.asksaveasfilename(
            parent=self.dialog,
            title="Экспорт пресета",
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Все файлы", "*.*")],
            initialfile=f"{preset['name']}.json"
        )
        if path:
            self.result = ('export', idx, path)
            self.dialog.destroy()

    def _import(self):
        path = filedialog.askopenfilename(
            parent=self.dialog,
            title="Импорт пресета",
            filetypes=[("JSON", "*.json"), ("Все файлы", "*.*")]
        )
        if path:
            self.result = ('import', path)
            self.dialog.destroy()
