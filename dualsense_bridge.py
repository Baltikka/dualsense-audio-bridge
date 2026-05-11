#!/usr/bin/env python3
"""
DualSense Audio-to-Trigger Bridge с двухполосным фильтром
Захватывает системный звук, отсекает средние частоты,
оставляя только НИЗКИЕ и ВЫСОКИЕ для управления триггерами.

"""

import time
import threading
import queue
import subprocess
import struct
import numpy as np
from scipy import signal
from dualsense_controller import DualSenseController

# ═══════════════════ НАСТРОЙКИ ═══════════════════
# Устройство для захвата
AUDIO_SOURCE = "@DEFAULT_MONITOR@"

# Частота дискретизации
SAMPLE_RATE = 16000
# Размер буфера
BUFFER_SIZE = 2048

# ════════ НАСТРОЙКИ ДВУХПОЛОСНОГО ФИЛЬТРА ════════
# Границы средних частот (которые будут ОТСЕЧЕНЫ)
MID_LOW_CUT = 200   # Нижняя граница средних частот (Гц)
MID_HIGH_CUT = 1500 # Верхняя граница средних частот (Гц)
# Всё что НИЖЕ MID_LOW_CUT - басы (пропускаем)
# Всё что ВЫШЕ MID_HIGH_CUT - высокие (пропускаем)
# Всё что МЕЖДУ ними - отсекается!

# Порядок фильтров (4 = хорошая избирательность)
FILTER_ORDER = 4

# Усиление басов
BASS_BOOST = 4 # 4
# Усиление высоких
TREBLE_BOOST = 6.5 # 6.5

# Баланс НЧ/ВЧ (0.0 = только ВЧ, 1.0 = только НЧ, 0.5 = поровну)
FREQ_BALANCE = 0.5  # 60% бас, 40% высокие

# Раздельное управление триггерами
SPLIT_TRIGGERS = True # Включить ли раздельное управление
FREQ_LEFT = "low" # low - низкие, high - высокие
FREQ_RIGHT = "high" # low - низкие, high - высокие


# ═══════════════════════════════════════════════════

# Порог тишины
SILENCE_THRESHOLD = 0.2 # 0.2
# Уровень громкости для максимального сопротивления
AUDIO_CEILING = 0.7
# Сглаживание
SMOOTHING = 0.1
# Затухание при тишине
DECAY = 0.3

# Сила сопротивления
MIN_FORCE = 1
MAX_FORCE = 255

# Частота обновления
UPDATE_RATE = 30 # 30 - хорошее значение

# Визуализация
SHOW_VU_METER = True
VU_WIDTH = 35
SHOW_SPECTRUM = True  # Показывать мини-спектрограмму

# Отладка
DEBUG = False
# ═══════════════════════════════════════════════════

