from typing import Dict, List

import numpy as np
from skfem import *
from skfem.helpers import dot, grad

from .base import PhysicsState
from .registry import (
    PhysicsDescriptor, FeatureType, ResultField, DomainProperty, BoundaryConditionType,
    register_physics,
)


class HeatTransferDescriptor(PhysicsDescriptor):
    """Plugin descriptor for heat transfer physics."""

    name = "Heat Transfer"
    abbreviation = "ht"
    icon = "heat_transfer.png"
    bc_label = "Temperature (K)"
    supported_study_types = ["Stationary", "Time Dependent"]

    domain_properties = [
        DomainProperty("thermal_conductivity", "Thermal Conductivity (k)", "1.0", "W/(m·K)"),
        DomainProperty("density", "Density (ρ)", "1.0", "kg/m³"),
        DomainProperty("heat_capacity", "Heat Capacity (Cₚ)", "1.0", "J/(kg·K)"),
    ]

    bc_types = [
        BoundaryConditionType(
            "temperature", "Temperature",
            default_props={"value": "293.15"},
            prop_labels={"value": "Temperature (T) [K]"}
        ),
        BoundaryConditionType(
            "heat_flux", "Heat Flux",
            default_props={"value": "0.0"},
            prop_labels={"value": "Heat Flux (q) [W/m²]"}
        ),
        BoundaryConditionType(
            "convection", "Convection",
            default_props={"h": "10.0", "T_ext": "293.15"},
            prop_labels={"h": "Heat Transfer Coefficient (h) [W/m²K]", "T_ext": "External Temperature (T_ext) [K]"}
        ),
        BoundaryConditionType("thermal_insulation", "Thermal Insulation"),
    ]

    feature_types = [
        FeatureType(
            kind="heat_source",
            label="Heat Source",
            icon="heat_transfer.png",
            default_props={"value": "0.0"},
            default_domains=["All"],
            prop_labels={"value": "Heat Source (Q) [W/m\u00B3]"},
        ),
    ]

    result_fields = [
        ResultField(key="T", label="T (Temperature)", field_type="scalar", unit="K"),
        ResultField(key="q", label="q (Heat Flux)", field_type="vector", unit="W/m²"),
    ]

    default_config = {
        "use_material": False,
        "thermal_conductivity": "1.0",
        "density": "1.0",
        "heat_capacity": "1.0",
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

        # --- Element-wise material properties ---
        k_el = np.ones(mesh.nelements)
        rho_el = np.ones(mesh.nelements)
        cp_el = np.ones(mesh.nelements)
        use_mat = state.physics_config.get("use_material", False)

        if use_mat and hasattr(state, "materials"):
            for mat in state.materials:
                def _get(key, default=1.0):
                    try:
                        return float(mat.properties.get(key, default))
                    except ValueError:
                        return default

                k_val = _get("thermal_conductivity")
                rho_val = _get("density")
                cp_val = _get("heat_capacity")

                if "All" in mat.domains:
                    k_el[:] = k_val
                    rho_el[:] = rho_val
                    cp_el[:] = cp_val
                else:
                    for dom in mat.domains:
                        if hasattr(mesh, "subdomains") and dom in mesh.subdomains:
                            k_el[mesh.subdomains[dom]] = k_val
                            rho_el[mesh.subdomains[dom]] = rho_val
                            cp_el[mesh.subdomains[dom]] = cp_val
        else:
            try:
                k_el[:] = float(state.physics_config.get("thermal_conductivity", "1.0"))
            except ValueError:
                k_el[:] = 1.0
            try:
                rho_el[:] = float(state.physics_config.get("density", "1.0"))
            except ValueError:
                rho_el[:] = 1.0
            try:
                cp_el[:] = float(state.physics_config.get("heat_capacity", "1.0"))
            except ValueError:
                cp_el[:] = 1.0

        k_qp = k_el[:, None]

        @BilinearForm
        def stiffness(u, v, _):
            return k_qp * dot(grad(u), grad(v))

        # --- Volumetric heat source ---
        Q_el = np.zeros(mesh.nelements)
        if hasattr(state, "physics_features"):
            for feat in state.physics_features:
                if feat.kind == "heat_source":
                    val = float(feat.properties.get("value", 0.0))
                    if "All" in feat.domains:
                        Q_el[:] += val
                    else:
                        for dom in feat.domains:
                            if dom in mesh.subdomains:
                                Q_el[mesh.subdomains[dom]] += val

        Q_qp = Q_el[:, None]

        @LinearForm
        def source_term(v, _w):
            return Q_qp * v

        K = asm(stiffness, basis)
        f = asm(source_term, basis)

        # --- Dirichlet and Neumann boundary conditions ---
        D_all: List[np.ndarray] = []
        x_known = np.zeros(basis.N)

        for bc in state.bc_items:
            bc_type = bc.kind
            for bname in bc.boundaries:
                if bname not in mesh.boundaries:
                    continue
                
                if bc_type == "temperature":
                    val = float(bc.properties.get("value", 293.15))
                    dofs = basis.get_dofs(mesh.boundaries[bname])
                    try:
                        idx = dofs.all()
                    except Exception:
                        idx = np.array(dofs)
                    D_all.append(idx)
                    x_known[idx] = val
                elif bc_type == "heat_flux":
                    val = float(bc.properties.get("value", 0.0))
                    f_basis = FacetBasis(mesh, Element(), facets=mesh.boundaries[bname])
                    @LinearForm
                    def flux_term(v, _w, val=val):
                        return val * v
                    f += asm(flux_term, f_basis)
                elif bc_type == "convection":
                    f_basis = FacetBasis(mesh, Element(), facets=mesh.boundaries[bname])
                    try:
                        h_val = float(bc.properties.get("h", "10.0"))
                        text_val = float(bc.properties.get("T_ext", "293.15"))
                    except ValueError:
                        h_val, text_val = 10.0, 293.15 # Fallback
                        
                    @BilinearForm
                    def conv_stiffness(u, v, _w, h=h_val):
                        return h * u * v
                        
                    @LinearForm
                    def conv_source(v, _w, h=h_val, text=text_val):
                        return h * text * v
                        
                    K += asm(conv_stiffness, f_basis)
                    f += asm(conv_source, f_basis)

        if D_all:
            D = np.unique(np.concatenate(D_all))
        else:
            D = np.array([0])

        # --- Select solver based on study type ---
        if state.abort_check and state.abort_check():
            raise InterruptedError("Solve aborted by user.")

        if state.study_type == "Time Dependent":
            times, T_all = cls._solve_transient(basis, K, f, D, x_known, state, mesh, rho_el, cp_el)

            # Compute heat flux at each time step
            basis_vec = InteriorBasis(mesh, ElementVector(Element()))
            k_mean = float(np.mean(k_el))
            
            if state.progress_callback:
                state.progress_callback(80)
            
            q_all = []
            total_steps = len(T_all)
            for i, T_step in enumerate(T_all):
                if state.abort_check and state.abort_check():
                    raise InterruptedError("Solve aborted by user.")
                if state.progress_callback:
                    state.progress_callback(80 + int(20 * (i + 1) / total_steps))
                
                temp_grad = basis.interpolate(T_step).grad
                grad_T = -basis_vec.project(temp_grad).reshape((mesh.dim(), -1), order='F')
                q_field = k_mean * grad_T
                if mesh.dim() == 2:
                    q_all.append((q_field[0], q_field[1]))
                else:
                    q_all.append((q_field[0], q_field[1], q_field[2]))

            state.basis = basis
            state.results = {'T': T_all, 'q': q_all, 'times': times}
            
            if state.progress_callback:
                state.progress_callback(100)
        else:
            if state.abort_check and state.abort_check():
                raise InterruptedError("Solve aborted by user.")
            if state.progress_callback:
                state.progress_callback(50)
                
            T = solve(*condense(K, f, D=D, x=x_known))

            # --- Heat flux  q = -k * grad(T); mirrors electrostatics E-field pattern ---
            temp_grad = basis.interpolate(T).grad
            basis_vec = InteriorBasis(mesh, ElementVector(Element()))
            grad_T = -basis_vec.project(temp_grad).reshape((mesh.dim(), -1), order='F')

            # Apply average k scaling
            k_mean = float(np.mean(k_el))
            q_field = k_mean * grad_T

            if mesh.dim() == 2:
                q_result = (q_field[0], q_field[1])
            else:
                q_result = (q_field[0], q_field[1], q_field[2])

            state.basis = basis
            state.results = {'T': T, 'q': q_result}
            
            if state.progress_callback:
                state.progress_callback(100)

        return state

    @classmethod
    def _solve_transient(cls, basis, K, f, D, x_known, state, mesh, rho_el, cp_el):
        """Backward Euler time stepping for the heat equation.
        Returns (times, T_solutions) where both are lists."""
        tc = state.time_config
        t_start = tc.get("t_start", 0.0)
        t_end = tc.get("t_end", 1.0)
        dt = tc.get("dt", 0.1)

        if dt <= 0:
            raise RuntimeError("Time step dt must be positive.")

        total_time = t_end - t_start
        if total_time <= 0:
            total_time = 1.0 # fallback

        # Mass matrix: M_ij = integral(rho * Cp * phi_i * phi_j)
        rho_cp_qp = (rho_el * cp_el)[:, None]

        @BilinearForm
        def mass_form(u, v, _):
            return rho_cp_qp * u * v

        M = asm(mass_form, basis)

        # Initial condition: use boundary values, zero elsewhere
        T_old = np.copy(x_known)

        times = [t_start]
        T_solutions = [T_old.copy()]

        t = t_start
        if state.progress_callback:
            state.progress_callback(0)
            
        while t < t_end - 1e-14:
            if state.abort_check and state.abort_check():
                raise InterruptedError("Solve aborted by user.")
                
            t += dt
            # Backward Euler: (M/dt + K) T_new = M/dt T_old + f
            A = M / dt + K
            b = M @ T_old / dt + f
            T_new = solve(*condense(A, b, D=D, x=x_known))
            T_old = T_new

            times.append(round(t, 10))
            T_solutions.append(T_new.copy())
            
            if state.progress_callback:
                progress = int(((t - t_start) / total_time) * 80)
                state.progress_callback(min(max(progress, 0), 80))

        return times, T_solutions


# ── Auto-register on import ──────────────────────────────────────────────────
register_physics(HeatTransferDescriptor)
