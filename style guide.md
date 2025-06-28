# Coding Style Guide

This project follows standard Python best practices with a few additional
requirements to ensure consistency across the code base.

## General Formatting
- Indent using **4 spaces**, never tabs.
- Limit lines to **79 characters**.
- Use meaningful variable and function names.
- Include module, class and function docstrings using the **Google** style.

## Naming Conventions
- Functions and variables use **snake_case**.
- Classes use **PascalCase**.
- Module-level constants use **UPPER_SNAKE_CASE**.

## Function Length
- Keep functions under **50 lines** when practical.
- Break complex operations into helper functions.

## Imports
- Use `isort --profile black` to sort imports in the following sections:
  1. Standard library
  2. Third-party packages
  3. Local packages
- Avoid unused imports and duplicate imports.

## Linting and Formatting Tools
- Run `black` to automatically format code.
- Run `flake8` and `pylint` for linting.
- Run `mypy` for static type checking.
- These tools are executed in the test suite to enforce the style guide.

## Typing
- Annotate all public functions and methods with type hints.
- Prefer precise types over ``Any`` when possible.

## Anti-Patterns to Avoid
- ``import *`` from modules.
- Large blocks of repeated code.
- Global mutable state.
- Deeply nested loops or conditionals.
- Catching broad ``Exception`` classes.

## General Principles
- Favor composition over inheritance.
- Prefer pure functions when practical.
- Use early returns to reduce nesting.

## Other Notes
- Avoid relative imports that escape the package.
- Limit parameter lists to keep APIs simple.
- Document non-obvious behavior with comments and docstrings.

