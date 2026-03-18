# Running a Study

## Study Types

| Type | Description |
|------|-------------|
| **Stationary** | Solve the time-independent (steady-state) problem |
| **Time Dependent** | Solve the transient problem using Backward Euler time stepping |

The available study types depend on the physics modules selected. Some modules (e.g. Electrostatics) support only Stationary; Heat Transfer supports both.

---

## Study Panel

The Study panel contains:

- **Study Type** selector
- **Time settings** (for Time Dependent): `t_start`, `t_end`, `dt`
- **Parametric Sweep** (optional): sweep a named parameter over a range
- **Compute** button

---

## Computing

Click **Compute** to begin the simulation. A progress bar and status message track the stages:

1. **Parameter evaluation** — resolves symbolic expressions
2. **Geometry build** — sends primitives and booleans to gmsh
3. **Mesh generation** — runs gmsh meshing algorithm
4. **FEM assembly** — builds stiffness/mass matrices via scikit-fem
5. **Solve** — direct sparse solver (Backward Euler steps for transient)
6. **Post-processing** — computes derived quantities (E, q, …)

The solver runs in a background thread so the GUI remains responsive. Click **Abort** to cancel.

---

## Aborting a Solve

Click the **Abort** button in the progress dialog. The solver thread checks the abort flag at each time step and after matrix assembly, and raises `InterruptedError` to stop cleanly.

---

## Parametric Sweep

Enable the parametric sweep to vary a single named parameter over a range:

| Setting | Description |
|---------|-------------|
| **Parameter** | Name of the parameter to sweep |
| **Start** | First value |
| **End** | Last value |
| **Step** | Increment |

After the sweep, use the sweep index slider in the Results panel to browse solutions.
