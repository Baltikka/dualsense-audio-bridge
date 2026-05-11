"""Панель управления настройками с ручным вводом значений."""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable


class ControlPanel:
    def __init__(
        self,
        parent: ttk.Frame,
        settings: Dict[str, tk.Variable],
        preset_callback: Callable,
        reset_callback: Callable
    ):
        self.frame = ttk.Frame(parent)
        self.settings = settings

        # ═══════════ Фильтр ═══════════
        ff = ttk.LabelFrame(self.frame, text="Фильтр (отсечка середины)", padding="8")
        ff.pack(fill="x", pady=(0, 5))

        # Нижняя граница
        row = 0
        ttk.Label(ff, text="Нижняя граница (Гц):", font=("", 8)).grid(
            row=row, column=0, sticky="w"
        )
        low_scale = ttk.Scale(
            ff, from_=20, to=1000, variable=settings['mid_low_cut'],
            command=self._on_low_scale
        )
        low_scale.grid(row=row, column=1, sticky="ew", padx=5)

        self.low_entry = ttk.Entry(ff, width=6, textvariable=settings['mid_low_cut'])
        self.low_entry.grid(row=row, column=2)
        self.low_entry.bind('<Return>', self._on_entry_return)
        self.low_entry.bind('<FocusOut>', self._on_entry_focusout)

        # Подсказка
        ttk.Label(ff, text="(20-1000)", font=("", 6), foreground="gray").grid(
            row=row, column=3, padx=(2, 0)
        )

        # Верхняя граница
        row = 1
        ttk.Label(ff, text="Верхняя граница (Гц):", font=("", 8)).grid(
            row=row, column=0, sticky="w", pady=(5, 0)
        )
        high_scale = ttk.Scale(
            ff, from_=500, to=5000, variable=settings['mid_high_cut'],
            command=self._on_high_scale
        )
        high_scale.grid(row=row, column=1, sticky="ew", padx=5, pady=(5, 0))

        self.high_entry = ttk.Entry(ff, width=6, textvariable=settings['mid_high_cut'])
        self.high_entry.grid(row=row, column=2, pady=(5, 0))
        self.high_entry.bind('<Return>', self._on_entry_return)
        self.high_entry.bind('<FocusOut>', self._on_entry_focusout)

        ttk.Label(ff, text="(500-5000)", font=("", 6), foreground="gray").grid(
            row=row, column=3, padx=(2, 0), pady=(5, 0)
        )

        # Усиление НЧ
        row = 2
        ttk.Label(ff, text="Усиление НЧ:", font=("", 8)).grid(
            row=row, column=0, sticky="w", pady=(5, 0)
        )
        ttk.Scale(
            ff, from_=0.5, to=10, variable=settings['bass_boost'],
            command=self._on_bass_scale
        ).grid(row=row, column=1, sticky="ew", padx=5, pady=(5, 0))

        self.bass_entry = ttk.Entry(ff, width=6, textvariable=settings['bass_boost'])
        self.bass_entry.grid(row=row, column=2, pady=(5, 0))
        self.bass_entry.bind('<Return>', self._on_entry_return)
        self.bass_entry.bind('<FocusOut>', self._on_entry_focusout)

        ttk.Label(ff, text="(0.5-10.0)", font=("", 6), foreground="gray").grid(
            row=row, column=3, padx=(2, 0), pady=(5, 0)
        )

        # Усиление ВЧ
        row = 3
        ttk.Label(ff, text="Усиление ВЧ:", font=("", 8)).grid(
            row=row, column=0, sticky="w", pady=(5, 0)
        )
        ttk.Scale(
            ff, from_=0.5, to=10, variable=settings['treble_boost'],
            command=self._on_treble_scale
        ).grid(row=row, column=1, sticky="ew", padx=5, pady=(5, 0))

        self.treble_entry = ttk.Entry(ff, width=6, textvariable=settings['treble_boost'])
        self.treble_entry.grid(row=row, column=2, pady=(5, 0))
        self.treble_entry.bind('<Return>', self._on_entry_return)
        self.treble_entry.bind('<FocusOut>', self._on_entry_focusout)

        ttk.Label(ff, text="(0.5-10.0)", font=("", 6), foreground="gray").grid(
            row=row, column=3, padx=(2, 0), pady=(5, 0)
        )

        # ═══════════ Чувствительность ═══════════
        sf = ttk.LabelFrame(self.frame, text="Чувствительность", padding="8")
        sf.pack(fill="x", pady=(0, 5))

        sens_params = [
            ("Порог тишины:", 'threshold', 0.01, 0.99, "(0.01-0.5)"),
            ("Порог макс. громкости:", 'ceiling', 0.1, 1.0, "(0.1-1.0)"),
            ("Сглаживание:", 'smoothing', 0.01, 0.99, "(0.01-0.5)"),
            ("Затухание:", 'decay', 0.01, 0.99, "(0.1-0.9)"),
        ]

        self.sens_entries = {}
        for i, (text, key, from_, to, hint) in enumerate(sens_params):
            ttk.Label(sf, text=text, font=("", 8)).grid(row=i, column=0, sticky="w")
            ttk.Scale(
                sf, from_=from_, to=to, variable=settings[key]
            ).grid(row=i, column=1, sticky="ew", padx=5)

            entry = ttk.Entry(sf, width=6, textvariable=settings[key])
            entry.grid(row=i, column=2)
            entry.bind('<Return>', self._on_entry_return)
            entry.bind('<FocusOut>', self._on_entry_focusout)
            self.sens_entries[key] = entry

            ttk.Label(sf, text=hint, font=("", 6), foreground="gray").grid(
                row=i, column=3, padx=(2, 0)
            )

        # ═══════════ Триггеры ═══════════
        tf = ttk.LabelFrame(self.frame, text="Назначение триггеров", padding="8")
        tf.pack(fill="x", pady=(0, 5))

        ttk.Label(tf, text="Левый:", font=("", 8)).grid(row=0, column=0, sticky="w")
        ttk.Combobox(
            tf, textvariable=settings['left_freq'], values=['low', 'high'],
            state='readonly', width=6
        ).grid(row=0, column=1, padx=5)
        ttk.Label(tf, text="low=басы high=ВЧ", font=("", 7)).grid(row=0, column=2)

        ttk.Label(tf, text="Правый:", font=("", 8)).grid(row=1, column=0, sticky="w", pady=(5, 0))
        ttk.Combobox(
            tf, textvariable=settings['right_freq'], values=['low', 'high'],
            state='readonly', width=6
        ).grid(row=1, column=1, padx=5, pady=(5, 0))
        ttk.Label(tf, text="low=басы high=ВЧ", font=("", 7)).grid(row=1, column=2, pady=(5, 0))

        # ═══════════ Сила ═══════════
        ff2 = ttk.LabelFrame(self.frame, text="Сила сопротивления", padding="8")
        ff2.pack(fill="x", pady=(0, 5))

        # Мин сила
        ttk.Label(ff2, text="Мин:", font=("", 8)).grid(row=0, column=0)
        ttk.Scale(
            ff2, from_=0, to=50, variable=settings['min_force']
        ).grid(row=0, column=1, sticky="ew", padx=5)

        self.min_entry = ttk.Entry(ff2, width=4, textvariable=settings['min_force'])
        self.min_entry.grid(row=0, column=2)
        self.min_entry.bind('<Return>', self._on_entry_return)
        self.min_entry.bind('<FocusOut>', self._on_entry_focusout)

        ttk.Label(ff2, text="(0-50)", font=("", 6), foreground="gray").grid(
            row=0, column=3, padx=(2, 0)
        )

        # Макс сила
        ttk.Label(ff2, text="Макс:", font=("", 8)).grid(row=1, column=0, pady=(5, 0))
        ttk.Scale(
            ff2, from_=1, to=255, variable=settings['max_force']
        ).grid(row=1, column=1, sticky="ew", padx=5, pady=(5, 0))

        self.max_entry = ttk.Entry(ff2, width=4, textvariable=settings['max_force'])
        self.max_entry.grid(row=1, column=2, pady=(5, 0))
        self.max_entry.bind('<Return>', self._on_entry_return)
        self.max_entry.bind('<FocusOut>', self._on_entry_focusout)

        ttk.Label(ff2, text="(1-255)", font=("", 6), foreground="gray").grid(
            row=1, column=3, padx=(2, 0), pady=(5, 0)
        )

    # ═══════════ Обработчики ввода ═══════════

    def _on_entry_return(self, event):
        """Нажатие Enter — валидация и обновление слайдера."""
        self._validate_and_update(event.widget)

    def _on_entry_focusout(self, event):
        """Потеря фокуса — валидация."""
        self._validate_and_update(event.widget)

    def _validate_and_update(self, widget):
        """Проверяет значение и обновляет связанную переменную."""
        try:
            value = float(widget.get())
            var_name = widget.cget('textvariable')

            # Ограничения для каждого параметра
            limits = {
                'mid_low_cut': (20, 1000),
                'mid_high_cut': (500, 5000),
                'bass_boost': (0.5, 10.0),
                'treble_boost': (0.5, 10.0),
                'threshold': (0.01, 0.99),
                'ceiling': (0.1, 1.0),
                'smoothing': (0.01, 0.99),
                'decay': (0.01, 0.99),
                'min_force': (0, 50),
                'max_force': (1, 255),
            }

            # Находим имя переменной
            for key, var in self.settings.items():
                if str(var) == var_name:
                    if key in limits:
                        min_val, max_val = limits[key]
                        value = max(min_val, min(value, max_val))
                        # Обновляем с округлением для целых
                        if key in ('mid_low_cut', 'mid_high_cut', 'min_force', 'max_force'):
                            value = int(value)
                        var.set(value)
                    break

        except ValueError:
            # Если ввели не число — игнорируем
            pass

    def _on_low_scale(self, value):
        """Слайдер нижней границы."""
        self.low_entry.delete(0, tk.END)
        self.low_entry.insert(0, str(int(float(value))))

    def _on_high_scale(self, value):
        """Слайдер верхней границы."""
        self.high_entry.delete(0, tk.END)
        self.high_entry.insert(0, str(int(float(value))))

    def _on_bass_scale(self, value):
        """Слайдер усиления НЧ."""
        self.bass_entry.delete(0, tk.END)
        self.bass_entry.insert(0, f"{float(value):.1f}")

    def _on_treble_scale(self, value):
        """Слайдер усиления ВЧ."""
        self.treble_entry.delete(0, tk.END)
        self.treble_entry.insert(0, f"{float(value):.1f}")
