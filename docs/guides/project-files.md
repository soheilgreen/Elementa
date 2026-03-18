# Project Files

Elementa saves and loads projects as `.elem` files — a ZIP archive containing all model data.

---

## File Format

An `.elem` file is a standard ZIP archive with the following contents:

| Entry | Description |
|-------|-------------|
| `state.json` | Full model state in JSON format |
| `mesh.msh` | gmsh mesh file (version 2.2), if mesh has been generated |
| `results.npz` | NumPy `.npz` archive of all result arrays, if solve has been run |

---

## `state.json` Structure

```json
{
  "settings": {
    "name": "MyProject",
    "space_dim": 2,
    "description": ""
  },
  "parameters": {
    "W": "0.1",
    "H": "0.05"
  },
  "geometry_items": [
    {"kind": "rectangle", "name": "domain", "params": {"dx": "W", "dy": "H", "cx": "0", "cy": "0"}}
  ],
  "boolean_operations": [],
  "selected_physics": ["Electrostatics"],
  "selected_study": "Stationary",
  "time_config": {"t_start": 0.0, "t_end": 1.0, "dt": 0.1},
  "bc_items": [
    {"name": "Ground 1", "kind": "ground", "properties": {}, "boundaries": ["domain_edge_0"]}
  ],
  "physics_config": {"use_material": false, "relative_permittivity": "1.0"},
  "plots": []
}
```

---

## Saving

**File → Save** (`Ctrl+S`) — saves to the current project path.  
**File → Save As** — prompts for a new path.

---

## Loading

**File → Open** (`Ctrl+O`) — opens a file dialog to select an `.elem` file.

On load, Elementa:
1. Resets the current state.
2. Parses `state.json` and reconstructs all model objects.
3. Extracts and loads `mesh.msh` via `skfem.Mesh.load()`.
4. Loads `results.npz` arrays back into the results dictionary.
5. Emits UI update signals so all panels refresh.

---

## Programmatic Access

You can inspect a project file without launching the GUI:

```python
import zipfile, json
import numpy as np

with zipfile.ZipFile("my_project.elem") as zf:
    state = json.loads(zf.read("state.json"))
    results = np.load(zf.open("results.npz"))

print(state["settings"]["name"])
print(results.files)          # e.g. ['phi', 'E']
phi = results["phi"]
```
