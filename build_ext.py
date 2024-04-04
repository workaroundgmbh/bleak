import os
from Cython.Build import cythonize
from pathlib import Path
from setuptools.command.build_ext import build_ext


root = Path(__file__).parent


def build(setup_kwargs):
    if not os.getenv("BLEAK_USE_CYTHON", False):
        return

    cython_files = [
        str(f)
        for package in setup_kwargs["packages"]
        for f in root.joinpath(package.replace(".", "/")).iterdir()
        if f.suffix == ".py"
        and f.is_file()
    ]

    setup_kwargs.update(
        {
            "ext_modules": cythonize(
                cython_files,
                compiler_directives={"language_level": 3},
            ),
            "exclude_package_data": {
                pkg: ["*.c"] for pkg in setup_kwargs["packages"]
            }
        }
    )
