# Elementa FEM

**Open-source Finite Element Method (FEM) simulation workbench for Python**

---

Elementa is a desktop simulation environment that provides a complete FEM workflow in a single Python application: parametric CAD modelling, automatic mesh generation, physics-based solvers, and interactive post-processing — all without commercial licences or external solver dependencies.

<div class="grid cards" markdown>

-   :material-cube-outline: **Parametric Geometry**

    Build 2-D and 3-D models from primitives with full boolean operations and symbolic parameters.

    [Geometry guide →](guides/geometry.md)

-   :material-grid: **Automatic Meshing**

    Generate triangular and tetrahedral meshes automatically via the gmsh engine.

    [Meshing guide →](guides/meshing.md)

-   :material-lightning-bolt: **Physics Solvers**

    Electrostatics and Heat Transfer (stationary & transient) built in; extensible plugin architecture.

    [Physics guide →](guides/physics.md)

-   :material-chart-line: **Post-Processing**

    Surface plots, arrow/vector plots, and point/line probes with interactive controls.

    [Post-processing guide →](guides/postprocessing.md)

</div>

---

## Quickstart

```bash
pip install elementa
elementa
```

---

## Physics Modules

| Module | Equation | Study Types |
|--------|----------|-------------|
| **Electrostatics** | $-\nabla \cdot (\varepsilon_0 \varepsilon_r \nabla \varphi) = \rho$ | Stationary |
| **Heat Transfer** | $\rho C_p \partial_t T - \nabla \cdot (k \nabla T) = Q$ | Stationary, Time Dependent |

---

## Installation

See the [Installation guide](guides/installation.md) for full platform-specific instructions.

---

## Contributing

Elementa is open source under the [GPL v3 licence](license.md).  
Contributions are welcome — see the [Contributing guide](contributing.md) to get started.
