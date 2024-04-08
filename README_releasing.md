# Releases to PIP

This documentation for releasing new versions to PIP is relevant only for repository maintainers. :)

- merge dev to master
- run hyperglot-validate
- run pytest tests (with all tox environments)
- manually sanity-check cli font check works
- bump version number
- push dev to github, test install from commit in new environment: pip install git+https://github.com/rosettatype/hyperglot.git@dev
- tag and push master
- make new dist package:

```
python -m build
```

- test-upload to testpypi:

```
python -m twine upload --repository testpypi dist/hyperglot-x.x.x*
```

- test install in new virtual env from pypi:

```
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple --no-deps hyperglot
```

- if all looks good (no deps so it'll most likely not run, but should install ok) then go ahead with real release:

```
python -m twine upload dist/hyperglot-x.x.x*
```

(This assumes a .pypirc with token configs for test.pypi and the main pypi)

- Make a new [Github release](https://github.com/rosettatype/hyperglot/releases/new) — use changelog since last version as description basis 