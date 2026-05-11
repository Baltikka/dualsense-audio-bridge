# DualSense Audio-to-Trigger Bridge for Linux

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Linux-lightgrey.svg)](https://www.linux.org/)

<p align="center">
  <img src="https://img.shields.io/badge/DualSense-Controller-0052CC?style=for-the-badge&logo=playstation&logoColor=white" alt="DualSense">
</p>

Преобразует системный звук в (почти) реальном времени в адаптивное сопротивление триггеров контроллера DualSense. Поддерживает фильтрацию частот для раздельной реакции на басы и высокие частоты.

Доступен в двух вариантах:
- **GUI версия** — графический интерфейс с визуальными индикаторами и управлением пресетами
- **CLI версия** — консольная версия со спектрограммой

## 📸 Скриншот
<img width="678" height="726" alt="изображение" src="https://github.com/user-attachments/assets/683e1e52-172e-4b80-b955-bf054ff1d605" />

## ⚠️ Предупреждение

**Фрагменты кода были сгенерированы ИИ — код может содержать ошибки.**

Существуют аналогичные проекты под Windows, но я не смог найти готового решения для Linux.

Проект тестировался только на одном ПК (Arch btw), и только с проводным подключением DualSense.

Используйте на свой страх и риск.

## ✨ Возможности

- 🎵 **Захват системного звука** в реальном времени через PipeWire/PulseAudio
- 🎛️ **Двухполосная фильтрация** — отсечка средних частот, только басы и высокие
- 🎮 **Раздельное управление** левым и правым триггерами (басы/высокие)
- 🖥️ **Графический интерфейс** (Tkinter) с индикаторами в реальном времени
- 📊 **Визуализация спектра** в консольной версии
- 💾 **Сохранение и загрузка пресетов** — создавайте свои профили настроек
- 📥 **Импорт/экспорт пресетов** — делитесь настройками с другими
- 📋 **Встроенные пресеты** для разных сценариев

## 📦 Варианты установки

### Вариант 1: Готовый бинарный файл (рекомендуется)

Скачайте последнюю версию из [Releases](https://github.com/Baltikka/dualsense-bridge/releases):

```bash
# Распакуйте архив
tar -xzf DualSenseBridge-linux-x86_64.tar.gz

# Установите системную зависимость
sudo apt install pulseaudio-utils  # или пакет с parec

# Запустите
./DualSenseBridge
```

### Вариант 2: Запуск из исходников

```bash
# Клонируйте репозиторий
git clone https://github.com/Baltikka/dualsense-bridge.git
cd dualsense-bridge

# Создайте виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Установите Python-зависимости
pip install -r requirements.txt

# Проверьте системные зависимости
which parec || echo "Установите pulseaudio-utils"

# Предоставьте доступ к контроллеру (при необходимости)
echo 'KERNEL=="hidraw*", ATTRS{idVendor}=="054c", ATTRS{idProduct}=="0ce6", MODE="0666"' | sudo tee /etc/udev/rules.d/99-dualsense.rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Запустите нужную версию
python3 dualsense-bridge.py          # GUI версия
python3 dualsense_bridge_cli.py      # CLI версия
```

### Вариант 3: Сборка из исходников

```bash
# Установите инструменты сборки
pip install -r requirements-build.txt

# Соберите бинарный файл
pyinstaller build.spec

# Готовый файл:
./dist/DualSenseBridge
```

## 🚀 Запуск

### GUI версия

```bash
# Простой запуск
python3 dualsense-bridge.py

# Или запуск бинарного файла
./DualSenseBridge
```
1. Подключите контроллер DualSense по USB
2. Запустите приложение
3. Настройте фильтры под свой вкус (или выберите пресет)
4. Нажмите «▶ Запустить»
5. Включите музыку или игру — триггеры начнут реагировать.

### CLI версия

```bash
# Базовый запуск
python3 dualsense_bridge.py

# С выбором пресета
python3 dualsense_bridge.py --preset

# С указанием границ отсечки
python3 dualsense_bridge.py 200 2500
```

## 🎛️ Управление пресетами (GUI)

В GUI версии доступно управление пресетами:

|Кнопка|Действие|
|---|---|
|**📋 Стандартный**|Циклическое переключение встроенных пресетов|
|**📂 Загрузить...**|Открыть список всех пресетов, загрузить/удалить|
|**💾 Сохранить...**|Сохранить текущие настройки как новый пресет|
|**📤 Экспорт**|Сохранить пресет в JSON-файл (в диалоге загрузки)|
|**📥 Импорт**|Загрузить пресет из JSON-файла (в диалоге загрузки)|

Пресеты сохраняются в `~/.config/dualsense-bridge/presets/`.

## ⚙️ Основные настройки

Все настройки доступны через GUI. При использовании CLI версии редактируются в коде:

```python
# Границы частот (отсекается всё между ними)
MID_LOW_CUT = 200    # Нижняя граница средних частот (Гц)
MID_HIGH_CUT = 1500  # Верхняя граница средних частот (Гц)

# Усиление частот
BASS_BOOST = 4.0     # Усиление низких частот
TREBLE_BOOST = 6.5   # Усиление высоких частот

# Чувствительность
SILENCE_THRESHOLD = 0.2  # Порог тишины (0-1)
AUDIO_CEILING = 0.7      # Максимальная громкость (0-1)

# Сглаживание
SMOOTHING = 0.1  # Скорость реакции (0-1)
DECAY = 0.3      # Скорость затухания (0-1)

# Сила сопротивления
MIN_FORCE = 5    # Минимальная сила (0-255)
MAX_FORCE = 255  # Максимальная сила (0-255)

# Назначение триггеров
FREQ_LEFT = "low"   # "low" = басы, "high" = высокие
FREQ_RIGHT = "high"
```

## 🛠️ Устранение неполадок

### Контроллер не найден

```bash
# Проверьте подключение
ls /dev/input/ | grep js

# Проверьте права доступа
ls -la /dev/hidraw*

# Добавьте udev-правило
echo 'KERNEL=="hidraw*", ATTRS{idVendor}=="054c", ATTRS{idProduct}=="0ce6", MODE="0666"' | sudo tee /etc/udev/rules.d/99-dualsense.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### Триггеры не реагируют

- Уменьшите `SILENCE_THRESHOLD` (порог тишины)
- Уменьшите `AUDIO_CEILING` (потолок громкости)
- Увеличьте `BASS_BOOST` и `TREBLE_BOOST`
- Проверьте, что звук действительно воспроизводится

### Ошибки при сборке

```bash
# Используйте Python 3.11 или 3.12
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements-build.txt
pyinstaller build.spec
```
