"""
pythong runtime — in-memory import hook for .cong files
"""

import sys
import os
import types
import importlib.abc
import importlib.util
import importlib.machinery

from pythong.lib.core import transform_cong_to_py, CongSyntaxError

CONG_EXT = ".cong"

_source_dirs: list[str] = []


def register_source_dirs(dirs: list[str]):
    _source_dirs.extend(dirs)


class CongLoader(importlib.abc.Loader):
    def __init__(self, path: str):
        self.path = path

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        with open(self.path, "r", encoding="utf-8") as f:
            source = f.read()
        try:
            py_source = transform_cong_to_py(source)
        except CongSyntaxError as e:
            raise ImportError(f"CongSyntaxError in {self.path}: {e}") from e

        code = compile(py_source, self.path, "exec")
        exec(code, module.__dict__)


class CongFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        search_dirs = list(path or []) + _source_dirs

        for directory in search_dirs:
            candidate = os.path.join(directory, fullname.replace(".", os.sep) + CONG_EXT)
            if os.path.isfile(candidate):
                loader = CongLoader(candidate)
                return importlib.util.spec_from_file_location(
                    fullname,
                    candidate,
                    loader=loader,
                    submodule_search_locations=[],
                )
        return None


def install_hook():
    sys.meta_path.insert(0, CongFinder())


def run_file(filepath: str):
    install_hook()

    dirpath = os.path.dirname(os.path.abspath(filepath))
    register_source_dirs([dirpath])
    if dirpath not in sys.path:
        sys.path.insert(0, dirpath)

    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        py_source = transform_cong_to_py(source)
    except CongSyntaxError as e:
        print(f"CongSyntaxError: {e}", file=sys.stderr)
        sys.exit(1)

    code = compile(py_source, filepath, "exec")
    globs = {
        "__name__": "__main__",
        "__file__": filepath,
        "__loader__": None,
        "__spec__": None,
    }
    exec(code, globs)
