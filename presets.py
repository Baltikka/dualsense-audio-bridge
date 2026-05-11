"""Управление пресетами: встроенные и пользовательские."""

import json
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional


# Встроенные пресеты
BUILTIN_PRESETS = [
    {
        'name': 'Стандартный',
        'mid_low_cut': 200, 'mid_high_cut': 1500,
        'bass_boost': 2.0, 'treble_boost': 7.5,
        'threshold': 0.2, 'ceiling': 0.7,
        'smoothing': 0.01, 'decay': 0.1,
        'min_force': 1, 'max_force': 255,
        'left_freq': 'low', 'right_freq': 'high',
    },
    {
        'name': 'Экстремальный',
        'mid_low_cut': 100, 'mid_high_cut': 3000,
        'bass_boost': 6.0, 'treble_boost': 8.0,
        'threshold': 0.15, 'ceiling': 0.6,
        'smoothing': 0.08, 'decay': 0.25,
        'min_force': 5, 'max_force': 255,
        'left_freq': 'low', 'right_freq': 'high',
    },
    {
        'name': 'Тихие звуки',
        'mid_low_cut': 200, 'mid_high_cut': 1500,
        'bass_boost': 16.0, 'treble_boost': 20.0,
        'threshold': 0.05, 'ceiling': 0.4,
        'smoothing': 0.05, 'decay': 0.2,
        'min_force': 3, 'max_force': 255,
        'left_freq': 'low', 'right_freq': 'high',
    },
    {
        'name': 'Ударные',
        'mid_low_cut': 150, 'mid_high_cut': 2000,
        'bass_boost': 5.0, 'treble_boost': 4.0,
        'threshold': 0.2, 'ceiling': 0.7,
        'smoothing': 0.1, 'decay': 0.3,
        'min_force': 5, 'max_force': 255,
        'left_freq': 'low', 'right_freq': 'high',
    },
    {
        'name': 'Без отсечки',
        'mid_low_cut': 100, 'mid_high_cut': 100,
        'bass_boost': 3.0, 'treble_boost': 3.0,
        'threshold': 0.2, 'ceiling': 0.7,
        'smoothing': 0.1, 'decay': 0.3,
        'min_force': 5, 'max_force': 255,
        'left_freq': 'low', 'right_freq': 'high',
    },
]


def get_presets_dir() -> Path:
    """Директория для хранения пользовательских пресетов."""
    xdg_config = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
    path = Path(xdg_config) / 'dualsense-bridge' / 'presets'
    path.mkdir(parents=True, exist_ok=True)
    return path


def sanitize_filename(name: str) -> str:
    """Делает из имени безопасное имя файла."""
    return "".join(c for c in name if c.isalnum() or c in ' _-').rstrip()


class PresetManager:
    """Менеджер пресетов."""

    def __init__(self):
        self.presets_dir = get_presets_dir()
        self._user_presets: List[Dict] = []
        self.load_user_presets()

    @property
    def all_presets(self) -> List[Dict]:
        """Все пресеты: встроенные + пользовательские."""
        return BUILTIN_PRESETS + self._user_presets

    @property
    def builtin_count(self) -> int:
        return len(BUILTIN_PRESETS)

    @property
    def user_count(self) -> int:
        return len(self._user_presets)

    def get_preset(self, index: int) -> Optional[Dict]:
        """Получить пресет по индексу (0-based, сквозной)."""
        if 0 <= index < len(self.all_presets):
            return self.all_presets[index].copy()
        return None

    def get_preset_by_name(self, name: str) -> Optional[Dict]:
        """Найти пресет по имени."""
        for p in self.all_presets:
            if p['name'] == name:
                return p.copy()
        return None

    def is_builtin(self, index: int) -> bool:
        """Встроенный ли пресет?"""
        return 0 <= index < self.builtin_count

    def load_user_presets(self):
        """Загружает пользовательские пресеты с диска."""
        self._user_presets = []
        if not self.presets_dir.exists():
            return

        for file in sorted(self.presets_dir.glob('*.json')):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    preset = json.load(f)
                if self._validate_preset(preset):
                    self._user_presets.append(preset)
            except (json.JSONDecodeError, KeyError):
                pass

    def save_preset(self, preset: Dict) -> bool:
        """
        Сохраняет пресет на диск.
        Если пресет с таким именем уже есть — перезаписывает.
        """
        if not self._validate_preset(preset):
            return False

        filename = sanitize_filename(preset['name']) + '.json'
        filepath = self.presets_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(preset, f, indent=2, ensure_ascii=False)

        # Обновляем список
        self.load_user_presets()
        return True

    def delete_preset(self, name: str) -> bool:
        """Удаляет пользовательский пресет по имени."""
        filename = sanitize_filename(name) + '.json'
        filepath = self.presets_dir / filename

        if filepath.exists():
            filepath.unlink()
            self.load_user_presets()
            return True
        return False

    def rename_preset(self, old_name: str, new_name: str) -> bool:
        """Переименовывает пресет."""
        old_file = self.presets_dir / (sanitize_filename(old_name) + '.json')
        new_file = self.presets_dir / (sanitize_filename(new_name) + '.json')

        if old_file.exists() and not new_file.exists():
            old_file.rename(new_file)
            self.load_user_presets()
            return True
        return False

    def _validate_preset(self, preset: Dict) -> bool:
        """Проверяет, что в пресете есть все нужные ключи."""
        required = [
            'name', 'mid_low_cut', 'mid_high_cut',
            'bass_boost', 'treble_boost',
            'threshold', 'ceiling', 'smoothing', 'decay',
            'min_force', 'max_force',
            'left_freq', 'right_freq',
        ]
        return all(k in preset for k in required)

    def export_preset(self, name: str, path: str) -> bool:
        """Экспортирует пресет в указанный файл."""
        preset = self.get_preset_by_name(name)
        if preset:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(preset, f, indent=2, ensure_ascii=False)
            return True
        return False

    def import_preset(self, path: str) -> Optional[str]:
        """Импортирует пресет из файла. Возвращает имя или None."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                preset = json.load(f)
            if self._validate_preset(preset):
                self.save_preset(preset)
                return preset['name']
        except:
            pass
        return None