class DualBandFilteredBridge:
    def __init__(self):
        self.audio_queue = queue.Queue(maxsize=5)
        self.spectrum_queue = queue.Queue(maxsize=3)
        self.running = False
        self.controller = None
        self.current_force_left = 0
        self.current_force_right = 0
        self.current_bass_volume = 0.0
        self.current_treble_volume = 0.0
        self.parec_process = None
        self.force_lock = threading.Lock()

        # Создаем фильтры
        self.create_filters()

        # Буфер для спектрального анализа
        self.sample_buffer = np.array([], dtype=np.float32)
        self.spectrum_buffer_size = SAMPLE_RATE // 8  # 125ms для анализа

    def create_filters(self):
        """Создает фильтры низких и высоких частот"""
        nyquist = SAMPLE_RATE / 2

        # Фильтр низких частот (пропускает всё ниже MID_LOW_CUT)
        low_cutoff = MID_LOW_CUT / nyquist
        if low_cutoff >= 1.0:
            low_cutoff = 0.99

        self.b_low, self.a_low = signal.butter(
            FILTER_ORDER, low_cutoff, btype='lowpass'
        )
        self.low_filter_state = signal.lfilter_zi(self.b_low, self.a_low)

        # Фильтр высоких частот (пропускает всё выше MID_HIGH_CUT)
        high_cutoff = MID_HIGH_CUT / nyquist
        if high_cutoff >= 1.0:
            high_cutoff = 0.99

        self.b_high, self.a_high = signal.butter(
            FILTER_ORDER, high_cutoff, btype='highpass'
        )
        self.high_filter_state = signal.lfilter_zi(self.b_high, self.a_high)

        print(f"🎛️ Двухполосный фильтр:")
        print(f"   Бас: 0 - {MID_LOW_CUT} Гц")
        print(f"   Отсечка: {MID_LOW_CUT} - {MID_HIGH_CUT} Гц")
        print(f"   Высокие: {MID_HIGH_CUT}+ Гц")
        print(f"   Баланс: {FREQ_BALANCE:.0%} бас / {1-FREQ_BALANCE:.0%} высокие")

    def apply_dual_band_filter(self, samples):
        """Применяет двухполосную фильтрацию"""
        if len(samples) == 0:
            return np.zeros_like(samples), np.zeros_like(samples)

        # Применяем фильтр низких частот
        bass_samples, self.low_filter_state = signal.lfilter(
            self.b_low, self.a_low, samples,
            zi=self.low_filter_state * samples[0]
        )
        bass_samples *= BASS_BOOST
        bass_samples = np.clip(bass_samples, -1.0, 1.0)

        # Применяем фильтр высоких частот
        treble_samples, self.high_filter_state = signal.lfilter(
            self.b_high, self.a_high, samples,
            zi=self.high_filter_state * samples[0]
        )
        treble_samples *= TREBLE_BOOST
        treble_samples = np.clip(treble_samples, -1.0, 1.0)

        return bass_samples, treble_samples

    def analyze_spectrum(self, samples):
        """Анализирует спектр для визуализации"""
        if len(samples) < 256:
            return np.zeros(10)

        # Применяем окно
        windowed = samples * np.hanning(len(samples))

        # FFT
        fft = np.abs(np.fft.rfft(windowed))
        freqs = np.fft.rfftfreq(len(windowed), 1.0 / SAMPLE_RATE)

        # Разбиваем на полосы для визуализации
        bands = 10
        band_energies = np.zeros(bands)

        # Логарифмическая шкала частот
        freq_bins = np.logspace(np.log10(20), np.log10(SAMPLE_RATE/2), bands + 1)

        for i in range(bands):
            mask = (freqs >= freq_bins[i]) & (freqs < freq_bins[i+1])
            if np.any(mask):
                band_energies[i] = np.sum(fft[mask] ** 2)

        # Нормализуем
        if np.max(band_energies) > 0:
            band_energies /= np.max(band_energies)

        return band_energies

    def spectrum_meter(self, spectrum, bass_vol, treble_vol, force_left, force_right):
        """Отображает спектрограмму и уровни"""
        if not SHOW_VU_METER:
            return

        # Очищаем строку
        print("\r\033[K", end="")

        # Отображаем спектр
        if SHOW_SPECTRUM and len(spectrum) > 0:
            # Определяем границы басов и высоких в спектре
            total_bands = len(spectrum)
            bass_bands = max(1, int(total_bands * MID_LOW_CUT / (SAMPLE_RATE/2)))
            treble_start = int(total_bands * MID_HIGH_CUT / (SAMPLE_RATE/2))

            spec_str = ""
            for i in range(total_bands):
                if i < bass_bands:
                    # Басы - синий
                    color = '\033[94m'
                elif i >= treble_start:
                    # Высокие - красный
                    color = '\033[91m'
                else:
                    # Средние (отсеченные) - тусклые
                    color = '\033[90m'

                bars = int(spectrum[i] * 8)
                if bars > 0:
                    spec_str += color + "▁▂▃▄▅▆▇█"[min(bars, 7)]
                else:
                    spec_str += " "

            spec_str += "\033[0m"
            print(f"🎵 [{spec_str}]")

        # Индикаторы громкости для басов и высоких
        bass_norm = min(bass_vol / AUDIO_CEILING, 1.0)
        treble_norm = min(treble_vol / AUDIO_CEILING, 1.0)

        bass_bars = int(bass_norm * VU_WIDTH)
        treble_bars = int(treble_norm * VU_WIDTH)

        bass_bar = '\033[94m' + "█" * bass_bars + '\033[90m' + "░" * (VU_WIDTH - bass_bars) + '\033[0m'
        treble_bar = '\033[91m' + "█" * treble_bars + '\033[90m' + "░" * (VU_WIDTH - treble_bars) + '\033[0m'

        # Силы триггеров
        if SPLIT_TRIGGERS:
            left_str = f"\033[94mЛ:{force_left:3d}\033[0m" if force_left > 0 else f"\033[90mЛ:{force_left:3d}\033[0m"
            right_str = f"\033[91mП:{force_right:3d}\033[0m" if force_right > 0 else f"\033[90mП:{force_right:3d}\033[0m"
        else:
            avg_force = (force_left + force_right) // 2
            left_str = right_str = f"\033[95m●:{avg_force:3d}\033[0m"

        print(f"\r🔊 Бас:  [{bass_bar}] {left_str}")
        print(f"\r🔔 ВЧ:   [{treble_bar}] {right_str}")

        # Перемещаем курсор вверх для перезаписи
        if SHOW_SPECTRUM:
            print("\033[3A", end="")
        else:
            print("\033[2A", end="")

    def audio_capture_loop(self):
        """Захват и двухполосная фильтрация звука"""
        print(f"🎤 Запуск захвата с двухполосным фильтром...")
        print(f"   Устройство: {AUDIO_SOURCE}")
        print(f"   Частота: {SAMPLE_RATE} Гц\n")

        cmd = [
            'parec',
            '--device=' + AUDIO_SOURCE,
            '--format=s16le',
            '--rate=' + str(SAMPLE_RATE),
            '--channels=1',
            '--latency-msec=10'
        ]

        try:
            self.parec_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=BUFFER_SIZE * 2
            )

            print("✅ Захват запущен")
            if SPLIT_TRIGGERS:
                print("   Левый триггер (🔊) = Басы")
                print("   Правый триггер (🔔) = Высокие частоты\n")
            else:
                print("   Оба триггера = Басы + Высокие\n")

            buffer = b''
            bytes_per_sample = 2

            while self.running:
                try:
                    data = self.parec_process.stdout.read(BUFFER_SIZE)

                    if not data:
                        if self.running:
                            print("\n⚠️ Переподключение аудио...")
                            self.parec_process.terminate()
                            self.parec_process = subprocess.Popen(
                                cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
                            )
                        continue

                    buffer += data
                    samples_count = len(buffer) // bytes_per_sample

                    if samples_count > 0:
                        # Конвертируем в float
                        samples = struct.unpack(f'<{samples_count}h',
                                               buffer[:samples_count * bytes_per_sample])
                        buffer = buffer[samples_count * bytes_per_sample:]
                        samples_float = np.array(samples, dtype=np.float32) / 32768.0

                        # Применяем двухполосный фильтр
                        bass, treble = self.apply_dual_band_filter(samples_float)

                        # Вычисляем RMS для каждой полосы
                        bass_rms = np.sqrt(np.mean(bass ** 2))
                        treble_rms = np.sqrt(np.mean(treble ** 2))

                        # Спектральный анализ
                        self.sample_buffer = np.append(self.sample_buffer, samples_float)
                        if len(self.sample_buffer) >= self.spectrum_buffer_size:
                            spectrum = self.analyze_spectrum(
                                self.sample_buffer[:self.spectrum_buffer_size]
                            )
                            try:
                                self.spectrum_queue.put_nowait((spectrum, bass_rms, treble_rms))
                            except queue.Full:
                                pass
                            self.sample_buffer = self.sample_buffer[self.spectrum_buffer_size:]

                        # Отправляем громкости
                        try:
                            self.audio_queue.put_nowait((bass_rms, treble_rms))
                        except queue.Full:
                            pass

                except Exception as e:
                    if self.running and DEBUG:
                        print(f"\nОшибка: {e}")
                    time.sleep(0.01)

        except FileNotFoundError:
            print("❌ 'parec' не найден. Установите: sudo apt install pulseaudio-utils")
            self.running = False
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            self.running = False

    def trigger_control_loop(self):
        """Управление триггерами с разделением по частотам"""
        print("🎮 Подключение DualSense...")

        try:
            devices = DualSenseController.enumerate_devices()
            if not devices:
                print("❌ Контроллер не найден!")
                self.running = False
                return

            print("✅ Контроллер найден")

            self.controller = DualSenseController(
                device_index_or_device_info=0,
                microphone_initially_muted=True
            )
            self.controller.activate()
            print("✅ Активирован\n")
            print("─" * 55)
            print("🎵 Воспроизведите музыку!")
            if FREQ_LEFT == "low":
                print("   Левый триггер = Низкие частоты")
            else:
                print("   Левый триггер = Высокие частоты")
            if FREQ_RIGHT == "low":
                print("   Правый триггер = Низкие частоты")
            else:
                print("   Правый триггер = Высокие частоты")
            print("   Средние частоты игнорируются!")
            print("─" * 55 + "\n")

        except Exception as e:
            print(f"❌ Ошибка: {e}")
            self.running = False
            return

        last_force_left = 0
        last_force_right = 0
        current_spectrum = np.zeros(10)

        while self.running:
            try:
                # Получаем громкости басов и высоких
                got_data = False
                bass_vol = 0.0
                treble_vol = 0.0

                while not self.audio_queue.empty():
                    try:
                        bass_vol, treble_vol = self.audio_queue.get_nowait()
                        got_data = True
                    except queue.Empty:
                        break

                # Получаем спектр
                while not self.spectrum_queue.empty():
                    try:
                        current_spectrum, _, _ = self.spectrum_queue.get_nowait()
                    except queue.Empty:
                        break

                # Сглаживание
                if got_data:
                    self.current_bass_volume = (SMOOTHING * self.current_bass_volume +
                                               (1 - SMOOTHING) * bass_vol)
                    self.current_treble_volume = (SMOOTHING * self.current_treble_volume +
                                                 (1 - SMOOTHING) * treble_vol)
                else:
                    self.current_bass_volume *= DECAY
                    self.current_treble_volume *= DECAY

                # Вычисляем силы для триггеров
                if SPLIT_TRIGGERS:
                    # Раздельный режим
                    if FREQ_LEFT == "low":
                        # Левый триггер - басы
                        if self.current_bass_volume > SILENCE_THRESHOLD:
                            bass_norm = min(self.current_bass_volume / AUDIO_CEILING, 1.0)
                            force_left = int(MIN_FORCE + bass_norm * (MAX_FORCE - MIN_FORCE))
                        else:
                            force_left = MIN_FORCE if MIN_FORCE > 0 else 0
                    else:
                        # Левый триггер - верха
                        if self.current_treble_volume > SILENCE_THRESHOLD:
                            treble_norm = min(self.current_treble_volume / AUDIO_CEILING, 1.0)
                            force_left = int(MIN_FORCE + treble_norm * (MAX_FORCE - MIN_FORCE))
                        else:
                            force_left = MIN_FORCE if MIN_FORCE > 0 else 0

                    if FREQ_RIGHT == "low":
                        # Правый триггер - басы
                        if self.current_bass_volume > SILENCE_THRESHOLD:
                            bass_norm = min(self.current_bass_volume / AUDIO_CEILING, 1.0)
                            force_right = int(MIN_FORCE + bass_norm * (MAX_FORCE - MIN_FORCE))
                        else:
                            force_right = MIN_FORCE if MIN_FORCE > 0 else 0
                    else:
                        # Правый триггер - верха
                        if self.current_treble_volume > SILENCE_THRESHOLD:
                            treble_norm = min(self.current_treble_volume / AUDIO_CEILING, 1.0)
                            force_right = int(MIN_FORCE + treble_norm * (MAX_FORCE - MIN_FORCE))
                        else:
                            force_right = MIN_FORCE if MIN_FORCE > 0 else 0
                else:
                    # Смешанный режим
                    combined = (self.current_bass_volume * FREQ_BALANCE +
                               self.current_treble_volume * (1 - FREQ_BALANCE))

                    if combined > SILENCE_THRESHOLD:
                        combined_norm = min(combined / AUDIO_CEILING, 1.0)
                        force_left = force_right = int(MIN_FORCE + combined_norm * (MAX_FORCE - MIN_FORCE))
                    else:
                        force_left = force_right = MIN_FORCE if MIN_FORCE > 0 else 0

                force_left = min(force_left, MAX_FORCE)
                force_right = min(force_right, MAX_FORCE)

                # Применяем эффекты
                if force_left != last_force_left:
                    with self.force_lock:
                        if force_left > 0:
                            self.controller.left_trigger.effect.continuous_resistance(0, force_left)
                        else:
                            self.controller.left_trigger.effect.off()
                    last_force_left = force_left

                if force_right != last_force_right:
                    with self.force_lock:
                        if force_right > 0:
                            self.controller.right_trigger.effect.continuous_resistance(0, force_right)
                        else:
                            self.controller.right_trigger.effect.off()
                    last_force_right = force_right

                # Визуализация
                self.spectrum_meter(current_spectrum,
                                  self.current_bass_volume,
                                  self.current_treble_volume,
                                  force_left, force_right)

                time.sleep(1.0 / UPDATE_RATE)

            except Exception as e:
                if DEBUG:
                    print(f"\nОшибка: {e}")
                time.sleep(0.1)

    def start(self):
        """Запуск"""
        print("\n" + "═" * 55)
        print("║       DualSense Audio-to-Trigger Bridge      ║")
        print("║  System Audio → Dual-Band Trigger Vibration  ║")
        print("═" * 55 + "\n")

        self.running = True

        audio_thread = threading.Thread(target=self.audio_capture_loop, daemon=True)
        trigger_thread = threading.Thread(target=self.trigger_control_loop, daemon=True)

        audio_thread.start()
        time.sleep(1)
        trigger_thread.start()

        try:
            while self.running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n\n🛑 Завершение...")
            self.stop()

    def stop(self):
        """Остановка"""
        self.running = False

        if self.parec_process:
            try:
                self.parec_process.terminate()
                self.parec_process.wait(timeout=2)
            except:
                try:
                    self.parec_process.kill()
                except:
                    pass

        if self.controller:
            try:
                self.controller.left_trigger.effect.off()
                self.controller.right_trigger.effect.off()
                time.sleep(0.1)
                self.controller.deactivate()
                print("✅ Контроллер деактивирован")
            except:
                pass

        print("✅ Мост остановлен")


