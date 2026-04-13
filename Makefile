lint:
	uv run --active ruff check imsize/[!a_]*.py

download:
ifeq (,$(wildcard ./test/images/*.CR2))
	cd ./test/images && http --download http://www.rawsamples.ch/raws/canon/RAW_CANON_1000D.CR2
endif

test: download lint
	uv run pytest -v

install:
	rm -rf dist || true
	uv build
	uv pip uninstall --quiet imsize
	uv pip install dist/*.whl || true
	unzip -v dist/*.whl
	@python3 -c 'import imsize; print(f"Installed imsize version {imsize.__version__}.")'

release:
	uv pip install twine
	make install
	twine upload dist/*

.PHONY: lint download test install release
