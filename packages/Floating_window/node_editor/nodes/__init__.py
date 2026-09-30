import importlib
from pathlib import Path

package_dir = Path(__file__).parent

for py_file in package_dir.rglob("*.py"):
    if py_file.name == "__init__.py":
        continue
    relative = py_file.relative_to(package_dir)
    module_path = ".".join(relative.with_suffix("").parts)
    importlib.import_module(f".{module_path}", package=__package__)