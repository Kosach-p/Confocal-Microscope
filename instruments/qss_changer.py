# replace_colors.py
import re

# Цвета для замены (Dark → Light)
colors = {
    # Основные фоны
    '#1d1d1d': '#e8edf2',
    '#303030': '#dce3eb',
    '#3d3d3d': '#d0d8e3',
    '#545454': '#c8d4e3',
    '#242424': '#e8edf2',

    # Акценты
    '#4d6490': '#8aa5c4',
    '#6c7d9d': '#B4C2DB',
    '#8a9bb9': '#8aa5c4',
    '#3a4a6b': '#8aa5c4',
    '#444460': '#b8c8dc',  # pressed фон для кнопок

    # Текст
    '#ffffff': '#000000',
    '#cccccc': '#3d3d3d',
    '#797979': '#8a9bad',

    # Границы
    '#353535': '#b8c5d4',
    '#545454': '#b0bfd0',
}

# Читаем dark.qss
with open('../service_files/themes/dark.qss', 'r', encoding='utf-8') as f:
    content = f.read()

# Меняем цвета
for old, new in colors.items():
    content = content.replace(old, new)

# Сохраняем как light.qss
with open('../service_files/themes/light.qss', 'w', encoding='utf-8') as f:
    f.write('/* Light theme */\n' + content)

print('✅ Готово! Создан light.qss')