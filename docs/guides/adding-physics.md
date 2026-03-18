# Adding a Physics Module

Elementa's physics system is designed for easy extension. This walkthrough adds a minimal **Poisson** (scalar diffusion) module as an example.

---

## 1. Create the Module File

Create `elementa/physics/poisson.py`:

```python
import numpy as np
from skfem import InteriorBasis, ElementTriP1, ElementTetP1, BilinearForm, LinearForm, asm
from skfem import solve, condense
from skfem.helpers import dot, grad

from .base import PhysicsState
from .registry import (
    PhysicsDescriptor, FeatureType, ResultField, DomainProperty,
    BoundaryConditionType, register_physics,
)


class PoissonDescriptor(PhysicsDescriptor):
    """Solves −∇·(D∇u) = f with Dirichlet/Neumann BCs."""

    name = "Poisson"
    abbreviation = "poi"
    icon = "physics.png"          # reuse existing icon or add your own
    bc_label = "Value"
    supported_study_types = ["Stationary"]

    domain_properties = [
        DomainProperty("diffusivity", "Diffusivity (D)", "1.0", "m²/s"),
    ]

    bc_types = [
        BoundaryConditionType(
            "dirichlet", "Dirichlet",
            default_props={"value": "0.0"},
            prop_labels={"value": "Value"},
        ),
        BoundaryConditionType(
            "neumann", "Neumann",
            default_props={"value": "0.0"},
            prop_labels={"value": "Normal Flux"},
        ),
    ]

    feature_types = [
        FeatureType(
            kind="source",
            label="Source Term",
            icon="physics.png",
            default_props={"value": "0.0"},
            default_domains=["All"],
            prop_labels={"value": "Source (f)"},
        ),
    ]

    result_fields = [
        ResultField(key="u", label="u (Solution)", field_type="scalar", unit=""),
    ]

    default_config = {
        "use_material": False,
        "diffusivity": "1.0",
    }

    @classmethod
    def assemble_and_solve(cls, state: PhysicsState) -> PhysicsState:
        mesh = state.mesh
        if mesh is None:
            raise RuntimeError("Mesh is required.")

        Element = ElementTriP1 if mesh.dim() == 2 else ElementTetP1
        basis = InteriorBasis(mesh, Element())

        # Diffusivity
        D_el = np.ones(mesh.nelements)
        try:
            D_el[:] = float(state.physics_config.get("diffusivity", "1.0"))
        except ValueError:
            pass
        D_qp = D_el[:, None]

        @BilinearForm
        def stiffness(u, v, _):
            return D_qp * dot(grad(u), grad(v))

        # Source term
        f_el = np.zeros(mesh.nelements)
        for feat in state.physics_features:
            if feat.kind == "source":
                val = float(feat.properties.get("value", 0.0))
                if "All" in feat.domains:
                    f_el[:] += val
        f_qp = f_el[:, None]

        @LinearForm
        def source(v, _w):
            return f_qp * v

        K = asm(stiffness, basis)
        f = asm(source, basis)

        # Boundary conditions
        from skfem import FacetBasis
        D_dofs, x_known = [], np.zeros(basis.N)

        for bc in state.bc_items:
            for bname in bc.boundaries:
                if bname not in mesh.boundaries:
                    continue
                if bc.kind == "dirichlet":
                    val = float(bc.properties.get("value", 0.0))
                    dofs = basis.get_dofs(mesh.boundaries[bname]).all()
                    D_dofs.append(dofs)
                    x_known[dofs] = val
                elif bc.kind == "neumann":
                    val = float(bc.properties.get("value", 0.0))
                    fb = FacetBasis(mesh, Element(), facets=mesh.boundaries[bname])
                    @LinearForm
                    def flux(v, _w, val=val): return val * v
                    f += asm(flux, fb)

        D = np.unique(np.concatenate(D_dofs)) if D_dofs else np.array([0])
        u = solve(*condense(K, f, D=D, x=x_known))

        state.basis = basis
        state.results = {"u": u}
        if state.progress_callback:
            state.progress_callback(100)
        return state


# Auto-register
register_physics(PoissonDescriptor)
```

---

## 2. Register the Import

Add one line to `elementa/physics/__init__.py`:

```python
from .poisson import PoissonDescriptor
```

And add `"PoissonDescriptor"` to `__all__`.

---

## 3. Add an Icon (Optional)

Place a 350×350 PNG in `elementa/assets/`. Reference its filename in the `icon` class attribute.

---

## 4. Checklist

- [ ] `name` is unique in the registry
- [ ] `assemble_and_solve` populates `state.basis` and `state.results`
- [ ] `state.progress_callback` is called at key stages (0, 50, 100)
- [ ] `state.abort_check` is consulted in long loops
- [ ] All result keys in `results` match `result_fields[*].key`
- [ ] Import added to `physics/__init__.py`
