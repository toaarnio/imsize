lint:
	flake8 imsize/imsize.py imsize/consoleapp.py
	pylint imsize/imsize.py imsize/consoleapp.py

test:
	python3 setup.py test

install:
	pip3 uninstall --yes imsize || true
	rm -rf build dist imsize.egg-info || true
	python3 setup.py sdist bdist_wheel
	pip3 install --user dist/*.whl
	@python3 -c 'import imsize; print(f"Installed imsize version {imsize.__version__}.")'

release:
	pip3 install --user setuptools wheel twine
	make install
	twine upload dist/*

.PHONY: lint test install release
