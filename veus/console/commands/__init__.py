# This file makes the commands directory a package and can be used for dynamic loading.
import pkgutil
import importlib

def load_commands():
    """Dynamically import all modules in this package."""
    for loader, module_name, is_pkg in pkgutil.walk_packages(__path__):
        full_module_name = f"{__name__}.{module_name}"
        importlib.import_module(full_module_name)
