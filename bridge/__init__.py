"""
Модуль обработки аудио и управления DualSense.
"""

from .core import DualBandBridge
from .filters import ButterworthFilter
from .simple_filters import SimpleLowpass, SimpleHighpass, DualBandFilter

__all__ = ['DualBandBridge', 'ButterworthFilter', 'SimpleLowpass', 'SimpleHighpass', 'DualBandFilter']
