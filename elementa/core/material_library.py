from typing import Dict, Any

# A basic built-in library of common materials for FEM simulations.
# Properties are defined in standard SI units.
MATERIAL_LIBRARY: Dict[str, Dict[str, Any]] = {
    "Air": {
        "relative_permittivity": "1.0",
        "electrical_conductivity": "0.0",
        "thermal_conductivity": "0.025",
        "density": "1.225",
        "heat_capacity": "1006.0",
    },
    "Vacuum": {
        "relative_permittivity": "1.0",
        "electrical_conductivity": "0.0",
        "thermal_conductivity": "0.0",
        "density": "0.0",
        "heat_capacity": "0.0",
    },
    "Water": {
        "relative_permittivity": "80.1",
        "electrical_conductivity": "5.5e-6",
        "thermal_conductivity": "0.598",
        "density": "997.0",
        "heat_capacity": "4184.0",
    },
    "Silicon": {
        "relative_permittivity": "11.68",
        "electrical_conductivity": "1.56e-3",
        "thermal_conductivity": "148.0",
        "density": "2330.0",
        "heat_capacity": "710.0",
    },
    "Copper": {
        "relative_permittivity": "1.0",  # Conductors technically have infinite/undefined but 1.0 is a typical placeholder
        "electrical_conductivity": "5.96e7",
        "thermal_conductivity": "400.0",
        "density": "8960.0",
        "heat_capacity": "385.0",
    },
}

def get_library_material_names():
    return list(MATERIAL_LIBRARY.keys())

def get_material_properties(name: str):
    return MATERIAL_LIBRARY.get(name, {}).copy()
