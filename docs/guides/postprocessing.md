# Post-Processing

After a successful solve, Elementa provides several tools to visualise and extract results.

---

## Adding Plots

In the **Results** panel, click **Add Plot** and choose the plot type.

### Surface Plot

Displays a colour-mapped scalar field over the mesh.

| Setting | Description |
|---------|-------------|
| **Field** | Result quantity (e.g. `V (Potential)`, `T (Temperature)`) |
| **Colormap** | Matplotlib colormap name (`viridis`, `hot`, `jet`, …) |
| **Show mesh** | Overlay mesh edges |

### Arrow Plot (Vector Field)

Displays arrows proportional to a vector field at each node.

| Setting | Description |
|---------|-------------|
| **Field** | Vector result (e.g. `E (Electric Field)`, `q (Heat Flux)`) |
| **Scale** | Arrow scale factor |
| **Density** | Subsample factor (1 = all nodes) |

### Contour Plot

Draws iso-lines (2-D) or iso-surfaces (3-D) at specified values of a scalar field.

---

## Probes

Probes extract numerical values from the solution at specific locations.

### Point Probe

Evaluates one or more result fields at a single spatial coordinate.

1. Click **Add Probe → Point Probe**.
2. Enter the coordinates `(x, y)` or `(x, y, z)`.
3. The probe value is shown in the log console and the probe table.

### Line Probe

Plots a result field quantity along a straight line between two points.

1. Click **Add Probe → Line Probe**.
2. Enter start and end coordinates.
3. Set the number of sample points.
4. A Matplotlib window opens with the profile plot.

---

## Time Slider

For **Time Dependent** results, a slider at the bottom of the plot canvas lets you step through all computed time steps. The current time is displayed above the slider.

---

## Exporting Results

- **Save figure** — right-click any Matplotlib plot → *Save As…*
- **Export data** — results arrays (`phi`, `T`, `E`, etc.) are NumPy arrays stored in the `.elem` project archive as `results.npz` and can be loaded with:

```python
import numpy as np
data = np.load("results.npz")
phi = data["phi"]
```
