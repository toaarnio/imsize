deps:
	pip3 install -r requirements.txt

lint:
	flake8 imsize/imsize.py imsize/consoleapp.py
	pylint imsize/imsize.py imsize/consoleapp.py

download:
ifeq (,$(wildcard ./test/images/*.DNG))
	cd ./test/images && http --download https://support.theta360.com/intl/download/sample/R0010001.DNG
endif

test: download
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

.PHONY: deps lint download test install release
