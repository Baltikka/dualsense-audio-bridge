"""Вспомогательные функции для обработки аудио."""

import struct
import math
from typing import List, Tuple, Optional


def rms(samples: List[float]) -> float:
    """Вычисляет RMS (среднеквадратичную громкость)."""
    if not samples:
        return 0.0
    return math.sqrt(sum(s * s for s in samples) / len(samples))


def parse_samples(data: bytes, count: int) -> List[float]:
    """Преобразует байты в нормализованные float-семплы."""
    samples = struct.unpack(f'<{count}h', data[:count * 2])
    return [s / 32768.0 for s in samples]


def smooth_volume(current: float, target: float, smoothing: float) -> float:
    """Экспоненциальное сглаживание громкости."""
    return smoothing * current + (1.0 - smoothing) * target


def calculate_force(
    volume: float,
    threshold: float,
    ceiling: float,
    min_force: int,
    max_force: int
) -> int:
    """Вычисляет силу сопротивления по громкости."""
    if volume > threshold:
        normalized = min(volume / ceiling, 1.0)
        return int(min_force + normalized * (max_force - min_force))
    return min_force


def get_parec_command(source: str, sample_rate: int = 16000) -> List[str]:
    """Формирует команду для запуска parec."""
    return [
        'parec',
        f'--device={source}',
        '--format=s16le',
        f'--rate={sample_rate}',
        '--channels=1',
        '--latency-msec=10',
    ]
