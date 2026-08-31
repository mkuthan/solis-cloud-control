# Contributing Guidelines

## Local development

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) tool.
2. Install project dependencies using `uv sync` command.
3. Run the integration locally using `./scripts/run` script and open the UI at <http://localhost:8123>
4. Configure the integration using the Home Assistant UI.

## Testing

Run all checks (lint, format, type, test) -- this is what CI runs:

```bash
mise run check
```

Run only the tests:

```bash
mise run test
```

Run a single test file while iterating (skips the coverage gate, which a partial run cannot meet):

```bash
uv run pytest --cov-fail-under=0 tests/test_init.py
```

## Releasing

To release a new version, create a new tag and push it to the repository:

```bash
git tag v1.0.1
git push origin v1.0.1
```

To release a new alpha version, create a new tag with the `alpha`, `beta` or `rc` suffix and push it to the repository:

```bash
git tag v1.0.1-alpha.1
git push origin v1.0.1-alpha.1
```

## Documentation

<https://deepwiki.com/mkuthan/solis-cloud-control/>
