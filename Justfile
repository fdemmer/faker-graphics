[private]
default:
    @just --list --unsorted

gha-update:
    uvx gha-update

test:
    uvx --with nox[pbs] nox

test-rust:
    #!/usr/bin/env bash
    set -euo pipefail
    uv venv --python 3.13 --allow-existing .venv
    source .venv/bin/activate
    uvx maturin develop --manifest-path rust/Cargo.toml --features python
    python -m unittest tests/test_rust_module.py -v

build-rust:
    uvx maturin build --manifest-path rust/Cargo.toml --features python --interpreter python3.13 --manylinux off

clean:
    rm -rf build dist
    rm -rf *.egg-info

build:
    uvx --from build pyproject-build

publish-test: clean build
    uvx twine upload -r testpypi dist/*

publish: clean build
    #!/usr/bin/env bash
    status=$(git status --porcelain)
    if [ -z "$status" ]; then
        uvx twine upload -r faker-graphics dist/*
    else
        echo "Aborting upload: working directory is dirty" >&2
        exit 1
    fi
