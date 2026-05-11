"""Панель управления настройками."""

import tkinter as tk
from tkinter import ttk
from typing import Dict


class ControlPanel:
    def __init__(self, parent, settings: Dict, preset_callback, reset_callback):
        self.frame = ttk.Frame(parent)

        # Фильтр
        ff = ttk.LabelFrame(self.frame, text="Фильтр (отсечка середины)", padding="8")
        ff.pack(fill="x", pady=(0, 5))

        for i, (text, var, from_, to) in enumerate([
            ("Нижняя граница (Гц):", settings['mid_low_cut'], 20, 500),
            ("Верхняя граница (Гц):", settings['mid_high_cut'], 500, 5000),
        ]):
            ttk.Label(ff, text=text, font=("", 8)).grid(row=i, column=0, sticky="w")
            ttk.Scale(ff, from_=from_, to=to, variable=var).grid(row=i, column=1, sticky="ew", padx=5)
            ttk.Label(ff, textvariable=var, width=5).grid(row=i, column=2)

        ttk.Label(ff, text="Усиление НЧ:", font=("", 8)).grid(row=2, column=0, sticky="w", pady=(5,0))
        ttk.Scale(ff, from_=1, to=20, variable=settings['bass_boost']).grid(row=2, column=1, sticky="ew", padx=5, pady=(5,0))
        ttk.Label(ff, textvariable=settings['bass_boost'], width=5).grid(row=2, column=2, pady=(5,0))

        ttk.Label(ff, text="Усиление ВЧ:", font=("", 8)).grid(row=3, column=0, sticky="w", pady=(5,0))
        ttk.Scale(ff, from_=1, to=20, variable=settings['treble_boost']).grid(row=3, column=1, sticky="ew", padx=5, pady=(5,0))
        ttk.Label(ff, textvariable=settings['treble_boost'], width=5).grid(row=3, column=2, pady=(5,0))

        # Чувствительность
        sf = ttk.LabelFrame(self.frame, text="Чувствительность", padding="8")
        sf.pack(fill="x", pady=(0, 5))

        for i, (text, var, from_, to) in enumerate([
            ("Порог тишины:", settings['threshold'], 0.01, 0.5),
            ("Макс. громкость:", settings['ceiling'], 0.1, 1.0),
            ("Сглаживание:", settings['smoothing'], 0.01, 0.5),
            ("Затухание:", settings['decay'], 0.1, 0.9),
        ]):
            ttk.Label(sf, text=text, font=("", 8)).grid(row=i, column=0, sticky="w")
            ttk.Scale(sf, from_=from_, to=to, variable=var).grid(row=i, column=1, sticky="ew", padx=5)
            ttk.Label(sf, textvariable=var, width=5).grid(row=i, column=2)

        # Триггеры
        tf = ttk.LabelFrame(self.frame, text="Назначение триггеров", padding="8")
        tf.pack(fill="x", pady=(0, 5))

        ttk.Label(tf, text="Левый:", font=("", 8)).grid(row=0, column=0, sticky="w")
        ttk.Combobox(tf, textvariable=settings['left_freq'], values=['low','high'],
                     state='readonly', width=6).grid(row=0, column=1, padx=5)
        ttk.Label(tf, text="low=басы high=ВЧ", font=("", 7)).grid(row=0, column=2)

        ttk.Label(tf, text="Правый:", font=("", 8)).grid(row=1, column=0, sticky="w", pady=(5,0))
        ttk.Combobox(tf, textvariable=settings['right_freq'], values=['low','high'],
                     state='readonly', width=6).grid(row=1, column=1, padx=5, pady=(5,0))
        ttk.Label(tf, text="low=басы high=ВЧ", font=("", 7)).grid(row=1, column=2, pady=(5,0))

        # Сила
        ff2 = ttk.LabelFrame(self.frame, text="Сила сопротивления", padding="8")
        ff2.pack(fill="x", pady=(0, 5))

        ttk.Label(ff2, text="Мин:", font=("", 8)).grid(row=0, column=0)
        ttk.Scale(ff2, from_=0, to=50, variable=settings['min_force']).grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Label(ff2, textvariable=settings['min_force'], width=3).grid(row=0, column=2)

        ttk.Label(ff2, text="Макс:", font=("", 8)).grid(row=1, column=0, pady=(5,0))
        ttk.Scale(ff2, from_=100, to=255, variable=settings['max_force']).grid(row=1, column=1, sticky="ew", padx=5, pady=(5,0))
        ttk.Label(ff2, textvariable=settings['max_force'], width=3).grid(row=1, column=2, pady=(5,0))
