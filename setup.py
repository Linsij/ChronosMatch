
from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
    Extension(
        "matching_engine.order_book",
        ["matching_engine/order_book.pyx"],
    )
]

setup(
    name="ChronosMatch",
    ext_modules=cythonize(
        extensions,
        compiler_directives={"language_level": "3"},
    ),
)
