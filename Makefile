lint:
	ruff check imsize/[^a]*.py

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
	hatch build  # pip install hatch
	uv pip uninstall --quiet imsize
	uv pip install dist/*.whl || true
	unzip -v dist/*.whl
	@python3 -c 'import imsize; print(f"Installed imsize version {imsize.__version__}.")'

qinstall:  # quick & quiet install; wheel only
	@hatch build -t wheel
	@uv pip uninstall --quiet imsize
	@uv pip install --quiet dist/*.whl || true

release:
	uv pip install twine
	make install
	twine upload dist/*

.PHONY: lint download test install release
