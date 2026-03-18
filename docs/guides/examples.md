# Examples

Ready-to-follow tutorials demonstrating common Elementa workflows.

---

## Example 1 — Parallel Plate Capacitor (2-D Electrostatics)

**Goal:** Compute the electric potential and field between two parallel conducting plates separated by vacuum.

### Setup

| Parameter | Value |
|-----------|-------|
| Plate width | 0.1 m |
| Plate height | 0.01 m |
| Gap | 0.02 m |
| Voltage | ±50 V |

### Steps

1. New project → 2D, Electrostatics, Stationary.
2. **Parameters:** `W=0.1`, `H=0.01`, `gap=0.02`.
3. **Geometry:**
   - Rectangle `domain`: `dx=0.15`, `dy=0.1`, `cx=0`, `cy=0`
   - Rectangle `plate_top`: `dx=W`, `dy=H`, `cx=0`, `cy=gap/2+H/2`
   - Rectangle `plate_bot`: `dx=W`, `dy=H`, `cx=0`, `cy=-gap/2-H/2`
4. **Mesh:** element size `0.004`.
5. **Boundary Conditions:**
   - `plate_top` boundaries → Electric Potential, `value = 50`
   - `plate_bot` boundaries → Electric Potential, `value = -50`
   - outer `domain` boundaries → Ground
6. **Solve.**
7. **Results:** surface plot of φ, arrow plot of **E**.

### Expected Result

The potential varies linearly between the plates. The electric field magnitude in the gap is approximately:

$$|E| \approx \frac{\Delta V}{d} = \frac{100 \text{ V}}{0.02 \text{ m}} = 5000 \text{ V/m}$$

---

## Example 2 — Heat Conduction Through a Wall (2-D Heat Transfer)

**Goal:** Compute the steady-state temperature distribution through a composite wall with fixed temperatures on each face.

### Setup

| Parameter | Value |
|-----------|-------|
| Wall thickness | 0.3 m |
| Wall height | 1.0 m |
| Inner temperature | 293 K (20 °C) |
| Outer temperature | 253 K (−20 °C) |
| Thermal conductivity | 0.04 W/(m·K) (insulation) |

### Steps

1. New project → 2D, Heat Transfer, Stationary.
2. **Parameters:** `L=0.3`, `H=1.0`, `k=0.04`.
3. **Geometry:** Rectangle `wall`: `dx=L`, `dy=H`, `cx=0`, `cy=0`.
4. **Physics config:** set Thermal Conductivity to `k`.
5. **Mesh:** element size `0.02`.
6. **Boundary Conditions:**
   - Left edge (`wall_edge_3`) → Temperature, `value = 293.15`
   - Right edge (`wall_edge_1`) → Temperature, `value = 253.15`
   - Top/bottom edges → Thermal Insulation
7. **Solve.**
8. **Results:** surface plot of T, arrow plot of heat flux **q**.

### Expected Result

A linear temperature gradient from 293 K to 253 K across the wall. Heat flux:

$$q = k \frac{\Delta T}{L} = 0.04 \times \frac{40}{0.3} \approx 5.3 \text{ W/m}^2$$

---

## Example 3 — Transient Heating of a Block (2-D Heat Transfer, Time Dependent)

**Goal:** Simulate heating of a solid block from an initial temperature of 20 °C when one face is held at 100 °C.

### Steps

1. New project → 2D, Heat Transfer, **Time Dependent**.
2. **Parameters:** `L=0.1`, `rho=2700`, `cp=900`, `k=200` (aluminium).
3. **Geometry:** Square block `block`: `dx=L`, `dy=L`.
4. **Physics config:**
   - Thermal Conductivity: `k`
   - Density: `rho`
   - Heat Capacity: `cp`
5. **Study → Time Dependent:** `t_start=0`, `t_end=100`, `dt=5`.
6. **Boundary Conditions:**
   - Left face → Temperature, `value = 373.15` (100 °C)
   - Others → Thermal Insulation
7. **Solve.**
8. **Results:** Use the time slider in the plot panel to animate the temperature field evolution.

---

## Example 4 — Sphere with Surface Charge (3-D Electrostatics)

**Goal:** Verify the analytical electric potential outside a uniformly charged sphere.

### Steps

1. New project → **3D**, Electrostatics, Stationary.
2. **Parameters:** `R=0.05`, `R_ext=0.2`.
3. **Geometry:**
   - Sphere `inner`: `r=R`
   - Sphere `outer`: `r=R_ext`
   - Boolean Difference `domain` = `outer` − `inner`
4. **Boundary Conditions:**
   - Inner sphere surface → Surface Charge Density, `value = 1e-6`
   - Outer sphere surface → Ground
5. **Mesh:** element size `0.02`.
6. **Solve.**
7. **Results:** surface plot of φ, verify against Coulomb's law.
