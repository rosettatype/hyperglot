from setuptools import setup
from lib.hyperglot import __version__

setup(name="hyperglot",
      version=__version__,
      python_requires='>3.6.0',
      description="Detect language support for font binaries",
      author="Johannes Neumeier - Rosetta",
      author_email="johannes@rosettatype.com",
      license="All rights reserved",
      packages=[
          "hyperglot"
      ],
      package_dir={"": "lib"},
      package_data={"hyperglot": ["hyperglot.yaml"]},
      include_package_data=True,
      entry_points={
          "console_scripts": [
              "hyperglot = hyperglot.main:cli",
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
          "unicodedata2>=13.0.0"
      ],
      )
