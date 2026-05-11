"""Главное окно приложения."""

import tkinter as tk
from tkinter import ttk, messagebox
import threading

from bridge.core import DualBandBridge
from .controls import ControlPanel
from .indicators import IndicatorPanel
from .log_panel import LogPanel
from .preset_dialog import SavePresetDialog, LoadPresetDialog
from presets import PresetManager


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("DualSense Audio → Trigger Bridge")
        self.root.geometry("680x700")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Настройки
        self.settings = self._create_settings()

        # Пресеты
        self.preset_manager = PresetManager()
        self.current_preset = 0

        # Компоненты
        self.bridge = None
        self.running = False

        # Сборка UI
        self._build_ui()
        self._apply_preset(0)

    def _create_settings(self):
        """Создаёт словарь с настройками (tk.Variable)."""
        return {
            'mid_low_cut': tk.IntVar(value=200),
            'mid_high_cut': tk.IntVar(value=1500),
            'bass_boost': tk.DoubleVar(value=4.0),
            'treble_boost': tk.DoubleVar(value=6.5),
            'threshold': tk.DoubleVar(value=0.2),
            'ceiling': tk.DoubleVar(value=0.7),
            'smoothing': tk.DoubleVar(value=0.1),
            'decay': tk.DoubleVar(value=0.3),
            'min_force': tk.IntVar(value=5),
            'max_force': tk.IntVar(value=255),
            'left_freq': tk.StringVar(value='low'),
            'right_freq': tk.StringVar(value='high'),
            'audio_source': tk.StringVar(value='@DEFAULT_MONITOR@'),
        }

    def _build_ui(self):
        """Собирает интерфейс."""
        main = ttk.Frame(self.root, padding="10")
        main.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Статус-бар
        self._build_status_bar(main)

        # Панели
        self.control_panel = ControlPanel(
            main, self.settings, self.next_preset, self.reset
        )
        self.control_panel.frame.grid(row=1, column=0, sticky="nsew", padx=(0, 5))

        right_panel = ttk.Frame(main)
        right_panel.grid(row=1, column=1, sticky="nsew")

        self.indicator_panel = IndicatorPanel(right_panel)
        self.indicator_panel.frame.pack(fill="x", pady=(0, 5))

        self.log_panel = LogPanel(right_panel)
        self.log_panel.frame.pack(fill="both", expand=True)

        # Кнопки
        self._build_buttons(main)

        main.columnconfigure(1, weight=1)
        main.rowconfigure(1, weight=1)

    def _build_status_bar(self, parent):
        """Создаёт статус-бар."""
        sf = ttk.LabelFrame(parent, text="Статус", padding="8")
        sf.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        self.status_lbl = ttk.Label(
            sf, text="● Остановлен", foreground="red", font=("", 10, "bold")
        )
        self.status_lbl.pack(side="left")

        self.ctrl_lbl = ttk.Label(sf, text=" | Контроллер: ?")
        self.ctrl_lbl.pack(side="left", padx=20)

    def _build_buttons(self, parent):
        """Создаёт кнопки управления."""
        btn = ttk.Frame(parent)
        btn.grid(row=2, column=0, columnspan=2, pady=(8, 0), sticky="ew")

        self.start_btn = ttk.Button(btn, text="▶ Запустить", command=self.start)
        self.start_btn.pack(side="left", padx=3)

        self.stop_btn = ttk.Button(
            btn, text="■ Остановить", command=self.stop, state="disabled"
        )
        self.stop_btn.pack(side="left", padx=3)

        self.preset_btn = ttk.Button(
            btn, text="📋 Стандартный", command=self.next_preset
        )
        self.preset_btn.pack(side="left", padx=3)

        ttk.Button(
            btn, text="📂 Загрузить...", command=self.load_preset_dialog
        ).pack(side="left", padx=3)

        ttk.Button(
            btn, text="💾 Сохранить...", command=self.save_preset_dialog
        ).pack(side="left", padx=3)

        ttk.Button(btn, text="🔄 Сброс", command=self.reset).pack(side="left", padx=3)

    # ═══════════════ Методы для пресетов ═══════════════

    def next_preset(self):
        """Переключение на следующий пресет (циклически)."""
        total = len(self.preset_manager.all_presets)
        if total == 0:
            return
        self.current_preset = (self.current_preset + 1) % total
        self._apply_preset(self.current_preset)

    def _apply_preset(self, index: int):
        """Применяет пресет по индексу к настройкам."""
        preset = self.preset_manager.get_preset(index)
        if not preset:
            return

        for key in preset:
            if key != 'name' and key in self.settings:
                self.settings[key].set(preset[key])

        self.current_preset = index
        self._update_preset_button()
        self.log(f"Загружен пресет: {preset['name']}")

    def _update_preset_button(self):
        """Обновляет текст на кнопке пресета."""
        if self.current_preset < len(self.preset_manager.all_presets):
            name = self.preset_manager.all_presets[self.current_preset]['name']
            self.preset_btn.config(text=f"📋 {name}")

    def load_preset_dialog(self):
        """Диалог управления пресетами (загрузка/удаление/экспорт/импорт)."""
        dialog = LoadPresetDialog(
            self.root,
            self.preset_manager.all_presets,
            self.preset_manager.builtin_count
        )
        result = dialog.wait()

        if result is None:
            return

        action = result[0]

        if action == 'load':
            self._apply_preset(result[1])

        elif action == 'delete':
            name = self.preset_manager.all_presets[result[1]]['name']
            if self.preset_manager.delete_preset(name):
                self.log(f"Пресет «{name}» удалён")
                # Если текущий пресет больше не существует — сбрасываем на первый
                if self.current_preset >= len(self.preset_manager.all_presets):
                    self.current_preset = 0
                    if self.preset_manager.all_presets:
                        self._apply_preset(0)
                    else:
                        self._update_preset_button()

        elif action == 'export':
            preset = self.preset_manager.all_presets[result[1]]
            if self.preset_manager.export_preset(preset['name'], result[2]):
                self.log(f"Пресет «{preset['name']}» экспортирован в {result[2]}")
            else:
                messagebox.showerror("Ошибка", "Не удалось экспортировать пресет.")

        elif action == 'import':
            name = self.preset_manager.import_preset(result[1])
            if name:
                self.log(f"Пресет «{name}» импортирован")
                # Переключаемся на импортированный пресет
                for i, p in enumerate(self.preset_manager.all_presets):
                    if p['name'] == name:
                        self._apply_preset(i)
                        break
            else:
                messagebox.showerror(
                    "Ошибка", "Не удалось импортировать пресет.\nПроверьте формат файла."
                )

    def save_preset_dialog(self):
        """Диалог сохранения текущих настроек как пресета."""
        current_name = ""
        if self.current_preset < len(self.preset_manager.all_presets):
            current_name = self.preset_manager.all_presets[self.current_preset]['name']

        dialog = SavePresetDialog(self.root, current_name)
        name = dialog.wait()

        if name:
            preset = {
                'name': name,
                'mid_low_cut': self.settings['mid_low_cut'].get(),
                'mid_high_cut': self.settings['mid_high_cut'].get(),
                'bass_boost': self.settings['bass_boost'].get(),
                'treble_boost': self.settings['treble_boost'].get(),
                'threshold': self.settings['threshold'].get(),
                'ceiling': self.settings['ceiling'].get(),
                'smoothing': self.settings['smoothing'].get(),
                'decay': self.settings['decay'].get(),
                'min_force': self.settings['min_force'].get(),
                'max_force': self.settings['max_force'].get(),
                'left_freq': self.settings['left_freq'].get(),
                'right_freq': self.settings['right_freq'].get(),
            }

            if self.preset_manager.save_preset(preset):
                self.log(f"Пресет «{name}» сохранён")
                # Переключаемся на сохранённый пресет
                for i, p in enumerate(self.preset_manager.all_presets):
                    if p['name'] == name:
                        self.current_preset = i
                        self._update_preset_button()
                        break
            else:
                messagebox.showerror("Ошибка", "Не удалось сохранить пресет.")

    def reset(self):
        """Сброс настроек к значениям по умолчанию."""
        defaults = {
            'mid_low_cut': 200,
            'mid_high_cut': 1500,
            'bass_boost': 4.0,
            'treble_boost': 6.5,
            'threshold': 0.2,
            'ceiling': 0.7,
            'smoothing': 0.1,
            'decay': 0.3,
            'min_force': 5,
            'max_force': 255,
            'left_freq': 'low',
            'right_freq': 'high',
        }
        for key, val in defaults.items():
            self.settings[key].set(val)
        self.log("Настройки сброшены")

    # ═══════════════ Геттер настроек ═══════════════

    def get_setting(self, key):
        """Возвращает текущее значение настройки."""
        return self.settings[key].get()

    # ═══════════════ Логирование и индикаторы ═══════════════

    def log(self, msg: str):
        """Добавляет сообщение в лог (потокобезопасно)."""
        self.root.after(0, self.log_panel.add, msg)

    def update_indicators(self, left: int, right: int):
        """Обновляет индикаторы силы (потокобезопасно)."""
        self.root.after(0, self.indicator_panel.update, left, right)

    # ═══════════════ Запуск/остановка моста ═══════════════

    def start(self):
        """Запускает мост."""
        self.running = True
        self.bridge = DualBandBridge(
            self.get_setting, self.log, self.update_indicators
        )
        self.bridge.running = True

        threading.Thread(target=self.bridge.audio_thread, daemon=True).start()
        threading.Thread(target=self.bridge.control_thread, daemon=True).start()

        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_lbl.config(text="● Запущен", foreground="green")
        self.ctrl_lbl.config(text=" | Контроллер: ⏳ поиск...")
        self.log("Мост запущен")

        # Проверка подключения контроллера
        self.root.after(2000, self._check_controller)

    def _check_controller(self):
        """Проверяет, подключился ли контроллер."""
        if self.bridge and self.bridge.controller:
            self.ctrl_lbl.config(text=" | Контроллер: ✅ Подключен")
        elif self.running:
            self.root.after(2000, self._check_controller)

    def stop(self):
        """Останавливает мост."""
        self.running = False
        if self.bridge:
            self.bridge.stop()
            self.bridge = None

        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_lbl.config(text="● Остановлен", foreground="red")
        self.ctrl_lbl.config(text=" | Контроллер: ?")
        self.update_indicators(0, 0)
        self.log("Мост остановлен")

    def on_close(self):
        """Закрытие окна."""
        self.stop()
        self.root.destroy()
