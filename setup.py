import os
import setuptools
import sys

PACKAGE_NAME = "nix_derivation_tools"

setuptools.setup(
    name=PACKAGE_NAME,
    version="0.0.0",
    package_dir={"": "src"},
    packages=setuptools.find_packages("src"),
    provides=setuptools.find_packages("src"),
    install_requires=open("requirements.txt").readlines(),
    data_files = [],
    entry_points={"console_scripts": [
        "derivtool=nix_derivation_tools.cli:main"
    ]}
)
