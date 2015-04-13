import os

from setuptools import find_packages, setup


with open(os.path.join(os.path.dirname(__file__), "README.rst")) as readme:
    long_description = readme.read()

classifiers = [
    "Development Status :: 3 - Alpha",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy"
]

setup(
    name="pier",
    packages=find_packages(),
    install_requires=[
        "betterpath >= 0.2.2",
        "characteristic",
        "docker-py >= 1.0.0",
    ],
    setup_requires=["vcversioner"],
    vcversioner={"version_module_paths": ["pier/__init__.py"]},
    author="Magnetic Engineering",
    author_email="engineering@magnetic.com",
    classifiers=classifiers,
    description="A high-level Docker API",
    license="MIT",
    long_description=long_description,
    url="https://github.com/Magnetic/Pier",
)
