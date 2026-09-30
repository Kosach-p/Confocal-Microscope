import subprocess
import os
from pathlib import Path

# Путь к папке с UI файлами
ui_folder = Path("../ui/Windows")

for ui_file in ui_folder.glob("*.ui"):
    py_file = ui_file.with_suffix('.py')
    subprocess.run(['pyuic6', str(ui_file), '-o', str(py_file)])
    print(f"Конвертирован: {ui_file.name} -> {py_file.name}")