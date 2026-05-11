"""Простые фильтры без scipy (на случай fallback)."""

import math
from typing import List, Tuple


class SimpleFilter:
    """Общий класс простого фильтра."""
    pass


class SimpleLowpass(SimpleFilter):
    """RC-фильтр нижних частот первого порядка."""

    def __init__(self, cutoff: float, sample_rate: int = 16000):
        super().__init__()
        rc = 1.0 / (2.0 * math.pi * cutoff)
        dt = 1.0 / sample_rate
        self.alpha = dt / (rc + dt)
        self.prev = 0.0

    def apply(self, sample: float) -> float:
        self.prev += self.alpha * (sample - self.prev)
        return self.prev


class SimpleHighpass(SimpleFilter):
    """RC-фильтр верхних частот первого порядка."""

    def __init__(self, cutoff: float, sample_rate: int = 16000):
        super().__init__()
        rc = 1.0 / (2.0 * math.pi * cutoff)
        dt = 1.0 / sample_rate
        self.alpha = rc / (rc + dt)
        self.prev_in = 0.0
        self.prev_out = 0.0

    def apply(self, sample: float) -> float:
        out = self.alpha * (self.prev_out + sample - self.prev_in)
        self.prev_in = sample
        self.prev_out = out
        return out


class DualBandFilter(SimpleFilter):
    """Двухполосный фильтр на простых RC-фильтрах."""

    def __init__(self, mid_low_cut: float, mid_high_cut: float, sample_rate: int = 16000):
        super().__init__()
        self.lowpass = SimpleLowpass(mid_low_cut, sample_rate)
        self.highpass = SimpleHighpass(mid_high_cut, sample_rate)

    def apply(
        self,
        samples: List[float],
        bass_boost: float = 1.0,
        treble_boost: float = 1.0
    ) -> Tuple[List[float], List[float]]:
        bass = []
        treble = []
        for s in samples:
            b = self.lowpass.apply(s) * bass_boost
            t = self.highpass.apply(s) * treble_boost
            bass.append(max(min(b, 1.0), -1.0))
            treble.append(max(min(t, 1.0), -1.0))
        return bass, treble
