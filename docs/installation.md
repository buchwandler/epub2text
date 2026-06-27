# Installation

## Requirements

- Python >= 3.10
- click >= 8.0.0
- rich >= 13.0.0
- ebooklib >= 0.18
- beautifulsoup4 >= 4.12.0
- defusedxml >= 0.7.1

## Optional Dependencies

- **lxml**: For better HTML parsing performance
- **phrasplit**: For sentence-level and clause-level formatting (depends on spaCy)

## Basic Installation

Install epub2text from PyPI:

```bash
pip install epub2text
```

## Installation with Extras

For better HTML parsing performance:

```bash
pip install epub2text[lxml]
```

After installing, download a spaCy language model:

```bash
python -m spacy download en_core_web_sm
```

For all optional features:

```bash
pip install epub2text[lxml,sentences]
```

## Development Installation

Clone the repository and install in development mode:

```bash
git clone https://github.com/buchwandler/epub2text
cd epub2text
pip install -e ".[dev]"
```

This installs all development dependencies including:

- pytest for testing
- ruff for linting
- pre-commit for code quality hooks

## Running Tests

Run the test suite:

```bash
pytest tests/
```

Run with coverage:

```bash
pytest tests/ --cov=epub2text --cov-report=html
```

## Pre-commit Hooks

Install pre-commit hooks for code quality:

```bash
pre-commit install
```

Run hooks manually:

```bash
pre-commit run --all-files
```
