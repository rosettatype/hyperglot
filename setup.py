from setuptools import setup
from lib.fontlang import __version__

setup(name="fontlang",
      version=__version__,
      python_requires='>3.6.0',
      description="Detect language support for font binaries",
      author="Johannes Neumeier - Rosetta",
      author_email="johannes@rosettatype.com",
      license="All rights reserved",
      packages=[
          "fontlang"
      ],
      package_dir={"": "lib"},
      package_data={"fontlang": ["rosetta.yaml"]},
      include_package_data=True,
      entry_points={
          "console_scripts": [
              "fontlang = fontlang.main:cli",
              "fontlang-validate = fontlang.validate:validate",
              "fontlang-save = fontlang.main:save_sorted",
              "fontlang-export = lib.fontlang.main:export"
          ]
      },
      install_requires=[
          "click>=7.0",
          "fonttools>=4.0.2",
          "pyyaml>=5.3",
          # For validation script only:
          "unicodedata2>=13.0.0"
      ],
      )