# ═══════════════════ ПРЕСЕТЫ ═══════════════════

# Можно добавить пресет для конкретной игры, если вибрация триггера плохо заметна на стандартных настройках

PRESETS = {
    'default': {
        'name': 'Стандартный (default)',
        'mid_low': 200,
        'mid_high': 1500,
        'bass_boost': 4.0,
        'treble_boost': 6.5,
        'description': 'Стабильная реакция на шумные звуки'
    },
    'extreme': {
        'name': 'Экстремальный (только края)',
        'mid_low': 100,
        'mid_high': 3000,
        'bass_boost': 6,
        'treble_boost': 8,
        'description': 'Максимальный контраст, широкая отсечка середины'
    },
    'no_mid_cut': {
        'name': 'Без отсечки середины',
        'mid_low': 100,
        'mid_high': 100,
        'bass_boost': 3,
        'treble_boost': 3,
        'description': 'Без отсечки середины, менее читаемые вибрации, но может быть полезно в некоторых играх'
    },
    'quiet': {
        'name': 'Усиление тихих звуков',
        'mid_low': 200,
        'mid_high': 1500,
        'bass_boost': 16,
        'treble_boost': 20,
        'description': 'Более заметная вибрация при тихих звуках'
    }
}


# ═══════════════════ ЗАПУСК ═══════════════════

