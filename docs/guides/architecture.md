# Architecture

This page describes Elementa's internal design for contributors and developers who want to extend the application.

---

## Package Layout

```
elementa/
├── __init__.py          # version, author, license
├── __main__.py          # CLI entry point: `elementa` / `python -m elementa`
├── assets/              # PNG icons and ICO files
├── cad/
│   └── cad.py           # ElementaCAD: thin wrapper around gmsh OCC kernel
├── core/
│   ├── cad_builder.py   # CADBuilder: drives ElementaCAD from ProjectState
│   ├── evaluator.py     # ParameterEvaluator: resolves symbolic parameters
│   ├── exceptions.py    # Custom exception hierarchy
│   ├── geometry_registry.py  # ShapeDef registry mapping kind→build method
│   ├── logger.py        # Logging factory (Python logging)
│   ├── material_library.py   # Static material property database
│   └── project_state.py # ProjectState (QObject): central data + serialisation
├── physics/
│   ├── base.py          # PhysicsState dataclass
│   ├── registry.py      # PhysicsDescriptor + PHYSICS_REGISTRY + helpers
│   ├── electrostatics.py
│   └── heat_transfer.py
└── ui/
    ├── expr.py           # safe_eval: sandboxed expression evaluator
    ├── graphics_canvas.py
    ├── icon_manager.py
    ├── main_window.py    # ElementaMainWindow + SolverThread
    ├── model_builder.py
    ├── new_project_wizard.py
    ├── plot_window.py
    ├── project_manager.py
    ├── property_panel.py
    ├── ribbon_toolbar.py
    ├── welcome_window.py
    └── panels/
        ├── mesh_panel.py
        ├── parameters_panel.py
        ├── physics_panel.py
        └── study_panel.py
```

---

## Data Flow

```
User Action
    │
    ▼
UI Panel / Ribbon
    │  updates
    ▼
ProjectState (QObject)
    │  emits signals (state_changed, geometry_changed, …)
    ▼
Main Window / Canvas
    │  reacts to signals
    │
    ├── CADBuilder.build_model(project)
    │       │  ParameterEvaluator.resolve_parameters()
    │       │  SHAPE_REGISTRY[kind].build(cad, name, params)
    │       └─► ElementaCAD (gmsh API)
    │
    └── SolverThread (QThread)
            │  PhysicsDescriptor.assemble_and_solve(PhysicsState)
            │  scikit-fem assembly + direct solve
            └─► ProjectState.set_results(basis, results)
                    │  emits results_changed
                    ▼
                Plot Window / Probes
```

---

## ProjectState

`ProjectState` is the single source of truth for all model data. It is a `QObject` and emits Qt signals when data changes, allowing all UI panels to stay in sync without direct coupling.

Key signals:

| Signal | Emitted when |
|--------|-------------|
| `state_changed` | Any general model update |
| `geometry_changed` | Geometry items or boolean ops modified |
| `mesh_changed` | Mesh generated or loaded |
| `results_changed` | Solver finished or results loaded |
| `selection_changed` | User selects boundaries/domains on canvas |

---

## Physics Plugin System

All physics modules register themselves into `PHYSICS_REGISTRY` (a dict mapping name → descriptor class). The main window queries the registry to populate the physics selector, build the physics panel, and dispatch to the correct `assemble_and_solve` method.

```
PHYSICS_REGISTRY = {
    "Electrostatics": ElectrostaticsDescriptor,
    "Heat Transfer": HeatTransferDescriptor,
    ...
}
```

Adding a new physics module requires zero changes to existing code — only an import in `physics/__init__.py`.

---

## Solver Thread

The solver runs in `SolverThread (QThread)` to keep the GUI responsive. It emits:

- `progress(int)` — 0–100 for the progress bar
- `status(str)` — human-readable stage description
- `finished_solve(PhysicsState)` — on success
- `error(str)` — on failure

The main window connects these signals and updates `ProjectState` on the main thread.

---

## Safe Expression Evaluator

`elementa.ui.expr.safe_eval` evaluates mathematical expressions from user input in a sandboxed environment. It uses Python's `ast` module to white-list only:

- Numeric constants
- Arithmetic operators
- Unary operators
- `ast.Name` nodes that are math functions or known parameter names
- Calls to `math` module functions

This prevents arbitrary code execution while supporting the full range of scientific expressions users need.
