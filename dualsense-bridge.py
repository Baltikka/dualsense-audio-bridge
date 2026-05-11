#!/usr/bin/env python3
"""
DualSense Audio-to-Trigger Bridge - GUI
Преобразует системный звук в сопротивление триггеров DualSense.
"""

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="dualsense_controller")

import tkinter as tk
from gui.app import App


def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
