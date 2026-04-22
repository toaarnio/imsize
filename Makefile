deps:
	uv sync --extra dev

lint:
	uv run --active ruff check imsize/[!a_]*.py

download:
ifeq (,$(wildcard ./test/images/*.CR2))
	cd ./test/images && http --download http://www.rawsamples.ch/raws/canon/RAW_CANON_1000D.CR2
endif

test: download lint
	uv run --active pytest -sv

install:
	rm -rf dist || true
	uv build
	uv pip uninstall --quiet imsize
	uv pip install dist/*.whl || true
	unzip -v dist/*.whl
	@python3 -c 'import imsize; print(f"Installed imsize version {imsize.__version__}.")'

release:
	@echo "Publishing is handled by GitHub Actions with PyPI Trusted Publishing."
	@echo "Create a GitHub Release to trigger the publish workflow."

.PHONY: deps lint download test install release
