"""
Tests for elementa.core.material_library.
"""

from elementa.core.material_library import (
    MATERIAL_LIBRARY,
    get_library_material_names,
    get_material_properties,
)


class TestMaterialLibrary:
    def test_built_in_materials_exist(self):
        names = get_library_material_names()
        for expected in ("Air", "Vacuum", "Water", "Silicon", "Copper"):
            assert expected in names

    def test_air_properties(self):
        props = get_material_properties("Air")
        assert float(props["relative_permittivity"]) == 1.0
        assert float(props["thermal_conductivity"]) > 0

    def test_copper_conductivity(self):
        props = get_material_properties("Copper")
        assert float(props["electrical_conductivity"]) > 1e6

    def test_unknown_material_returns_empty(self):
        props = get_material_properties("Unobtainium")
        assert props == {}

    def test_returns_copy(self):
        """Mutating the returned dict should not affect the library."""
        props = get_material_properties("Air")
        props["relative_permittivity"] = "999"
        original = get_material_properties("Air")
        assert original["relative_permittivity"] == "1.0"
