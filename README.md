# imsize

[![Build Status](https://travis-ci.org/toaarnio/imsize.svg?branch=master)](https://travis-ci.org/toaarnio/imsize)

Lightning-fast extraction of image dimensions & bit depth. Tested on Python 3.6+.

Supports PGM / PPM / PNM / PNG / JPG / TIFF.

**Installing on Linux:**
```
pip install imsize
```

**Building & installing from source:**
```
git clean -dfx
python setup.py bdist_wheel
pip uninstall imsize
pip install --user dist/*.whl
```

**Releasing to PyPI:**
```
pip install --user --upgrade setuptools wheel twine
python setup.py sdist bdist_wheel
twine upload dist/*
```
