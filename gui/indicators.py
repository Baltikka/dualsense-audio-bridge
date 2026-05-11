"""Панель индикаторов силы триггеров."""

import tkinter as tk
from tkinter import ttk


class IndicatorPanel:
    def __init__(self, parent):
        self.frame = ttk.LabelFrame(parent, text="Уровни триггеров", padding="8")

        ttk.Label(self.frame, text="Левый:").grid(row=0, column=0, sticky="w")
        self.left_bar = ttk.Progressbar(self.frame, length=180, mode='determinate', maximum=255)
        self.left_bar.grid(row=0, column=1, padx=5)
        self.left_val = ttk.Label(self.frame, text="0", width=4)
        self.left_val.grid(row=0, column=2)

        ttk.Label(self.frame, text="Правый:").grid(row=1, column=0, sticky="w", pady=(5,0))
        self.right_bar = ttk.Progressbar(self.frame, length=180, mode='determinate', maximum=255)
        self.right_bar.grid(row=1, column=1, padx=5, pady=(5,0))
        self.right_val = ttk.Label(self.frame, text="0", width=4)
        self.right_val.grid(row=1, column=2, pady=(5,0))

    def update(self, left: int, right: int):
        self.left_bar['value'] = left
        self.right_bar['value'] = right
        self.left_val.config(text=str(left))
        self.right_val.config(text=str(right))
