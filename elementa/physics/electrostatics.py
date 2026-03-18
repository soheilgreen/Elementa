from typing import Dict, List

import numpy as np
from skfem import *
from skfem.helpers import dot, grad

from .base import PhysicsState
from .registry import (
    PhysicsDescriptor, FeatureType, ResultField, DomainProperty, BoundaryConditionType,
    register_physics,
)


class ElectrostaticsDescriptor(PhysicsDescriptor):
    """Plugin descriptor for electrostatics physics."""

    name = "Electrostatics"
    abbreviation = "es"
    icon = "electrostatics.png"
    bc_label = "Voltage (V)"
    supported_study_types = ["Stationary"]

    domain_properties = [
        DomainProperty("relative_permittivity", "Relative Permittivity (ε_r)", "1.0"),
    ]

    bc_types = [
        BoundaryConditionType(
            "electric_potential", "Electric Potential",
            default_props={"value": "0.0"},
            prop_labels={"value": "Electric Potential (V) [V]"}
        ),
        BoundaryConditionType("ground", "Ground"),
        BoundaryConditionType(
            "surface_charge_density", "Surface Charge Density",
            default_props={"value": "0.0"},
            prop_labels={"value": "Surface Charge Density (\u03C1_s) [C/m²]"}
        ),
        BoundaryConditionType("zero_charge", "Zero Charge"),
    ]

    feature_types = [
        FeatureType(
            kind="charge_density",
            label="Charge Density",
            icon="electrostatics.png",
            default_props={"value": "0.0"},
            default_domains=["All"],
            prop_labels={"value": "Charge Density (\u03C1) [C/m\u00B3]"},
        ),
    ]

    result_fields = [
        ResultField(key="phi", label="V (Potential)", field_type="scalar", unit="V"),
        ResultField(key="E",   label="E (Electric Field)", field_type="vector", unit="V/m"),
    ]

    default_config = {
        "use_material": False,
        "relative_permittivity": "1.0",
    }

    @classmethod
    def assemble_and_solve(cls, state: PhysicsState) -> PhysicsState:
        if state.mesh is None:
            raise RuntimeError("Mesh is required to solve.")
        mesh = state.mesh
        if mesh.dim() == 2:
            Element = ElementTriP1
        elif mesh.dim() == 3:
            Element = ElementTetP1
        else:
            raise RuntimeError(f"Unsupported mesh dimension: {mesh.dim()}")

        basis = InteriorBasis(mesh, Element())

        # Construct element-wise permittivity
        eps_r = np.ones(mesh.nelements)
        use_mat = state.physics_config.get("use_material", False)

        if use_mat and hasattr(state, "materials"):
            for mat in state.materials:
                try:
                    val = float(mat.properties.get("relative_permittivity", 1.0))
                except ValueError:
                    val = 1.0
                if "All" in mat.domains:
                    eps_r[:] = val
                else:
                    for dom in mat.domains:
                        if hasattr(mesh, "subdomains") and dom in mesh.subdomains:
                            eps_r[mesh.subdomains[dom]] = val
        else:
            eps_r_str = state.physics_config.get("relative_permittivity", "1.0")
            try:
                val = float(eps_r_str)
            except ValueError:
                val = 1.0
            eps_r[:] = val

        # SI Units: Permittivity of free space
        epsilon_0 = 8.8541878128e-12  # F/m
        epsilon_qp = (eps_r * epsilon_0)[:, None]

        @BilinearForm
        def laplace(u, v, _):
            return epsilon_qp * dot(grad(u), grad(v))

        # Construct element-wise source from physics_features
        rho_el = np.zeros(mesh.nelements)
        if hasattr(state, "physics_features"):
            for feat in state.physics_features:
                if feat.kind == "charge_density":
                    val = float(feat.properties.get("value", 0.0))
                    if "All" in feat.domains:
                        rho_el[:] += val
                    else:
                        for dom in feat.domains:
                            if dom in mesh.subdomains:
                                rho_el[mesh.subdomains[dom]] += val

        rho_qp = rho_el[:, None]

        @LinearForm
        def source_term(v, _w):
            return rho_qp * v

        A = asm(laplace, basis)
        b = asm(source_term, basis)

        # Dirichlet and Neumann DOFs from named boundaries
        D_all: List[np.ndarray] = []
        x_known = np.zeros(basis.N)

        for bc in state.bc_items:
            bc_type = bc.kind
            for bname in bc.boundaries:
                if bname not in mesh.boundaries:
                    continue
                
                if bc_type in ("electric_potential", "ground"):
                    val = float(bc.properties.get("value", 0.0))
                    v_val = 0.0 if bc_type == "ground" else val
                    dofs = basis.get_dofs(mesh.boundaries[bname])
                    try:
                        idx = dofs.all()
                    except Exception:
                        idx = np.array(dofs)
                    D_all.append(idx)
                    x_known[idx] = v_val
                elif bc_type == "surface_charge_density":
                    val = float(bc.properties.get("value", 0.0))
                    f_basis = FacetBasis(mesh, Element(), facets=mesh.boundaries[bname])
                    @LinearForm
                    def flux_term(v, _w, val=val):
                        return val * v
                    b += asm(flux_term, f_basis)

        if D_all:
            D = np.unique(np.concatenate(D_all))
            if state.abort_check and state.abort_check():
                raise InterruptedError("Solve aborted by user.")
            if state.progress_callback:
                state.progress_callback(50)
            phi = solve(*condense(A, b, D=D, x=x_known))
        else:
            # Pin first DOF to avoid singularity for pure Neumann
            if state.abort_check and state.abort_check():
                raise InterruptedError("Solve aborted by user.")
            if state.progress_callback:
                state.progress_callback(50)
            phi = solve(*condense(A, b, D=np.array([0]), x=x_known))

        # Electric field E = -grad(phi); project to nodes
        pot_grad = basis.interpolate(phi).grad
        basis_vec = InteriorBasis(mesh, ElementVector(Element()))
        E_field = -basis_vec.project(pot_grad).reshape((mesh.dim(), -1), order='F')

        if mesh.dim() == 2:
            E_result = (E_field[0], E_field[1])
        else:
            E_result = (E_field[0], E_field[1], E_field[2])

        state.basis = basis
        state.results = {'phi': phi, 'E': E_result}
        
        if state.progress_callback:
            state.progress_callback(100)
            
        return state


# ── Auto-register on import ──────────────────────────────────────────────────
register_physics(ElectrostaticsDescriptor)
