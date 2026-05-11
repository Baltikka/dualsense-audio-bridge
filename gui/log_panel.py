"""Панель лога."""

import tkinter as tk
from tkinter import ttk, scrolledtext
import time


class LogPanel:
    def __init__(self, parent):
        self.frame = ttk.LabelFrame(parent, text="Лог", padding="5")
        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)

        self.widget = scrolledtext.ScrolledText(
            self.frame, height=12, state='disabled', font=("monospace", 8)
        )
        self.widget.grid(row=0, column=0, sticky="nsew")

    def add(self, msg: str):
        self.widget.config(state='normal')
        self.widget.insert('end', f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.widget.see('end')
        self.widget.config(state='disabled')
