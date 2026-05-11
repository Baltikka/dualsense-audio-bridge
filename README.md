# DualSense Audio-to-Trigger Bridge for Linux

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Linux-lightgrey.svg)](https://www.linux.org/)

<p align="center">
  <img src="https://img.shields.io/badge/DualSense-Controller-0052CC?style=for-the-badge&logo=playstation&logoColor=white" alt="DualSense">
</p>

Преобразует системный звук в реальном времени в адаптивное сопротивление триггеров контроллера DualSense. Поддерживает фильтрацию частот для раздельной реакции на басы и высокие частоты.

## ⚠️ Предупреждение

**Фрагменты скрипта были сгенерированы ИИ - код может содержать ошибки.**

Существуют аналогичные проекты под Windows, но я не смог найти готового решения для Linux.
Проект тестировался только на одном ПК (arch btw), и только с проводным подключением Dualsense.

Используйте на свой страх и риск.

## Возможности

- 🎵 **Захват системного звука** в реальном времени через PipeWire/PulseAudio
- 🎛️ **Двухполосная фильтрация** с отсечкой средних частот
- 🎮 **Раздельное управление** левым и правым триггерами
- 📊 **Визуализация спектра** в консоли
- 📋 **Готовые пресеты** для разных случаев, и возможность создавать собственные

## Требования

- **Python 3.8+**
- **Контроллер DualSense** (по USB)
- **Linux с PipeWire или PulseAudio**
- **Утилита `parec`**

## Установка

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/yourusername/dualsense-audio-bridge.git
cd dualsense-audio-bridge

# 2. Создайте виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# 3. Установите Python-зависимости
pip install -r requirements.txt

# 4. Проверьте наличие parec
which parec
# Если утилиты нет, то требуется установить pulseaudio-utils или иной пакет где есть parec

# 5. Предоставьте доступ к контроллеру (при необходимости)
./controller_permission.sh
```

## Запуск

```bash

# Базовый запуск
python3 dualsense_bridge.py
# С выбором пресета
python3 dualsense_bridge.py --preset
# С указанием границ отсечки (НЧ_граница ВЧ_граница)
python3 dualsense_bridge.py 200 2500
```

## Основные настройки

```python
# Границы частот
MID_LOW_CUT = 200   # Нижняя граница средних частот (Гц)
MID_HIGH_CUT = 1500 # Верхняя граница средних частот (Гц)

# Усиление частот
BASS_BOOST = 4 # Усиление басов
TREBLE_BOOST = 6.5 # Усиление высоких

# Баланс НЧ/ВЧ (0.0 = только ВЧ, 1.0 = только НЧ, 0.5 = поровну)
FREQ_BALANCE = 0.5

# Раздельное управление триггерами
SPLIT_TRIGGERS = True # Включить ли раздельное управление
FREQ_LEFT = "low" # low - низкие, high - высокие
FREQ_RIGHT = "high" # low - низкие, high - высокие

# Настройки границ громкости
SILENCE_THRESHOLD = 0.2 # Порог тишины
AUDIO_CEILING = 0.7 # Уровень громкости для максимального сопротивления

# Сглаживание
SMOOTHING = 0.1 # Сглаживание
DECAY = 0.3 # Затухание при тишине

# Сила сопротивления
MIN_FORCE = 1
MAX_FORCE = 255

# Частота обновления
UPDATE_RATE = 30
```

## 🛠️ Устранение неполадок

### Контроллер не найден

```bash
# Проверьте подключение
ls /dev/input/ | grep js
# Добавьте права (если нужно)
./controller_permission.sh
# ИЛИ добавьте права командами вручную:
echo 'KERNEL=="hidraw*", ATTRS{idVendor}=="054c", ATTRS{idProduct}=="0ce6", MODE="0666"' | sudo tee /etc/udev/rules.d/99-dualsense.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### Нет звука

```bash
# Проверьте аудиоустройства
pactl list sources short | grep monitor
# Измените AUDIO_SOURCE в скрипте
AUDIO_SOURCE = "@DEFAULT_MONITOR@"
# или конкретное устройство:
AUDIO_SOURCE = "alsa_output.pci-0000_00_1f.3.analog-stereo.monitor"
```