if __name__ == "__main__":
    import sys

    # Проверка зависимостей
    try:
        import scipy
    except ImportError:
        print("❌ Требуется scipy. Установите: pip install scipy")
        sys.exit(1)

    # Выбор пресета если указан
    if '--preset' in sys.argv:
        print("\n📋 Доступные пресеты:\n")
        for key, preset in PRESETS.items():
            print(f"  {key:12} - {preset['name']}")
            print(f"             {preset['description']}")
            print()

        choice = input("Выберите пресет (или Enter для 'default'): ").strip().lower()

        if choice in PRESETS:
            preset = PRESETS[choice]
            MID_LOW_CUT = preset['mid_low']
            MID_HIGH_CUT = preset['mid_high']
            BASS_BOOST = preset['bass_boost']
            TREBLE_BOOST = preset['treble_boost']
            print(f"✅ Выбран пресет: {preset['name']}\n")
    elif len(sys.argv) > 1:
        # Можно указать границы в командной строке
        try:
            MID_LOW_CUT = float(sys.argv[1])
            if len(sys.argv) > 2:
                MID_HIGH_CUT = float(sys.argv[2])
            print(f"🎛️ Отсечка: {MID_LOW_CUT} - {MID_HIGH_CUT} Гц\n")
        except ValueError:
            print(f"❌ Неверные параметры")
            sys.exit(1)

    bridge = DualBandFilteredBridge()
    bridge.start()
