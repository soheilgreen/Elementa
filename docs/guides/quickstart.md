# Quickstart

This guide walks through a complete simulation in Elementa from geometry creation to results visualisation.

## 1. Launch Elementa

```bash
elementa
# or
python -m elementa
```

The **Welcome Window** opens. Click **New Project** or select a template.

---

## 2. Configure the Project

In the **New Project Wizard**:

- **Project name** — a descriptive label (e.g. `parallel_plate_capacitor`)
- **Space dimension** — `2D` or `3D`
- **Physics** — select one or more physics modules (e.g. `Electrostatics`)
- **Study type** — `Stationary` or `Time Dependent`

Click **Finish** to open the main window.

---

## 3. Add Parameters

Open the **Definitions → Parameters** panel and define symbolic constants, for example:

| Name | Expression | Description |
|------|-----------|-------------|
| `W` | `0.1` | Plate width (m) |
| `H` | `0.01` | Plate height (m) |
| `gap` | `0.02` | Gap between plates (m) |

Parameters can reference each other and use standard mathematical functions (`sin`, `cos`, `sqrt`, …).

---

## 4. Build the Geometry

1. Open the **Geometry** panel.
2. Click **Add → Rectangle** and enter expressions using your parameters:
   - `dx = W`, `dy = H`, `cx = 0`, `cy = gap/2`  → name it `plate_top`
   - `dx = W`, `dy = H`, `cx = 0`, `cy = -gap/2` → name it `plate_bot`
3. Add a surrounding domain: a large rectangle covering both plates.
4. Use **Boolean → Difference** to cut out the plates from the domain to create a dielectric gap region.

---

## 5. Generate the Mesh

1. Open the **Mesh** panel.
2. Set **Element Size** (e.g. `0.005` m for a fine mesh).
3. Click **Generate Mesh**.

The mesh is visualised on the canvas with coloured boundaries.

---

## 6. Set Materials (Optional)

Open the **Materials** panel. Each domain can be assigned a material from the built-in library (Air, Vacuum, Water, Silicon, Copper) or a custom material with user-specified property values.

Enable **Use Material Properties** in the Physics settings to activate domain-dependent material values.

---

## 7. Define Boundary Conditions

Open the **Physics** panel:

1. Click on a boundary in the canvas (it highlights) or type the boundary name.
2. Click **Add Boundary Condition** and select the type:
   - `Electric Potential` → set `value = 100` V on `plate_top`
   - `Ground` on `plate_bot`

---

## 8. Solve

1. Open the **Study** panel.
2. Click **Compute**.

A progress bar tracks assembly and solving. The log console displays solver status.

---

## 9. Visualise Results

After solving, open the **Results** panel:

- **Surface Plot** — colour-map of electric potential φ or any scalar field.
- **Arrow Plot** — vector arrows showing the electric field **E**.
- **Point Probe** — extract the field value at a specific coordinate.
- **Line Probe** — plot a field quantity along a line.

Use the **Plot** ribbon tab to add multiple plots to the canvas.

---

## 10. Save the Project

Press **Ctrl+S** or **File → Save**. Projects are saved as `.elem` files (a portable ZIP archive containing the model state, mesh, and results).

---

## Next Steps

- [Geometry guide](geometry.md) — boolean operations, 3-D primitives
- [Physics guide](physics.md) — all boundary conditions and domain features
- [Examples](examples.md) — ready-to-run tutorials
