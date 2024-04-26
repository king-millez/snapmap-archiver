# -*- coding: utf-8 -*-
"""setup.py: setuptools control."""

from setuptools import setup

version = "2.1.2"
with open("README.md", "r") as f:
    long_descr = f.read()

setup(
    name="snapmap-archiver",
    packages=["snapmap_archiver"],
    entry_points={"console_scripts": ["snapmap-archiver = snapmap_archiver:main"]},
    version=version,
    description="Download all Snap Map content from a specific location.",
    long_description=long_descr,
    author="Miles Greenwark",
    author_email="millez.dev@gmail.com",
    url="https://github.com/king-millez/snapmap-archiver",
    python_requires=">=3.10",
    install_requires=[
        "certifi",
        "chardet",
        "idna",
        "requests",
        "urllib3",
    ],
)
