# Physics & Boundary Conditions

Elementa uses a plugin architecture for physics modules. Each module declares the governing equation it solves, the material properties it needs, and the boundary condition types it supports.

---

## Electrostatics

**Governing equation (Poisson):**

$$-\nabla \cdot (\varepsilon_0 \varepsilon_r \nabla \varphi) = \rho$$

where $\varepsilon_0 = 8.854 \times 10^{-12}$ F/m.

**Material property required:** Relative Permittivity $\varepsilon_r$ (dimensionless)

**Supported study types:** Stationary

### Boundary Conditions

| Type | Description | Properties |
|------|-------------|------------|
| **Electric Potential** | Dirichlet — fixes the voltage | `value` (V) |
| **Ground** | Shorthand for Electric Potential = 0 | — |
| **Surface Charge Density** | Neumann — prescribes normal flux | `value` (C/m²) |
| **Zero Charge** | Homogeneous Neumann (default on unset boundaries) | — |

### Domain Features

| Feature | Description | Properties |
|---------|-------------|------------|
| **Charge Density** | Volumetric free charge $\rho$ | `value` (C/m³) |

### Result Fields

| Key | Label | Type | Unit |
|-----|-------|------|------|
| `phi` | V (Potential) | Scalar | V |
| `E` | E (Electric Field) | Vector | V/m |

---

## Heat Transfer

**Governing equation:**

$$\rho C_p \frac{\partial T}{\partial t} - \nabla \cdot (k \nabla T) = Q$$

For stationary analysis the time derivative is dropped.

**Material properties required:**

| Property | Symbol | Unit |
|----------|--------|------|
| Thermal Conductivity | $k$ | W/(m·K) |
| Density | $\rho$ | kg/m³ |
| Heat Capacity | $C_p$ | J/(kg·K) |

**Supported study types:** Stationary, Time Dependent

### Boundary Conditions

| Type | Description | Properties |
|------|-------------|------------|
| **Temperature** | Dirichlet — fixed temperature | `value` (K) |
| **Heat Flux** | Neumann — prescribed normal heat flux | `value` (W/m²) |
| **Convection** | Robin — convective heat transfer | `h` (W/m²K), `T_ext` (K) |
| **Thermal Insulation** | Homogeneous Neumann (zero flux) | — |

The convective boundary condition applies:

$$-k \nabla T \cdot \hat{n} = h (T - T_\text{ext})$$

### Domain Features

| Feature | Description | Properties |
|---------|-------------|------------|
| **Heat Source** | Volumetric heat generation $Q$ | `value` (W/m³) |

### Result Fields

| Key | Label | Type | Unit |
|-----|-------|------|------|
| `T` | T (Temperature) | Scalar | K |
| `q` | q (Heat Flux) | Vector | W/m² |

---

## Time Dependent Studies

When **Time Dependent** is selected in the Study panel, configure:

| Setting | Description | Default |
|---------|-------------|---------|
| `t_start` | Start time (s) | 0.0 |
| `t_end` | End time (s) | 1.0 |
| `dt` | Time step (s) | 0.1 |

Elementa uses **Backward Euler** time integration. After solving, a time slider in the Results panel lets you step through the computed solutions.

---

## Material Properties and Physics

Enable **Use Material Properties** in the Physics settings panel to apply domain-specific material values from the Materials panel. When disabled, the uniform values entered in the Physics config apply everywhere.

### Built-in Material Library

| Material | $\varepsilon_r$ | $\sigma$ (S/m) | $k$ (W/mK) | $\rho$ (kg/m³) | $C_p$ (J/kgK) |
|----------|----------------|----------------|------------|----------------|----------------|
| Air | 1.0 | 0 | 0.025 | 1.225 | 1006 |
| Vacuum | 1.0 | 0 | 0 | 0 | 0 |
| Water | 80.1 | 5.5×10⁻⁶ | 0.598 | 997 | 4184 |
| Silicon | 11.68 | 1.56×10⁻³ | 148 | 2330 | 710 |
| Copper | 1.0 | 5.96×10⁷ | 400 | 8960 | 385 |
