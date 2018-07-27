from importlib import import_module


def class_from_string(import_str):
    module_path, class_name = import_str.rsplit('.', 1)
    module = import_module(module_path, class_name)
    return getattr(module, class_name)
