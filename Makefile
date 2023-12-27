lint:
	ruff check --show-source imsize/[^a]*.py

download:
ifeq (,$(wildcard ./test/images/*.DNG))
	cd ./test/images && http --download https://support.theta360.com/intl/download/sample/R0010001.DNG
endif
ifeq (,$(wildcard ./test/images/*.CR2))
	cd ./test/images && http --download http://www.rawsamples.ch/raws/canon/RAW_CANON_1000D.CR2
endif

test: download
	pytest -v
	make lint

install:
	pip3 install --user build
	rm -rf build dist || true
	pip3 uninstall --yes imsize || true
	pyproject-build || true
	pip3 install --user dist/*.whl || true
	rm -rf build imsize.egg-info || true
	@python3 -c 'import imsize; print(f"Installed imsize version {imsize.__version__}.")'

release:
	pip3 install --user twine
	make install
	twine upload dist/*

.PHONY: lint download test install release
