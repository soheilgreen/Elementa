# Interface Overview

Elementa's main window is divided into five functional areas.

```
┌─────────────────────────────────────────────────────────┐
│                    Ribbon Toolbar                       │
├──────────────┬──────────────────────────┬──────────────┤
│              │                          │              │
│   Model      │    Graphics Canvas       │   Property   │
│   Builder    │                          │   Panel      │
│   (Tree)     │                          │              │
│              │                          │              │
├──────────────┴──────────────────────────┴──────────────┤
│                    Log Console                          │
└─────────────────────────────────────────────────────────┘
```

---

## Ribbon Toolbar

The ribbon provides tab-based access to all major workflows:

| Tab | Contents |
|-----|----------|
| **File** | New, Open, Save, Save As |
| **Geometry** | Add primitives, boolean operations |
| **Mesh** | Generate, mesh settings |
| **Physics** | Physics panel, boundary conditions |
| **Study** | Study type, compute |
| **Results** | Add plots, probes |
| **Help** | Documentation, about |

---

## Model Builder (Tree)

The left panel is a hierarchical tree of the model:

```
Component1
├── Definitions
│   └── Parameters
├── Geometry
│   ├── Rectangle 1
│   └── Disk 1
├── Materials
│   └── Material 1
├── Physics
│   └── Electrostatics
│       ├── Electric Potential 1
│       └── Ground 1
├── Mesh
└── Study
    └── Stationary
```

Click any node to load its settings in the **Property Panel**.

---

## Graphics Canvas

The central canvas displays:

- **Geometry view** — wireframe or solid rendering of CAD primitives
- **Mesh view** — coloured triangular / tetrahedral mesh with labelled boundaries
- **Results view** — colour-mapped scalar and vector fields

**Navigation:**
- **Left drag** — pan
- **Scroll wheel** — zoom
- **Click boundary** — select for boundary condition assignment

---

## Property Panel

The right panel shows context-sensitive settings for the selected tree node: parameter values, geometry dimensions, material properties, boundary condition values, and study settings.

---

## Log Console

The bottom panel streams solver progress, warnings, and error messages. Errors are highlighted in red.
