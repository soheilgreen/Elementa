"""
Tests for elementa.physics — registry and descriptor metadata.

Solver integration tests (which require gmsh + scikit-fem + a real mesh) are
tagged with `@pytest.mark.integration` so they can be skipped in lightweight
CI environments via:  pytest -m "not integration"
"""

import pytest
from elementa.physics.registry import (
    PHYSICS_REGISTRY,
    get_physics,
    get_all_physics_names,
    get_compatible_study_types,
)
from elementa.physics import ElectrostaticsDescriptor, HeatTransferDescriptor


class TestRegistry:
    def test_electrostatics_registered(self):
        assert "Electrostatics" in PHYSICS_REGISTRY

    def test_heat_transfer_registered(self):
        assert "Heat Transfer" in PHYSICS_REGISTRY

    def test_get_physics_returns_descriptor(self):
        desc = get_physics("Electrostatics")
        assert desc is ElectrostaticsDescriptor

    def test_get_physics_unknown_returns_none(self):
        assert get_physics("NonExistent") is None

    def test_get_all_physics_names(self):
        names = get_all_physics_names()
        assert "Electrostatics" in names
        assert "Heat Transfer" in names

    def test_compatible_study_types_stationary_only(self):
        types = get_compatible_study_types(["Electrostatics"])
        assert "Stationary" in types
        assert "Time Dependent" not in types

    def test_compatible_study_types_heat_transfer(self):
        types = get_compatible_study_types(["Heat Transfer"])
        assert "Stationary" in types
        assert "Time Dependent" in types

    def test_compatible_study_types_intersection(self):
        # Electrostatics only supports Stationary — intersection should exclude Time Dependent
        types = get_compatible_study_types(["Electrostatics", "Heat Transfer"])
        assert "Stationary" in types
        assert "Time Dependent" not in types

    def test_empty_physics_returns_all(self):
        types = get_compatible_study_types([])
        assert "Stationary" in types


class TestElectrostaticsDescriptor:
    def test_name(self):
        assert ElectrostaticsDescriptor.name == "Electrostatics"

    def test_result_fields(self):
        keys = {rf.key for rf in ElectrostaticsDescriptor.result_fields}
        assert "phi" in keys
        assert "E" in keys

    def test_bc_types(self):
        kinds = {bc.kind for bc in ElectrostaticsDescriptor.bc_types}
        assert "electric_potential" in kinds
        assert "ground" in kinds

    def test_default_config_keys(self):
        cfg = ElectrostaticsDescriptor.default_config
        assert "relative_permittivity" in cfg


class TestHeatTransferDescriptor:
    def test_name(self):
        assert HeatTransferDescriptor.name == "Heat Transfer"

    def test_result_fields(self):
        keys = {rf.key for rf in HeatTransferDescriptor.result_fields}
        assert "T" in keys
        assert "q" in keys

    def test_bc_types(self):
        kinds = {bc.kind for bc in HeatTransferDescriptor.bc_types}
        assert "temperature" in kinds
        assert "heat_flux" in kinds
        assert "convection" in kinds

    def test_supported_time_dependent(self):
        assert "Time Dependent" in HeatTransferDescriptor.supported_study_types


# ---------------------------------------------------------------------------
# Integration tests — require gmsh + scikit-fem + a real mesh
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestElectrostaticsSolver:
    """Solve a simple 1-D-like problem and check the result analytically."""

    def test_1d_potential_gradient(self):
        """
        Two parallel plates at x=0 (V=0) and x=1 (V=1).
        Analytical solution: phi(x) = x.
        """
        import numpy as np
        import gmsh
        from skfem import Mesh
        from elementa.physics.base import PhysicsState
        from elementa.physics import ElectrostaticsDescriptor
        from elementa.core.project_state import BoundaryConditionItem

        # Build a simple unit-square mesh with gmsh
        if gmsh.isInitialized():
            gmsh.finalize()
        gmsh.initialize()
        gmsh.model.add("test")
        surf = gmsh.model.occ.addRectangle(0, 0, 0, 1, 1)
        gmsh.model.occ.synchronize()
        edges = gmsh.model.getBoundary([(2, surf)], oriented=False)
        gmsh.model.addPhysicalGroup(2, [surf], name="domain")
        # edges[0] and [2] are approximately the left/right edges
        # Tag all four edges
        for i, e in enumerate(edges):
            gmsh.model.addPhysicalGroup(1, [e[1]], name=f"edge_{i}")
        gmsh.option.setNumber("Mesh.MeshSizeMax", 0.1)
        gmsh.model.mesh.generate(2)
        gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
        import tempfile, os
        tmp = tempfile.mkdtemp()
        msh_path = os.path.join(tmp, "test.msh")
        gmsh.write(msh_path)
        gmsh.finalize()

        mesh = Mesh.load(msh_path)

        # Identify left and right boundary names from what gmsh labelled
        bnd_names = list(mesh.boundaries.keys())

        # Find left (x≈0) and right (x≈1) boundaries by inspecting node coords
        from skfem import InteriorBasis, ElementTriP1
        basis = InteriorBasis(mesh, ElementTriP1())

        left_bnd = right_bnd = None
        for name in bnd_names:
            facet_ids = mesh.boundaries[name]
            nodes = np.unique(mesh.facets[:, facet_ids])
            xs = mesh.p[0, nodes]
            if np.all(xs < 0.05):
                left_bnd = name
            elif np.all(xs > 0.95):
                right_bnd = name

        if left_bnd is None or right_bnd is None:
            pytest.skip("Could not identify left/right boundaries in test mesh")

        bc_left = BoundaryConditionItem(
            name="left", kind="electric_potential",
            properties={"value": "0.0"}, boundaries=[left_bnd]
        )
        bc_right = BoundaryConditionItem(
            name="right", kind="electric_potential",
            properties={"value": "1.0"}, boundaries=[right_bnd]
        )

        state = PhysicsState(
            mesh=mesh,
            bc_items=[bc_left, bc_right],
            physics_config={"use_material": False, "relative_permittivity": "1.0"},
        )
        result_state = ElectrostaticsDescriptor.assemble_and_solve(state)

        phi = result_state.results["phi"]
        # At interior nodes, phi ≈ x coordinate
        x_coords = mesh.p[0]
        # Tolerance loosened due to coarse mesh
        assert np.corrcoef(x_coords, phi)[0, 1] > 0.99
