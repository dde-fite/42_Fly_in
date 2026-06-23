# CLAUDE.md

## General

* Follow existing patterns in the codebase.
* Prefer readability over cleverness.
* Keep code simple, explicit, and easy to maintain.
* Avoid unnecessary abstractions and premature optimization.
* Prefer small files with a single responsibility.
* Split large or complex files into smaller modules.

## Backend (Python)

* Use FastAPI conventions and existing project patterns.
* Add type hints always.
* Check flake8 and mypy.
* Write a test for every non-trivial function.
* Use Pytest for all tests.

## Frontend (React + Vite)

* Follow existing component and folder structure.
* Keep components small and focused.
* Prefer clear state management over complex abstractions.

## Testing

* Every moderately complex function must have tests.
* Cover normal cases, edge cases, and failure cases when relevant.
* Keep tests simple, readable, and deterministic.

## Code Quality

* Prioritize clarity over brevity.
* Use descriptive names.
* Leave the codebase easier to understand than you found it.
