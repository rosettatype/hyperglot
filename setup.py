from setuptools import setup

setup(name="fontlang",
      version="0.1.4",
      description="Detect language support for font binaries",
      author="Johannes Neumeier - Rosetta",
      author_email="johannes@rosettatype.com",
      license="All rights reserved",
      packages=[
          "lib.fontlang"
      ],
      entry_points={
          "console_scripts": [
              "fontlang = lib.fontlang.main:cli",
              "fontlang-validate = lib.fontlang.validate:validate",
              "fontlang-save = lib.fontlang.main:save_sorted"
          ]
      },
      include_package_data=True,
      install_requires=[
          "click>=7.0",
          "fonttools>=4.0.2",
          "pyaml>=19.4.1"
      ],
      data_files=[("database", ["data/rosetta.yaml"])]
      )
