# Changelog

All notable changes to Elementa are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).  
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [1.0.0] — 2026

### Added
- Initial public release.
- Parametric 2-D and 3-D CAD geometry builder (rectangle, disk, polygon, box, sphere, cylinder).
- Boolean operations: union, difference, intersection.
- Automatic triangular (2-D) and tetrahedral (3-D) meshing via gmsh.
- Physics plugin registry with two built-in solvers:
  - **Electrostatics** — Poisson equation for electric potential.
  - **Heat Transfer** — stationary and transient heat equation with backward-Euler time stepping.
- Supported boundary conditions per physics module.
- Parametric expression evaluator with dependency resolution.
- Built-in material library (Air, Vacuum, Water, Silicon, Copper).
- Interactive 2-D/3-D graphics canvas for geometry and mesh visualisation.
- Post-processing: surface plots, arrow/vector plots, point and line probes.
- Portable `.elem` project file format (ZIP archive: JSON state + `.msh` mesh + `.npz` results).
- PyQt6-based GUI with ribbon toolbar, dockable panels, and welcome wizard.
- `elementa` console script entry point.
- GPL v3 licence.
