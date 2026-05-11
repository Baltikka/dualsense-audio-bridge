"""Основная логика моста."""

import threading
import time
import queue
import subprocess
import struct
from typing import Optional, Callable, Any

# Пробуем scipy-фильтры, fallback на простые
try:
    import numpy as np
    from .filters import ButterworthFilter as FilterClass
    print("[core] Используются фильтры scipy (Butterworth)")
except ImportError:
    np = None  # type: ignore
    from .simple_filters import DualBandFilter as FilterClass
    print("[core] Используются простые RC-фильтры (без scipy)")

from .utils import (
    rms, parse_samples, smooth_volume,
    calculate_force, get_parec_command
)

# Проверка dualsense
try:
    from dualsense_controller import DualSenseController
    DUALSENSE_OK = True
except ImportError:
    DUALSENSE_OK = False


class DualBandBridge:
    """Мост: аудио → фильтрация → триггеры DualSense."""

    def __init__(
        self,
        settings_getter: Callable[[str], Any],
        log_callback: Callable[[str], None],
        indicator_callback: Callable[[int, int], None]
    ):
        self.get_setting = settings_getter
        self.log = log_callback
        self.update_indicators = indicator_callback

        self.audio_queue: queue.Queue = queue.Queue(maxsize=5)
        self.running = False
        self.controller = None
        self.parec_process: Optional[subprocess.Popen] = None
        self.force_lock = threading.Lock()

        self.filter: FilterClass = None
        self._last_filter_params = (-1, -1)

    def _get_filter(self) -> FilterClass:
        """Возвращает фильтр, пересоздавая при изменении параметров."""
        ml = self.get_setting('mid_low_cut')
        mh = self.get_setting('mid_high_cut')

        if self.filter is None or (ml, mh) != self._last_filter_params:
            self.filter = FilterClass(ml, mh, 16000)
            self._last_filter_params = (ml, mh)

        return self.filter

    def audio_thread(self):
        """Поток захвата и обработки звука."""
        sample_rate = 16000
        self.log("Запуск захвата звука...")

        cmd = get_parec_command(self.get_setting('audio_source'), sample_rate)

        try:
            self.parec_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=4096
            )
            self.log("Захват запущен")
        except Exception as e:
            self.log(f"Ошибка parec: {e}")
            return

        buffer = b''
        bass_vol, treble_vol = 0.0, 0.0
        min_samples = sample_rate // 60

        while self.running:
            try:
                data = self.parec_process.stdout.read(2048)
                if not data:
                    if self.running:
                        self.log("⚠ Переподключение аудио...")
                        self.parec_process.terminate()
                        self.parec_process = subprocess.Popen(
                            cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=4096
                        )
                    continue

                buffer += data
                n = len(buffer) // 2

                if n >= min_samples:
                    # Парсинг семплов
                    samples_f = np.array(
                        struct.unpack(f'<{n}h', buffer[:n*2]),
                        dtype=np.float32
                    ) / 32768.0 if np else parse_samples(buffer, n)
                    buffer = buffer[n*2:]

                    # Фильтрация
                    filter_obj = self._get_filter()
                    bass_boost = self.get_setting('bass_boost')
                    treble_boost = self.get_setting('treble_boost')

                    if np is not None:
                        bass, treble = filter_obj.apply(samples_f, bass_boost, treble_boost)
                        b_rms = float(np.sqrt(np.mean(bass**2)))
                        t_rms = float(np.sqrt(np.mean(treble**2)))
                    else:
                        bass, treble = filter_obj.apply(samples_f, bass_boost, treble_boost)
                        b_rms = rms(bass)
                        t_rms = rms(treble)

                    # Сглаживание
                    smoothing = self.get_setting('smoothing')
                    decay = self.get_setting('decay')

                    bass_vol = smooth_volume(bass_vol, b_rms, smoothing)
                    treble_vol = smooth_volume(treble_vol, t_rms, smoothing)

                    # Отправка в очередь управления
                    try:
                        self.audio_queue.put_nowait((bass_vol, treble_vol))
                    except queue.Full:
                        pass

                    # Обновление GUI-индикаторов
                    threshold = self.get_setting('threshold')
                    ceiling = self.get_setting('ceiling')
                    bf = int(min(bass_vol/ceiling, 1.0)*255) if bass_vol > threshold else 0
                    tf = int(min(treble_vol/ceiling, 1.0)*255) if treble_vol > threshold else 0
                    self.update_indicators(bf, tf)

                    # Затухание
                    bass_vol *= decay
                    treble_vol *= decay

            except Exception as e:
                if self.running:
                    self.log(f"Ошибка аудио: {e}")
                time.sleep(0.1)

    def control_thread(self):
        """Поток управления триггерами."""
        self.log("Поиск DualSense...")

        if not DUALSENSE_OK:
            self.log("❌ dualsense-controller не установлен!")
            return

        try:
            devices = DualSenseController.enumerate_devices()
            if not devices:
                self.log("Контроллер не найден!")
                return

            self.controller = DualSenseController(
                device_index_or_device_info=0,
                microphone_initially_muted=True
            )
            self.controller.activate()
            self.log("Контроллер активирован")
        except Exception as e:
            self.log(f"Ошибка контроллера: {e}")
            return

        last_left, last_right = -1, -1

        while self.running:
            try:
                try:
                    bv, tv = self.audio_queue.get(timeout=0.05)
                except queue.Empty:
                    time.sleep(0.005)
                    continue

                threshold = self.get_setting('threshold')
                ceiling = self.get_setting('ceiling')
                min_f = self.get_setting('min_force')
                max_f = self.get_setting('max_force')

                # Левый триггер
                vol = bv if self.get_setting('left_freq') == 'low' else tv
                fl = calculate_force(vol, threshold, ceiling, min_f, max_f)

                # Правый триггер
                vol = bv if self.get_setting('right_freq') == 'low' else tv
                fr = calculate_force(vol, threshold, ceiling, min_f, max_f)

                # Применение
                self._apply_force('left', fl, last_left)
                last_left = fl
                self._apply_force('right', fr, last_right)
                last_right = fr

            except Exception as e:
                if self.running:
                    self.log(f"Ошибка управления: {e}")
                time.sleep(0.1)

    def _apply_force(self, side: str, force: int, last: int):
        """Применяет силу к триггеру."""
        if force == last:
            return

        with self.force_lock:
            try:
                trigger = (
                    self.controller.left_trigger if side == 'left'
                    else self.controller.right_trigger
                )
                if force > 0:
                    trigger.effect.continuous_resistance(0, force)
                else:
                    trigger.effect.off()
            except Exception:
                pass

    def stop(self):
        """Останавливает мост."""
        self.running = False

        if self.parec_process:
            try:
                self.parec_process.terminate()
                self.parec_process.wait(timeout=1)
            except:
                try:
                    self.parec_process.kill()
                except:
                    pass

        if self.controller:
            try:
                self.controller.left_trigger.effect.off()
                self.controller.right_trigger.effect.off()
                self.controller.deactivate()
            except:
                pass
