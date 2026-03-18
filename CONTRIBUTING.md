# Contributing to Elementa

Thank you for your interest in contributing! This document explains how to set up a development environment, run tests, and submit changes.

---

## Development Setup

```bash
# 1. Fork and clone
git clone https://github.com/<your-username>/elementa.git
cd elementa

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. Install in editable mode with dev extras
pip install -e ".[dev]"
```

---

## Code Style

Elementa uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting.

```bash
ruff check .
ruff format .
```

Please run these before submitting a pull request.

---

## Running Tests

```bash
pytest
```

---

## Adding a New Physics Module

1. Create `elementa/physics/<name>.py`.
2. Import and subclass `PhysicsDescriptor` from `elementa.physics.registry`.
3. Define all required class attributes (`name`, `abbreviation`, `icon`, `bc_types`, `result_fields`, `default_config`, …).
4. Implement `assemble_and_solve(cls, state: PhysicsState) -> PhysicsState`.
5. Call `register_physics(YourDescriptor)` at the bottom of the file.
6. Add the import to `elementa/physics/__init__.py`.
7. Add an icon file (PNG, 64×64) to `elementa/assets/`.

See `docs/guides/adding-physics.md` for a detailed walkthrough.

---

## Adding a New Geometry Primitive

1. Subclass `ShapeDef` in `elementa/core/geometry_registry.py`.
2. Set `kind`, `dim`, and `params`.
3. Implement `build(cls, cad, name, params) -> int` using the `ElementaCAD` API.
4. Add the class to `SHAPE_REGISTRY`.
5. Add a corresponding `add_<shape>` method to `ElementaCAD` in `elementa/cad/cad.py` if required.

---

## Pull Request Guidelines

- Target the `main` branch.
- Include a clear description of the change and the motivation.
- Add or update tests where appropriate.
- Keep commits focused; squash fixup commits before requesting review.
- Reference related issues with `Fixes #<issue>` in the PR description.

---

## Reporting Bugs

Open an issue at <https://github.com/soheilhajibaba/elementa/issues> with:

- A minimal reproducible example.
- Python version, OS, and package versions (`pip show elementa-fem`).
- Full traceback if applicable.

---

## Code of Conduct

Be respectful and constructive in all interactions. We follow the [Contributor Covenant](https://www.contributor-covenant.org/).
