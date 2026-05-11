"""Фильтры на основе scipy (Butterworth)."""

from typing import Tuple
import numpy as np
from scipy import signal


class ButterworthFilter:
    """Двухполосный фильтр Баттерворта (низкие + высокие, без середины)."""

    def __init__(self, mid_low_cut: float, mid_high_cut: float, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.mid_low_cut = mid_low_cut
        self.mid_high_cut = mid_high_cut
        self.order = 4

        # Состояния фильтров
        self.low_zi = None
        self.high_zi = None

        self._create_coefficients()

    def _create_coefficients(self):
        """Создаёт коэффициенты фильтров."""
        nyquist = self.sample_rate / 2.0

        # Низкочастотный
        low_cutoff = min(self.mid_low_cut / nyquist, 0.99)
        self.b_low, self.a_low = signal.butter(self.order, low_cutoff, btype='lowpass')
        self.low_zi = signal.lfilter_zi(self.b_low, self.a_low)

        # Высокочастотный
        high_cutoff = min(self.mid_high_cut / nyquist, 0.99)
        self.b_high, self.a_high = signal.butter(self.order, high_cutoff, btype='highpass')
        self.high_zi = signal.lfilter_zi(self.b_high, self.a_high)

    def needs_update(self, mid_low_cut: float, mid_high_cut: float) -> bool:
        """Проверяет, нужно ли пересоздать фильтры."""
        return (
            abs(self.mid_low_cut - mid_low_cut) > 0.5 or
            abs(self.mid_high_cut - mid_high_cut) > 0.5
        )

    def apply(
        self,
        samples: np.ndarray,
        bass_boost: float = 1.0,
        treble_boost: float = 1.0
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Применяет фильтры к массиву семплов."""
        if len(samples) == 0:
            return np.zeros(1), np.zeros(1)

        # Обновляем zi для текущего блока
        self.low_zi = self.low_zi * samples[0]
        self.high_zi = self.high_zi * samples[0]

        # Применяем фильтры
        bass, self.low_zi = signal.lfilter(self.b_low, self.a_low, samples, zi=self.low_zi)
        treble, self.high_zi = signal.lfilter(self.b_high, self.a_high, samples, zi=self.high_zi)

        # Усиление и клиппинг
        bass = np.clip(bass * bass_boost, -1.0, 1.0)
        treble = np.clip(treble * treble_boost, -1.0, 1.0)

        return bass, treble
