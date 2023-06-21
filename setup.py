import codecs
import os.path
from setuptools import setup

# Single version reference in lib/hyperglot/__init__.py read via 1.) method via
# https://packaging.python.org/guides/single-sourcing-package-version/#single-sourcing-the-version  # noqa


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()


def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


# Shared README.md for pip long description and repository
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(name="hyperglot",
      version=get_version("lib/hyperglot/__init__.py"),
      python_requires='>3.6.0',
      description="Detect language support for font binaries",
      long_description=long_description,
      long_description_content_type="text/markdown",
      url="https://github.com/rosettatype/hyperglot",
      project_urls={
          "Hyperglot web interface": "https://hyperglot.rosettatype.com",
      },
      author="Johannes Neumeier - Rosetta",
      author_email="johannes@rosettatype.com",
      license="GNU GPLv3",
      classifiers=[
          "Programming Language :: Python :: 3.6",
          "Operating System :: OS Independent",
          "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
          "Intended Audience :: End Users/Desktop",
          "Intended Audience :: Information Technology",
          "Topic :: Text Processing :: Fonts",
          "Topic :: Text Processing :: Linguistic",
      ],
      packages=[
          "hyperglot"
      ],
      package_dir={"": "lib"},
      package_data={"hyperglot": ["data/*.yaml"]},
      include_package_data=True,
      entry_points={
          "console_scripts": [
              "hyperglot = hyperglot.main:cli",
              "hyperglot-data = hyperglot.main:data",
              "hyperglot-validate = hyperglot.validate:validate",
              "hyperglot-save = hyperglot.main:save_sorted",
              "hyperglot-export = lib.hyperglot.main:export"
          ]
      },
      install_requires=[
          "click>=7.0",
          "fonttools>=4.0.2",
          "pyyaml>=5.3",
          # For validation and decompositionq
          "unicodedata2>=13.0.0",
          # For nicer validation output
          "colorlog>=4.7.2"
      ],
      )
