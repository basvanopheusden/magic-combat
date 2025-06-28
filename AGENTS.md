To run tests, use pytest
When adding new tests, ensure they are placed in the appropriate test module and follow the naming conventions outlined in the style guide.
When adding tests that require understanding the rules of Magic: The Gathering, include a docstring quoting a relevant passage from the Magic Comprehensive Rules that the test exercises. 

Ensure that all code passes PEP 8 style checks, and that it follows the style guide in style_guide.md.
In particular, use the following linters and formatters:
- Use `black` to automatically format code.
- Use `isort --profile black` to sort imports.
- Use `flake8` together with `flake8-import-order` and `pyflakes` to check
  for style issues.
- Run `pycodestyle` for additional PEP 8 checks.
- Run `autoflake` to remove unused imports and variables.
- Run `pylint` for more comprehensive linting.
- Run `mypy` for static type checking.
- Run `pyright` for additional type checking.
- These tools are executed in the test suite to enforce the style guide.
